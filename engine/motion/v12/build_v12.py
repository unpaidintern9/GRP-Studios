"""V12 native look-development patch, applied to a reconstructed V11F scene.

Inputs: a local/private V11F reconstruction, the exact private fair contour
artifact, and a fresh output path. Run with Blender 4.5.17. The packed V11F
scene was not archived, so reconstruct it from the recorded V11 sources and
retain the resulting scene hash. No image overlays, no substitute font, no
GPU allocation. A successful build is NOT visual approval.
"""
import bpy,sys,math,json,hashlib
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from mathutils.kdtree import KDTree
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent))
from transition_contract import cues,ease,FEATHER,validate as validate_transition
from sculpt_profile import surface_z,validate as validate_profile
from gold_light_v02 import world_point,UNITS_PER_PIXEL,CENTER
from gold_light_v06_contours import mask,sampled

FAIR_SHA="965ef68b193f2d28cd73c9e9b310395170cfb10cf130043252a35a3edf289d80"
SOURCE_SHA="57640212bfc8173a8cb5c2b740129ba365898c95846db1156035c3efe1ccdf76"
GROUPS=("silver-monogram","gold-r")
W,H=1536,934

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polygon(loop):
    out=[]
    for pt in sampled(loop):
        v=Vector(world_point(*pt)[:2])
        if not out or (out[-1]-v).length>.0025:out.append(v)
    if (out[-1]-out[0]).length<.0025:out.pop()
    a=sum(v.x*w.y-v.y*w.x for v,w in zip(out,out[1:]+out[:1]))
    if a<0:out.reverse()
    if len(out)<3:raise RuntimeError("Invalid contour")
    return out

def interior_points(p,kd,step=.013):
    ymin=min(v.y for v in p);ymax=max(v.y for v in p)
    y=math.ceil(ymin/step)*step
    while y<ymax:
        xs=[]
        for a,b in zip(p,p[1:]+p[:1]):
            if min(a.y,b.y)<=y<max(a.y,b.y):
                xs.append(a.x+(y-a.y)*(b.x-a.x)/(b.y-a.y))
        xs.sort()
        if len(xs)%2:raise RuntimeError("Odd scanline")
        for a,b in zip(xs[::2],xs[1::2]):
            x=math.ceil(a/step)*step
            while x<b:
                v=Vector((x,y))
                if kd.find(Vector((x,y,0)))[2]>.008:yield v
                x+=step
        y+=step

def planar_mesh(p):
    kd=KDTree(len(p))
    for i,v in enumerate(p):kd.insert(Vector((v.x,v.y,0)),i)
    kd.balance()
    N=len(p);points=p+list(interior_points(p,kd))
    edges=[(i,(i+1)%N) for i in range(N)]
    v,e,f,ov,oe,of=delaunay_2d_cdt(points,[],[list(range(N))],0,1e-5,True)
    if not f or any(len(t)!=3 for t in f):raise RuntimeError("Expected constrained triangles")
    tris=[]
    for t,original_faces in zip(f,of):
        if 0 not in original_faces:continue
        a,b,c=[v[i] for i in t];cross=(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)
        if abs(cross)<1e-18:raise RuntimeError("Zero area constrained triangle: "+repr((tuple(t),[tuple(z) for z in (a,b,c)],cross)))
        tris.append(tuple(t if cross>0 else t[::-1]))
    if not tris:raise RuntimeError("No nondegenerate constrained triangles")
    used=sorted({i for t in tris for i in t});remap={i:j for j,i in enumerate(used)}
    v=[v[i] for i in used];tris=[tuple(remap[i] for i in t) for t in tris]
    edge_count=Counter(tuple(sorted((a,b))) for t in tris for a,b in zip(t,t[1:]+t[:1]))
    if max(edge_count.values())>2:raise RuntimeError("Nonmanifold planar mesh")
    boundary={i for e,n in edge_count.items() if n==1 for i in e}
    if len(boundary)<3:raise RuntimeError("Missing exact boundary")
    boundary_edges=[e for e,n in edge_count.items() if n==1]
    neighbors={i:[] for i in boundary}
    for a,b in boundary_edges:neighbors[a].append(b);neighbors[b].append(a)
    if any(len(q)!=2 for q in neighbors.values()):raise RuntimeError("Boundary not a simple loop")
    visited=set();stack=[next(iter(boundary))]
    while stack:
        i=stack.pop()
        if i in visited:continue
        visited.add(i);stack.extend(j for j in neighbors[i] if j not in visited)
    if visited!=boundary:raise RuntimeError("Extra native boundary loop")
    if max(kd.find(Vector((v[i].x,v[i].y,0)))[2] for i in boundary)>.004:raise RuntimeError("Boundary escaped source corridor")
    if len(v)-len(edge_count)+len(tris)!=1:raise RuntimeError("Invalid planar topology")
    heights=[]
    for i,x in enumerate(v):
        d=0. if i in boundary else kd.find(Vector((x.x,x.y,0)))[2]
        heights.append(surface_z(d))
    # Boundary orientation follows CCW face winding; the side quad uses
    # the opposite edge direction so every shell edge has two incident faces.
    outer=[(a,b) for t in tris for a,b in zip(t,t[1:]+t[:1]) if edge_count[tuple(sorted((a,b)))]==1]
    return v,tris,heights,outer

