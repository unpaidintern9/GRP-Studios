"""Texture-based native Earth look, isolated from brand lighting and camera.
Solar System Scope maps are staged privately and packed into the blend.
"""
import bpy, math, hashlib, json
from pathlib import Path
from mathutils import Vector, Matrix
from horizon_math import screen_ray, fit_horizon, unit
LICENSE="https://creativecommons.org/licenses/by/4.0/"
def load_maps(root):
    root=Path(root).resolve();m=json.loads((root/"earth-assets.json").read_text())
    if m.get("provider")!="Solar System Scope" or m.get("license")!=LICENSE or set(m["assets"])!={"day","night","clouds"}:raise RuntimeError("Invalid Earth asset provenance")
    images={}
    for role,a in m["assets"].items():
        p=(root/a["file"]).resolve()
        if p.parent!=root or hashlib.sha256(p.read_bytes()).hexdigest()!=a["sha256"]:raise RuntimeError("Earth texture digest mismatch")
        im=bpy.data.images.load(str(p),check_existing=False)
        if tuple(im.size)!=(8192,4096):raise RuntimeError("Expected 8K map")
        im.name="V10 "+role+" — licensed Earth map";im.pack()
        images[role]=im
    return images,m

def nodes(name):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
    return m,nt.nodes,nt.links
def scalar(n,l,op,a,b=None):
    k=n.new("ShaderNodeMath");k.operation=op
    for i,v in enumerate([a] if b is None else [a,b]):
        if isinstance(v,(float,int)):k.inputs[i].default_value=v
        else:l.new(v,k.inputs[i])
    return k.outputs[0]
def image(n,l,coord,im):
    k=n.new("ShaderNodeTexImage");k.image=im;k.extension="REPEAT";k.interpolation="Linear";l.new(coord,k.inputs["Vector"]);return k.outputs["Color"]
def multiply(n,l,col,c):
    k=n.new("ShaderNodeMixRGB");k.blend_type="MULTIPLY";k.inputs[0].default_value=1;k.inputs[2].default_value=(*c,1);l.new(col,k.inputs[1]);return k.outputs[0]
def uv(n,l):
    # Explicit equirectangular mapping from local sphere coordinates:
    # longitude -180..180, latitude -90..90, north at image top.
    coord=n.new("ShaderNodeTexCoord");sub=n.new("ShaderNodeVectorMath");sub.operation="SUBTRACT";sub.inputs[1].default_value=(.5,.5,.5);l.new(coord.outputs["Generated"],sub.inputs[0])
    norm=n.new("ShaderNodeVectorMath");norm.operation="NORMALIZE";l.new(sub.outputs[0],norm.inputs[0])
    xyz=n.new("ShaderNodeSeparateXYZ");l.new(norm.outputs[0],xyz.inputs[0])
    u=scalar(n,l,"ADD",scalar(n,l,"DIVIDE",scalar(n,l,"ARCTAN2",xyz.outputs["Y"],xyz.outputs["X"]),2*math.pi),.5)
    v=scalar(n,l,"ADD",scalar(n,l,"DIVIDE",scalar(n,l,"ARCSINE",xyz.outputs["Z"]),math.pi),.5)
    combine=n.new("ShaderNodeCombineXYZ");l.new(u,combine.inputs["X"]);l.new(v,combine.inputs["Y"]);return combine.outputs[0]
def dayfactor(n,l,sun):
    g=n.new("ShaderNodeNewGeometry");d=n.new("ShaderNodeVectorMath");d.operation="DOT_PRODUCT";l.new(g.outputs["Normal"],d.inputs[0]);d.inputs[1].default_value=tuple(sun)
    q=n.new("ShaderNodeMapRange");q.clamp=True;q.interpolation_type="SMOOTHERSTEP";q.inputs["From Min"].default_value=-.16;q.inputs["From Max"].default_value=.15;l.new(d.outputs["Value"],q.inputs["Value"]);return q.outputs["Result"]
def surface(images,sun):
    m,n,l=nodes("V10 Earth | mapped ocean, land and genuine city-light texture")
    xy=uv(n,l);day=image(n,l,xy,images["day"]);night=image(n,l,xy,images["night"])
    daylight=dayfactor(n,l,sun);dark=scalar(n,l,"SUBTRACT",1,daylight)
    p=n.new("ShaderNodeBsdfPrincipled");l.new(multiply(n,l,day,(.32,.40,.53)),p.inputs["Base Color"]);p.inputs["Roughness"].default_value=.73;p.inputs["Metallic"].default_value=0
    # Suppress background lift and retain warm urban clusters.
    e=n.new("ShaderNodeEmission");l.new(multiply(n,l,night,(1.0,.83,.60)),e.inputs["Color"]);l.new(scalar(n,l,"MULTIPLY",dark,3.6),e.inputs["Strength"])
    a=n.new("ShaderNodeAddShader");l.new(p.outputs[0],a.inputs[0]);l.new(e.outputs[0],a.inputs[1]);o=n.new("ShaderNodeOutputMaterial");l.new(a.outputs[0],o.inputs["Surface"]);return m
