"""Seven-second cinematic V08. Keep original fitted contours and rebuild timing."""
import bpy
from mathutils import Vector
from gold_light_v07 import create_scene as v07_scene, track
from gold_light_v07_beats import shot_plan
from gold_light_v08_beats import TOTAL,retime,retimed_shots,WORDMARK,TAGLINE,HORIZON
from gold_light_v02 import world_point
from gold_light_v03 import keys
def channels(action):
    fc=getattr(action,"fcurves",None)
    if fc is not None and len(fc):
        yield from fc
        return
    for layer in getattr(action,"layers",()):
        for strip in layer.strips:
            for bag in getattr(strip,"channelbags",()):
                yield from bag.fcurves
def stretch_actions():
    for action in list(bpy.data.actions):
        for fc in channels(action):
            for k in fc.keyframe_points:
                x=float(k.co.x);a=float(k.handle_left.x);b=float(k.handle_right.x)
                k.co.x=retime(x);k.handle_left.x=retime(a);k.handle_right.x=retime(b)
            fc.update()
def create_scene(g,sha):
    s,geo,_=v07_scene(g,sha)
    stretch_actions()
    for marker in s.timeline_markers:marker.frame=round(retime(marker.frame))
    def bounds(name):
        group=next(x for x in g["groups"] if x["name"]==name)
        pts=[world_point(*p) for loop in group["loops"] for p in loop]
        return (min(p[0] for p in pts),max(p[0] for p in pts),min(p[1] for p in pts),max(p[1] for p in pts))
    silver,gold=bounds("silver-monogram"),bounds("gold-r")
    fy=min(bounds(x["name"])[2] for x in g["groups"])-.035
    shift=fy+.045-min(silver[2],gold[2])
    sl,sh,sb,st=silver;group=next(x for x in g["groups"] if x["name"]=="silver-monogram")
    pts=[Vector(world_point(*p)) for loop in group["loops"] for p in loop]
    anchor=min(pts,key=lambda p:(p.x-(sl+.19*(sh-sl)))**2+(p.y-(st-.12*(st-sb)))**2)
    plan=retimed_shots(shot_plan(silver,gold,fy,shift,(anchor.x,anchor.y+shift)))
    revised=[]
    for frame,p,t,l,roll in plan:
        if frame in (29,41):
            p=(t[0]+(p[0]-t[0])*1.22,t[1]+(p[1]-t[1])*1.12,p[2]);roll-=3
        revised.append((frame,p,t,l,roll))
    positions=track(s.camera,revised,frame_end=TOTAL)
    for name in ("silver-wordmark","gold-descriptor"):
        tree=bpy.data.objects[name].data.materials[0].node_tree
        tree.animation_data_clear()
        mix=next(n for n in tree.nodes if n.type=="MIX_SHADER")
        keys(mix.inputs[0],WORDMARK)
    for name,scale in (("V06 physical night-planet",75/22),("V06 thin physical atmosphere",75.12/22.10)):
        ob=bpy.data.objects[name];ob.scale=(scale,)*3
        # Delete previous location keys only, preserving rotation and visibility.
        action=ob.animation_data.action
        for fc in list(channels(action)):
            if fc.data_path=="location":
                for k in list(fc.keyframe_points):fc.keyframe_points.remove(k,fast=True)
                fc.update()
        for frame,y in HORIZON:
            ob.location=(0,y,-135);ob.keyframe_insert(data_path="location",frame=frame)
    globe=bpy.data.objects["V06 physical night-planet"]
    for n in globe.data.materials[0].node_tree.nodes:
        if n.type=="EMISSION" and not n.inputs["Color"].is_linked:
            c=n.inputs["Color"].default_value
            if c[0]>.9 and c[1]>.3:
                n.inputs["Color"].default_value=(1,.55,.13,1)
                for link in n.inputs["Strength"].links:
                    node=link.from_node
                    if node.type=="MATH" and node.operation=="MULTIPLY" and not node.inputs[1].is_linked:node.inputs[1].default_value=20
            elif c[2]>c[0]:n.inputs["Color"].default_value=(.055,.12,.22,1)
    limb=bpy.data.objects["V06 thin physical atmosphere"]
    e=next(n for n in limb.data.materials[0].node_tree.nodes if n.type=="EMISSION")
    e.inputs["Color"].default_value=(.055,.18,.50,1);e.inputs["Strength"].default_value=1.35
    tag=bpy.data.objects["V06 closing tagline"];tag.data.size=.205;tag.data.space_character=1.75
    tag.location.y=bounds("gold-descriptor")[2]-.39
    tree=tag.data.materials[0].node_tree;tree.animation_data_clear()
    mix=next(n for n in tree.nodes if n.type=="MIX_SHADER");keys(mix.inputs[0],TAGLINE)
    s.name="GRP V08 — seven-second cinematic";s.frame_start=1;s.frame_end=TOTAL;s.render.fps=24;s.render.fps_base=1
    s["creative_status"]="unapproved seven-second native motion proof";s["closing_treatment"]="broad procedural night-Earth horizon, warm lights and SEE BEYOND THE NOISE."
    s["duration_seconds"]=7
    return s,geo,positions
