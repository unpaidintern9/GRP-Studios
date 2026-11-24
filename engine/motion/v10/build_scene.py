"""V10 native reconstruction from immutable V09e geometry. No GPU provisioning.
Run with Blender 4.5.17: blender -b --factory-startup --python-exit-code 1
 --python build_scene.py -- PRIVATE_V09E.blend PRIVATE_OUTPUT.blend
Outputs projection/geometry receipt; no render or creative approval implied.
"""
import bpy, sys, math, json, hashlib
from pathlib import Path
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from shot_contract import *
from gold_light_v09 import monotone, linear_baked
from gold_light_v02 import rectangle_light, aim, optical_card
from gold_light_v03 import keys, power
from gold_light_v06_closing import planet_material, atmosphere_material

BASE="86ff34d0a65c2bac53317b0539537dc9dfea0163504d207fadc1ea3801e8ee00"
NAMES=("silver-monogram","gold-r","silver-wordmark","gold-descriptor")
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def geometry_signature():
    out={}
    for name in NAMES:
        o=bpy.data.objects[name];c=o.data
        data=[(sp.type,sp.use_cyclic_u,[(tuple(p.co),tuple(p.handle_left),tuple(p.handle_right),p.handle_left_type,p.handle_right_type) for p in sp.bezier_points]) for sp in c.splines]
        dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);m=ev.to_mesh()
        try:
            if not m.polygons:raise RuntimeError("Empty native fill "+name)
            # Include actual tessellated fill, not contour similarity alone.
            mesh=([tuple(v.co) for v in m.vertices],[tuple(p.vertices) for p in m.polygons])
            out[name]={"curves":hashlib.sha256(repr(data).encode()).hexdigest(),"mesh":hashlib.sha256(repr(mesh).encode()).hexdigest(),"faces":len(m.polygons)}
        finally:ev.to_mesh_clear()
    return out
def group_points(names):
    return [o.matrix_world @ Vector(p) for name in names for o in [bpy.data.objects[name]] for p in o.bound_box]
def extent(s,cam,pts):
    p=[world_to_camera_view(s,cam,v) for v in pts]
    if min(v.z for v in p)<=0:raise RuntimeError("Camera crosses logo")
    return min(v.x for v in p),max(v.x for v in p),min(v.y for v in p),max(v.y for v in p)
def pose(s,cam,target,d,yaw,pitch,roll,lens):
    ya,pi=map(math.radians,(yaw,pitch))
    cam.location=target+Vector((d*math.sin(ya)*math.cos(pi),d*math.sin(pi),d*math.cos(ya)*math.cos(pi)))
    aim(cam,target);cam.rotation_quaternion=cam.rotation_quaternion @ Quaternion((0,0,1),math.radians(roll))
    cam.data.lens=lens;cam.data.shift_x=cam.data.shift_y=0
    bpy.context.view_layer.update()
def solve(s,cam,pts,target,w,cx,cy,yaw,pitch,roll,lens):
    # Fit actual projected geometry. Shift is calibrated through Blender's
    # projection, avoiding hand-coded aspect/shift sign assumptions.
    span=max((p-target).length for p in pts);lo=max(.05,span*1.05);hi=max(10,span*100)
    for _ in range(48):
        mid=(lo+hi)/2;pose(s,cam,target,mid,yaw,pitch,roll,lens);b=extent(s,cam,pts)
        if b[1]-b[0]>w:lo=mid
        else:hi=mid
    d=hi;pose(s,cam,target,d,yaw,pitch,roll,lens)
    b=extent(s,cam,pts)
    for attr,axis,want in (("shift_x",0,cx),("shift_y",2,cy)):
        base=(b[axis]+b[axis+1])/2;setattr(cam.data,attr,.01);b2=extent(s,cam,pts)
        slope=((b2[axis]+b2[axis+1])/2-base)/.01
        if abs(slope)<1e-6:raise RuntimeError("Projection shift calibration failed")
        setattr(cam.data,attr,(want-base)/slope);b=extent(s,cam,pts)
    if abs(b[1]-b[0]-w)>.012:raise RuntimeError("Projection width mismatch")
    return d,b
