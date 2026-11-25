"""Reference contour cleanup with independent raster parity check (no bpy)."""
import math

def dist(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    q=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/q)) if q else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)

def rdp(a,tol):
    if len(a)<=2:return a
    d,i=max((dist(p,a[0],a[-1]),i) for i,p in enumerate(a[1:-1],1))
    if d<=tol:return [a[0],a[-1]]
    return rdp(a[:i+1],tol)[:-1]+rdp(a[i:],tol)

def fit(loop,tol):
    p=[tuple(x) for x in loop]
    if len(p)<3:raise ValueError("Invalid source loop")
    k=max(range(1,len(p)),key=lambda i:math.dist(p[0],p[i]))
    q=rdp(p[:k+1],tol)[:-1]+rdp(p[k:]+p[:1],tol)[:-1]
    if len(q)<3:return fit(p,tol/2) if tol>.03 else [(x,x,x) for x in p]
    out=[]
    for i,b in enumerate(q):
        a,d=q[i-1],q[(i+1)%len(q)]
        u=(b[0]-a[0],b[1]-a[1]);v=(d[0]-b[0],d[1]-b[1]);lu,lv=math.hypot(*u),math.hypot(*v)
        if min(lu,lv)<1e-8:raise ValueError("Duplicate fitted knot")
        U=(u[0]/lu,u[1]/lu);V=(v[0]/lv,v[1]/lv);dot=U[0]*V[0]+U[1]*V[1]
        if dot>.78:
            tx,ty=U[0]+V[0],U[1]+V[1];m=math.hypot(tx,ty);t=(tx/m,ty/m)
        else:t=None
        def h(D,L):
            if t is None:return (D[0]*L/3,D[1]*L/3)
            dev=abs(t[0]*D[1]-t[1]*D[0]);h=min(L/3,.28/max(dev,1e-8))
            return (t[0]*h,t[1]*h)
        l,r=h(U,lu),h(V,lv)
        out.append(((b[0]-l[0],b[1]-l[1]),b,(b[0]+r[0],b[1]+r[1])))
    return out

def sampled(curve):
    points=[]
    for i,(_,a,b) in enumerate(curve):
        c,d,_=curve[(i+1)%len(curve)]
        n=max(8,math.ceil(math.dist(a,d)/1.5))
        for j in range(n):
            t=j/n;u=1-t
            points.append(tuple(u**3*a[k]+3*u*u*t*b[k]+3*u*t*t*c[k]+t**3*d[k] for k in (0,1)))
    return points

def mask(loops,w,h):
    rows=[[] for _ in range(h)]
    for loop in loops:
        for i,p in enumerate(loop):
            q=loop[(i+1)%len(loop)]
            if p[1]==q[1]:continue
            a,b=(p,q) if p[1]<q[1] else (q,p)
            for y in range(max(0,math.ceil(a[1]-.5)),min(h,math.ceil(b[1]-.5))):
                rows[y].append(a[0]+(y+.5-a[1])*(b[0]-a[0])/(b[1]-a[1]))
    masks=[]
    for row in rows:
        row.sort()
        if len(row)%2:raise ValueError("Odd contour crossing count")
        v=0
        for l,r in zip(row[::2],row[1::2]):
            x=max(0,min(w,math.ceil(l-.5)));z=max(0,min(w,math.ceil(r-.5)))
            if z>x:v|=((1<<(z-x))-1)<<x
        masks.append(v)
    return masks

def fit_group(loops,w,h,mark):
    orig=mask(loops,w,h)
    for tol in ([.85,.55,.35,.18] if mark else [.40,.24,.12]):
        curves=[fit(loop,tol) for loop in loops];other=mask([sampled(c) for c in curves],w,h)
        i=sum((a&b).bit_count() for a,b in zip(orig,other));u=sum((a|b).bit_count() for a,b in zip(orig,other))
        if not u:raise ValueError("Empty original contour")
        iou=i/u
        if iou>=.992:
            return curves,{"sourceKnots":sum(map(len,loops)),"fittedKnots":sum(map(len,curves)),"sampledSilhouetteIoU":iou,"loopCount":len(curves),"tolerancePixels":tol}
    raise ValueError("Contour refit fails 99.2% raster silhouette parity")
