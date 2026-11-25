"""V11 native-fill gate. Import private raster-validated candidates only if
Blender's actual tessellated planar fill independently matches their masks.
Never use rejected V09d or overwrite the original geometry blindly.
"""
import hashlib,json,math,sys
from pathlib import Path
import bpy,numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from gold_light_v02 import CENTER,UNITS_PER_PIXEL,world_point
from gold_light_v06_contours import mask,sampled
SOURCE="57640212bfc8173a8cb5c2b740129ba365898c95846db1156035c3efe1ccdf76"
CANDIDATE="b2449b972d53d893604b2601d2800e26fca4663892b7c38212e3556d3c4a42aa"
W,H=1536,934
def fill_parity(curve,curves):
    # Evaluate a zero-thickness clone. Rasterize actual native mesh triangles,
    # not a second trace of the same cubic spline. Detect malformed counters.
    c=curve.copy();c.extrude=0;c.bevel_depth=0;c.offset=0
    o=bpy.data.objects.new("Private V11 native planar fill QA",c);bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    try:
        m.calc_loop_triangles();pred=np.zeros((H,W),dtype=bool);count=0
        for tr in m.loop_triangles:
            a,b,d=[np.array([m.vertices[i].co.x/UNITS_PER_PIXEL+CENTER[0],CENTER[1]-m.vertices[i].co.y/UNITS_PER_PIXEL]) for i in tr.vertices]
            cross=lambda a,b,p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
            if abs(cross(a,b,d))<1e-10:continue
            lo=np.minimum(np.minimum(a,b),d);hi=np.maximum(np.maximum(a,b),d)
            x0=max(0,math.floor(lo[0]));x1=min(W,math.ceil(hi[0])+1);y0=max(0,math.floor(lo[1]));y1=min(H,math.ceil(hi[1])+1)
            if x1<=x0 or y1<=y0:continue
            xx,yy=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
            p=(xx,yy);e=[cross(a,b,p),cross(b,d,p),cross(d,a,p)]
            v=(e[0]>=-1e-7)&(e[1]>=-1e-7)&(e[2]>=-1e-7)|(e[0]<=1e-7)&(e[1]<=1e-7)&(e[2]<=1e-7)
            pred[y0:y1,x0:x1]|=v;count+=1
        if not count:raise RuntimeError("Empty evaluated native fill")
        expected=mask([sampled(loop) for loop in curves],W,H)
        got=[int.from_bytes(row.tobytes(),"little") for row in np.packbits(pred,axis=1,bitorder="little")]
        inter=sum((a&b).bit_count() for a,b in zip(expected,got));union=sum((a|b).bit_count() for a,b in zip(expected,got))
        return {"nativeFillIoU":inter/union,"triangles":count}
    finally:
        ev.to_mesh_clear();bpy.data.objects.remove(o,do_unlink=True);bpy.data.curves.remove(c)
def fair_silver_top_serif(curves):
    # Exact private candidate is hash-pinned. The P's nearly horizontal top
    # serif has many 1px reversals in the raster alpha, producing metre-scale
    # bevel miters despite a valid planar fill. Replace that one flat run
    # with a C1-compatible straight cubic; leave every other curve intact.
    import copy
    q=copy.deepcopy(curves);loop=q[1];i,j=15,71
    a,b=loop[i][1],loop[j][1]
    if len(q)!=2 or len(loop)!=276 or not (952<a[0]<953 and 1096<b[0]<1097 and 116<a[1]<117 and 116<b[1]<117):
        raise RuntimeError("Pinned silver serif geometry changed")
    if any(not (951<p[1][0]<1098 and 115<p[1][1]<117.1) for p in loop[i:j+1]):
        raise RuntimeError("Serif cleanup exceeds local source corridor")
    v=[(b[k]-a[k])/3 for k in (0,1)]
    loop[i][2]=[a[k]+v[k] for k in (0,1)]
    loop[j][0]=[b[k]-v[k] for k in (0,1)]
    q[1]=loop[:i+1]+loop[j:]
    ref=mask([sampled(l) for l in curves],W,H);out=mask([sampled(l) for l in q],W,H)
    inter=sum((a&b).bit_count() for a,b in zip(ref,out));union=sum((a|b).bit_count() for a,b in zip(ref,out))
    if inter/union<.998:raise RuntimeError("Serif fairing changed too much of the source silhouette")
    return q,{"serifFairingIoU":inter/union,"removedRasterReversalKnots":j-i-1}

