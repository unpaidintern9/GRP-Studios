"""Reference-led native 3D motion study. No reference pixels in output.
Official traced logo is invariant; V02 is rejected. Preview only, not master.
"""
import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gold_light_v02 import load_geometry, make_group, material, rectangle_light, aim, private_path, WORK, EXPECTED

OUT=WORK.parent/"gold-light-v03"/"lookdev"
CHECKPOINTS=tuple(1+round(i*.4*24) for i in range(12))
# 50 genuine native frames at 10fps, sampling the 24fps master timeline.
PREVIEW=tuple(1+round(i*24/10) for i in range(50))
def linearize(v):
    v=v/255
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def srgb(rgb):return tuple(linearize(v) for v in rgb)
def keys(socket,values):
    for f,v in values:
        socket.default_value=v
        socket.keyframe_insert(data_path="default_value",frame=f)
def power(light,values):
    for f,v in values:
        light.data.energy=v;light.data.keyframe_insert(data_path="energy",frame=f)
def reveal(mat,values):
    n=mat.node_tree.nodes;l=mat.node_tree.links
    out=n.get("Material Output");metal=n.get("Principled BSDF")
    mix=n.new("ShaderNodeMixShader");transparent=n.new("ShaderNodeBsdfTransparent")
    l.new(transparent.outputs[0],mix.inputs[1]);l.new(metal.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs["Surface"])
    keys(mix.inputs[0],values)
def emission(name,color,strength):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    e=n.new("ShaderNodeEmission");e.inputs["Color"].default_value=(*color,1);e.inputs["Strength"].default_value=strength
    o=n.new("ShaderNodeOutputMaterial");l.new(e.outputs[0],o.inputs["Surface"])
    return m,e.inputs["Strength"]
def curve(name,points,radius,mat):
    c=bpy.data.curves.new(name,"CURVE");c.dimensions="3D";c.resolution_u=32;c.bevel_depth=radius;c.bevel_resolution=4
    sp=c.splines.new("BEZIER");sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type="AUTO";p.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(mat)
    return o
def trim(o,values):
    for f,a,b in values:
        o.data.bevel_factor_start=a;o.data.bevel_factor_end=b
        o.data.keyframe_insert(data_path="bevel_factor_start",frame=f);o.data.keyframe_insert(data_path="bevel_factor_end",frame=f)
