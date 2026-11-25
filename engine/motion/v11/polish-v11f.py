"""V11F production correction: fade studio silk off during floor reveal."""
import bpy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,"/tmp/grp-v11/repo/engine/motion/v11")
from motion_contract import ease
s=bpy.context.scene;s.frame_set(168)
nt=bpy.data.objects["V11D camera-reflected studio silk"].data.materials[0].node_tree
n,l=nt.nodes,nt.links;mix=next(k for k in n if k.type=="MIX_SHADER");prior=mix.inputs[0].links[0].from_socket
gain=n.new("ShaderNodeValue");gain.label="Clear reflective stage; reintroduce silk only after Earth arrives"
mul=n.new("ShaderNodeMath");mul.operation="MULTIPLY";l.new(prior,mul.inputs[0]);l.new(gain.outputs[0],mul.inputs[1]);l.new(mul.outputs[0],mix.inputs[0])
for f in range(1,169):
    # Keep macro silk, let real gold pools/metal reflections drive the stage.
    value=1-ease(60,78,f)+.58*ease(127,141,f)
    gain.outputs[0].default_value=value;gain.outputs[0].keyframe_insert("default_value",frame=f)
s.name="GRP V11F native refined chrome and Earth"
s["creative_status"]="V11F native review proof, owner approval pending"
s.frame_set(168)
root=Path("/tmp/grp-v11");out=root/"v11f.blend"
if out.exists():raise RuntimeError("Do not overwrite previous proof")
bpy.ops.wm.save_as_mainfile(filepath=str(out))
r=json.loads((root/"v11e-geometry.json").read_text());r["parentSceneSha256"]=r["sceneSha256"];r["sceneSha256"]=hashlib.sha256(out.read_bytes()).hexdigest();r["stageCorrection"]="Diagnostic frame 85 confirmed camera-reflected silk caused white slab. Card transparency eased to zero by f78 and retained through f127, then partially restored over Earth. Geometry unchanged."
(root/"v11f-geometry.json").write_text(json.dumps(r,indent=2));print("V11F_NATIVE_SCENE_PASS",r["sceneSha256"],flush=True)
