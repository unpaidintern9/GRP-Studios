import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;s.frame_set(168);cam=s.camera
def key(socket,values):
    for f,v in values:
        socket.default_value=v;socket.keyframe_insert("default_value",frame=f)
def mnode(n,l,op,a,b):
    k=n.new("ShaderNodeMath");k.operation=op
    for i,v in enumerate((a,b)):
        if isinstance(v,(int,float)):k.inputs[i].default_value=v
        else:l.new(v,k.inputs[i])
    return k.outputs[0]
# All optical cards use compact support at UV edges: zero opacity at every edge.
for ob in list(s.objects):
    if ob.type!="MESH" or ob.parent!=cam or not ob.data.materials:continue
    nt=ob.data.materials[0].node_tree
    if not nt:continue
    ctl=next((n for n in nt.nodes if n.label=="Opening flare intensity"),None)
    if not ctl:continue
    n,l=nt.nodes,nt.links
    mix=next((k for k in n if k.type=="MIX_SHADER"),None)
    if not mix or not mix.inputs[0].is_linked:continue
    prior=mix.inputs[0].links[0].from_socket
    xy=n.new("ShaderNodeSeparateXYZ");coord=n.new("ShaderNodeTexCoord");l.new(coord.outputs["UV"],xy.inputs[0])
    fades=[]
    for axis in ("X","Y"):
        u=xy.outputs[axis];v=mnode(n,l,"MINIMUM",u,mnode(n,l,"SUBTRACT",1,u))
        ramp=n.new("ShaderNodeMapRange");ramp.clamp=True;ramp.interpolation_type="SMOOTHERSTEP"
        ramp.inputs["From Max"].default_value=.20;l.new(v,ramp.inputs["Value"]);fades.append(ramp.outputs["Result"])
    l.new(mnode(n,l,"MULTIPLY",prior,mnode(n,l,"MULTIPLY",*fades)),mix.inputs[0])
    if ob.name.startswith("V10 sun"):
        em=next(k for k in n if k.type=="EMISSION")
        em.inputs["Strength"].default_value*=.58
        if "halo" in ob.name:
            ob.scale.x*=1.4;ob.scale.y*=1.7
            em.inputs["Strength"].default_value*=.55
        if "streak" in ob.name:
            ob.scale.x*=1.25
# Restore broad clean metal reflections and a legible lockup using physically lit surfaces.
brand=bpy.data.collections["V10 brand and stage"]
def area(name,pos,target,w,h,energy,color,beats):
    d=bpy.data.lights.new(name,"AREA");d.shape="RECTANGLE";d.size=w;d.size_y=h;d.color=color
    ob=bpy.data.objects.new(name,d);brand.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()
    ob.lightgroup="SilverKey"
    for f,v in beats:d.energy=energy*v;d.keyframe_insert("energy",frame=f)
    return ob
area("V10B broad frontal silk reflection",(-.8,1.4,6.5),(0,.2,0),8.5,5.5,1550,(.90,.94,1),[(1,0),(12,0),(29,.55),(43,.78),(57,.75),(71,.85),(85,1),(168,1)])
area("V10B warm lower fill",(1.2,-1.2,5),(0,-1.1,0),5,2.7,650,(1,.77,.43),[(1,0),(16,0),(29,1),(57,.4),(71,.4),(85,.85),(168,1)])
for name in ("silver-monogram","gold-r","silver-wordmark","gold-descriptor"):
    p=next(n for n in bpy.data.objects[name].data.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    p.inputs["Roughness"].default_value=.24 if name in ("silver-monogram","gold-r") else .30
    if name in ("silver-wordmark","gold-descriptor"):p.inputs["Metallic"].default_value=.72
for name in ("V10 amber softbox","V10 traveling narrow strip"):
    ob=bpy.data.objects.get(name)
    if not ob:continue
    a=ob.data.animation_data.action
    fs=getattr(a,"fcurves",None)
    curves=list(fs) if fs is not None and len(fs) else [fc for ly in a.layers for st in ly.strips for bag in st.channelbags for fc in bag.fcurves]
    for fc in curves:
        if fc.data_path=="energy":
            for k in fc.keyframe_points:k.co.y*=.65;k.handle_left.y*=.65;k.handle_right.y*=.65
            fc.update()
# Make the existing native tagline large enough to read within the real gap.
tag=bpy.data.objects["V06 closing tagline"];desc=bpy.data.objects["gold-descriptor"]
def ext(o):
    p=[world_to_camera_view(s,cam,o.matrix_world@Vector(v)) for v in o.bound_box]
    return min(v.x for v in p),max(v.x for v in p),min(v.y for v in p),max(v.y for v in p)
bpy.context.view_layer.update()
db=ext(desc);tb=ext(tag);gap=db[2]-.195
tag.data.size*=min(4.,max(1.,(gap-.018)/(tb[3]-tb[2])))
bpy.context.view_layer.update();tb=ext(tag);cur=(tb[2]+tb[3])/2;desired=(db[2]+.195)/2
tag.location.y+=.1;bpy.context.view_layer.update();bb=ext(tag);slope=((bb[2]+bb[3])/2-cur)/.1
tag.location.y-=.1;tag.location.y+=(desired-cur)/slope;bpy.context.view_layer.update();tb=ext(tag)
if tb[2]<.200 or tb[3]>db[2]-.005:raise RuntimeError("Tagline overlaps closing")
for n in s.node_tree.nodes:
    if n.type=="GLARE":
        n.inputs["Threshold"].default_value=2.6;n.inputs["Strength"].default_value=.13
    if n.type=="RGB":
        n.outputs[0].default_value=(.0014,.0035,.008,1)
# Reduce day-side wash while preserving real city-light texture.
sun=bpy.data.objects.get("V10 horizon solar illumination")
if sun:sun.data.energy=.75
planet=bpy.data.objects.get("V10 mapped night Earth")
if planet:
    p=next(n for n in planet.data.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    for n in planet.data.materials[0].node_tree.nodes:
        if n.type=="MATH" and n.operation=="MULTIPLY":
            for inp in n.inputs:
                if not inp.is_linked and abs(inp.default_value-3.6)<1e-4:inp.default_value=2.0
s.name="GRP V10B native cinematic review";s["creative_status"]="V10B requested native review render; not approved"
s.frame_set(168);bpy.ops.wm.save_as_mainfile(filepath="/tmp/grp-v10/v10b.blend")
print("V10B_CLOSING",json.dumps({"tagline_bounds":tb,"descriptor_bounds":db}),flush=True)
p=bpy.context.preferences.addons["cycles"].preferences;p.compute_device_type="OPTIX";p.get_devices()
if not any(d.type=="OPTIX" for d in p.devices):raise RuntimeError("No OptiX")
for d in p.devices:d.use=d.type=="OPTIX"
s.cycles.device="GPU";s.cycles.denoiser="OPTIX";s.cycles.use_denoising=True;s.cycles.samples=24;s.cycles.adaptive_threshold=.035
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.render.image_settings.color_depth="8"
out=Path("/tmp/grp-v10/b-check");out.mkdir(exist_ok=False)
for f in (29,85,127,141,155,168):
    s.frame_set(f);s.render.filepath=str(out/f"frame-{f:03}.png");bpy.ops.render.render(write_still=True)
print("V10B_CHECK_PASS",flush=True)
