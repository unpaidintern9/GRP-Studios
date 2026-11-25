"""V12C: retain macro chrome definition, lower the broad environment only
while the physical obsidian floor is visible. Preserve V12B native geometry,
lighting passes and 50-frame spatial reveal."""
import bpy, json,hashlib
from pathlib import Path
s=bpy.context.scene;s.frame_set(168)
root=Path("/tmp/grp-v12");out=root/"v12c.blend"
if out.exists():raise RuntimeError("Preserve previous proof")
nt=s.world.node_tree;output=next(n for n in nt.nodes if n.type=="OUTPUT_WORLD")
mix=output.inputs["Surface"].links[0].from_node
assert mix.type=="MIX_SHADER"
bg=mix.inputs[2].links[0].from_node
assert bg.type=="BACKGROUND"
def ease(a,b,f):
    u=max(0.,min(1.,(f-a)/(b-a)));return u*u*u*(10-15*u+6*u*u)
# Smoothly reduce only the glossy field when the stage enters. The original
# lights and genuine physical logo/floor reflections remain unaffected.
for f in range(1,169):
    bg.inputs["Strength"].default_value=1-.83*ease(43,56,f)+.63*ease(131,148,f)
    bg.inputs["Strength"].keyframe_insert("default_value",frame=f)
s.name="GRP V12C sculpted chrome and continuous horizon"
s["creative_status"]="V12C native review, not creative approval"
s.frame_set(168);bpy.ops.wm.save_as_mainfile(filepath=str(out))
r=json.loads((root/"v12b.json").read_text());r["parentSceneSha256"]=r["sceneSha256"];r["sceneSha256"]=hashlib.sha256(out.read_bytes()).hexdigest();r["stageLighting"]="Broad glossy world smoothly attenuated during physical floor sequence; restored after floor disappears";(root/"v12c.json").write_text(json.dumps(r,indent=2))
print("V12C_SCENE_PASS",r["sceneSha256"],flush=True)