def clouds(images,sun):
    m,n,l=nodes("V10 Earth | thin cloud shell")
    c=image(n,l,uv(n,l),images["clouds"]);bw=n.new("ShaderNodeRGBToBW");l.new(c,bw.inputs[0])
    q=n.new("ShaderNodeMapRange");q.clamp=True;q.inputs["From Min"].default_value=.10;q.inputs["From Max"].default_value=.83;q.inputs["To Max"].default_value=.45;l.new(bw.outputs[0],q.inputs["Value"])
    p=n.new("ShaderNodeBsdfPrincipled");p.inputs["Base Color"].default_value=(.28,.39,.58,1);p.inputs["Roughness"].default_value=.92
    tr=n.new("ShaderNodeBsdfTransparent");a=n.new("ShaderNodeMixShader");l.new(q.outputs["Result"],a.inputs[0]);l.new(tr.outputs[0],a.inputs[1]);l.new(p.outputs[0],a.inputs[2]);o=n.new("ShaderNodeOutputMaterial");l.new(a.outputs[0],o.inputs["Surface"]);return m
def atmosphere(sun):
    m,n,l=nodes("V10 Earth | thin blue and amber limb")
    g=n.new("ShaderNodeNewGeometry");v=n.new("ShaderNodeVectorMath");v.operation="DOT_PRODUCT";l.new(g.outputs["Normal"],v.inputs[0]);l.new(g.outputs["Incoming"],v.inputs[1])
    rim=scalar(n,l,"POWER",scalar(n,l,"SUBTRACT",1,scalar(n,l,"ABSOLUTE",v.outputs["Value"])),4.5)
    alpha=scalar(n,l,"MULTIPLY",rim,scalar(n,l,"SUBTRACT",1,g.outputs["Backfacing"]))
    d=dayfactor(n,l,sun);mix=n.new("ShaderNodeMixRGB");l.new(d,mix.inputs[0]);mix.inputs[1].default_value=(.055,.20,.58,1);mix.inputs[2].default_value=(1,.64,.25,1)
    e=n.new("ShaderNodeEmission");l.new(mix.outputs[0],e.inputs["Color"]);e.inputs["Strength"].default_value=1.5
    tr=n.new("ShaderNodeBsdfTransparent");a=n.new("ShaderNodeMixShader");l.new(alpha,a.inputs[0]);l.new(tr.outputs[0],a.inputs[1]);l.new(e.outputs[0],a.inputs[2]);o=n.new("ShaderNodeOutputMaterial");l.new(a.outputs[0],o.inputs["Surface"]);return m

def build(s,cam,collection,maps):
    frame=cam.data.view_frame(scene=s)
    fr=(min(v.x for v in frame),max(v.x for v in frame),min(v.y for v in frame),max(v.y for v in frame),frame[0].z)
    fit=fit_horizon(fr,radius=100,apex=.805,edge=.875);center=cam.matrix_world@Vector(fit["center"])
    rotation=cam.matrix_world.to_quaternion();ray=Vector(screen_ray(fr,.5,fit["apex"]));worldray=rotation@ray
    down=Vector((0,-1,0))-ray*Vector((0,-1,0)).dot(ray);down.normalize()
    radial=rotation@(-down);north=worldray.normalized();east=north.cross(radial).normalized()
    lat,lon=map(math.radians,(39,-87));source=Vector((math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat)))
    sn=(Vector((0,0,1))-source*source.z).normalized();se=sn.cross(source).normalized()
    orient=(Matrix((east,north,radial)).transposed()@Matrix((se,sn,source))).to_quaternion()
    sun=(worldray+.025*radial).normalized()
    def put(ob):
        for c in list(ob.users_collection):c.objects.unlink(ob)
        collection.objects.link(ob)
    for name,r,mat in [("V10 mapped night Earth",100,surface(maps,sun)),("V10 mapped clouds",100.15,clouds(maps,sun)),("V10 atmospheric limb",100.34,atmosphere(sun))]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=256,ring_count=128,radius=r,location=center)
        ob=bpy.context.object;ob.name=name;ob.rotation_mode="QUATERNION";ob.rotation_quaternion=orient;ob.data.materials.append(mat);put(ob)
        for p in ob.data.polygons:p.use_smooth=True
        ob.visible_shadow=False
    data=bpy.data.lights.new("V10 horizon solar illumination","SUN");data.energy=2.0;data.color=(1,.76,.43);data.angle=.0093
    ob=bpy.data.objects.new(data.name,data);collection.objects.link(ob);ob.rotation_euler=(-sun).to_track_quat("-Z","Y").to_euler()
    fit.update({"world_center":list(center),"geographic_reference":[39,-87],"textured":True,"artistic_not_live":True})
    return fit
