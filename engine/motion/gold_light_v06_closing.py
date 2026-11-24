"""Native 3D night-planet finale; no reference imagery or generated logo.
The planet is an artistic procedural Earth-like horizon, not geographic data.
"""
import bpy, math
from mathutils import Vector
from gold_light_v03 import keys
from gold_light_v02 import optical_card

def mathnode(n,l,op,a,b=None):
    p=n.new("ShaderNodeMath");p.operation=op
    for i,v in enumerate([a] if b is None else [a,b]):
        if isinstance(v,(int,float)):p.inputs[i].default_value=v
        else:l.new(v,p.inputs[i])
    return p.outputs[0]

def noise(n,l,coord,scale,detail,rough):
    p=n.new("ShaderNodeTexNoise");p.inputs["Scale"].default_value=scale;p.inputs["Detail"].default_value=detail;p.inputs["Roughness"].default_value=rough;l.new(coord,p.inputs["Vector"]);return p.outputs["Fac"]

def ramp(n,l,value,stops):
    p=n.new("ShaderNodeValToRGB");r=p.color_ramp
    for i,(at,c) in enumerate(stops):
        e=r.elements[0] if i==0 else r.elements[-1] if i==len(stops)-1 else r.elements.new(at)
        e.position=at;e.color=(*c,1)
    l.new(value,p.inputs[0]);return p.outputs["Color"]

def planet_material():
    m=bpy.data.materials.new("Night planet | clustered lights and cloud wisps");m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    c=n.new("ShaderNodeTexCoord").outputs["Generated"]
    continents=noise(n,l,c,5.2,4.0,.65)
    land=mathnode(n,l,"GREATER_THAN",continents,.49)
    relief=noise(n,l,c,28,4,.68)
    base=ramp(n,l,mathnode(n,l,"MULTIPLY",land,relief),[(0,(.0011,.0038,.009)),(.27,(.004,.012,.020)),(.7,(.012,.024,.035))])
    clusters=noise(n,l,c,37,3,.7)
    settle=mathnode(n,l,"MULTIPLY",land,mathnode(n,l,"GREATER_THAN",clusters,.56))
    fine=noise(n,l,c,285,2,.72)
    dots=mathnode(n,l,"POWER",mathnode(n,l,"MAXIMUM",mathnode(n,l,"SUBTRACT",fine,.56),0),1.5)
    intensity=mathnode(n,l,"MULTIPLY",mathnode(n,l,"MULTIPLY",settle,dots),11.0)
    # Long cloud filaments, subdued rather than bright noisy wallpaper.
    stretch=n.new("ShaderNodeVectorMath");stretch.operation="MULTIPLY";stretch.inputs[1].default_value=(.8,2.2,1.0);l.new(c,stretch.inputs[0])
    clouds=noise(n,l,stretch.outputs[0],12,3,.65)
    cloud=mathnode(n,l,"MULTIPLY",mathnode(n,l,"MAXIMUM",mathnode(n,l,"SUBTRACT",clouds,.52),0),.22)
    p=n.new("ShaderNodeEmission");l.new(base,p.inputs["Color"]);p.inputs["Strength"].default_value=1
    q=n.new("ShaderNodeEmission");q.inputs["Color"].default_value=(1,.42,.07,1);l.new(intensity,q.inputs["Strength"])
    h=n.new("ShaderNodeEmission");h.inputs["Color"].default_value=(.14,.27,.5,1);l.new(cloud,h.inputs["Strength"])
    add=n.new("ShaderNodeAddShader");l.new(p.outputs[0],add.inputs[0]);l.new(q.outputs[0],add.inputs[1])
    add2=n.new("ShaderNodeAddShader");l.new(add.outputs[0],add2.inputs[0]);l.new(h.outputs[0],add2.inputs[1])
    out=n.new("ShaderNodeOutputMaterial");l.new(add2.outputs[0],out.inputs["Surface"])
    return m

def atmosphere_material():
    m=bpy.data.materials.new("Thin atmospheric blue limb");m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    geom=n.new("ShaderNodeNewGeometry");dot=n.new("ShaderNodeVectorMath");dot.operation="DOT_PRODUCT";l.new(geom.outputs["Normal"],dot.inputs[0]);l.new(geom.outputs["Incoming"],dot.inputs[1])
    rim=mathnode(n,l,"POWER",mathnode(n,l,"SUBTRACT",1,mathnode(n,l,"ABSOLUTE",dot.outputs["Value"])),3.6)
    back=mathnode(n,l,"SUBTRACT",1,geom.outputs["Backfacing"])
    alpha=mathnode(n,l,"MULTIPLY",rim,back)
    e=n.new("ShaderNodeEmission");e.inputs["Color"].default_value=(.035,.24,1,1);e.inputs["Strength"].default_value=2.4
    tr=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader");l.new(alpha,mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);o=n.new("ShaderNodeOutputMaterial");l.new(mix.outputs[0],o.inputs["Surface"])
    return m