def rebuild_camera(s):
    cam=s.camera;cam.animation_data_clear();cam.data.animation_data_clear();cam.data.sensor_fit="HORIZONTAL";cam.data.sensor_width=36;cam.data.clip_start=.01;cam.data.clip_end=1000
    cam.data.dof.focus_object=None;cam.rotation_mode="QUATERNION"
    shots=[];receipts=[]
    regions={"silver":(NAMES[0],),"gold":(NAMES[1],),"mark":NAMES[:2],"lockup":NAMES}
    for f,region,w,x,y,yaw,pitch,roll,lens in SHOTS:
        s.frame_set(f);pts=group_points(regions[region])
        target=Vector(tuple((min(p[i] for p in pts)+max(p[i] for p in pts))/2 for i in range(3)))
        if region=="silver":
            # Target an actual silver G shoulder, not the neighboring gold R.
            o=bpy.data.objects[NAMES[0]];v=[o.matrix_world@p.co for sp in o.data.splines for p in sp.bezier_points]
            x0=min(p.x for p in v);x1=max(p.x for p in v);y0=min(p.y for p in v);y1=max(p.y for p in v)
            anchor=min(v,key=lambda p:(p.x-(x0+.14*(x1-x0)))**2+(p.y-(y0+.82*(y1-y0)))**2)
            target=anchor.copy();target.z=max(p.z for p in pts)
            # A compact physical patch around the chosen shoulder, not a
            # projection fit to the combined G/P bounding box.
            h=(y1-y0)*.24
            pts=[target+Vector((dx*h,dy*h,0)) for dx in (-.5,.5) for dy in (-.5,.5)]
            w=.98
        elif region=="gold" and f==29:
            target.y+=.10*(max(p.y for p in pts)-min(p.y for p in pts))
        cx,cy=widescreen(x,y);d,b=solve(s,cam,pts,target,projected_width(w),cx,cy,yaw,pitch,roll,lens)
        if not bounds_ok(b,region):raise RuntimeError("Clipped full logo at "+str(f))
        shots.append((f,tuple(cam.location),cam.rotation_quaternion.copy(),lens,cam.data.shift_x,cam.data.shift_y,d))
        receipts.append({"frame":f,"region":region,"projected_bounds":list(b),"focus_distance":d})
    # Monotone location/lens/shift, quaternion slerp with eased continuous
    # timing; bake every native frame. Stable from f85 through the close.
    prev=None
    for f in range(1,TOTAL+1):
        i=next((i for i in range(len(shots)-1) if shots[i][0]<=f<=shots[i+1][0]),len(shots)-2)
        a,b=shots[i:i+2];u=(f-a[0])/(b[0]-a[0]);u=u*u*(3-2*u)
        cam.location=tuple(monotone([(p[0],p[1][j]) for p in shots],f) for j in range(3))
        q=a[2].slerp(b[2],u)
        if prev is not None and prev.dot(q)<0:q.negate()
        prev=q.copy();cam.rotation_quaternion=q
        for j,name in ((3,"lens"),(4,"shift_x"),(5,"shift_y")):setattr(cam.data,name,monotone([(p[0],p[j]) for p in shots],f));cam.data.keyframe_insert(name,frame=f)
        cam.data.dof.focus_distance=monotone([(p[0],p[6]) for p in shots],f)
        cam.data.dof.aperture_fstop=monotone([(1,16),(15,8),(43,11),(57,16),(168,16)],f)
        cam.data.dof.use_dof=10<=f<57
        for prop in ("focus_distance","aperture_fstop","use_dof"):cam.data.dof.keyframe_insert(prop,frame=f)
        for prop in ("location","rotation_quaternion"):cam.keyframe_insert(prop,frame=f)
    linear_baked(cam);linear_baked(cam.data)
    # Verify evaluated anchor frames after baking, not just the solver.
    for row in receipts:
        f=row["frame"];region=row["region"];s.frame_set(f)
        if region in ("mark","lockup"):
            b=extent(s,cam,group_points(regions[region]))
            if not bounds_ok(b,region):raise RuntimeError("Baked camera clips at "+str(f))
            row["baked_bounds"]=list(b)
    return receipts

