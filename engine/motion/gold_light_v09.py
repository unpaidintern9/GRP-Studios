"""V09 native cinematic lookdev; preserve the V08 fitted brand curves.

Can rebuild from the verified private geometry or revise the recovered V08
.blend directly. Seven seconds, no Earth/tagline or unrelated effects.
This is an unreviewed scene candidate, not a creative acceptance receipt.
"""
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gold_light_v02 import EXPECTED, rectangle_light, aim
from gold_light_v03 import keys, power
from gold_light_v08 import create_scene as v08_scene

FPS = 24
TOTAL = 168
CHECKPOINTS = (1, 20, 39, 65, 92, 120, 145, 168)
GROUPS = tuple(EXPECTED)

def bounds(ob):
    pts = [p.co for sp in ob.data.splines for p in sp.bezier_points]
    if not pts:
        raise RuntimeError("Expected original fitted Bezier geometry: " + ob.name)
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts))

def monotone(knots, frame):
    """Shape-preserving cubic Hermite: no channel overshoot or end velocity."""
    if frame <= knots[0][0]: return knots[0][1]
    if frame >= knots[-1][0]: return knots[-1][1]
    i = next(i for i in range(len(knots)-1) if knots[i][0] <= frame <= knots[i+1][0])
    d = [(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(knots,knots[1:])]
    def slope(j):
        if j == 0 or j == len(knots)-1: return 0.
        a,b = d[j-1],d[j]
        if a*b <= 0: return 0.
        h0=knots[j][0]-knots[j-1][0]; h1=knots[j+1][0]-knots[j][0]
        w1=2*h1+h0;w2=h1+2*h0
        return (w1+w2)/(w1/a+w2/b)
    a,p=knots[i];b,q=knots[i+1];h=b-a;t=(frame-a)/h
    return ((2*t**3-3*t*t+1)*p+(t**3-2*t*t+t)*h*slope(i)
            +(-2*t**3+3*t*t)*q+(t**3-t*t)*h*slope(i+1))

def action_curves(action):
    if not action: return
    fc=getattr(action,"fcurves",None)
    if fc is not None and len(fc):
        yield from fc
        return
    for layer in getattr(action,"layers",()):
        for strip in layer.strips:
            for bag in getattr(strip,"channelbags",()):
                yield from bag.fcurves

def linear_baked(idblock):
    if not idblock.animation_data: return
    for fc in action_curves(idblock.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation="LINEAR"
        fc.update()

def metal(ob, mark, gold):
    c=ob.data
    c.resolution_u=32 if mark else 20
    c.render_resolution_u=c.resolution_u
    c.extrude=.23 if mark else .026
    c.bevel_depth=.011 if mark else .0016
    c.bevel_resolution=12 if mark else 8
    for sp in c.splines: sp.use_smooth=True
    m=bpy.data.materials.new("V09 precision "+("gold" if gold else "silver")+" / "+ob.name)
    m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links
    p=n.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(.86,.49,.105,1) if gold else (.79,.83,.88,1)
    p.inputs["Metallic"].default_value=1.
    p.inputs["Roughness"].default_value=.25 if mark else .32
    for k in ("Anisotropic IOR Level","Anisotropic"):
        if p.inputs.get(k):
            p.inputs[k].default_value=.27 if mark else .12
            break
    tex=n.new("ShaderNodeTexCoord");v=n.new("ShaderNodeVectorMath");v.operation="MULTIPLY"
    v.inputs[1].default_value=(5,360,80)
    l.new(tex.outputs["Object"],v.inputs[0])
    noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=1.1;noise.inputs["Detail"].default_value=2
    l.new(v.outputs[0],noise.inputs["Vector"])
    rough=n.new("ShaderNodeMapRange");rough.clamp=True
    rough.inputs["To Min"].default_value=.21 if mark else .27
    rough.inputs["To Max"].default_value=.28 if mark else .34
    l.new(noise.outputs["Fac"],rough.inputs["Value"]);l.new(rough.outputs["Result"],p.inputs["Roughness"])
    bump=n.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.09 if mark else .035
    bump.inputs["Distance"].default_value=.00035
    l.new(noise.outputs["Fac"],bump.inputs["Height"]);l.new(bump.outputs["Normal"],p.inputs["Normal"])
    tr=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader")
    l.new(tr.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2])
    l.new(mix.outputs[0],n.get("Material Output").inputs["Surface"])
    keys(mix.inputs[0],[(1,0),(9,0),(22,1),(168,1)] if mark else [(1,0),(65,0),(93,1),(168,1)])
    c.materials.clear();c.materials.append(m)

def camera(s, b):
    cam=s.camera;cam.animation_data_clear();cam.data.animation_data_clear()
    cam.rotation_mode="QUATERNION";cam.data.sensor_width=36
    cam.data.clip_start=.025;cam.data.clip_end=250
    lo,hi,bot,top=b["gold-r"];h=top-bot
    all_lo=min(v[0] for v in b.values());all_hi=max(v[1] for v in b.values())
    all_bot=min(v[2] for v in b.values());all_top=max(v[3] for v in b.values())
    cx=(all_lo+all_hi)/2;cy=(all_bot+all_top)/2
    midx=(lo+hi)/2;midy=(bot+top)/2
    source=[p.co for sp in bpy.data.objects["gold-r"].data.splines for p in sp.bezier_points]
    anchor=min(source,key=lambda p:(p.x-(lo+.70*(hi-lo)))**2+(p.y-(top-.12*h))**2)
    final_lens=52.
    final_d=max((all_hi-all_lo)*final_lens/(36*.72),(all_top-all_bot)*final_lens/(20.25*.64))
    # Frames, target x/y, log distance, yaw, pitch, lens, roll.
    # Shape-preserving curves keep monotonic pullback and intentional settling.
    spec=[
      (1,anchor.x,anchor.y,h*.70,30,10,65,-8),
      (18,anchor.x-.045*h,anchor.y-.08*h,h*.70,27,9,65,-7),
      (39,midx+.10*h,midy+.10*h,h*1.20,22,8,61,-4),
      (65,midx-.12*h,midy-.04*h,h*2.10,15,6,57,-2),
      (92,cx,cy+.12*h,final_d*.80,8,5,54,-.7),
      (120,cx,cy,final_d*.97,2,3,52,0),
      (145,cx,cy,final_d,0,3,52,0),
      (168,cx,cy,final_d,0,3,52,0)]
    channels=[[(p[0],math.log(p[i]) if i==3 else p[i]) for p in spec] for i in range(1,8)]
    previous=None;positions=[]
    cam.data.dof.use_dof=True;cam.data.dof.aperture_blades=9
    for f in range(1,TOTAL+1):
        x,y,logd,yaw,pitch,lens,roll=[monotone(k,f) for k in channels]
        d=math.exp(logd);ya=math.radians(yaw);pi=math.radians(pitch)
        t=Vector((x,y,.18 if f<65 else 0.))
        # Smooth the focus plane transition as the shot resolves.
        t.z=.18*(1-min(1,max(0,(f-39)/53))**2*(3-2*min(1,max(0,(f-39)/53))))
        pos=t+Vector((d*math.sin(ya)*math.cos(pi),d*math.sin(pi),d*math.cos(ya)*math.cos(pi)))
        z=(pos-t).normalized();right=Vector((0,1,0)).cross(z).normalized();up=z.cross(right).normalized()
        q=Matrix((right,up,z)).transposed().to_quaternion() @ Quaternion((0,0,1),math.radians(roll))
        if previous is not None and previous.dot(q)<0:q.negate()
        previous=q.copy();cam.location=pos;cam.rotation_quaternion=q;cam.data.lens=lens
        cam.data.dof.focus_distance=d;cam.data.dof.aperture_fstop=monotone([(1,16),(20,8),(65,10),(120,16),(168,16)],f)
        # Optical opening cards are near the camera: keep them crisp until gone.
        cam.data.dof.use_dof=f>=18
        for k in ("location","rotation_quaternion"):cam.keyframe_insert(data_path=k,frame=f)
        cam.data.keyframe_insert(data_path="lens",frame=f)
        for k in ("focus_distance","aperture_fstop","use_dof"):
            cam.data.dof.keyframe_insert(data_path=k,frame=f)
        positions.append(tuple(pos))
    linear_baked(cam);linear_baked(cam.data)
    return positions

def matte(name,base,rough,metallic):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*base,1);p.inputs["Roughness"].default_value=rough
    p.inputs["Metallic"].default_value=metallic
    return m