def sphere(name,cam,radius,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128,ring_count=64,radius=radius)
    o=bpy.context.object;o.name=name;o.parent=cam;o.location=(0,-39,-55)
    o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    for attr in ("visible_shadow","visible_diffuse","visible_glossy","visible_transmission","visible_volume_scatter"):
        if hasattr(o,attr):setattr(o,attr,False)
    for frame,y in [(1,-39),(78,-39),(85,-34),(88,-30.5),(98,-29.6),(120,-29.6)]:
        o.location.y=y;o.keyframe_insert(data_path="location",frame=frame)
    for frame,visible in [(1,False),(78,False),(79,True),(120,True)]:
        o.hide_render=not visible;o.keyframe_insert(data_path="hide_render",frame=frame)
    return o

def add_closing(s,bounds):
    cam=s.camera
    globe=sphere("V06 physical night-planet",cam,22,planet_material())
    for f,theta in [(1,0),(79,0),(98,.025),(120,.042)]:
        globe.rotation_euler=(.26,theta,.12);globe.keyframe_insert(data_path="rotation_euler",frame=f)
    sphere("V06 thin physical atmosphere",cam,22.10,atmosphere_material())
    # The new physical horizon rises as the reflective stage dissolves into
    # darkness; the official wordmark stays in place in its own scene.
    floor=bpy.data.objects["Polished reflective obsidian stage"]
    tree=floor.data.materials[0].node_tree
    fade=next(n for n in tree.nodes if n.type=="MATH" and n.operation=="MULTIPLY")
    keys(fade.inputs[1],[(1,0),(9,0),(20,.4),(36,1),(78,1),(84,.6),(89,.08),(93,0),(120,0)])
    streak=bpy.data.objects["Grounded gold reflection streak"]
    em=next(n for n in streak.data.materials[0].node_tree.nodes if n.type=="EMISSION")
    keys(em.inputs["Strength"],[(78,1),(84,.4),(90,0),(98,0),(120,0)])
    # Small sunset flare at the physical horizon. No brand image overlay.
    for name,depth,sx,sy,col,strength in [
        ("Horizon thin golden ray",.62,.16,.0022,(1,.52,.12),4.2),
        ("Horizon warm white core",.60,.025,.006,(1,.81,.4),6.0),
        ("Horizon amber halo",.64,.10,.018,(1,.38,.08),.75)]:
        o=optical_card(cam,name,depth,sx,sy,col,strength,.25,.18);o.location.y=-.077
        tree=o.data.materials[0].node_tree;tree.animation_data_clear()
        ctl=next(n for n in tree.nodes if n.label=="Opening flare intensity")
        keys(ctl.outputs[0],[(1,0),(78,0),(85,.08),(88,.55),(97,1),(106,.42),(120,.28)])
    # Separately authorized campaign line, native lettering; original
    # stacked GRP artwork is untouched. Anchor below its exact bounds.
    c=bpy.data.curves.new("Approved campaign line","FONT");c.body="SEE BEYOND THE NOISE.";c.align_x="CENTER";c.align_y="CENTER";c.size=.165;c.space_character=1.6
    o=bpy.data.objects.new("V06 closing tagline",c);s.collection.objects.link(o)
    bottom=bounds["gold-descriptor"][2];o.location=(0,bottom-.30,.015)
    mat=bpy.data.materials.new("Quiet white closing typography");mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
    e=n.new("ShaderNodeEmission");e.inputs["Color"].default_value=(.82,.88,1,1);e.inputs["Strength"].default_value=1.2
    t=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader");l.new(t.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);out=n.new("ShaderNodeOutputMaterial");l.new(mix.outputs[0],out.inputs["Surface"]);keys(mix.inputs[0],[(1,0),(99,0),(106,1),(120,1)])
    c.materials.append(mat)
    s["closing_treatment"]="native procedural night planet and SEE BEYOND THE NOISE."
    s.timeline_markers.new("Night horizon emerges",frame=87);s.timeline_markers.new("Campaign line resolves",frame=106)
