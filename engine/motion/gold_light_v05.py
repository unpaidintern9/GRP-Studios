"""Native V05 motion proof: bounded, actual 24 FPS, no generated logo.
V04 stage is deliberately restaged. Reference pixels are never used.
"""
import bpy, math, hashlib, json, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gold_light_v02 import load_geometry, private_path, WORK, EXPECTED, world_point, UNITS_PER_PIXEL, rectangle_light, aim
from gold_light_v04 import create_scene as base_scene, bbox
from gold_light_v03 import power, keys

OUT=WORK.parent/"gold-light-v05"/"lookdev"
REFERENCE="2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26"
FRAMES=tuple(range(1,121))
SIZE=(768,432)
SAMPLES=6

def refined_curves(g):
    # Bounded cubic handles: each control point stays within a .45-source-pixel
    # corridor around its original segment. Cubic convex hull bounds deviation.
    # Corners stay vector/straight, smooth bends use common tangent directions.
    # Every original contour vertex and topology remains unchanged.
    max_offset=0.;points=0
    for group in g["groups"]:
        ob=bpy.data.objects[group["name"]];c=ob.data;c.splines.clear()
        c.resolution_u=6;c.render_resolution_u=6
        c.bevel_depth=.042 if group["name"] in ("silver-monogram","gold-r") else .0028
        c.bevel_resolution=8
        for poly in group["loops"]:
            coords=[Vector(world_point(x,y)) for x,y in poly];n=len(coords)
            sp=c.splines.new("BEZIER");sp.bezier_points.add(n-1);sp.use_cyclic_u=True;sp.use_smooth=True
            for i,p in enumerate(sp.bezier_points):
                a,b,d=coords[i-1],coords[i],coords[(i+1)%n]
                u=b-a;v=d-b
                if min(u.length,v.length)<1e-8:raise RuntimeError("Duplicate contour point")
                U=u.normalized();V=v.normalized()
                tangent=(U+V).normalized() if U.dot(V)>.82 else None
                def handle(seg,unit):
                    nonlocal max_offset
                    if tangent is None:return unit*seg.length/3
                    # Positive projection and bounded lateral departure.
                    deviation=(tangent-unit*tangent.dot(unit)).length
                    h=tangent*min(seg.length/3,.45*UNITS_PER_PIXEL/max(deviation,1e-8))
                    max_offset=max(max_offset,(h-unit*h.dot(unit)).length/UNITS_PER_PIXEL)
                    return h
                p.co=b;p.handle_left_type="FREE";p.handle_right_type="FREE"
                p.handle_left=b-handle(u,U);p.handle_right=b+handle(v,V)
                points+=1
    if max_offset>.450001:raise RuntimeError("Spline corridor exceeded")
    return {"originalContourVertices":points,"maxControlDeviationPixels":max_offset,"topologyPreserved":True}

def clear_animation(obj):
    obj.animation_data_clear()
    if obj.data:obj.data.animation_data_clear()

def sample_path(knots,f):
    # Cubic Hermite with shared knot slopes. Unlike ease-in/out at every
    # waypoint, this produces continuous velocity through intermediate beats.
    if f<=knots[0][0]:return knots[0][1]
    if f>=knots[-1][0]:return knots[-1][1]
    i=next(i for i in range(len(knots)-1) if knots[i][0]<=f<=knots[i+1][0])
    t0,p0=knots[i];t1,p1=knots[i+1];dt=t1-t0;t=(f-t0)/dt
    def slope(j):
        if j==0 or j==len(knots)-1:return p0*0
        a,x=knots[j-1];b,y=knots[j+1];return (y-x)/(b-a)
    m0=slope(i)*dt;m1=slope(i+1)*dt
    return (2*t**3-3*t*t+1)*p0+(t**3-2*t*t+t)*m0+(-2*t**3+3*t*t)*p1+(t**3-t*t)*m1

def baked_camera(cam,knots):
    clear_animation(cam);cam.rotation_mode="QUATERNION"
    pos=[(f,Vector(p)) for f,p,t,l in knots];targets=[(f,Vector(t)) for f,p,t,l in knots];lenses=[(f,l) for f,p,t,l in knots]
    prior=None;positions=[]
    for frame in FRAMES:
        p=sample_path(pos,frame);target=sample_path(targets,frame)
        z=(p-target).normalized();x=Vector((0,1,0)).cross(z).normalized();y=z.cross(x).normalized()
        q=Matrix((x,y,z)).transposed().to_quaternion()
        if prior is not None and prior.dot(q)<0:q.negate()
        prior=q.copy();cam.location=p;cam.rotation_quaternion=q;cam.data.lens=sample_path(lenses,frame)
        cam.keyframe_insert(data_path="location",frame=frame);cam.keyframe_insert(data_path="rotation_quaternion",frame=frame)
        cam.data.keyframe_insert(data_path="lens",frame=frame)
        positions.append(tuple(p))
    return positions

