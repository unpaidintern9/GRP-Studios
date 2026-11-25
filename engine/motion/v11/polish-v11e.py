"""V11E: directional logo-only reflection card and restrained wordmark."""
import bpy,math,json,hashlib
from pathlib import Path
s=bpy.context.scene;s.frame_set(168)
ob=bpy.data.objects["V11D camera-reflected studio silk"];nt=ob.data.materials[0].node_tree;n,l=nt.nodes,nt.links
mix=next(k for k in n if k.type=="MIX_SHADER");prior=mix.inputs[0].links[0].from_socket
g=n.new("ShaderNodeNewGeometry");p=n.new("ShaderNodeSeparateXYZ");v=n.new("ShaderNodeSeparateXYZ");l.new(g.outputs["Position"],p.inputs[0]);l.new(g.outputs["Incoming"],v.inputs[0])
def m(op,a,b):
    k=n.new("ShaderNodeMath");k.operation=op
    for i,x in enumerate((a,b)):
        if isinstance(x,(int,float)):k.inputs[i].default_value=x
        else:l.new(x,k.inputs[i])
    return k.outputs[0]
def window(a,lo,hi,fade):
    left=n.new("ShaderNodeMapRange");left.clamp=True;left.interpolation_type="SMOOTHERSTEP";left.inputs["From Min"].default_value=lo;left.inputs["From Max"].default_value=lo+fade;l.new(a,left.inputs["Value"])
    right=n.new("ShaderNodeMapRange");right.clamp=True;right.interpolation_type="SMOOTHERSTEP";right.inputs["From Min"].default_value=hi-fade;right.inputs["From Max"].default_value=hi;right.inputs["To Min"].default_value=1;right.inputs["To Max"].default_value=0;l.new(a,right.inputs["Value"])
    return m("MULTIPLY",left.outputs["Result"],right.outputs["Result"])
# Project incident ray back onto the plane of the original logo.
ratio=m("DIVIDE",p.outputs["Z"],v.outputs["Z"])
x=m("SUBTRACT",p.outputs["X"],m("MULTIPLY",ratio,v.outputs["X"]))
y=m("SUBTRACT",p.outputs["Y"],m("MULTIPLY",ratio,v.outputs["Y"]))
f=m("MULTIPLY",window(x,-3.65,3.65,.22),window(y,-2.35,2.45,.22))
l.new(m("MULTIPLY",prior,f),mix.inputs[0])
# Lower warm text light, maintain bright actual metal reflection.
for ob in bpy.data.collections["V10 brand and stage"].objects:
    if ob.type=="LIGHT" and ob.name.startswith("V11 warm typography key"):
        a=ob.data.animation_data.action
        fs=getattr(a,"fcurves",None);curves=list(fs) if fs is not None and len(fs) else [fc for ly in a.layers for st in ly.strips for bag in st.channelbags for fc in bag.fcurves]
        for fc in curves:
            if fc.data_path=="energy":
                for k in fc.keyframe_points:k.co.y*=.62;k.handle_left.y*=.62;k.handle_right.y*=.62
                fc.update()
s.name="GRP V11E refined reflective cinema";s["creative_status"]="V11E native review proof, not approved";s.frame_set(168)
root=Path("/tmp/grp-v11");out=root/"v11e.blend"
if out.exists():raise RuntimeError("Preserve previous proof")
bpy.ops.wm.save_as_mainfile(filepath=str(out))
receipt=json.loads((root/"v11d-geometry.json").read_text())
receipt["geometrySourceSceneSha256"]=receipt["sceneSha256"];receipt["sceneSha256"]=hashlib.sha256(out.read_bytes()).hexdigest();receipt["lightingRevision"]="directional studio reflection card; reduced warm typography fill";(root/"v11e-geometry.json").write_text(json.dumps(receipt,indent=2));print("V11E_SCENE_PASS",receipt["sceneSha256"],flush=True)