def environment(s,fy):
    # Discard procedural stretched stripes, old glare streaks and extraneous
    # closing objects. Keep original brand and opening optical cards.
    for ob in list(s.objects):
        if ob.type=="LIGHT" or ob.name in ("Grounded gold reflection streak","Late diagonal optical sweep","V06 physical night-planet","V06 thin physical atmosphere","V06 closing tagline"):
            bpy.data.objects.remove(ob,do_unlink=True)
    world=bpy.data.worlds.new("V09 neutral midnight reflection environment");world.use_nodes=True;s.world=world
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.008,.012,.022,1);bg.inputs["Strength"].default_value=.18
    floor=bpy.data.objects["Polished reflective obsidian stage"]
    floor.animation_data_clear();floor.location.y=fy
    floor.data.materials.clear();floor.data.materials.append(matte("V09 satin obsidian",(.022,.026,.034),.31,.32))
    bpy.ops.mesh.primitive_plane_add(size=80,location=(0,3,-11))
    back=bpy.context.object;back.name="V09 deep stage / physical backdrop"
    back.data.materials.append(matte("V09 midnight cyclorama",(.018,.032,.065),.85,0))
    bpy.ops.mesh.primitive_cube_add(size=2,location=(0,fy+3.6,-5.5))
    haze=bpy.context.object;haze.name="V09 bounded atmospheric depth";haze.scale=(11,6,4.2)
    m=bpy.data.materials.new("V09 soft atmospheric scattering");m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    volume=n.new("ShaderNodeVolumeScatter");volume.inputs["Color"].default_value=(.42,.56,.78,1)
    volume.inputs["Density"].default_value=.005;volume.inputs["Anisotropy"].default_value=.25
    out=n.new("ShaderNodeOutputMaterial");l.new(volume.outputs[0],out.inputs["Volume"]);haze.data.materials.append(m)
    # Physical large sources; warm key and cool fill stay separate.
    def area(name,p,t,w,h,e,c,beat):
        ob=rectangle_light(name,p,t,w,h,0,c);power(ob,[(f,e*v) for f,v in beat]);return ob
    beat=[(1,0),(9,0),(22,.62),(39,1),(92,1),(168,.95)]
    area("V09 broad silver gradient",(-5,4.5,5.5),(0,.4,0),5.5,3.8,850,(.88,.94,1),beat)
    area("V09 warm sculpting key",(3,3.2,4.4),(0,.1,0),4.3,2.5,720,(1,.72,.38),beat)
    area("V09 narrow silver edge",(5,1.9,1.6),(0,.5,0),.7,4.7,280,(.76,.86,1),beat)
    area("V09 soft frontal reflection",(-1,.6,6),(0,0,0),6,2.5,280,(.92,.95,1),[(1,0),(39,0),(65,.4),(93,1),(168,1)])
    area("V09 gold rear edge",(-3,2,-2.1),(0,0,0),3,1.6,260,(1,.52,.18),beat)
    area("V09 background depth key",(-4,4,-4),(0,1,-11),5,4,750,(.23,.40,.82),[(1,0),(16,0),(55,1),(168,1)])
    area("V09 warm depth accent",(6,2,-5),(2,.4,-11),3,3,200,(1,.51,.17),[(1,0),(26,0),(75,1),(168,.7)])
    sweep=area("V09 choreographed traveling softbox",(-3,2.2,3),(0,.7,.2),.65,2.4,480,(1,.72,.32),[(1,0),(9,0),(20,1),(65,.9),(115,.45),(145,.12),(168,.12)])
    for f in range(1,TOTAL+1):
        x=monotone([(1,-4),(20,-3.1),(65,1.3),(120,4.8),(145,5),(168,5)],f)
        y=monotone([(1,2.8),(40,2.2),(90,1.4),(145,2),(168,2)],f)
        sweep.location=(x,y,3.5)
        aim(sweep,(x*.28,.3,.18))
        sweep.keyframe_insert(data_path="location",frame=f)
        sweep.keyframe_insert(data_path="rotation_quaternion",frame=f)
    linear_baked(sweep)

