"""Native storyboard look development. No reference pixels, no flat logo overlay.
Five full-HD checkpoints; full motion is NOT approved by a render receipt.
"""
import bpy, math, hashlib, json, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gold_light_v02 import load_geometry, make_group, rectangle_light, aim, private_path, WORK, EXPECTED, world_point
from gold_light_v03 import keys, power, emission, curve, trim, reveal, srgb

OUT=WORK.parent/"gold-light-v04"/"lookdev"
FRAMES=(1,11,20,39,78)
REFERENCE="2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26"

def metal(name,gold):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*( (.82,.43,.095) if gold else (.72,.76,.82)),1)
    p.inputs["Metallic"].default_value=1
    p.inputs["Roughness"].default_value=.205 if gold else .19
    # Blender builds can expose either anisotropy socket name. Isotropic
    # metallic specular is valid if neither is available.
    for name in ("Anisotropic IOR Level","Anisotropic"):
        socket=p.inputs.get(name)
        if socket is not None:
            socket.default_value=.13
            break
    return m

def rect(name,loc,target,w,h,energy,color):
    return rectangle_light(name,loc,target,w,h,energy,color)

def bbox(group):
    pts=[world_point(x,y) for polygon in group["loops"] for x,y in polygon]
    return min(p[0] for p in pts),max(p[0] for p in pts),min(p[1] for p in pts),max(p[1] for p in pts)

def backdrop():
    # Actual geometry behind the logo, with stretched low-frequency blue
    # structure. Its shader is also visible in the polished stage reflections.
    bpy.ops.mesh.primitive_plane_add(size=60,location=(0,4,-9))
    ob=bpy.context.object;ob.name="Deep blue layered studio cyclorama"
    m=bpy.data.materials.new("Procedural obsidian cloud field");m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    uv=n.new("ShaderNodeTexCoord");v=n.new("ShaderNodeVectorMath");v.operation="MULTIPLY";v.inputs[1].default_value=(.13,.40,.2)
    l.new(uv.outputs["Object"],v.inputs[0])
    noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=1.9;noise.inputs["Detail"].default_value=3.2;noise.inputs["Roughness"].default_value=.65;l.new(v.outputs[0],noise.inputs["Vector"])
    ramp=n.new("ShaderNodeValToRGB");r=ramp.color_ramp
    for i,(at,c) in enumerate([(0.0,(.0009,.002,.004)),(.37,(.002,.006,.013)),(.56,(.008,.020,.042)),(.72,(.027,.067,.135)),(1,(.055,.12,.23))]):
        e=r.elements[0] if i==0 else r.elements[-1] if i==4 else r.elements.new(at);e.position=at;e.color=(*c,1)
    l.new(noise.outputs["Fac"],ramp.inputs[0])
    em=n.new("ShaderNodeEmission");em.inputs["Strength"].default_value=.75;l.new(ramp.outputs[0],em.inputs[0])
    out=n.new("ShaderNodeOutputMaterial");l.new(em.outputs[0],out.inputs["Surface"]);ob.data.materials.append(m)
    return ob

def stage(y):
    bpy.ops.mesh.primitive_plane_add(size=100,location=(0,y,0),rotation=(-math.pi/2,0,0))
    ob=bpy.context.object;ob.name="Polished reflective obsidian stage"
    m=bpy.data.materials.new("Dark navy polished stage");m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF");p.inputs["Base Color"].default_value=(.055,.073,.105,1)
    p.inputs["Metallic"].default_value=.78;p.inputs["Roughness"].default_value=.12
    ob.data.materials.append(m);return ob

def spot(name,loc,target,power_,color,size):
    d=bpy.data.lights.new(name,"SPOT");d.energy=power_;d.color=color;d.spot_size=size;d.spot_blend=.75;d.shadow_soft_size=.2
    ob=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(ob);ob.location=loc;aim(ob,target);return ob