def stage(s):
    # Restore the real stage V09 hid. Never change the verified contour mesh.
    for ob in list(s.objects):
        if ob.type=="LIGHT" or ob.name.startswith(("V09 deep stage","V09 bounded atmospheric","V06 physical night","V06 thin physical","Horizon ","Grounded gold","Late diagonal")):
            bpy.data.objects.remove(ob,do_unlink=True)
    s.frame_set(168);bpy.context.view_layer.update()
    bottom=min(p.y for p in group_points(NAMES));markbottom=min(p.y for p in group_points(NAMES[:2]))
    fy=bottom-.025
    for name in NAMES[:2]:
        ob=bpy.data.objects[name];ob.animation_data_clear();base=ob.location.copy()
        for f,k in [(1,1),(71,1),(85,0),(168,0)]:
            ob.location=base+Vector((0,(bottom-markbottom)*k,0));ob.keyframe_insert("location",frame=f)
    for name in NAMES:
        ob=bpy.data.objects[name];m=ob.data.materials[0];nt=m.node_tree;nt.animation_data_clear()
        mix=next(n for n in nt.nodes if n.type=="MIX_SHADER")
        keys(mix.inputs[0],[(1,0),(8,0),(15,1),(168,1)] if name in NAMES[:2] else WORDMARK)
        p=next(n for n in nt.nodes if n.type=="BSDF_PRINCIPLED")
        # Remove exaggerating micro-bump; preserve the verified geometry.
        for link in list(p.inputs["Normal"].links):nt.links.remove(link)
        for link in list(p.inputs["Roughness"].links):nt.links.remove(link)
        p.inputs["Roughness"].default_value=.19 if name in NAMES[:2] else .24
    floor=bpy.data.objects["Polished reflective obsidian stage"];floor.animation_data_clear();floor.hide_render=False;floor.location.y=fy
    m=bpy.data.materials.new("V10 polished dark stage");m.use_nodes=True;floor.data.materials.clear();floor.data.materials.append(m)
    nt=m.node_tree;n=nt.nodes;l=nt.links;p=n.get("Principled BSDF");p.inputs["Base Color"].default_value=(.026,.032,.043,1);p.inputs["Metallic"].default_value=.72;p.inputs["Roughness"].default_value=.105
    geo=n.new("ShaderNodeNewGeometry");dist=n.new("ShaderNodeVectorMath");dist.operation="DISTANCE";dist.inputs[1].default_value=(0,fy,0);l.new(geo.outputs["Position"],dist.inputs[0])
    fall=n.new("ShaderNodeMapRange");fall.clamp=True;fall.interpolation_type="SMOOTHERSTEP";fall.inputs["From Min"].default_value=5;fall.inputs["From Max"].default_value=23;fall.inputs["To Min"].default_value=1;fall.inputs["To Max"].default_value=0;l.new(dist.outputs["Value"],fall.inputs["Value"])
    fade=n.new("ShaderNodeMath");fade.operation="MULTIPLY";l.new(fall.outputs["Result"],fade.inputs[0]);keys(fade.inputs[1],FLOOR)
    tr=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader");l.new(fade.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get("Material Output").inputs["Surface"])
    world=bpy.data.worlds.new("V10 subtle midnight world");world.use_nodes=True;s.world=world;bg=world.node_tree.nodes.get("Background");bg.inputs["Color"].default_value=(.035,.052,.085,1);bg.inputs["Strength"].default_value=.23
    layer=bpy.context.view_layer
    for name in ("SilverKey","GoldKey","StageWarm","CoolRim","Travel"):
        if not layer.lightgroups.get(name):layer.lightgroups.add(name=name)
    def light(name,group,pos,target,w,h,e,c,beats):
        ob=rectangle_light(name,pos,target,w,h,0,c);ob.lightgroup=group;power(ob,[(f,e*k) for f,k in beats]);return ob
    main=((1,0),(8,0),(15,.75),(29,1),(168,1))
    light("V10 silver silkbox","SilverKey",(-4,4,4),(0,.5,0),4,2.5,790,(.83,.91,1),main)
    light("V10 amber softbox","GoldKey",(3,3,3),(0,.4,0),3,1.6,920,(1,.68,.28),((1,0),(15,.08),(29,1),(168,.75)))
    light("V10 blue edge","CoolRim",(4,3,-2),(0,0,0),2,4,480,(.34,.55,1),main)
    light("V10 long stage reflection","StageWarm",(-2,fy+1.7,2),(0,fy,0),.5,3.2,540,(1,.53,.16),((1,0),(43,0),(57,1),(113,1),(127,0),(168,0)))
    hot=light("V10 traveling narrow strip","Travel",(-3,2,1),(0,0,0),.18,2.8,1100,(1,.72,.31),((1,0),(15,.7),(29,1),(57,.8),(113,.6),(141,.15),(168,.15)))
    for f,pos,target in [(15,(-3,2,1),(-1,1,0)),(29,(2,2,2),(.6,1,0)),(43,(3,.1,2),(1,0,0)),(57,(-3,fy+.8,2),(0,fy,0)),(85,(3,fy+.7,2),(0,fy,0)),(113,(3,4,2),(0,1,0)),(168,(3,4,2),(0,1,0))]:
        hot.location=pos;aim(hot,target);hot.keyframe_insert("location",frame=f);hot.keyframe_insert("rotation_quaternion",frame=f)
    # Real low-density atmospheric depth behind the letters. Keep it away
    # from the lens and taper out its contribution before the Earth composite.
    bpy.ops.mesh.primitive_cube_add(size=2,location=(0,fy+3,-7))
    haze=bpy.context.object;haze.name="V10 soft bounded atmospheric depth";haze.scale=(12,6,4.5)
    m=bpy.data.materials.new("V10 subtle nonuniform volume");m.use_nodes=True;haze.data.materials.append(m)
    nt=m.node_tree;n=nt.nodes;l=nt.links;n.clear()
    coord=n.new("ShaderNodeTexCoord");noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=2.4;noise.inputs["Detail"].default_value=2
    l.new(coord.outputs["Generated"],noise.inputs["Vector"])
    remap=n.new("ShaderNodeMapRange");remap.inputs["To Min"].default_value=.2;remap.inputs["To Max"].default_value=1
    l.new(noise.outputs["Fac"],remap.inputs["Value"])
    density=n.new("ShaderNodeMath");density.operation="MULTIPLY";l.new(remap.outputs["Result"],density.inputs[0])
    keys(density.inputs[1],[(1,0),(15,.002),(43,.008),(57,.009),(113,.009),(127,0),(168,0)])
    volume=n.new("ShaderNodeVolumeScatter");volume.inputs["Color"].default_value=(.35,.50,.75,1);volume.inputs["Anisotropy"].default_value=.3;l.new(density.outputs[0],volume.inputs["Density"])
    output=n.new("ShaderNodeOutputMaterial");l.new(volume.outputs[0],output.inputs["Volume"])
    light("V10 atmosphere rim","CoolRim",(-5,fy+4,-5),(1,fy+1,-8),2,4,550,(.30,.49,.85),((1,0),(15,.12),(57,1),(113,.8),(127,0),(168,0)))
    return fy