def apply_v09(s):
    b={name:bounds(bpy.data.objects[name]) for name in GROUPS}
    for name in GROUPS:
        ob=bpy.data.objects[name];ob.animation_data_clear();ob.location=(0,0,0)
        metal(ob,name in ("gold-r","silver-monogram"),EXPECTED[name][1]=="gold")
    fy=min(v[2] for v in b.values())-.055
    environment(s,fy)
    positions=camera(s,b)
    s.name="GRP V09 - controlled cinematic motion and studio lookdev"
    s.frame_start=1;s.frame_end=TOTAL;s.render.fps=FPS;s.render.fps_base=1
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
    s.render.engine="CYCLES";s.cycles.samples=128;s.cycles.adaptive_threshold=.012
    s.cycles.use_adaptive_sampling=True;s.cycles.use_denoising=True
    s.cycles.max_bounces=10;s.cycles.glossy_bounces=6;s.cycles.volume_bounces=1
    s.render.use_persistent_data=True;s.render.use_motion_blur=True;s.render.motion_blur_shutter=.25
    s.view_settings.view_transform="AgX";s.view_settings.exposure=-.15
    if s.node_tree:
        for n in s.node_tree.nodes:
            if n.type=="GLARE":
                if n.inputs.get("Strength"):n.inputs["Strength"].default_value=.08
                if n.inputs.get("Threshold"):n.inputs["Threshold"].default_value=4.
    s.timeline_markers.clear()
    for f,label in [(1,"Gold ignition"),(20,"Machined macro"),(39,"Gold R track"),(65,"Continuous reveal"),(92,"Full lockup"),(120,"Controlled settle"),(145,"Signature hold")]:
        s.timeline_markers.new(label,frame=f)
    s["creative_status"]="unapproved V09 native scene; stills and motion require review"
    s["closing_treatment"]="original lockup, no globe or tagline"
    s["duration_seconds"]=7
    return positions

def create_scene(g,sha):
    s,geo,_=v08_scene(g,sha)
    return s,geo,apply_v09(s)

def main():
    """Use with an already opened verified V08 blend. Save a new private file."""
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    if tuple(bpy.app.version)!=(4,5,17):raise RuntimeError("Pinned Blender 4.5.17 required")
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    s=bpy.context.scene;apply_v09(s)
    prefs=bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type="OPTIX";prefs.get_devices()
    devices=[d for d in prefs.devices if d.type=="OPTIX"]
    if not devices:raise RuntimeError("No OptiX GPU; refusing CPU fallback")
    for d in prefs.devices:d.use=d.type=="OPTIX"
    s.cycles.device="GPU"
    s.frame_set(120)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"gold-light-v09.blend"))
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB"
    if args.preview:
        s.cycles.samples=32;s.cycles.adaptive_threshold=.035
        for frame in CHECKPOINTS:
            s.frame_set(frame);s.render.filepath=str(out/f"checkpoint-{frame:03d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        s.render.filepath=str(out/"frame-");bpy.ops.render.render(animation=True)

if __name__=="__main__":main()