def atmosphere(floor):
    # Local, bounded volume behind the object only. Does not fog the camera or
    # soften the logo faces. Real light scattering from two diagonal spots.
    bpy.ops.mesh.primitive_cube_add(size=2,location=(0,floor+3.5,-4))
    ob=bpy.context.object;ob.name="Localized blue atmosphere";ob.scale=(12,5,3)
    m=bpy.data.materials.new("Fine blue stage haze");m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    v=n.new("ShaderNodeVolumeScatter");v.inputs["Color"].default_value=(.27,.47,.8,1);v.inputs["Density"].default_value=.012;v.inputs["Anisotropy"].default_value=.35
    o=n.new("ShaderNodeOutputMaterial");l.new(v.outputs[0],o.inputs["Volume"]);ob.data.materials.append(m)
    spot("Diagonal blue atmosphere left",(-7,floor+7,-2),(2,floor+.4,-6),1500,(.20,.42,1),.68)
    spot("Diagonal blue atmosphere right",(6,floor+6,-2),(-3,floor+1,-7),1000,(.33,.55,1),.55)
    return ob

def cam_key(cam,f,pos,target,lens):
    pos=Vector(pos);target=Vector(target);z=(pos-target).normalized()
    x=Vector((0,1,0)).cross(z).normalized();y=z.cross(x).normalized()
    cam.location=pos;cam.rotation_mode="XYZ";cam.rotation_euler=Matrix((x,y,z)).transposed().to_euler("XYZ")
    cam.data.lens=lens;cam.data.dof.focus_distance=(pos-target).length
    for k in ("location","rotation_euler"):cam.keyframe_insert(data_path=k,frame=f)
    cam.data.keyframe_insert(data_path="lens",frame=f)
    cam.data.dof.keyframe_insert(data_path="focus_distance",frame=f)

def flare(camera):
    # Crisp horizontal core, narrow warm halo, separately controlled.
    from gold_light_v02 import optical_card
    for name,depth,sx,sy,color,pwr,spreadx,spready in [
      ("Fine opening amber aura",.6,.18,.012,(1,.29,.035),.6,.25,.13),
      ("Opening thin gold ray",.59,.25,.0012,(1,.55,.12),3.2,.37,.06),
      ("Small white gold center",.58,.029,.0032,(1,.85,.49),8,.17,.10)]:
        ob=optical_card(camera,name,depth,sx,sy,color,pwr,spreadx,spready)
        tree=ob.data.materials[0].node_tree;tree.animation_data_clear()
        control=next(x for x in tree.nodes if x.label=="Opening flare intensity")
        keys(control.outputs[0],[(1,1),(5,.7),(8,.12),(11,0),(120,0)])

