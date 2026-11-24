"""V07 native shot reconstruction: reference-led stage, physical metal, traveling light.
Keeps approved logo, does not embed reference imagery. Unapproved candidate.
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gold_light_v02 import world_point, rectangle_light, aim, EXPECTED
from gold_light_v03 import keys, power, emission, curve, trim
from gold_light_v04 import create_scene as old_scene
from gold_light_v05 import sample_path
from gold_light_v06_contours import fit_group
from gold_light_v06_closing import add_closing
from gold_light_v07_beats import shot_plan, WORDMARK_KEYS, SHIFT_KEYS

def refit(g):
    result={}
    for group in g["groups"]:
        name=group["name"];mark=name in ("silver-monogram","gold-r")
        c=bpy.data.objects[name].data
        curves,info=fit_group(group["loops"],g.get("width",1536),g.get("height",934),mark)
        c.splines.clear();c.resolution_u=12;c.render_resolution_u=12
        # Smaller controlled bevel avoids self-intersection on thin serifs.
        # Native sidewalls remain deep enough for macro parallax.
        c.extrude=.21 if mark else .028;c.bevel_depth=.013 if mark else .0018;c.bevel_resolution=6
        for fitted in curves:
            sp=c.splines.new("BEZIER");sp.bezier_points.add(len(fitted)-1);sp.use_cyclic_u=True;sp.use_smooth=True
            for b,(l,p,r) in zip(sp.bezier_points,fitted):
                b.handle_left_type="FREE";b.handle_right_type="FREE";b.co=world_point(*p);b.handle_left=world_point(*l);b.handle_right=world_point(*r)
        result[name]=info
    return result

def stage(s,floor_y):
    # A directional environment, not a backdrop wall. Dark stage fades
    # into the surrounding world, so there is no room-shaped horizon.
    for o in list(bpy.data.objects):
        if o.type=="LIGHT" or o.name in ("Deep blue layered studio cyclorama","Localized blue atmosphere","Storyboard upper sweep"):
            bpy.data.objects.remove(o,do_unlink=True)
    w=bpy.data.worlds.new("Seamless midnight atmosphere");w.use_nodes=True;s.world=w;n=w.node_tree.nodes;l=w.node_tree.links;n.clear()
    tex=n.new("ShaderNodeTexCoord");stretch=n.new("ShaderNodeVectorMath");stretch.operation="MULTIPLY";stretch.inputs[1].default_value=(1.5,8.0,2.6);l.new(tex.outputs["Normal"],stretch.inputs[0])
    noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=2.1;noise.inputs["Detail"].default_value=2.0;noise.inputs["Roughness"].default_value=.48;l.new(stretch.outputs[0],noise.inputs["Vector"])
    ramp=n.new("ShaderNodeValToRGB");ramp.color_ramp.elements[0].position=.30;ramp.color_ramp.elements[0].color=(.0002,.0004,.0009,1);ramp.color_ramp.elements[1].position=.83;ramp.color_ramp.elements[1].color=(.012,.035,.078,1);l.new(noise.outputs["Fac"],ramp.inputs[0])
    bg=n.new("ShaderNodeBackground");l.new(ramp.outputs[0],bg.inputs["Color"]);keys(bg.inputs["Strength"],[(1,0),(6,0),(12,.8),(40,.85),(120,.8)]);out=n.new("ShaderNodeOutputWorld");l.new(bg.outputs[0],out.inputs["Surface"])
    floor=bpy.data.objects["Polished reflective obsidian stage"];m=floor.data.materials[0];n=m.node_tree.nodes;l=m.node_tree.links
    p=n.get("Principled BSDF");p.inputs["Base Color"].default_value=(.028,.032,.042,1);p.inputs["Metallic"].default_value=.84;p.inputs["Roughness"].default_value=.085
    geom=n.new("ShaderNodeNewGeometry");d=n.new("ShaderNodeVectorMath");d.operation="DISTANCE";d.inputs[1].default_value=(0,floor_y,0);l.new(geom.outputs["Position"],d.inputs[0])
    fall=n.new("ShaderNodeMapRange");fall.clamp=True;fall.inputs["From Min"].default_value=7;fall.inputs["From Max"].default_value=27;fall.inputs["To Min"].default_value=1;fall.inputs["To Max"].default_value=0;l.new(d.outputs["Value"],fall.inputs["Value"])
    weight=n.new("ShaderNodeMath");weight.operation="MULTIPLY";l.new(fall.outputs["Result"],weight.inputs[0]);keys(weight.inputs[1],[(1,0),(9,0),(20,.4),(36,1),(120,1)])
    tr=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader");l.new(weight.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get("Material Output").inputs["Surface"])

def track(cam,knots,frame_end=120):
    cam.animation_data_clear();cam.data.animation_data_clear();cam.rotation_mode="QUATERNION"
    position=[(f,Vector(p)) for f,p,t,l,r in knots];target=[(f,Vector(t)) for f,p,t,l,r in knots]
    lenses=[(f,l) for f,p,t,l,r in knots];rolls=[(f,r) for f,p,t,l,r in knots]
    prior=None;positions=[]
    for f in range(1,frame_end+1):
        p=sample_path(position,f);t=sample_path(target,f);z=(p-t).normalized();x=Vector((0,1,0)).cross(z).normalized();y=z.cross(x).normalized()
        q=Matrix((x,y,z)).transposed().to_quaternion() @ Quaternion((0,0,1),math.radians(sample_path(rolls,f)))
        if prior is not None and prior.dot(q)<0:q.negate()
        prior=q.copy();cam.location=p;cam.rotation_quaternion=q;cam.data.lens=sample_path(lenses,f)
        cam.keyframe_insert(data_path="location",frame=f);cam.keyframe_insert(data_path="rotation_quaternion",frame=f);cam.data.keyframe_insert(data_path="lens",frame=f)
        positions.append(tuple(p))
    return positions

def lighting(s,bounds,fy,shift):
    def area(name,loc,target,w,h,e,col,beats):
        ob=rectangle_light(name,loc,target,w,h,0,col);power(ob,[(f,e*v) for f,v in beats]);return ob
    beats=[(1,0),(6,0),(11,.45),(20,.85),(39,1),(59,1),(120,.95)]
    area("Broad silver gradient",(-4,4,5),(0,0,0),4.5,2.4,520,(.81,.89,1),beats)
    area("Cool edge contrast",(4.8,1.6,1.3),(0,.2,0),1.0,4.5,330,(.78,.88,1),beats)
    area("Warm soft reflection",(.2,2.8,4),(0,.2,0),4.0,2.1,230,(1,.70,.33),beats)
    area("Wide back edge",(-1,2.0,-2.3),(0,.3,0),3,1.2,160,(1,.43,.12),beats)
    # Moving area source follows the actual R rather than keeping a fixed
    # hot spot. Its changing reflections are part of the shot choreography.
    lo,hi,b,t=bounds["gold-r"];rx=(lo+hi)/2;ry=(b+t)/2
    hot=area("Traveling contour highlight",(rx-1.5,t+shift,2),(rx,t+shift,.2),.22,1.5,620,(1,.60,.18),[(1,0),(7,0),(11,.75),(20,1),(30,.9),(40,.65),(59,.45),(78,.6),(104,.1),(120,.08)])
    for f,pos,look in [(7,(rx-2,t+shift,1.5),(rx,t+shift,.2)),(20,(hi+.4,ry+shift+.1,1.8),(hi,ry+shift,.2)),(30,(hi+.9,b+shift+.25,1.5),(hi,b+shift+.35,.2)),(40,(rx+.8,fy+.35,2),(rx,fy+.2,.2)),(59,(-3,fy+.7,2),(0,fy+.4,.2)),(78,(3.4,1.2,2),(0,.7,.2)),(104,(5,2.0,4),(0,.3,.2)),(120,(5,2.0,4),(0,.3,.2))]:
        hot.location=pos;aim(hot,look);hot.keyframe_insert(data_path="location",frame=f);hot.keyframe_insert(data_path="rotation_quaternion",frame=f)
    words=bpy.data.collections.new("V06 typography illumination");s.collection.children.link(words)
    for name in EXPECTED:
        ob=bpy.data.objects[name];m=ob.data.materials[0];p=m.node_tree.nodes.get("Principled BSDF")
        mark=name in ("gold-r","silver-monogram")
        p.inputs["Metallic"].default_value=1 if mark else .77;p.inputs["Roughness"].default_value=.19 if mark else .26
        p.inputs["Base Color"].default_value=(*( (.83,.42,.075) if EXPECTED[name][1]=="gold" else (.74,.79,.85)),1)
        if not mark:words.objects.link(ob)
    fill=area("Legible wordmark key",(0,fy+.8,4),(0,fy+.6,0),4.8,1.6,460,(1,.90,.72),[(1,0),(45,0),(59,1),(120,1)])
    if hasattr(fill,"light_linking"):fill.light_linking.receiver_collection=words
    # Amber floor streak is real stage geometry rather than rectangular
    # white reflections. A later thin optical arc matches the storyboard.
    mat,level=emission("Gold stage glint",(1,.44,.07),0)
    ray=curve("Grounded gold reflection streak",[(-4.3,fy+.012,.6),(-1.7,fy+.012,.48),(1,fy+.012,.42),(4.3,fy+.012,.65)],.005,mat)
    trim(ray,[(1,0,0),(32,0,0),(39,0,.7),(49,0,1),(70,0,1),(98,.3,1),(120,.3,1)])
    keys(level,[(1,0),(32,0),(39,2.2),(49,1.6),(78,1.0),(120,.55)])
    mat,level=emission("Upper optical sweep",(1,.52,.12),0)
    arc=curve("Late diagonal optical sweep",[(-6,2.6,-.8),(-2.8,3.5,-.8),(1,4.0,-.8),(5,4.4,-.8)],.004,mat)
    trim(arc,[(1,0,0),(61,0,0),(68,0,.52),(78,.12,.9),(86,.65,1),(92,1,1),(120,1,1)])
    keys(level,[(1,0),(61,0),(68,1.9),(78,1),(92,0),(120,0)])

def create_scene(g,sha):
    s,bounds=old_scene(g,sha);s.name="GRP V07 — timed face-first choreography"
    geom=refit(g);fy=min(v[2] for v in bounds.values())-.035
    silver=bounds["silver-monogram"];gold=bounds["gold-r"];low=min(silver[2],gold[2]);shift=fy+.045-low
    stage(s,fy);lighting(s,bounds,fy,shift)
    lo,hi,b,t=gold;rx=(lo+hi)/2;ry=(b+t)/2+shift
    sl,sh,sb,st=silver
    # Use an actual contour location at the silver upper-left shoulder.
    group=next(x for x in g["groups"] if x["name"]=="silver-monogram")
    pts=[Vector(world_point(*p)) for loop in group["loops"] for p in loop]
    anchor=min(pts,key=lambda p:(p.x-(sl+.19*(sh-sl)))**2+(p.y-(st-.12*(st-sb)))**2);sx,sy=anchor.x,anchor.y+shift
    mid=(max(silver[3],gold[3])+low)/2+shift
    # 0.4 macro bevel, .8 close R, 1.2 wider R, 1.6 low three-quarter,
    # 2.0 smaller monogram, 2.4 full lockup, 2.8-3.2 optical sweep.
    shots=shot_plan(silver,gold,fy,shift,(sx,sy))
    pos=track(s.camera,shots)
    for name in ("silver-monogram","gold-r"):
        ob=bpy.data.objects[name];ob.animation_data_clear()
        for f,v in [(f,shift*v) for f,v in SHIFT_KEYS]:
            ob.location.y=v;ob.keyframe_insert(data_path="location",frame=f)
    for name in ("silver-wordmark","gold-descriptor"):
        mat=bpy.data.objects[name].data.materials[0];tree=mat.node_tree;tree.animation_data_clear()
        mix=next(n for n in tree.nodes if n.type=="MIX_SHADER")
        keys(mix.inputs[0],WORDMARK_KEYS)
    add_closing(s,bounds)
    s.camera.data.dof.use_dof=False
    s.render.use_motion_blur=True;s.render.motion_blur_shutter=.32
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
    s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=120
    s.cycles.samples=64;s.cycles.adaptive_threshold=.035;s.cycles.max_bounces=7;s.cycles.glossy_bounces=4;s.cycles.use_denoising=True
    s.view_settings.exposure=-.25
    s["creative_status"]="unapproved V07 scene";s["reference_sha256"]="2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26"
    return s,geom,pos
