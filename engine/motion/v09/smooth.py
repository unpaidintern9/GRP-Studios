import bpy,sys,math,json
from mathutils import Vector
sys.path.insert(0,"/tmp/grp-v09/repo/engine/motion")
from gold_light_v06_contours import mask,sampled
from gold_light_v02 import CENTER,UNITS_PER_PIXEL
s=bpy.context.scene
def pix(v):return (v.x/UNITS_PER_PIXEL+CENTER[0],CENTER[1]-v.y/UNITS_PER_PIXEL)
def co(v):return ((v[0]-CENTER[0])*UNITS_PER_PIXEL,(CENTER[1]-v[1])*UNITS_PER_PIXEL,0)
def get(sp):return [(pix(p.handle_left),pix(p.co),pix(p.handle_right)) for p in sp.bezier_points]
def poly(curve):
    # Start from dense native fitted shape, not a retyped logo.
    raw=[Vector(x) for x in sampled(curve)]
    q=[raw[0]]
    for p in raw[1:]:
        if (p-q[-1]).length>=.5:q.append(p)
    if (q[-1]-q[0]).length<.25:q.pop()
    return q
def tangent(q,i,d,span=4.0):
    n=len(q);v=q[i];last=v;dist=0.
    for j in range(1,n):
        p=q[(i+j*d)%n];dl=(p-last).length
        if dist+dl>=span and dl>0:
            z=last.lerp(p,(span-dist)/dl);return (z-v).normalized()
        last=p;dist+=dl
    return (last-v).normalized()
def fitclosed(curve,tol):
    q=poly(curve);N=len(q)
    # Real corners become separate segments; gently curving areas share
    # a central tangent across adaptive splits.
    corners=[i for i in range(N) if tangent(q,i,-1).dot(tangent(q,i,1))>-.60]
    picked=[]
    for i in sorted(corners,key=lambda j:tangent(q,j,-1).dot(tangent(q,j,1)),reverse=True):
        if all(min((i-j)%N,(j-i)%N)>8 for j in picked):picked.append(i)
    if len(picked)<2:
        picked=[0,N//2]
    breaks=sorted(set(picked))
    def tjoin(i):
        a=tangent(q,i,-1);b=tangent(q,i,1)
        return (b-a).normalized()
    def fit(points,t0,t1,depth=0):
        p0,p3=points[0],points[-1];n=len(points);L=(p3-p0).length
        if n<3 or depth>18:
            return [(p0,p0+t0*L/3,p3+t1*L/3,p3)]
        u=[0.]
        for a,b in zip(points,points[1:]):u.append(u[-1]+(b-a).length)
        if u[-1]<1e-8:return [(p0,p0,p3,p3)]
        u=[a/u[-1] for a in u]
        c00=c01=c11=x0=x1=0.
        for p,t in zip(points,u):
            b0=(1-t)**3;b1=3*t*(1-t)**2;b2=3*t*t*(1-t);b3=t**3
            a=t0*b1;b=t1*b2;d=p-(p0*(b0+b1)+p3*(b2+b3))
            c00+=a.dot(a);c01+=a.dot(b);c11+=b.dot(b);x0+=a.dot(d);x1+=b.dot(d)
        det=c00*c11-c01*c01
        aa=(x0*c11-x1*c01)/det if abs(det)>1e-10 else L/3
        bb=(c00*x1-c01*x0)/det if abs(det)>1e-10 else L/3
        if min(aa,bb)<L*.001 or max(aa,bb)>u[-1]+L*4:aa=bb=L/3
        p1=p0+t0*aa;p2=p3+t1*bb
        errs=[(p-(p0*(1-t)**3+p1*(3*t*(1-t)**2)+p2*(3*t*t*(1-t))+p3*t**3)).length for p,t in zip(points,u)]
        j=max(range(1,n-1),key=lambda k:errs[k])
        if errs[j]<=tol:return [(p0,p1,p2,p3)]
        k=max(0,j-3);h=min(n-1,j+3)
        mid=(points[h]-points[k]).normalized()
        return fit(points[:j+1],t0,-mid,depth+1)+fit(points[j:],mid,t1,depth+1)
    seg=[]
    for i,a in enumerate(breaks):
        b=breaks[(i+1)%len(breaks)];points=q[a:b+1] if b>a else q[a:]+q[:b+1]
        if len(points)<2:continue
        t0=tangent(q,a,1) if a in corners else tjoin(a)
        t1=tangent(q,b,-1) if b in corners else -tjoin(b)
        seg.extend(fit(points,t0,t1))
    return [(tuple(seg[i-1][2]),tuple(x[0]),tuple(x[1])) for i,x in enumerate(seg)]
report={}
for name in ("silver-monogram","gold-r"):
    c=bpy.data.objects[name].data;old=[get(sp) for sp in c.splines];base=mask([sampled(x) for x in old],1536,934)
    selected=old;best=1.;attempts=[]
    for tol in (1.15,.90,.7,.5,.35):
        try:
            candidate=[fitclosed(x,tol) for x in old];new=mask([sampled(x) for x in candidate],1536,934)
            iou=sum((a&b).bit_count() for a,b in zip(base,new))/sum((a|b).bit_count() for a,b in zip(base,new))
            attempts.append((tol,iou,sum(map(len,candidate))))
            if iou>=.992 and sum(map(len,candidate))<sum(map(len,old))*.90:
                selected=candidate;best=iou;break
        except Exception as e:attempts.append((tol,str(e)))
    if selected is not old:
        c.splines.clear()
        for curve in selected:
            sp=c.splines.new("BEZIER");sp.bezier_points.add(len(curve)-1);sp.use_cyclic_u=True;sp.use_smooth=True
            for p,(a,b,d) in zip(sp.bezier_points,curve):
                p.handle_left_type="FREE";p.handle_right_type="FREE";p.co=co(b);p.handle_left=co(a);p.handle_right=co(d)
    c.resolution_u=64;c.render_resolution_u=64;c.bevel_resolution=16
    report[name]={"relativeToV08FittedSilhouetteIoU":best,"loops":len(old),"oldKnots":sum(map(len,old)),"newKnots":sum(map(len,selected)),"attempts":attempts,"changed":selected is not old}
p=bpy.context.preferences.addons["cycles"].preferences;p.compute_device_type="OPTIX";p.get_devices()
if not any(d.type=="OPTIX" for d in p.devices):raise RuntimeError("No OptiX")
for d in p.devices:d.use=d.type=="OPTIX"
s.cycles.device="GPU";s.cycles.denoiser="OPTIX";s.cycles.samples=48;s.cycles.adaptive_threshold=.022
s.frame_set(120);bpy.ops.wm.save_as_mainfile(filepath="/tmp/grp-v09/preview/gold-light-v09d.blend")
open("/tmp/grp-v09/contour-d-receipt.json","w").write(json.dumps(report,indent=2))
print("V09_CONTOUR_D",json.dumps(report),flush=True)
for f in (20,65,145):
    s.frame_set(f);s.render.filepath=f"/tmp/grp-v09/preview/smooth-{f:03}.png";bpy.ops.render.render(write_still=True)
print("V09_SMOOTH_PREVIEW_PASS",flush=True)