def relight(s,bounds):
    # Remove the two blown-out strip reflections and the artificial patchy
    # clouds. Studio metal reads through broad luminous gradients.
    for name in ("Gold reflected floor strip left","Gold reflected floor strip right","Localized blue atmosphere","Diagonal blue atmosphere left","Diagonal blue atmosphere right","Storyboard upper sweep"):
        ob=bpy.data.objects.get(name)
        if ob:bpy.data.objects.remove(ob,do_unlink=True)
    bg=bpy.data.objects["Deep blue layered studio cyclorama"];bg.animation_data_clear()
    m=bg.data.materials[0];n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    coord=n.new("ShaderNodeTexCoord");vec=n.new("ShaderNodeVectorMath");vec.operation="MULTIPLY";vec.inputs[1].default_value=(.055,.10,.05);l.new(coord.outputs["Object"],vec.inputs[0])
    tex=n.new("ShaderNodeTexNoise");tex.inputs["Scale"].default_value=1.1;tex.inputs["Detail"].default_value=1.5;l.new(vec.outputs[0],tex.inputs["Vector"])
    ramp=n.new("ShaderNodeValToRGB");ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=(.001,.003,.007,1);ramp.color_ramp.elements[1].position=.86;ramp.color_ramp.elements[1].color=(.018,.052,.11,1)
    l.new(tex.outputs["Fac"],ramp.inputs[0]);e=n.new("ShaderNodeEmission");e.inputs["Strength"].default_value=.8;l.new(ramp.outputs[0],e.inputs[0]);o=n.new("ShaderNodeOutputMaterial");l.new(e.outputs[0],o.inputs["Surface"])
    bg.hide_render=False;bg.keyframe_insert(data_path="hide_render",frame=1)
    floor=bpy.data.objects["Polished reflective obsidian stage"];p=floor.data.materials[0].node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(.035,.045,.063,1);p.inputs["Metallic"].default_value=.60;p.inputs["Roughness"].default_value=.21
    floor_y=min(v[2] for v in bounds.values())-.035
    # Broad key and lower separate typography fill with explicit light linking.
    for name in ("Broad cool silver key","Narrow white edge card","Moving warm specular strip","Soft frontal reflection"):
        ob=bpy.data.objects[name];clear_animation(ob);ob.data.energy=0
    lights=[
      ("Long soft silver",(-4.3,4.2,4.5),(0,.5,0),5.5,2.6,900,(.85,.93,1)),
      ("Warm broad gold key",(2.7,3.0,3.1),(.2,.6,0),3.6,1.6,620,(1,.64,.27)),
      ("Low silver reflection",(-3.8,-.2,4.0),(0,.3,0),2.6,2.2,490,(.8,.89,1)),
      ("Wide rear gold edge",(2.6,1.5,-2.5),(0,0,0),2.4,1.3,500,(1,.48,.12))]
    for name,loc,target,w,h,e,color in lights:
        ob=rectangle_light(name,loc,target,w,h,0,color)
        power(ob,[(1,0),(5,0),(11,e*.8),(20,e),(39,e),(78,e),(120,e)])
    # Low-frequency gold pools from small point sources rather than white
    # rectangular emitter images. Physically reflected points on the floor.
    for x in (-2.6,-.9,1.2,2.8):
        d=bpy.data.lights.new("Amber floor pool","POINT");d.color=(1,.42,.085);d.shadow_soft_size=.22;d.energy=0
        ob=bpy.data.objects.new("Amber floor pool",d);bpy.context.collection.objects.link(ob);ob.location=(x,floor_y+.4,.8)
        power(ob,[(1,0),(30,0),(39,48),(60,60),(120,48)])
    words=bpy.data.collections.new("Wordmark only lighting");s.collection.children.link(words)
    for name in ("silver-wordmark","gold-descriptor"):
        ob=bpy.data.objects[name];words.objects.link(ob)
        mat=ob.data.materials[0];p=mat.node_tree.nodes.get("Principled BSDF")
        p.inputs["Metallic"].default_value=.68;p.inputs["Roughness"].default_value=.28
        p.inputs["Base Color"].default_value=(*( (.95,.57,.13) if name=="gold-descriptor" else (.83,.86,.9)),1)
    fill=rectangle_light("Dedicated lower wordmark key",(0,floor_y+1.2,4),(0,floor_y+.6,0),5.2,1.9,0,(1,.93,.78))
    if hasattr(fill,"light_linking"):fill.light_linking.receiver_collection=words
    power(fill,[(1,0),(49,0),(59,480),(78,600),(120,600)])

