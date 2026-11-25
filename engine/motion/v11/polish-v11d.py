"""V11D: bounded native bevel mesh plus camera-aware physical reflections."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from mathutils.kdtree import KDTree
import numpy as np
ROOT=Path("/tmp/grp-v11");sys.path.insert(0,str(ROOT/"repo/engine/motion"));sys.path.insert(0,str(ROOT/"repo/engine/motion/v11"))
from gold_light_v02 import world_point,UNITS_PER_PIXEL,CENTER
from gold_light_v06_contours import mask,sampled
from geometry import fair_silver_top_serif
from motion_contract import cues
s=bpy.context.scene;s.frame_set(168)
q=json.load(open(ROOT/"fair-v11d.json"))
assert q["sourceSha256"]=="57640212bfc8173a8cb5c2b740129ba365898c95846db1156035c3efe1ccdf76"
brand=bpy.data.collections["V10 brand and stage"]
def signed_area(p):return sum(a.x*b.y-b.x*a.y for a,b in zip(p,p[1:]+p[:1]))*.5
def compact(p):
    # Sampled original cubic silhouette: remove only sub-0.06px duplicate
    # points, preserving large curve and serif shape.
    out=[]
    for v in p:
        if not out or (out[-1]-v).length>.00038:out.append(v)
    if len(out)>2 and (out[-1]-out[0]).length<.00038:out.pop()
    return out
def normal(p,i):
    v=p[i];a=v-p[i-1];b=p[(i+1)%len(p)]-v
    # Look a few source pixels away for a stable polished-edge normal,
    # while keeping the actual outline itself unchanged.
    def neighbor(d):
        j=i;dist=0.
        while dist<.011:
            k=(j+d)%len(p);dist+=(p[k]-p[j]).length;j=k
            if j==i:break
        return p[j]
    a=v-neighbor(-1);b=neighbor(1)-v
    if a.length<1e-9:a=v-p[i-1]
    if b.length<1e-9:b=p[(i+1)%len(p)]-v
    a.normalize();b.normalize()
    n1=Vector((a.y,-a.x,0));n2=Vector((b.y,-b.x,0))
    n=n1+n2
    if n.length<1e-5:n=n2
    n.normalize()
    return n,min(1.35,1/max(.74,n.dot(n2)))
def rasterize_triangles(verts,tris):
    W,H=1536,934;pred=np.zeros((H,W),dtype=bool)
    for tri in tris:
        a,b,c=[np.array([verts[i][0]/UNITS_PER_PIXEL+CENTER[0],CENTER[1]-verts[i][1]/UNITS_PER_PIXEL]) for i in tri]
        cross=lambda a,b,p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        if abs(cross(a,b,c))<1e-10:continue
        lo=np.minimum(np.minimum(a,b),c);hi=np.maximum(np.maximum(a,b),c)
        x0=max(0,math.floor(lo[0]));x1=min(W,math.ceil(hi[0])+1);y0=max(0,math.floor(lo[1]));y1=min(H,math.ceil(hi[1])+1)
        if x1<=x0 or y1<=y0:continue
        xx,yy=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
        e=[cross(a,b,(xx,yy)),cross(b,c,(xx,yy)),cross(c,a,(xx,yy))]
        pred[y0:y1,x0:x1]|=(e[0]>=-1e-7)&(e[1]>=-1e-7)&(e[2]>=-1e-7)|(e[0]<=1e-7)&(e[1]<=1e-7)&(e[2]<=1e-7)
    return [int.from_bytes(r.tobytes(),"little") for r in np.packbits(pred,axis=1,bitorder="little")]
def sample_mesh(loop):
    out=[]
    for i,(_,a,b) in enumerate(loop):
        c,d,_=loop[(i+1)%len(loop)];n=max(2,math.ceil(math.dist(a,d)/.65))
        for j in range(n):
            t=j/n;u=1-t;out.append(tuple(u**3*a[k]+3*u*u*t*b[k]+3*u*t*t*c[k]+t**3*d[k] for k in (0,1)))
    return out
def rounded_mesh(g,curves):
    name=g["name"];old=bpy.data.objects[name];vertices=[];faces=[];normals=[];caps=[];flat=[]
    # Outward rounded bevel uses the validated cap silhouette exactly; no
    # unbounded curve miters, no new shapes or generic replacement font.
    thickness=.175;bevel=.027;steps=10
    profile=[]
    for i in range(steps+1):
        a=(math.pi/2)*i/steps
        profile.append((bevel*math.sin(a),thickness+bevel*(math.cos(a)-1),math.sin(a),math.cos(a)))
    for i in range(steps,-1,-1):
        a=(math.pi/2)*i/steps
        profile.append((bevel*math.sin(a),-thickness-bevel*(math.cos(a)-1),math.sin(a),-math.cos(a)))
    for l in curves:
        p=compact([Vector(world_point(*x)) for x in sample_mesh(l)])
        if signed_area(p)<0:p.reverse()
        N=len(p);offset=len(vertices)
        ns=[normal(p,i) for i in range(N)]
        for radial,z,nrad,nz in profile:
            for v,(n,k) in zip(p,ns):
                d=v+n*(radial*k);vertices.append((d.x,d.y,z));normals.append((n.x*nrad,n.y*nrad,nz))
        for j in range(len(profile)-1):
            a=offset+j*N;b=a+N
            for i in range(N):
                k=(i+1)%N
                faces.append((a+i,b+i,b+k,a+k));flat.append(False)
        # Native tessellation for simple filled letter contour, preserving cap.
        tri=tessellate_polygon([p])
        if not tri:raise RuntimeError("Native cap missing")
        for tr in tri:
            if isinstance(tr[0],int):ix=list(tr)
            else:
                ix=[min(range(N),key=lambda i:(p[i]-v).length_squared) for v in tr]
            if len(set(ix))!=3:continue
            a,b,c=[p[i] for i in ix]
            if (b-a).cross(c-a).z<0:ix.reverse()
            front=tuple(offset+i for i in ix);back=tuple(offset+(len(profile)-1)*N+i for i in reversed(ix))
            faces.extend([front,back]);flat.extend([True,True]);caps.append(front)
    expected=mask([sampled(l) for l in curves],1536,934);actual=rasterize_triangles(vertices,caps)
    iou=sum((a&b).bit_count() for a,b in zip(expected,actual))/sum((a|b).bit_count() for a,b in zip(expected,actual))
    if iou<.998:raise RuntimeError("Rounded mesh cap parity failed: "+str(iou))
    # Validate surface geometry is finite, all faces index valid vertices,
    # and all face/cross-section offsets were analytically bounded.
    mesh=bpy.data.meshes.new(name+" bounded precision-machined geometry");mesh.from_pydata(vertices,[],faces)
    if mesh.validate(verbose=False):raise RuntimeError("Mesh validation modified new geometry")
    mesh.update()
    for poly,isflat in zip(mesh.polygons,flat):poly.use_smooth=not isflat
    mesh.normals_split_custom_set_from_vertices(normals)
    for mat in old.data.materials:mesh.materials.append(mat)
    old.name=name+" source curves (private, non-rendering)";old.hide_render=True;old.hide_viewport=True
    ob=bpy.data.objects.new(name,mesh);brand.objects.link(ob);ob.matrix_world=old.matrix_world.copy()
    if old.animation_data and old.animation_data.action:
        ob.animation_data_create();ob.animation_data.action=old.animation_data.action
    ob["source_raster_iou"]=g["check"]["iou"];ob["native_cap_iou"]=iou;ob["bevel_depth"]=bevel
    return {"name":name,"nativeCapIoU":iou,"vertices":len(vertices),"faces":len(faces),"maxAnalyticBevelOffset":bevel*1.35,"sourceCandidateRasterIoU":g["check"]["iou"]}
report={}
for g in q["groups"][:2]:
    curves=g["curves"]
    report[g["name"]+"Fairing"]=g["fairing"]
    report[g["name"]]=rounded_mesh(g,curves)
# Actual camera-reflected broad gradient softbox, not face emission. Match
# virtual mirror-ray intersection through the entire camera travel.
def reflect_panel(name,w,h,depth,peak):
    bpy.ops.mesh.primitive_plane_add(size=2);ob=bpy.context.object;ob.name=name;ob.scale=(w/2,h/2,1)
    for c in list(ob.users_collection):c.objects.unlink(ob)
    brand.objects.link(ob)
    ob.visible_camera=False;ob.visible_glossy=True;ob.visible_diffuse=False;ob.visible_shadow=False;ob.visible_transmission=False
    if hasattr(ob,"visible_volume_scatter"):ob.visible_volume_scatter=False
    m=bpy.data.materials.new(name);m.use_nodes=True;ob.data.materials.append(m);nt=m.node_tree;n=nt.nodes;l=nt.links;n.clear()
    uv=n.new("ShaderNodeTexCoord");xy=n.new("ShaderNodeSeparateXYZ");l.new(uv.outputs["UV"],xy.inputs[0])
    def mth(op,a,b):
        k=n.new("ShaderNodeMath");k.operation=op
        for i,v in enumerate((a,b)):
            if isinstance(v,(int,float)):k.inputs[i].default_value=v
            else:l.new(v,k.inputs[i])
        return k.outputs[0]
    # Broad luminance gradients across the reflection, alternating dark
    # bands and warm/silver highlights instead of uniformly white faces.
    v=mth("ADD",mth("MULTIPLY",xy.outputs["X"],.75),mth("MULTIPLY",xy.outputs["Y"],.25))
    ramp=n.new("ShaderNodeValToRGB");ramp.color_ramp.interpolation="EASE";ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    e=ramp.color_ramp.elements[0];e.position=0;e.color=(.012,.019,.035,1)
    for pos,c in [(.15,(.035,.055,.09,1)),(.28,(.48,.58,.73,1)),(.42,(1,.94,.82,1)),(.55,(.15,.19,.26,1)),(.67,(.025,.035,.06,1)),(.78,(.55,.65,.80,1)),(.89,(.95,.99,1,1)),(1,(.13,.17,.24,1))]:
        ramp.color_ramp.elements.new(pos).color=c
    l.new(v,ramp.inputs["Fac"])
    edges=[]
    for axis in ("X","Y"):
        u=xy.outputs[axis];v=mth("MINIMUM",u,mth("SUBTRACT",1,u));r=n.new("ShaderNodeMapRange");r.clamp=True;r.interpolation_type="SMOOTHERSTEP";r.inputs["From Max"].default_value=.12;l.new(v,r.inputs["Value"]);edges.append(r.outputs["Result"])
    gain=n.new("ShaderNodeValue");e=n.new("ShaderNodeEmission");l.new(ramp.outputs["Color"],e.inputs["Color"]);l.new(gain.outputs[0],e.inputs["Strength"])
    tr=n.new("ShaderNodeBsdfTransparent");mix=n.new("ShaderNodeMixShader");l.new(mth("MULTIPLY",*edges),mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);out=n.new("ShaderNodeOutputMaterial");l.new(mix.outputs[0],out.inputs["Surface"])
    for f in range(1,169):
        s.frame_set(f);cam=s.camera
        # Reflect rays from the actual camera aim. Use actual target
        # intersection with logo plane and move panel smoothly behind it.
        direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1))
        t=-cam.location.z/direction.z
        target=cam.location+direction*t
        target.z=0
        v=cam.location-target
        reflected=Vector((-v.x,-v.y,v.z)).normalized()
        center=target+reflected*(depth/max(.15,reflected.z))
        ob.location=center+Vector((.25*math.sin(f*.045),.12,0))
        ob.rotation_euler=(target-ob.location).to_track_quat("Z","Y").to_euler()
        ob.keyframe_insert("location",frame=f);ob.keyframe_insert("rotation_euler",frame=f)
        gain.outputs[0].default_value=peak*cues(f)["mark"];gain.outputs[0].keyframe_insert("default_value",frame=f)
    return ob
panel=reflect_panel("V11D camera-reflected studio silk",10.0,6.0,5.2,2.5)
for f in range(1,169):
    s.frame_set(f);cam=s.camera;dist=abs(cam.location.z)
    w=max(2.7,min(10.0,(dist+5.2)*36/cam.data.lens*1.30));h=max(2.0,w*.57)
    panel.scale=(w/2,h/2,1);panel.keyframe_insert("scale",frame=f)
# More forgiving but still reflective materials.
for name in ("silver-monogram","gold-r","silver-wordmark","gold-descriptor"):
    ob=bpy.data.objects[name];p=next(n for n in ob.data.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    gold=name in ("gold-r","gold-descriptor")
    p.inputs["Roughness"].default_value=(.14 if gold else .115) if name in ("silver-monogram","gold-r") else .19
    p.inputs["Base Color"].default_value=(.87,.42,.08,1) if gold else (.82,.87,.92,1)
# Wordmark must be legible, not a fully black mirror. Physically lit alloy.
for name in ("silver-wordmark","gold-descriptor"):
    p=next(n for n in bpy.data.objects[name].data.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED");p.inputs["Metallic"].default_value=.82
# Preserve a subtle environment reflection even outside the bright card.
w=s.world.node_tree.nodes.get("Background");w.inputs["Color"].default_value=(.055,.075,.105,1);w.inputs["Strength"].default_value=.19
# Mapped night Earth, dark terrain, city lights, narrow atmospheric limb.
sys.path.insert(0,str(ROOT/"repo/engine/motion/v10"))
from earth_look import uv,image,multiply
planet=bpy.data.objects["V10 mapped night Earth"];nt=planet.data.materials[0].node_tree
maps={role:next(im for im in bpy.data.images if im.name.startswith("V10 "+role+" —")) for role in ("day","night","clouds")}
n,l=nt.nodes,nt.links;n.clear();xy=uv(n,l)
day=image(n,l,xy,maps["day"]);night=image(n,l,xy,maps["night"])
a=multiply(n,l,day,(.018,.027,.043));b=multiply(n,l,night,(1,.71,.39))
terrain=n.new("ShaderNodeEmission");l.new(a,terrain.inputs["Color"]);terrain.inputs["Strength"].default_value=.95
cities=n.new("ShaderNodeEmission");l.new(b,cities.inputs["Color"]);cities.inputs["Strength"].default_value=1.65
add=n.new("ShaderNodeAddShader");l.new(terrain.outputs[0],add.inputs[0]);l.new(cities.outputs[0],add.inputs[1]);out=n.new("ShaderNodeOutputMaterial");l.new(add.outputs[0],out.inputs["Surface"])
cloud=bpy.data.objects["V10 mapped clouds"]
for k in cloud.data.materials[0].node_tree.nodes:
    if k.type=="BSDF_PRINCIPLED":k.inputs["Base Color"].default_value=(.008,.015,.028,1)
    if k.type=="MAP_RANGE":k.inputs["To Max"].default_value=.12
limb=bpy.data.objects["V10 atmospheric limb"]
for k in limb.data.materials[0].node_tree.nodes:
    if k.type=="MATH" and k.operation=="POWER":k.inputs[1].default_value=24.0
    if k.type=="EMISSION":k.inputs["Strength"].default_value=1.35
floor=bpy.data.objects["Polished reflective obsidian stage"];p=next(n for n in floor.data.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED")
p.inputs["Base Color"].default_value=(.009,.010,.014,1);p.inputs["Metallic"].default_value=.22;p.inputs["Roughness"].default_value=.15
if p.inputs.get("Specular IOR Level"):p.inputs["Specular IOR Level"].default_value=.24
for ob in brand.objects:
    if ob.type=="LIGHT" and ob.name.startswith("V11 elongated golden floor pool"):
        ob.data.size=.16;ob.data.size_y=2.4
# Keep all lighting/scene motion and original private source curves.
s.name="GRP V11D fair chrome and dark mapped Earth";s["creative_status"]="native V11D review, no creative approval"
s.frame_set(168);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"v11d.blend"))
report["sceneSha256"]=hashlib.sha256((ROOT/"v11d.blend").read_bytes()).hexdigest();report["creativeApproval"]=False
(ROOT/"v11d-geometry.json").write_text(json.dumps(report,indent=2));print("V11D_NATIVE_GEOMETRY",json.dumps(report),flush=True)
