import bpy
s=bpy.context.scene
def curves(a):
    fc=getattr(a,"fcurves",None)
    return list(fc) if fc is not None and len(fc) else [f for layer in a.layers for strip in layer.strips for bag in strip.channelbags for f in bag.fcurves]
floor=bpy.data.objects["Polished reflective obsidian stage"]
floor.animation_data_clear();floor.hide_render=True
back=bpy.data.objects["V09 deep stage / physical backdrop"];back.location=(0,0,-13)
m=back.data.materials[0];m.node_tree.animation_data_clear()
n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
coord=n.new("ShaderNodeTexCoord");vec=n.new("ShaderNodeVectorMath");vec.operation="DISTANCE";vec.inputs[1].default_value=(.44,.56,0);l.new(coord.outputs["Generated"],vec.inputs[0])
r=n.new("ShaderNodeMapRange");r.clamp=True;r.interpolation_type="SMOOTHERSTEP";r.inputs["From Max"].default_value=.24;r.inputs["To Min"].default_value=1;r.inputs["To Max"].default_value=0;l.new(vec.outputs["Value"],r.inputs["Value"])
c=n.new("ShaderNodeMixRGB");c.inputs[1].default_value=(.002,.0035,.007,1);c.inputs[2].default_value=(.022,.038,.068,1);l.new(r.outputs["Result"],c.inputs[0])
e=n.new("ShaderNodeEmission");l.new(c.outputs[0],e.inputs["Color"]);e.inputs["Strength"].default_value=.85
tr=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader");l.new(tr.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);o=n.new("ShaderNodeOutputMaterial");l.new(mix.outputs[0],o.inputs["Surface"])
for f,v in [(1,0),(13,0),(26,1),(108,1),(132,0),(168,0)]:
    mix.inputs[0].default_value=v;mix.inputs[0].keyframe_insert("default_value",frame=f)
haze=bpy.data.objects["V09 bounded atmospheric depth"];haze.scale=(14,9,5);haze.location=(0,1.5,-6)
for name in ("V06 physical night-planet","V06 thin physical atmosphere"):
    ob=bpy.data.objects[name]
    for fc in curves(ob.animation_data.action):
        if fc.data_path=="location" and fc.array_index==1:
            for k in fc.keyframe_points:
                k.co.y-=3.4;k.handle_left.y-=3.4;k.handle_right.y-=3.4
            fc.update()
for name in ("Horizon thin golden ray","Horizon warm white core","Horizon amber halo"):
    ob=bpy.data.objects.get(name)
    if ob:
        ob.location.y-=.022
        nt=ob.data.materials[0].node_tree;ctl=next((x for x in nt.nodes if x.label=="Opening flare intensity"),None)
        if ctl:
            nt.animation_data_clear()
            for f,v in [(1,0),(115,0),(129,.12),(145,.21),(168,.12)]:
                ctl.outputs[0].default_value=v;ctl.outputs[0].keyframe_insert("default_value",frame=f)
for name in ("V09 warm sculpting key","V09 narrow silver edge","V09 soft frontal reflection"):
    ob=bpy.data.objects[name]
    for fc in curves(ob.data.animation_data.action):
        if fc.data_path=="energy":
            for k in fc.keyframe_points:
                k.co.y*=.78;k.handle_left.y*=.78;k.handle_right.y*=.78
            fc.update()
s["creative_status"]="V09 revised stage and horizon; unapproved"
s.frame_set(120);bpy.ops.wm.save_as_mainfile(filepath="/tmp/grp-v09/preview/gold-light-v09b.blend")
s.cycles.samples=48;s.cycles.adaptive_threshold=.025
for f in (20,65,92,120,145,168):
    s.frame_set(f);s.render.filepath=f"/tmp/grp-v09/preview/revised-{f:03}.png";bpy.ops.render.render(write_still=True)