def rasterize(verts,tris):
    pred=np.zeros((H,W),dtype=bool)
    for t in tris:
        a,b,c=[np.array([verts[i][0]/UNITS_PER_PIXEL+CENTER[0],CENTER[1]-verts[i][1]/UNITS_PER_PIXEL]) for i in t]
        cross=lambda a,b,p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        lo=np.minimum(np.minimum(a,b),c);hi=np.maximum(np.maximum(a,b),c)
        x0=max(0,math.floor(lo[0]));x1=min(W,math.ceil(hi[0])+1)
        y0=max(0,math.floor(lo[1]));y1=min(H,math.ceil(hi[1])+1)
        if x1<=x0 or y1<=y0:continue
        xx,yy=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
        e=[cross(a,b,(xx,yy)),cross(b,c,(xx,yy)),cross(c,a,(xx,yy))]
        pred[y0:y1,x0:x1]|=(e[0]>=-1e-7)&(e[1]>=-1e-7)&(e[2]>=-1e-7)|(e[0]<=1e-7)&(e[1]<=1e-7)&(e[2]<=1e-7)
    return [int.from_bytes(r.tobytes(),"little") for r in np.packbits(pred,axis=1,bitorder="little")]

def sculpt(g):
    name=g["name"];ob=bpy.data.objects[name]
    if ob.type!="MESH":raise RuntimeError("Reconstruct native V11F mesh first")
    curves=g["curves"];vertices=[];faces=[];caps=[]
    # The two monogram groups contain simple filled components, not nested
    # counters. The exact expected topology is deliberately enforced here.
    if len(curves)!=(2 if name=="silver-monogram" else 1):
        raise RuntimeError("Unexpected monogram component topology")
    for loop in curves:
        p=polygon(loop);v,tri,h,outer=planar_mesh(p)
        n=len(v);off=len(vertices)
        vertices.extend((a.x,a.y,z) for a,z in zip(v,h))
        vertices.extend((a.x,a.y,-z) for a,z in zip(v,h))
        front=[tuple(off+i for i in t) for t in tri]
        faces.extend(front);caps.extend(front)
        faces.extend(tuple(off+n+i for i in reversed(t)) for t in tri)
        faces.extend((off+b,off+a,off+n+a,off+n+b) for a,b in outer)
    if not all(math.isfinite(x) for v in vertices for x in v):raise RuntimeError("Nonfinite crown")
    count=Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1]))
    if not count or set(count.values())!={2}:raise RuntimeError("Crown shell must be watertight")
    expected=mask([sampled(l) for l in curves],W,H);actual=rasterize(vertices,caps)
    union=sum((a|b).bit_count() for a,b in zip(expected,actual))
    iou=sum((a&b).bit_count() for a,b in zip(expected,actual))/union
    if iou<.998:
        print("CAP_DIAGNOSTIC",name,len(vertices),len(caps),sum(a.bit_count() for a in expected),sum(a.bit_count() for a in actual),sum((a&b).bit_count() for a,b in zip(expected,actual)),flush=True)
        arr=np.zeros((H,W,3),dtype=np.uint8)
        for y,(a,b) in enumerate(zip(expected,actual)):
            arr[y,:,0]=np.unpackbits(np.frombuffer(a.to_bytes(W//8,"little"),np.uint8),bitorder="little")*255
            arr[y,:,1]=np.unpackbits(np.frombuffer(b.to_bytes(W//8,"little"),np.uint8),bitorder="little")*255
        np.save("/tmp/grp-v12/cap-diagnostic.npy",arr)
        raise RuntimeError("Native sculpted-cap projection mismatch "+str(iou))
    old=ob.data;new=bpy.data.meshes.new(name+" V12 inset sculpted crown")
    new.from_pydata(vertices,[],faces)
    if new.validate(verbose=False):raise RuntimeError("Unexpected native mesh correction")
    new.update()
    for p in new.polygons:p.use_smooth=True
    for m in old.materials:new.materials.append(m)
    old.use_fake_user=True;ob.data=new
    # Smoothly varying metal normals, not an emissive face.
    p=next(n for n in new.materials[0].node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    p.inputs["Metallic"].default_value=1.
    p.inputs["Roughness"].default_value=.11 if name=="silver-monogram" else .14
    p.inputs["Base Color"].default_value=(.83,.88,.94,1) if name=="silver-monogram" else (.85,.43,.075,1)
    if p.inputs.get("Emission Strength"):p.inputs["Emission Strength"].default_value=0
    return {"name":name,"nativeCapIoU":iou,"watertight":True,"vertices":len(vertices),
            "faces":len(faces),"sourceRasterIoU":g["fairing"]["directOriginalRasterIoU"],
            "maxDepth":max(v[2] for v in vertices)-min(v[2] for v in vertices)}

def anim(socket,values):
    for f,v in values:
        socket.default_value=v;socket.keyframe_insert("default_value",frame=f)

def math_node(nt,op,a,b):
    n=nt.nodes.new("ShaderNodeMath");n.operation=op
    for i,v in enumerate((a,b)):
        if isinstance(v,(float,int)):n.inputs[i].default_value=v
        else:nt.links.new(v,n.inputs[i])
    return n.outputs[0]

def value(nt,name,fn):
    n=nt.nodes.new("ShaderNodeValue");n.label=name
    anim(n.outputs[0],[(f,fn(f)) for f in range(1,169)])
    return n.outputs[0]

def spatial_reveal(nt,kind):
    n,l=nt.nodes,nt.links
    tex=n.new("ShaderNodeTexCoord")
    xyz=n.new("ShaderNodeSeparateXYZ");l.new(tex.outputs["Window"],xyz.inputs[0])
    head=value(nt,"V12 "+kind+" advancing feather",lambda f:cues(f)[kind+"_head"])
    dist=math_node(nt,"SUBTRACT",math_node(nt,"ADD",head,FEATHER/2),xyz.outputs["Y"])
    ramp=n.new("ShaderNodeMapRange");ramp.clamp=True;ramp.interpolation_type="SMOOTHERSTEP"
    ramp.inputs["From Min"].default_value=0.;ramp.inputs["From Max"].default_value=FEATHER
    l.new(dist,ramp.inputs["Value"])
    return ramp.outputs["Result"]

def wrap_surface(nt,factor):
    out=next(n for n in nt.nodes if n.type=="OUTPUT_MATERIAL" and n.is_active_output)
    old=out.inputs["Surface"].links[0].from_socket
    transparent=nt.nodes.new("ShaderNodeBsdfTransparent");mix=nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(factor,mix.inputs[0]);nt.links.new(transparent.outputs[0],mix.inputs[1])
    nt.links.new(old,mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs["Surface"])

def transition(s):
    # Spatial rather than simultaneous global dissolve. The Earth stays
    # fixed, with its real textures, thin limb and actual broad curvature.
    for name in ("V10 mapped night Earth","V10 mapped clouds","V10 atmospheric limb"):
        ob=bpy.data.objects[name];nt=ob.data.materials[0].node_tree
        wrap_surface(nt,spatial_reveal(nt,"earth"))
    floor=bpy.data.objects["Polished reflective obsidian stage"]
    nt=floor.data.materials[0].node_tree
    out=next(n for n in nt.nodes if n.type=="OUTPUT_MATERIAL" and n.is_active_output)
    mix=out.inputs["Surface"].links[0].from_node
    if mix.type!="MIX_SHADER":raise RuntimeError("Unexpected stage opacity")
    old=mix.inputs[0].links[0].from_node
    if old.type!="MATH" or old.operation!="MULTIPLY" or not old.inputs[0].is_linked:
        raise RuntimeError("Expected original spatial stage falloff")
    falloff=old.inputs[0].links[0].from_socket
    entrance=value(nt,"V12 original stage entrance",lambda f:ease(43,57,f))
    tail=value(nt,"V12 final stage clearance",lambda f:cues(f)["stage_tail"])
    keep=math_node(nt,"SUBTRACT",1.,spatial_reveal(nt,"stage"))
    opacity=math_node(nt,"MULTIPLY",math_node(nt,"MULTIPLY",falloff,entrance),math_node(nt,"MULTIPLY",keep,tail))
    nt.links.new(opacity,mix.inputs[0])
    # Earth opacity is now controlled by its own feathered geometry; do
    # not attenuate it again with the old 14-frame compositor dissolve.
    over=[n for n in s.node_tree.nodes if n.type=="ALPHAOVER" and n.inputs[2].is_linked and
          n.inputs[2].links[0].from_node.type=="R_LAYERS" and n.inputs[2].links[0].from_node.layer=="Earth"]
    if len(over)!=1:raise RuntimeError("Missing isolated Earth composite")
    anim(over[0].inputs[0],[(f,1.) for f in range(1,169)])
    for ob in s.objects:
        if ob.type=="MESH" and ob.name.startswith("V10 sun") and ob.data.materials:
            nt=ob.data.materials[0].node_tree
            ctl=next(n for n in nt.nodes if n.label=="Opening flare intensity")
            anim(ctl.outputs[0],[(f,cues(f)["sunrise"]) for f in range(1,169)])
        if ob.type=="LIGHT" and ob.name.startswith("V11 elongated golden floor pool"):
            s.frame_set(113);energy=ob.data.energy
            for f in range(91,169):
                ob.data.energy=energy*cues(f)["ground_glints"];ob.data.keyframe_insert("energy",frame=f)
    tag=bpy.data.objects["V06 closing tagline"];nt=tag.data.materials[0].node_tree
    mix=next(n for n in nt.nodes if n.type=="MIX_SHADER")
    anim(mix.inputs[0],[(f,cues(f)["tagline"]) for f in range(1,169)])
    # Do not change the original camera aim or physical Earth placement.
    s.cycles.transparent_max_bounces=max(24,s.cycles.transparent_max_bounces)
    return validate_transition()

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("baseline");p.add_argument("fair");p.add_argument("output");a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    src,fair,out=map(Path,(a.baseline,a.fair,a.output));src=src.resolve();out=out.resolve()
    if tuple(bpy.app.version)!=(4,5,17) or out.exists() or src==out:raise RuntimeError("Pinned Blender and fresh output required")
    if sha(fair)!=FAIR_SHA:raise RuntimeError("Wrong private fair contours")
    q=json.loads(fair.read_text())
    if q["sourceSha256"]!=SOURCE_SHA:raise RuntimeError("Original artwork mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;s.frame_set(168)
    if not s.name.startswith("GRP V11F"):raise RuntimeError("Reconstruct V11F first")
    if (s.frame_start,s.frame_end,s.render.fps,s.render.fps_base)!=(1,168,24,1):raise RuntimeError("Wrong native format")
    profile=validate_profile();geo=[sculpt(g) for g in q["groups"] if g["name"] in GROUPS]
    if len(geo)!=2:raise RuntimeError("Missing monogram")
    timing=transition(s);s.name="GRP V12 sculpted chrome and continuous horizon"
    s["creative_status"]="V12 unapproved look development; native visual and motion QA required"
    s.frame_set(168);bpy.context.view_layer.update()
    out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
    out.with_suffix(".json").write_text(json.dumps({"baselineSha256":sha(src),"sceneSha256":sha(out),"fairSha256":FAIR_SHA,"geometry":geo,"profile":profile,"transition":timing,"nativeRender":False,"creativeApproval":False},indent=2))
if __name__=="__main__":main()
