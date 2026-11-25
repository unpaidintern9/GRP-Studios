"""V12B: directional reflected light field for curved metal.
Keep the world dark for camera/diffuse rays; add broad and narrow glossy-only
lobes facing the monogram, away from the floor reflection direction.
"""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;s.frame_set(168)
root=Path("/tmp/grp-v12");out=root/"v12b.blend"
if out.exists():raise RuntimeError("Preserve earlier proof")
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
world=s.world;nt=world.node_tree;n,l=nt.nodes,nt.links
old=next(k for k in n if k.type=="OUTPUT_WORLD")
prior=old.inputs["Surface"].links[0].from_socket
coord=n.new("ShaderNodeTexCoord");ray=n.new("ShaderNodeLightPath")
def lobe(direction,lo,hi,color):
    d=n.new("ShaderNodeVectorMath");d.operation="DOT_PRODUCT";d.inputs[1].default_value=Vector(direction).normalized();l.new(coord.outputs["Normal"],d.inputs[0])
    r=n.new("ShaderNodeMapRange");r.clamp=True;r.interpolation_type="SMOOTHERSTEP";r.inputs["From Min"].default_value=lo;r.inputs["From Max"].default_value=hi;l.new(d.outputs["Value"],r.inputs["Value"])
    x=n.new("ShaderNodeVectorMath");x.operation="SCALE";x.inputs[0].default_value=color;l.new(r.outputs["Result"],x.inputs["Scale"]);return x.outputs["Vector"]
def add(a,b):
    k=n.new("ShaderNodeVectorMath");k.operation="ADD"
    for i,q in enumerate((a,b)):
        if isinstance(q,tuple):k.inputs[i].default_value=q
        else:l.new(q,k.inputs[i])
    return k.outputs["Vector"]
# A gentle cool base and a broad silver-white sweep across the metal's
# normals. Directional variation gives the crown a legible midtone, not glow.
color=add((.025,.034,.052),lobe((-.24,.30,.92),.20,.94,(.48,.57,.72)))
color=add(color,lobe((.52,.24,.82),.70,.99,(.68,.57,.44)))
color=add(color,lobe((-.70,.56,.43),.89,.999,(1.1,1.05,.94)))
bg=n.new("ShaderNodeBackground");bg.inputs["Strength"].default_value=1.;l.new(color,bg.inputs["Color"])
mix=n.new("ShaderNodeMixShader");l.new(ray.outputs["Is Glossy Ray"],mix.inputs[0]);l.new(prior,mix.inputs[1]);l.new(bg.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],old.inputs["Surface"])
for name in ("silver-monogram","gold-r"):
    p=next(k for k in bpy.data.objects[name].data.materials[0].node_tree.nodes if k.type=="BSDF_PRINCIPLED")
    p.inputs["Roughness"].default_value=.16 if name=="silver-monogram" else .17
    p.inputs["Metallic"].default_value=1.
# Reduce excessively bright warm reflected typography and keep the hero mark
# visually dominant. Still physical metal and real floor reflections.
for ob in bpy.data.collections["V10 brand and stage"].objects:
    if ob.type=="LIGHT" and ob.name.startswith("V11 warm typography key"):
        a=ob.data.animation_data.action
        fs=getattr(a,"fcurves",None)
        cs=list(fs) if fs is not None and len(fs) else [fc for ly in a.layers for st in ly.strips for bag in st.channelbags for fc in bag.fcurves]
        for fc in cs:
            if fc.data_path=="energy":
                for k in fc.keyframe_points:k.co.y*=.68;k.handle_left.y*=.68;k.handle_right.y*=.68
                fc.update()
s.name="GRP V12B sculpted metal and gradual Earth"
s["creative_status"]="V12B native review; creative acceptance pending"
s.frame_set(168);bpy.ops.wm.save_as_mainfile(filepath=str(out))
r=json.loads((root/"v12.json").read_text());r["parentSceneSha256"]=r["sceneSha256"];r["sceneSha256"]=digest(out);r["lookDevelopment"]="Glossy-only broad directional reflection field, physically curved silver and gold faces, reduced typography illumination";(root/"v12b.json").write_text(json.dumps(r,indent=2))
print("V12B_SCENE_PASS",r["sceneSha256"],flush=True)