def create_scene(g,sha):
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name="GRP V04 storyboard lighting and dimensional stage"
    s["geometry_sha256"]=sha;s["reference_sha256"]=REFERENCE;s["creative_status"]="unapproved look-development"
    s.render.engine="CYCLES";s.cycles.device="CPU";s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.045
    s.cycles.max_bounces=7;s.cycles.glossy_bounces=4;s.cycles.transparent_max_bounces=8;s.cycles.volume_bounces=1
    s.render.use_persistent_data=True;s.render.threads_mode="FIXED";s.render.threads=4
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=24;s.frame_start=1;s.frame_end=120
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.view_settings.view_transform="AgX"
    s.view_settings.exposure=-.35
    w=bpy.data.worlds.new("Deep blue low ambient");w.use_nodes=True;s.world=w
    w.node_tree.nodes.get("Background").inputs["Color"].default_value=(.035,.055,.10,1)
    w.node_tree.nodes.get("Background").inputs["Strength"].default_value=.18
    bounds={x["name"]:bbox(x) for x in g["groups"]}
    print("V04 geometry bounds:",bounds,flush=True)
    floor_y=min(v[2] for v in bounds.values())-.035
    mark_low=min(bounds["silver-monogram"][2],bounds["gold-r"][2])
    early_shift=floor_y+.045-mark_low
    groups={}
    for group in g["groups"]:
        name=group["name"];is_gold=EXPECTED[name][1]=="gold";mark=name in ("silver-monogram","gold-r")
        m=metal(name+" polished physically based metal",is_gold);ob=make_group(group,m)
        # True thick sidewalls: total extrusion is twice Blender curve extrude.
        ob.data.extrude=.24 if mark else .035;ob.data.bevel_depth=.028 if mark else .0022;ob.data.bevel_resolution=6
        for spline in ob.data.splines:spline.use_smooth=True
        groups[name]=ob
        if mark:
            for f,y in [(1,early_shift),(39,early_shift),(49,early_shift),(59,0),(120,0)]:
                ob.location.y=y;ob.keyframe_insert(data_path="location",frame=f)
            reveal(m,[(1,0),(6,0),(11,1),(120,1)])
        else:reveal(m,[(1,0),(49,0),(59,1),(120,1)])
    stage(floor_y);back=backdrop();haze=atmosphere(floor_y)
    # Prevent the dark scene from appearing behind the first isolated optical beat.
    for ob in (back,haze):
        ob.hide_render=True;ob.keyframe_insert(data_path="hide_render",frame=1)
        ob.hide_render=False;ob.keyframe_insert(data_path="hide_render",frame=11)
    camera=bpy.data.objects.new("Cinematic macro dolly",bpy.data.cameras.new("Physical focal lengths"));bpy.context.collection.objects.link(camera);s.camera=camera
    camera.data.sensor_width=36;camera.data.clip_start=.015;camera.data.dof.use_dof=False
    # Use the verified R outline itself to locate macro targets, not guessed letter positions.
    rg=next(x for x in g["groups"] if x["name"]=="gold-r");lo,hi,bot,top=bounds["gold-r"]
    points=[Vector(world_point(x,y,.21)) for poly in rg["loops"] for x,y in poly]
    upper=min(points,key=lambda p:(p.x-(lo+.65*(hi-lo)))**2+(p.y-(top-.12*(top-bot)))**2)
    bowl=min(points,key=lambda p:(p.x-(lo+.76*(hi-lo)))**2+(p.y-(bot+.62*(top-bot)))**2)
    lower=min(points,key=lambda p:(p.x-(lo+.88*(hi-lo)))**2+(p.y-(bot+.10*(top-bot)))**2)
    def macro(p,offset,lens,frame):
        target=Vector((p.x,p.y+early_shift,p.z));cam_key(camera,frame,target+Vector(offset),target,lens)
    macro(upper,(-.8,.38,1.12),75,1);macro(upper,(-.95,.32,.95),75,11)
    macro(bowl,(1.05,.32,1.65),65,20);macro(lower,(.72,.45,2.8),58,30)
    # Camera above the floor, aimed downward: floor occupies the lower third.
    mark_mid=(max(bounds["gold-r"][3],bounds["silver-monogram"][3])+mark_low)/2+early_shift
    cam_key(camera,39,(-2.3,floor_y+2.55,8.8),(0,mark_mid-.35,.0),50)
    cam_key(camera,49,(-.9,floor_y+3.0,10.6),(0,mark_mid-.4,.0),48)
    cam_key(camera,59,(-.4,floor_y+4.15,13.6),(0,-.48,0),48)
    cam_key(camera,78,(0,floor_y+4.10,14.1),(0,-.48,0),48)
    cam_key(camera,120,(0,floor_y+4.10,14.1),(0,-.48,0),48)
    # Contrasting broad cards and narrow strips make polished curved bevels and
    # deep sides read as metal rather than uniformly overexposed front surfaces.
    silver=rect("Broad cool silver key",(-4,4,5),(0,0,0),4.8,1.5,0,(.78,.87,1))
    edge=rect("Narrow white edge card",(3.2,2.9,1.9),(0,.1,0),.42,4.3,0,(.91,.96,1))
    gold=rect("Moving warm specular strip",(-1,2,2.2),(0,.1,0),2.8,.23,0,(1,.62,.24))
    fill=rect("Soft frontal reflection",(0,3.2,7),(0,0,0),5.5,2.6,0,(.82,.90,1))
    floor_l=rect("Gold reflected floor strip left",(-2.7,floor_y+.34,1.6),(-1.8,floor_y,3),1.1,.18,0,(1,.48,.12))
    floor_r=rect("Gold reflected floor strip right",(2.5,floor_y+.38,1.2),(1.8,floor_y,3),1.2,.16,0,(1,.56,.2))
    for light,curve_ in [(silver,[(1,0),(11,380),(20,420),(39,520),(78,420),(120,420)]),(edge,[(1,0),(11,240),(20,200),(39,220),(78,170),(120,170)]),(gold,[(1,0),(11,480),(20,680),(39,420),(78,290),(120,290)]),(fill,[(1,0),(20,90),(39,110),(59,300),(120,300)]),(floor_l,[(1,0),(30,0),(39,260),(78,200),(120,180)]),(floor_r,[(1,0),(30,0),(39,230),(78,180),(120,160)])]:power(light,curve_)
    for frame,p in [(11,upper),(20,bowl),(30,lower),(39,bowl),(78,upper),(120,upper)]:
        shift=early_shift if frame<=49 else 0
        gold.location=(p.x-.6,p.y+shift+.6,2.1);aim(gold,(p.x,p.y+shift,.2))
        gold.keyframe_insert(data_path="location",frame=frame);gold.keyframe_insert(data_path="rotation_quaternion",frame=frame)
    flare(camera)
    # Delicate later diagonal arc, in world space above the logo, not across text.
    mat,level=emission("Warm diagonal upper sweep",(1,.45,.10),1.5)
    trail=curve("Storyboard upper sweep",[(-6,2.0,.6),(-3.2,3.1,.6),(0,4.0,.6),(5,4.8,.6)],.003,mat)
    trim(trail,[(1,0,0),(59,0,0),(69,0,.55),(78,.15,.9),(88,1,1),(120,1,1)])
    keys(level,[(1,0),(59,0),(69,1.5),(78,.65),(88,0),(120,0)])
    s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();r=nt.nodes.new("CompositorNodeRLayers")
    gl=nt.nodes.new("CompositorNodeGlare");gl.glare_type="FOG_GLOW";gl.quality="HIGH"
    if "Threshold" in gl.inputs:gl.inputs["Threshold"].default_value=3.5
    if "Strength" in gl.inputs:gl.inputs["Strength"].default_value=.13
    out=nt.nodes.new("CompositorNodeComposite");nt.links.new(r.outputs["Image"],gl.inputs["Image"]);nt.links.new(gl.outputs["Image"],out.inputs["Image"])
    for frame,label in zip(FRAMES,("Isolated gold flare","Macro sidewall","Gold R contour","Reflective monogram stage","Final metallic lockup")):s.timeline_markers.new(label,frame=frame)
    return s,bounds