def bevel_guard(ob):
    # Planar fill alone cannot detect bevel spikes. Compare every actual
    # evaluated 3D vertex to the curve's sampled outline in local XY.
    from mathutils.kdtree import KDTree
    pts=[]
    for sp in ob.data.splines:
        p=sp.bezier_points
        for i,a in enumerate(p):
            b=p[(i+1)%len(p)]
            n=max(8,int((a.co-b.co).length/.0015)+1)
            for j in range(n):
                t=j/n;u=1-t;v=u**3*a.co+3*u*u*t*a.handle_right+3*u*t*t*b.handle_left+t**3*b.co
                pts.append((v.x,v.y,0.0))
    kd=KDTree(len(pts))
    for i,p in enumerate(pts):kd.insert(p,i)
    kd.balance()
    bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    try:
        worst=max(kd.find((v.co.x,v.co.y,0.0))[2] for v in m.vertices)
        if worst>.055:raise RuntimeError("Native bevel displacement exceeds limit: "+str(worst))
        return {"maximumNativeBevelDisplacement":worst,"vertices":len(m.vertices)}
    finally:ev.to_mesh_clear()

def apply(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CANDIDATE:raise RuntimeError("Wrong private V11 geometry candidate")
    q=json.loads(raw)
    if q["sourceSha256"]!=SOURCE:raise RuntimeError("Wrong original brand source")
    result={}
    for g in q["groups"]:
        name=g["name"];ob=bpy.data.objects[name]
        if g["candidateStatus"]!="RASTER_PARITY_ONLY":
            result[name]={"status":"retained verified baseline","reason":"new raster fit did not meet acceptance"};continue
        if g["check"]["iou"]<.992 or not g["check"]["topology"] or g["check"]["crossing"]:raise RuntimeError("Raster guard failed")
        original=ob.data;curves=g['curves'];fair={}
        if name=='silver-monogram':curves,fair=fair_silver_top_serif(curves)
        c=original.copy();c.splines.clear();c.resolution_u=24;c.render_resolution_u=24
        c.bevel_resolution=8;c.extrude=.18;c.bevel_depth=.012
        for loop in curves:
            sp=c.splines.new("BEZIER");sp.bezier_points.add(len(loop)-1);sp.use_cyclic_u=True;sp.use_smooth=True
            for p,(left,center,right) in zip(sp.bezier_points,loop):
                p.handle_left_type="FREE";p.handle_right_type="FREE";p.co=world_point(*center);p.handle_left=world_point(*left);p.handle_right=world_point(*right)
        try:check=fill_parity(c,curves)
        except Exception as e:
            bpy.data.curves.remove(c);result[name]={"status":"retained verified baseline","reason":str(e)};continue
        if check["nativeFillIoU"]<.998:
            bpy.data.curves.remove(c);result[name]={"status":"retained verified baseline","reason":"native fill mismatch",**check};continue
        ob.data=c;bevel=None;attempts=[]
        for depth in (.012,.008,.006,.004):
            c.bevel_depth=depth
            try:
                bevel=bevel_guard(ob);bevel["bevelDepth"]=depth;break
            except RuntimeError as e:attempts.append({"depth":depth,"reason":str(e)})
        if bevel is None:
            ob.data=original;bpy.data.curves.remove(c);result[name]={"status":"retained verified baseline","reason":"No safe rounded bevel",**check,**fair,"bevelAttempts":attempts};continue
        result[name]={"status":"native fill and bevel checked, visual review required","sourceCandidateRasterIoU":g["check"]["iou"],**check,**fair,**bevel,"bevelAttempts":attempts}
    return result