def closing(s):
    # Separate Earth-only view layer: a fixed world-space sphere, not the
    # prior tiny camera-parented globe. No texture rights assumption.
    s.frame_set(168);cam=s.camera
    earth=bpy.data.collections.new("V10 independent horizon");s.collection.children.link(earth)
    def move(o):
        for c in list(o.users_collection):c.objects.unlink(o)
        earth.objects.link(o)
    radius=100;distance=185
    # Solve the actual top tangent using Blender's lens projection instead
    # of assuming angle_y uses the active 16:9 sensor fit.
    lo,hi=-.8,.8
    for _ in range(48):
        a=(lo+hi)/2
        p=cam.matrix_world @ Vector((0,math.tan(a),-1))
        if world_to_camera_view(s,cam,p).y<.23:lo=a
        else:hi=a
    theta=(lo+hi)/2
    check=world_to_camera_view(s,cam,cam.matrix_world @ Vector((0,math.tan(theta),-1))).y
    if abs(check-.23)>1e-5:raise RuntimeError("Horizon tangent projection failed")
    phi=theta-math.asin(radius/distance)
    center=cam.matrix_world@Vector((0,distance*math.sin(phi),-distance*math.cos(phi)))
    for name,r,mat in [("V10 procedural night world",radius,planet_material()),("V10 thin atmosphere",radius+.23,atmosphere_material())]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=256,ring_count=128,radius=r,location=center)
        ob=bpy.context.object;ob.name=name;ob.data.materials.append(mat);move(ob)
        for p in ob.data.polygons:p.use_smooth=True
    # Warm sunrise is an original optical effect in the independent layer.
    for name,depth,w,h,c,e in [("V10 sun core",.65,.035,.013,(1,.85,.55),8),("V10 sun streak",.66,.23,.003,(1,.56,.17),4),("V10 sun halo",.67,.13,.043,(1,.39,.09),1.8)]:
        ob=optical_card(cam,name,depth,w,h,c,e,.3,.22);move(ob);ob.location.y=depth*math.tan(theta)
        nt=ob.data.materials[0].node_tree;nt.animation_data_clear();ctl=next(n for n in nt.nodes if n.label=="Opening flare intensity");keys(ctl.outputs[0],SUN)
    tag=bpy.data.objects["V06 closing tagline"];tag.animation_data_clear();tag.data.size=.205
    # Set above horizon, below descriptor. Keep actual campaign typography.
    bottom=min(p.y for p in group_points((NAMES[3],)));tag.location.y=bottom-.35
    nt=tag.data.materials[0].node_tree;nt.animation_data_clear();mix=next(n for n in nt.nodes if n.type=="MIX_SHADER");keys(mix.inputs[0],TAG)
    # Explicit isolation even when a recovered scene links geometry directly
    # to the scene root. The camera is the only object shared by both layers.
    brand_collection=bpy.data.collections.new("V10 brand and stage");s.collection.children.link(brand_collection)
    if cam.name not in s.collection.objects:s.collection.objects.link(cam)
    for ob in list(s.objects):
        if ob==cam or ob.name in earth.objects:continue
        for c in list(ob.users_collection):c.objects.unlink(ob)
        brand_collection.objects.link(ob)
    main=bpy.context.view_layer;main.name="BrandStage";layer=s.view_layers.new("Earth")
    main.layer_collection.children[earth.name].exclude=True
    for c in layer.layer_collection.children:
        if c.name!=earth.name:c.exclude=True
    bpy.context.view_layer.update()
    if any(name in layer.objects for name in NAMES):raise RuntimeError("Brand leaked into Earth layer")
    # Existing opening optical geometry stays in stage, reset to ignition f1.
    for ob in s.objects:
        if ob.parent==cam and ob.name not in earth.objects and ob.type=="MESH" and ob.data.materials:
            nt=ob.data.materials[0].node_tree
            ctl=next((n for n in nt.nodes if n.label=="Opening flare intensity"),None) if nt else None
            if ctl:nt.animation_data_clear();keys(ctl.outputs[0],[(1,1),(7,.6),(15,0),(168,0)])
    s.render.film_transparent=True
    main.use_pass_cryptomatte_object=True;main.use_pass_cryptomatte_material=True
    for v in (main,layer):
        v.use_pass_z=True;v.use_pass_normal=True;v.use_pass_emit=True;v.use_pass_glossy_direct=True;v.use_pass_glossy_indirect=True;v.cycles.denoising_store_passes=True
    s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
    brand=n.new("CompositorNodeRLayers");brand.layer=main.name
    globe=n.new("CompositorNodeRLayers");globe.layer=layer.name
    bg=n.new("CompositorNodeRGB");bg.outputs[0].default_value=(.004,.009,.019,1)
    over=n.new("CompositorNodeAlphaOver");l.new(bg.outputs[0],over.inputs[1]);l.new(globe.outputs["Image"],over.inputs[2]);keys(over.inputs[0],EARTH)
    mix=n.new("CompositorNodeAlphaOver");mix.inputs[0].default_value=1;l.new(over.outputs[0],mix.inputs[1]);l.new(brand.outputs["Image"],mix.inputs[2])
    glare=n.new("CompositorNodeGlare");glare.glare_type="FOG_GLOW";glare.quality="HIGH";l.new(mix.outputs[0],glare.inputs["Image"])
    # Blender 4.5 exposes glare controls as sockets; no silent fallback.
    glare.inputs["Threshold"].default_value=1.8;glare.inputs["Strength"].default_value=.25
    out=n.new("CompositorNodeComposite");l.new(glare.outputs["Image"],out.inputs["Image"])
    return {"earth_center":list(center),"radius":radius,"horizon_target_y":.23,"horizon_projected_tangent_y":check,"procedural_not_geographic":True}