def main():
    if tuple(bpy.app.version)!=(4,5,17):raise RuntimeError("Expected Blender 4.5.17")
    g,sha=load_geometry();out=private_path(OUT);out.mkdir(parents=True,exist_ok=False)
    s,bounds=create_scene(g,sha)
    s.frame_set(78);bpy.ops.wm.save_as_mainfile(filepath=str(out/"gold-light-v04.blend"))
    # Validate native geometry, including actual Z thickness.
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    meshes=[]
    for name in EXPECTED:
        ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);mesh=ev.to_mesh()
        try:
            z=[p.co.z for p in mesh.vertices]
            if not z or not mesh.polygons or max(z)-min(z)<.04:raise RuntimeError("Insufficient native extrusion: "+name)
            meshes.append({"name":name,"faces":len(mesh.polygons),"depth":max(z)-min(z)})
        finally:ev.to_mesh_clear()
    images=[]
    for frame in FRAMES:
        s.frame_set(frame);dst=out/f"frame-{frame:03d}.png";s.render.filepath=str(dst)
        bpy.ops.render.render(write_still=True)
        images.append({"frame":frame,"file":dst.name,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest()})
    receipt={"status":"unapproved-v04-lookdev","version":bpy.app.version_string,"engine":"Cycles CPU","referenceSha256":REFERENCE,"geometrySha256":sha,"resolution":[1920,1080],"samples":24,"keyframes":images,"meshes":meshes,"background":"native procedural stage and bounded haze","creativeApproval":False}
    (out/"v04-receipt.json").write_text(json.dumps(receipt,indent=2))
if __name__=="__main__":main()