def create_scene(g,sha):
    s,bounds=base_scene(g,sha);s.name="GRP V05 — directed native motion"
    s["creative_status"]="unapproved motion proof";s["geometry_sha256"]=sha
    geometry=refined_curves(g);relight(s,bounds)
    floor_y=min(v[2] for v in bounds.values())-.035;low=min(bounds["silver-monogram"][2],bounds["gold-r"][2]);shift=floor_y+.045-low
    # Begin on a genuine silver bevel, travel to the gold R, then pull
    # continuously back into full lockup. Correct focal length and framing.
    # Avoid extreme near-plane clipping, repeated stops or Euler flipping.
    lo,hi,bot,top=bounds["gold-r"];rx=(lo+hi)/2;ry=(bot+top)/2+shift
    silver=bounds["silver-monogram"];sx=silver[0]+.18*(silver[1]-silver[0]);sy=silver[3]-.19*(silver[3]-silver[2])+shift
    mid=(max(bounds["gold-r"][3],silver[3])+low)/2+shift
    knots=[(1,(sx-1.35,sy+.5,1.8),(sx,sy,.16),58),
           (11,(sx-1.1,sy+.46,2.1),(sx+.10,sy-.04,.15),61),
           (20,(rx+1.05,ry+.48,2.7),(rx,ry,.13),57),
           (30,(rx+.95,ry+.6,4.7),(rx,ry-.12,.10),53),
           (39,(-1.85,floor_y+2.3,8.9),(0,mid-.28,0),48),
           (49,(-.80,floor_y+2.7,11.4),(0,mid-.30,0),48),
           (59,(-.28,floor_y+3.3,14.9),(0,-.25,0),48),
           (78,(0,floor_y+3.7,15.9),(0,-.34,0),48),
           (106,(0,floor_y+3.7,15.9),(0,-.34,0),48),
           (120,(0,floor_y+3.7,15.9),(0,-.34,0),48)]
    pos=baked_camera(s.camera,knots)
    s.camera.data.dof.use_dof=False
    if hasattr(s.render,"use_motion_blur"):s.render.use_motion_blur=True
    if hasattr(s.render,"motion_blur_shutter"):s.render.motion_blur_shutter=.28
    s.view_settings.exposure=.15
    s.render.resolution_x=SIZE[0];s.render.resolution_y=SIZE[1];s.render.resolution_percentage=100
    s.cycles.samples=SAMPLES;s.cycles.adaptive_threshold=.095;s.cycles.max_bounces=4;s.cycles.glossy_bounces=3
    s.cycles.volume_bounces=0;s.cycles.use_denoising=True
    return s,geometry,pos

def main():
    if tuple(bpy.app.version)!=(4,5,17):raise RuntimeError("Expected Blender 4.5.17")
    g,sha=load_geometry();out=private_path(OUT);out.mkdir(parents=True,exist_ok=False)
    s,geometry,pos=create_scene(g,sha);frames=out/"frames";frames.mkdir()
    # Editable source saved at master resolution and higher sample settings.
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.cycles.samples=64
    s.frame_set(78);bpy.ops.wm.save_as_mainfile(filepath=str(out/"gold-light-v05.blend"))
    s.render.resolution_x,s.render.resolution_y=SIZE;s.cycles.samples=SAMPLES
    hashes=[]
    for f in FRAMES:
        s.frame_set(f);dst=frames/f"frame-{f:03d}.png";s.render.filepath=str(dst);bpy.ops.render.render(write_still=True)
        hashes.append(hashlib.sha256(dst.read_bytes()).hexdigest())
    receipt={"status":"unapproved-v05-motion-proof","version":bpy.app.version_string,"engine":"Cycles CPU","referenceSha256":REFERENCE,"geometrySha256":sha,"geometry":geometry,"resolution":list(SIZE),"samples":SAMPLES,"nativeFrames":120,"fps":24,"frameHashes":hashes,"creativeApproval":False,"motionBlur":bool(getattr(s.render,"use_motion_blur",False))}
    (out/"v05-receipt.json").write_text(json.dumps(receipt,indent=2))
if __name__=="__main__":main()
