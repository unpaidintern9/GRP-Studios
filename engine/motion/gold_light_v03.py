"""Reference-led native 3D motion study. No reference pixels in output.
Official traced logo is invariant; V02 is rejected. Preview only, not master.
"""
import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gold_light_v02 import load_geometry, make_group, material, rectangle_light, aim, private_path, WORK, EXPECTED, optical_card

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
def camera_track(camera):
    # Positions and targets in original logo world coordinates; fixed world-Y
    # up vector avoids the unwanted roll of V02's quaternion camera.
    shots=[
      (1,(-.75,1.6,2.9),(-.35,1.45,.15),64,9),
      (11,(-.85,1.7,2.25),(-.10,1.45,.19),78,3.5),
      (20,(1.05,1.45,3.05),(.42,1.12,.12),68,4.5),
      (30,(.45,.45,5.0),(.38,.92,.05),58,5.6),
      (39,(-1.25,-.32,8.4),(0,1.03,.03),52,7.1),
      (49,(-.55,-.20,10.7),(0,.80,.03),48,8.0),
      (59,(-.18,-.35,13.8),(0,.08,.03),48,9.0),
      (78,(0,-.30,14.5),(0,.05,.03),48,10),
      (88,(0,-.24,14.7),(0,.05,.03),48,11),
      (120,(0,-.24,14.7),(0,.05,.03),48,11)]
    prev=None
    for frame in range(1,121):
        a,b=next((shots[i],shots[i+1]) for i in range(len(shots)-1) if shots[i][0]<=frame<=shots[i+1][0])
        t=(frame-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
        pos=Vector(a[1]).lerp(Vector(b[1]),t);target=Vector(a[2]).lerp(Vector(b[2]),t)
        z=(pos-target).normalized();x=Vector((0,1,0)).cross(z).normalized();y=z.cross(x).normalized()
        rot=Matrix((x,y,z)).transposed().to_euler("XYZ")
        if prev is not None:rot.make_compatible(prev)
        prev=rot.copy();camera.location=pos;camera.rotation_mode="XYZ";camera.rotation_euler=rot
        camera.data.lens=a[3]+t*(b[3]-a[3]);camera.data.dof.focus_distance=(pos-target).length
        camera.data.dof.aperture_fstop=a[4]+t*(b[4]-a[4])
        for path in ("location","rotation_euler"):camera.keyframe_insert(data_path=path,frame=frame)
        camera.data.keyframe_insert(data_path="lens",frame=frame)
        for path in ("focus_distance","aperture_fstop"):camera.data.dof.keyframe_insert(data_path=path,frame=frame)
def create_scene(g,sha):
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
    s.name="GRP Gold Light V03 — cinematic storyboard";s["geometry_sha256"]=sha;s["creative_status"]="unapproved motion study"
    s.render.engine="CYCLES";s.cycles.device="CPU";s.cycles.samples=12;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.08
    s.render.use_persistent_data=True;s.render.threads_mode="FIXED";s.render.threads=4
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=120
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.view_settings.view_transform="AgX"
    camera=bpy.data.objects.new("Storyboard macro-to-wide camera",bpy.data.cameras.new("Cinematic lens"))
    bpy.context.collection.objects.link(camera);s.camera=camera;camera.data.sensor_width=36;camera.data.clip_start=.015;camera.data.dof.use_dof=True
    camera_track(camera)
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
      "gold-r":[(1,0),(6,0),(11,1),(120,1)],
      "silver-monogram":[(1,0),(6,0),(11,1),(120,1)],
      "silver-wordmark":[(1,0),(49,0),(59,1),(120,1)],
      "gold-descriptor":[(1,0),(49,0),(59,1),(120,1)]}
    for group in g["groups"]:
        name=group["name"];gold=EXPECTED[name][1]=="gold"
        m=material(name+" polished metal",(.86,.49,.12) if gold else (.76,.80,.86),.14,.19,.18 if gold else .1)
        # Broad specular gradients, no high contrast scratch marks.
        ob=make_group(group,m);ob.data.extrude=.15 if name in ("gold-r","silver-monogram") else .027
        # Slight bevel with more subdivisions; preserve source contours and validate visually.
        ob.data.bevel_depth=.018 if name in ("gold-r","silver-monogram") else .0025;ob.data.bevel_resolution=6
        reveal(m,timing[name]);groups[name]=ob
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,-2.92,0),rotation=(-math.pi/2,0,0))
    floor=bpy.context.object;floor.name="Obsidian reflective stage"
    fm=bpy.data.materials.new("Polished obsidian floor");fm.use_nodes=True
    p=fm.node_tree.nodes.get("Principled BSDF");p.inputs["Base Color"].default_value=(.016,.024,.043,1);p.inputs["Metallic"].default_value=.8;p.inputs["Roughness"].default_value=.17
    floor.data.materials.append(fm)
    key=rectangle_light("Broad silver reflection",(-3,4,5),(0,0,0),6,2.5,0,(.87,.94,1))
    gold=rectangle_light("Moving gold grazing strip",(-3,1.8,2.3),(0,.5,0),2.6,.35,0,(1,.69,.31))
    rim=rectangle_light("Cool lower softbox",(1,-3,3.6),(0,0,0),5,.8,0,(.62,.76,1))
    front=rectangle_light("Controlled front reflection",(0,2.2,7),(0,0,0),6,3,0,(1,.97,.91))
    power(key,[(1,0),(6,0),(11,350),(20,450),(30,530),(39,760),(59,660),(120,590)])
    power(gold,[(1,0),(6,0),(11,650),(20,1050),(30,820),(39,760),(59,500),(78,440),(120,320)])
    power(rim,[(1,0),(6,0),(11,130),(30,240),(39,380),(59,300),(120,270)])
    power(front,[(1,0),(39,0),(59,250),(78,380),(120,380)])
    for f,x,y in [(1,-3,1.8),(20,-.8,2.1),(30,.4,2.2),(39,2.3,1.3),(78,-2.1,2.2),(92,.2,2.2),(120,1.5,2.1)]:
        gold.location=(x,y,2.3);aim(gold,(x*.45,.6,0));gold.keyframe_insert(data_path="location",frame=f);gold.keyframe_insert(data_path="rotation_quaternion",frame=f)
    ground=rectangle_light("Gold floor reflection",(-1.2,-2.3,1.6),(0,-2.92,1.1),2.2,.28,0,(1,.53,.16))
    power(ground,[(1,0),(30,0),(39,300),(59,190),(78,90),(120,40)])
    # Opening centered gold optical flare, then true specular metal highlights.
    for name,depth,sx,sy,col,pow_,spreadx,spready in [
      ("Opening amber halo",.6,.25,.032,(1,.26,.035),1.4,.27,.18),
      ("Opening gold hairline",.59,.35,.0028,(1,.55,.10),9,.44,.08),
      ("Opening white-gold core",.58,.075,.009,(1,.86,.48),16,.19,.12)]:
        ob=optical_card(camera,name,depth,sx,sy,col,pow_,spreadx,spready)
        tree=ob.data.materials[0].node_tree
        control=next(x for x in tree.nodes if x.label=="Opening flare intensity")
        tree.animation_data_clear()
        keys(control.outputs[0],[(1,1),(5,.85),(8,.24),(11,0),(120,0)])
    mat,strength=emission("Fine gold atmosphere sweep",(1,.49,.12),2.3)
    trail=curve("Upper trailing light arc",[(-5,.9,.8),(-3,2.5,.8),(-1,3.45,.9),(2,3.75,1),(5,3.9,1.1)],.004,mat)
    trim(trail,[(1,0,0),(62,0,0),(69,0,.28),(78,.35,.78),(87,1,1),(120,1,1)])
    keys(strength,[(1,0),(62,0),(69,2.3),(78,1.4),(87,0),(120,0)])
    s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();r=nt.nodes.new("CompositorNodeRLayers");gl=nt.nodes.new("CompositorNodeGlare");gl.glare_type="FOG_GLOW";gl.quality="HIGH"
    if "Threshold" in gl.inputs:gl.inputs["Threshold"].default_value=2
    if "Strength" in gl.inputs:gl.inputs["Strength"].default_value=.25
    out=nt.nodes.new("CompositorNodeComposite");nt.links.new(r.outputs["Image"],gl.inputs["Image"]);nt.links.new(gl.outputs["Image"],out.inputs["Image"])
    for f,lab in [(1,"Centered gold flare"),(11,"Metal edge macro"),(20,"Gold R surface"),(30,"Dimensional R"),(39,"Monogram over reflective floor"),(49,"Pullback"),(59,"Complete wordmark"),(69,"Upper gold sweep"),(88,"Metallic closing hold")]:s.timeline_markers.new(lab,frame=f)
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
    receipt={"status":"native-v03-motion-study","version":bpy.app.version_string,"engine":"Cycles CPU","geometrySha256":sha,"referenceSha256":"2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26","resolution":[640,360],"fps":10,"frameCount":50,"sampledMasterFrames":list(PREVIEW)}
    (out/"motion-receipt.json").write_text(json.dumps(receipt,indent=2))
if __name__=="__main__":main()