def main():
    if tuple(bpy.app.version)!=(4,5,17):raise RuntimeError("Pinned Blender 4.5.17 required")
    src,dst=map(Path,sys.argv[sys.argv.index("--")+1:]);src=src.resolve();dst=dst.resolve()
    if src==dst or dst.exists():raise RuntimeError("Preserve original and prior candidate")
    if digest(src)!=BASE:raise RuntimeError("Wrong V09e baseline digest")
    bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;s.frame_set(168);before=geometry_signature()
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=168
    stage(s);projection=rebuild_camera(s);environment=closing(s)
    s.frame_set(168);after=geometry_signature()
    if before!=after:raise RuntimeError("Verified logo geometry mutated")
    s.render.engine="CYCLES";s.view_settings.view_transform="AgX";s.render.image_settings.file_format="OPEN_EXR_MULTILAYER";s.render.image_settings.color_depth="16";s.render.image_settings.exr_codec="ZIP";s.cycles.samples=64;s.cycles.adaptive_threshold=.02
    s["creative_status"]="V10 source candidate, not approved";s["reference_sha256"]="2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26"
    dst.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(dst))
    dst.with_suffix(".json").write_text(json.dumps({"baseline_sha256":BASE,"candidate_sha256":digest(dst),"geometry":after,"projection":projection,"environment":environment,"native_render":False,"creative_approval":False},indent=2))
if __name__=="__main__":main()