def create_scene(g,sha):
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
    s.name="GRP Gold Light V03 — reference-led";s["geometry_sha256"]=sha;s["creative_status"]="unapproved motion study"
    s.render.engine="CYCLES";s.cycles.device="CPU";s.cycles.samples=12;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.08
    s.render.use_persistent_data=True;s.render.threads_mode="FIXED";s.render.threads=4
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=120
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.view_settings.view_transform="AgX"
    # Camera looks straight down -Z, +Y is screen up. No quaternion interpolation or roll.
    camera=bpy.data.objects.new("Locked upright camera",bpy.data.cameras.new("Locked 48mm"))
    bpy.context.collection.objects.link(camera);s.camera=camera;camera.data.lens=48;camera.data.sensor_width=36;camera.data.dof.use_dof=False
    camera.location=(0,0,17.8);camera.rotation_euler=(0,0,0)
    # Camera-ray-only deep navy gradient; illumination comes from physical cards.
    w=bpy.data.worlds.new("Obsidian blue studio");w.use_nodes=True;s.world=w;n=w.node_tree.nodes;l=w.node_tree.links;n.clear()
    ray=n.new("ShaderNodeLightPath");ambient=n.new("ShaderNodeBackground");ambient.inputs["Color"].default_value=(.12,.16,.22,1);ambient.inputs["Strength"].default_value=.035
    tc=n.new("ShaderNodeTexCoord");dot=n.new("ShaderNodeVectorMath");dot.operation="DOT_PRODUCT";dot.inputs[1].default_value=(0,0,-1);l.new(tc.outputs["Normal"],dot.inputs[0])
    ramp=n.new("ShaderNodeMapRange");ramp.inputs["From Min"].default_value=.93;ramp.inputs["From Max"].default_value=1.;ramp.inputs["To Min"].default_value=0;ramp.inputs["To Max"].default_value=1;l.new(dot.outputs["Value"],ramp.inputs["Value"])
    blend=n.new("ShaderNodeMixRGB");blend.inputs[1].default_value=(*srgb((0,6,14)),1);blend.inputs[2].default_value=(*srgb((5,15,25)),1);l.new(ramp.outputs[0],blend.inputs[0])
    bg=n.new("ShaderNodeBackground");l.new(blend.outputs[0],bg.inputs["Color"]);bg.inputs["Strength"].default_value=1
    mix=n.new("ShaderNodeMixShader");l.new(ray.outputs["Is Camera Ray"],mix.inputs[0]);l.new(ambient.outputs[0],mix.inputs[1]);l.new(bg.outputs[0],mix.inputs[2]);o=n.new("ShaderNodeOutputWorld");l.new(mix.outputs[0],o.inputs[0])
    groups={}
    timing={
      "gold-r":[(1,0),(10,0),(20,.35),(30,.92),(39,1),(120,1)],
      "silver-monogram":[(1,0),(20,0),(30,.08),(39,.65),(49,1),(120,1)],
      "silver-wordmark":[(1,0),(39,0),(49,.10),(59,.55),(69,1),(120,1)],
      "gold-descriptor":[(1,0),(59,0),(69,.7),(78,1),(120,1)]}
    for group in g["groups"]:
        name=group["name"];gold=EXPECTED[name][1]=="gold"
        m=material(name+" polished metal",(.83,.48,.13) if gold else (.72,.76,.82),.16,.21,.12 if gold else .08)
        # Broad specular gradients, no high contrast scratch marks.
        ob=make_group(group,m);ob.data.extrude=.055 if name in ("gold-r","silver-monogram") else .018
        # Slight bevel with more subdivisions; preserve source contours and validate visually.
        ob.data.bevel_depth=.009 if name in ("gold-r","silver-monogram") else .002;ob.data.bevel_resolution=5
        reveal(m,timing[name]);groups[name]=ob
    key=rectangle_light("Broad silver reflection",(-3,4,5),(0,0,0),6,2.5,0,(.87,.94,1))
    gold=rectangle_light("Moving gold grazing strip",(-3,1.8,2.3),(0,.5,0),2.6,.35,0,(1,.69,.31))
    rim=rectangle_light("Cool lower softbox",(1,-3,3.6),(0,0,0),5,.8,0,(.62,.76,1))
    front=rectangle_light("Controlled front reflection",(0,2.2,7),(0,0,0),6,3,0,(1,.97,.91))
    power(key,[(1,0),(20,0),(30,15),(39,230),(49,540),(78,510),(120,510)])
    power(gold,[(1,0),(10,0),(20,370),(30,640),(39,590),(78,440),(120,350)])
    power(rim,[(1,0),(30,0),(49,130),(78,230),(120,230)])
    power(front,[(1,0),(39,0),(59,250),(78,380),(120,380)])
    for f,x,y in [(1,-3,1.8),(20,-.8,2.1),(30,.4,2.2),(39,2.3,1.3),(78,-2.1,2.2),(92,.2,2.2),(120,1.5,2.1)]:
        gold.location=(x,y,2.3);aim(gold,(x*.45,.6,0));gold.keyframe_insert(data_path="location",frame=f);gold.keyframe_insert(data_path="rotation_quaternion",frame=f)
    # Reference square coordinates, centered into 16:9 without stretching.
    # The gold head moves from screen-left along a curved path into the R.
    def pt(x,y,z=.16):return ((x-179)*7.5/358,(179-y)*7.5/358,z)
    goldmat,strength=emission("Fine warm trail",(1,.42,.075),3.3)
    headmat,headpower=emission("White gold leading highlight",(1,.79,.42),9)
    trail=curve("Primary curved light path",[pt(x,y) for x,y in [(0,222),(28,212),(78,194),(137,185),(199,187),(235,199),(278,222),(328,225),(358,226)]],.009,goldmat)
    trim(trail,[(1,0,.075),(10,.02,.43),(20,.12,.72),(30,.35,1),(49,.70,1),(69,1,1),(120,1,1)])
    fine=curve("Secondary restrained arc",[pt(x,y,.14) for x,y in [(0,232),(80,202),(150,175),(230,190),(310,211),(358,216)]],.0025,goldmat)
    trim(fine,[(1,0,.12),(10,0,.7),(30,0,1),(69,.3,1),(92,1,1),(120,1,1)])
    head=curve("Travelling white gold core",[pt(x,y,.17) for x,y in [(0,222),(28,212),(78,194),(137,185),(199,187),(235,199),(278,222),(328,225),(358,226)]],.014,headmat)
    trim(head,[(1,.065,.085),(10,.40,.45),(20,.68,.73),(30,.95,1),(39,1,1),(120,1,1)])
    keys(strength,[(1,2.2),(20,3.3),(39,1.1),(69,.25),(92,0),(120,0)])
    keys(headpower,[(1,8),(20,11),(30,7),(39,0),(120,0)])
    s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();r=nt.nodes.new("CompositorNodeRLayers");gl=nt.nodes.new("CompositorNodeGlare");gl.glare_type="FOG_GLOW";gl.quality="HIGH"
    if "Threshold" in gl.inputs:gl.inputs["Threshold"].default_value=2
    if "Strength" in gl.inputs:gl.inputs["Strength"].default_value=.25
    out=nt.nodes.new("CompositorNodeComposite");nt.links.new(r.outputs["Image"],gl.inputs["Image"]);nt.links.new(gl.outputs["Image"],out.inputs["Image"])
    for f,lab in [(1,"Left gold sweep"),(20,"R lights"),(39,"Silver G/P reveal"),(59,"Wordmark reveal"),(69,"Descriptor"),(78,"Final traveling reflection"),(106,"Stable closing lockup")]:s.timeline_markers.new(lab,frame=f)
    return s
def main():
    if tuple(bpy.app.version)!=(4,5,17):raise RuntimeError("Expected Blender 4.5.17")
    g,sha=load_geometry();out=private_path(OUT);out.mkdir(parents=True,exist_ok=False);s=create_scene(g,sha)
    s.frame_set(106);bpy.ops.wm.save_as_mainfile(filepath=str(out/"gold-light-v03.blend"))
    s.render.resolution_percentage=100;s.render.resolution_x=640;s.render.resolution_y=360;s.cycles.samples=8
    frames=out/"frames";frames.mkdir()
    # Continuous motion review at 10fps, not image interpolation or a final master.
    for i,f in enumerate(PREVIEW):
        s.frame_set(f);s.render.filepath=str(frames/f"frame-{i:03d}.png");bpy.ops.render.render(write_still=True)
    receipt={"status":"native-v03-motion-study","version":bpy.app.version_string,"engine":"Cycles CPU","geometrySha256":sha,"referenceSha256":"cae1eae2d5d5aa4d0b68c222e8ae82e30e4a195435f0a66d44d769eb28ae2366","resolution":[640,360],"fps":10,"frameCount":50,"sampledMasterFrames":list(PREVIEW)}
    (out/"motion-receipt.json").write_text(json.dumps(receipt,indent=2))
if __name__=="__main__":main()
