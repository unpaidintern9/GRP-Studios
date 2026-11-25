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
        original=ob.data;c=original.copy();c.splines.clear();c.resolution_u=64;c.render_resolution_u=64
        c.bevel_resolution=16;c.extrude=.18;c.bevel_depth=.012
        for loop in g["curves"]:
            sp=c.splines.new("BEZIER");sp.bezier_points.add(len(loop)-1);sp.use_cyclic_u=True;sp.use_smooth=True
            for p,(left,center,right) in zip(sp.bezier_points,loop):
                p.handle_left_type="FREE";p.handle_right_type="FREE";p.co=world_point(*center);p.handle_left=world_point(*left);p.handle_right=world_point(*right)
        try:check=fill_parity(c,g["curves"])
        except Exception as e:
            bpy.data.curves.remove(c);result[name]={"status":"retained verified baseline","reason":str(e)};continue
        if check["nativeFillIoU"]<.998:
            bpy.data.curves.remove(c);result[name]={"status":"retained verified baseline","reason":"native fill mismatch",**check};continue
        ob.data=c
        result[name]={"status":"native fill checked, visual review required","sourceRasterIoU":g["check"]["iou"],**check}
    return result
