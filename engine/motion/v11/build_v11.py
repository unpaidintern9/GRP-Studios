"""V11 reflective-metal lookdev; native Cycles, no image overlays or logo redraw.
Build a new review scene from the verified V09E source and licensed private maps.
Native runtime and creative quality must be evaluated before full delivery.
"""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent/"v10"));sys.path.insert(0,str(HERE.parent))
import build_scene as base
from motion_contract import SHOTS,frames_for,cues,assert_contract
from geometry import apply as apply_geometry
from gold_light_v02 import rectangle_light,aim,optical_card
from gold_light_v03 import keys,power,emission,curve,trim
def mul(n,l,a,b):
    k=n.new("ShaderNodeMath");k.operation="MULTIPLY"
    for i,v in enumerate((a,b)):
        if isinstance(v,(float,int)):k.inputs[i].default_value=v
        else:l.new(v,k.inputs[i])
    return k.outputs[0]
def mathnode(n,l,op,a,b):
    k=n.new("ShaderNodeMath");k.operation=op
    for i,v in enumerate((a,b)):
        if isinstance(v,(float,int)):k.inputs[i].default_value=v
        else:l.new(v,k.inputs[i])
    return k.outputs[0]
def compact_edge(n,l,uv):
    xy=n.new("ShaderNodeSeparateXYZ");l.new(uv,xy.inputs[0]);f=[]
    for axis in ("X","Y"):
        a=xy.outputs[axis];v=mathnode(n,l,"MINIMUM",a,mathnode(n,l,"SUBTRACT",1,a))
        r=n.new("ShaderNodeMapRange");r.clamp=True;r.interpolation_type="SMOOTHERSTEP";r.inputs["From Max"].default_value=.22;l.new(v,r.inputs["Value"]);f.append(r.outputs["Result"])
    return mul(n,l,*f)
def reflection_card(name,location,target,w,h,color,strength,beats,collection):
    # An actual 3D light card visible to glossy rays. Dark surrounding world
    # yields contrasting chrome reflections; the card is never a visible overlay.
    bpy.ops.mesh.primitive_plane_add(size=2);o=bpy.context.object;o.name=name;o.location=location;o.scale=(w/2,h/2,1)
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("Z","Y").to_euler()
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o)
    o.visible_camera=False;o.visible_diffuse=False;o.visible_glossy=True;o.visible_shadow=False;o.visible_transmission=False
    if hasattr(o,"visible_volume_scatter"):o.visible_volume_scatter=False
    m=bpy.data.materials.new(name);m.use_nodes=True;o.data.materials.append(m);n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    uv=n.new("ShaderNodeTexCoord");edge=compact_edge(n,l,uv.outputs["UV"])
    em=n.new("ShaderNodeEmission");em.inputs["Color"].default_value=(*color,1)
    gain=n.new("ShaderNodeValue");keys(gain.outputs[0],[(f,strength*v) for f,v in beats]);l.new(mul(n,l,edge,gain.outputs[0]),em.inputs["Strength"])
    t=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader");l.new(edge,mix.inputs[0]);l.new(t.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);out=n.new("ShaderNodeOutputMaterial");l.new(mix.outputs[0],out.inputs["Surface"]);return o
def relight(s):
    s.frame_set(168)
    brand=bpy.data.collections["V10 brand and stage"];earth=bpy.data.collections["V10 independent horizon"]
    for ob in list(brand.objects):
        if ob.type=="LIGHT":bpy.data.objects.remove(ob,do_unlink=True)
    for name in base.NAMES:
        ob=bpy.data.objects[name];p=next(n for n in ob.data.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED")
        gold=name in ("gold-r","gold-descriptor");mark=name in ("silver-monogram","gold-r")
        p.inputs["Base Color"].default_value=(.83,.47,.105,1) if gold else (.78,.83,.89,1)
        p.inputs["Metallic"].default_value=1.
        p.inputs["Roughness"].default_value=(.115 if gold else .075) if mark else .18
        for k in ("Anisotropic IOR Level","Anisotropic"):
            if p.inputs.get(k):p.inputs[k].default_value=.10 if mark else .03
        # No face emission or overexposed white fill.
        if p.inputs.get("Emission Strength"):p.inputs["Emission Strength"].default_value=0.
    floor=bpy.data.objects["Polished reflective obsidian stage"];p=next(n for n in floor.data.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value=(.009,.013,.021,1);p.inputs["Metallic"].default_value=.66;p.inputs["Roughness"].default_value=.075
    world=s.world.node_tree.nodes.get("Background");world.inputs["Strength"].default_value=.12
    # Narrow cards create differentiated reflections, rather than bathing all
    # letters in uniform illumination. The moving card tracks the macro arc.
    alive=[(f,cues(f)["mark"]) for f in range(1,169)]
    reflection_card("V11 silver long strip",(-4,3.6,3.6),(0,.5,0),5.0,.9,(.83,.92,1),6.5,alive,brand)
    reflection_card("V11 neutral broad gradient",(-.5,1.8,7),(0,.2,0),5.0,2.7,(.93,.96,1),2.0,alive,brand)
    reflection_card("V11 silver edge strip",(4.7,1.1,2.2),(0,.3,0),.7,5.8,(.75,.85,1),4.0,alive,brand)
    reflection_card("V11 warm sculpted gold strip",(2.2,3.1,3.9),(0,0,0),3.2,1.25,(1,.63,.18),4.8,alive,brand)
    travel=reflection_card("V11 traveling reflection",(-4,1.7,2.2),(0,0,0),.45,2.6,(1,.71,.28),7.0,
      [(f,.12+.80*max(cues(f)["silver_sweep"],cues(f)["gold_sweep"],cues(f)["upper_sweep"])) for f in range(1,169)],brand)
    for f,p,t in [(1,(-4,2.6,2.4),(-2,1,0)),(15,(-2.7,2.5,2.5),(-2,1,0)),(29,(.3,2.3,2.3),(.5,1,0)),(43,(2.5,-.5,2.7),(.7,-.5,0)),(71,(3,1,3),(0,.5,0)),(99,(-3,3,3),(0,0,0)),(113,(4,3,3),(0,0,0)),(168,(4,3,3),(0,0,0))]:
        travel.location=p;travel.rotation_euler=(Vector(t)-travel.location).to_track_quat("Z","Y").to_euler();travel.keyframe_insert("location",frame=f);travel.keyframe_insert("rotation_euler",frame=f)
    fy=floor.location.y
    def area(name,pos,target,w,h,e,col,beats,group):
        ob=rectangle_light(name,pos,target,w,h,0,col)
        for c in list(ob.users_collection):c.objects.unlink(ob)
        brand.objects.link(ob);ob.lightgroup=group;power(ob,[(f,e*v) for f,v in beats]);return ob
    area("V11 restrained metal key",(-4,3,5),(0,0,0),4,2,300,(.88,.94,1),alive,"SilverKey")
    area("V11 warm typography key",(0,fy+1.1,4),(0,fy+.5,0),4.8,1.4,380,(1,.84,.55),frames_for("wordmark"),"GoldKey")
    area("V11 cool silhouette separation",(4,3,-3),(0,0,0),2,4,420,(.28,.48,.82),alive,"CoolRim")
    for x,z,e in [(-3.3,1.6,290),(-.9,2.1,180),(1.1,1.2,270),(3.4,2.4,210)]:
        area("V11 elongated golden floor pool",(x,fy+.85,z),(x,fy,z-.8),.22,1.8,e,(1,.49,.085),frames_for("floor_glints"),"StageWarm")
    area("V11 atmosphere depth key",(-6,fy+6,-4),(1,fy+1,-8),2,5,650,(.19,.38,.73),[(f,cues(f)["stage"]) for f in range(1,169)],"CoolRim")
    # Warm sweeping light creates a foreground optical transition. It does
    # not redraw or pass through the original logo. Compact support prevents
    # rectangular flare artifacts.
    mat,level=emission("V11 subtle upper diagonal sweep",(1,.55,.15),0)
    ob=curve("V11 physical upper arc",[(-7,2.7,-1.5),(-3,3.6,-1.5),(1,4.2,-1.5),(7,4.5,-1.5)],.009,mat)
    for c in list(ob.users_collection):c.objects.unlink(ob)
    brand.objects.link(ob);keys(level,[(f,2.1*cues(f)["upper_sweep"]) for f in range(1,169)])
    trim(ob,[(1,0,0),(87,0,0),(96,0,.65),(103,.24,1),(113,1,1),(168,1,1)])
    # True nighttime maps with a very dark diffuse ocean/land contribution.
    planet=bpy.data.objects["V10 mapped night Earth"];nt=planet.data.materials[0].node_tree
    for n in nt.nodes:
        if n.type=="MIX_RGB" and n.blend_type=="MULTIPLY":
            color=n.inputs[2].default_value
            if abs(color[0]-.32)<.01:n.inputs[2].default_value=(.035,.065,.11,1)
            elif abs(color[0]-1)<.01:n.inputs[2].default_value=(1,.72,.38,1)
        if n.type=="MATH" and n.operation=="MULTIPLY":
            for inp in n.inputs:
                if not inp.is_linked and abs(inp.default_value-3.6)<1e-4:inp.default_value=2.3
    sun=bpy.data.objects["V10 horizon solar illumination"];sun.data.energy=.32
    cloud=bpy.data.objects["V10 mapped clouds"]
    for n in cloud.data.materials[0].node_tree.nodes:
        if n.type=="BSDF_PRINCIPLED":n.inputs["Base Color"].default_value=(.045,.075,.13,1)
        if n.type=="MAP_RANGE":n.inputs["To Max"].default_value=.24
    limb=bpy.data.objects["V10 atmospheric limb"]
    for n in limb.data.materials[0].node_tree.nodes:
        if n.type=="EMISSION":n.inputs["Strength"].default_value=.78
    # Physically curved limb, concentrated sunrise; no full-width white ray.
    for ob in list(s.objects):
        if ob.type!="MESH" or ob.parent!=s.camera or not ob.data.materials:continue
        nt=ob.data.materials[0].node_tree;ctl=next((n for n in nt.nodes if n.label=="Opening flare intensity"),None) if nt else None
        if not ctl:continue
        n,l=nt.nodes,nt.links;mix=next(k for k in n if k.type=="MIX_SHADER")
        if mix.inputs[0].is_linked:
            prior=mix.inputs[0].links[0].from_socket;coord=n.new("ShaderNodeTexCoord");l.new(mul(n,l,prior,compact_edge(n,l,coord.outputs["UV"])),mix.inputs[0])
        if ob.name.startswith("V10 sun"):
            nt.animation_data_clear();keys(ctl.outputs[0],frames_for("sunrise"))
            e=next(k for k in n if k.type=="EMISSION");e.inputs["Strength"].default_value*=.48
            if "streak" in ob.name:ob.scale.x*=.45
            if "halo" in ob.name:ob.scale.x*=.7;ob.scale.y*=1.4
    for n in s.node_tree.nodes:
        if n.type=="GLARE":n.inputs["Threshold"].default_value=3.2;n.inputs["Strength"].default_value=.13
        if n.type=="RGB":n.outputs[0].default_value=(.002,.0045,.011,1)
    s.name="GRP V11 reflective cinematic lookdev"
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("baseline");p.add_argument("assets");p.add_argument("geometry");p.add_argument("output");a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    out=Path(a.output).resolve()
    if out.exists() or tuple(bpy.app.version)!=(4,5,17):raise RuntimeError("Use new output and Blender 4.5.17")
    if base.digest(a.baseline)!=base.BASE:raise RuntimeError("Wrong V09E geometry baseline")
    contract=assert_contract();bpy.ops.wm.open_mainfile(filepath=str(Path(a.baseline).resolve()));s=bpy.context.scene;s.frame_set(168)
    geo=apply_geometry(a.geometry);native=base.geometry_signature()
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=168
    base.SHOTS=SHOTS;base.WORDMARK=frames_for("wordmark")
    base.closing_cues=lambda f:{"earth":cues(f)["earth"],"stage":1-cues(f)["earth"],"sun":cues(f)["sunrise"],"tagline":cues(f)["tagline"]}
    base.stage(s);projection=base.rebuild_camera(s);environment=base.closing(s,Path(a.assets));relight(s)
    s.frame_set(168)
    if base.geometry_signature()!=native:raise RuntimeError("Post-lighting logo geometry changed")
    s.render.engine="CYCLES";s.view_settings.view_transform="AgX";s.view_settings.exposure=-.2
    s.render.image_settings.file_format="OPEN_EXR_MULTILAYER";s.render.image_settings.color_depth="16";s.render.image_settings.exr_codec="ZIP"
    s.cycles.samples=64;s.cycles.adaptive_threshold=.018;s.cycles.max_bounces=12;s.cycles.glossy_bounces=8;s.cycles.transparent_max_bounces=16
    s.render.use_motion_blur=True;s.render.motion_blur_shutter=.22
    s["creative_status"]="V11 unapproved lookdev; requires native still and motion review";s["reference_sha256"]="2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26"
    out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
    receipt={"sceneSha256":base.digest(out),"sourceBaseline":base.BASE,"geometry":geo,"nativeGeometry":native,"motion":contract,"projection":projection,"environment":environment,"nativeRender":False,"creativeApproval":False}
    out.with_suffix(".json").write_text(json.dumps(receipt,indent=2))
if __name__=="__main__":main()
