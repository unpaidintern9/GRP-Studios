"""Fair the original verified brand contours using bounded arc-length smoothing.
All private input/output remains outside public Git. Direct original raster QA."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from PIL import Image
from collections import deque
root=Path("/tmp/grp-v11")
raw=(root/"original.png").read_bytes()
assert hashlib.sha256(raw).hexdigest()=="57640212bfc8173a8cb5c2b740129ba365898c95846db1156035c3efe1ccdf76"
q=json.loads((root/"candidate.json").read_text());a=np.array(Image.open(root/"original.png").convert("RGBA"))
H,W=a.shape[:2];assert (W,H)==(1536,934)
# Same component/color contract as the original verified tracer.
fg=a[:,:,3]>=128;seen=np.zeros((H,W),bool);source=np.zeros((H,W),np.uint8);gold=(a[:,:,0].astype(int)-a[:,:,2].astype(int))>40
for y,x in zip(*np.where(fg)):
    if seen[y,x]:continue
    todo=[(int(y),int(x))];seen[y,x]=True;head=0
    while head<len(todo):
        yy,xx=todo[head];head+=1
        for y1,x1 in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
            if 0<=y1<H and 0<=x1<W and fg[y1,x1] and not seen[y1,x1]:
                seen[y1,x1]=True;todo.append((y1,x1))
    if len(todo)<32:continue
    yy,xx=np.array(todo).T;frac=float(gold[yy,xx].mean());assert frac<=.3 or frac>=.7
    assert not (yy.min()<555<=yy.max())
    source[yy,xx]=(1 if frac<.7 else 2)+(2 if yy.min()>=555 else 0)
def sample(loop,step=.35):
    pts=[]
    for i,(_,p0,p1) in enumerate(loop):
        p2,p3,_=loop[(i+1)%len(loop)]
        A,B,C,D=map(np.array,(p0,p1,p2,p3));n=max(8,int((np.linalg.norm(B-A)+np.linalg.norm(C-B)+np.linalg.norm(D-C))/step)+1)
        t=np.arange(n)[:,None]/n;u=1-t;pts.extend(u**3*A+3*u*u*t*B+3*u*t*t*C+t**3*D)
    return np.asarray(pts)
def smooth(loop,sigma):
    p=sample(loop);seg=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);keep=seg>1e-6;p=p[keep]
    d=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);ar=np.r_[0,np.cumsum(d)];L=ar[-1]
    n=max(32,round(L/.40));t=np.arange(n)*L/n
    z=np.vstack([p,p[0]]);p=np.column_stack([np.interp(t,ar,z[:,i]) for i in (0,1)])
    spacing=L/n;k=np.arange(-math.ceil(4*sigma/spacing),math.ceil(4*sigma/spacing)+1);w=np.exp(-.5*(k*spacing/sigma)**2);w/=w.sum()
    out=sum(v*np.roll(p,int(i),axis=0) for i,v in zip(k,w))
    # Resample the fair contour into smooth C1 cubic knots at ~1.25px.
    # Keep short tangent handles and avoid arbitrary polyline noise.
    d=np.linalg.norm(np.roll(out,-1,axis=0)-out,axis=1);ar=np.r_[0,np.cumsum(d)];L=ar[-1];t=np.arange(max(24,round(L/1.25)))*L/max(24,round(L/1.25));z=np.vstack([out,out[0]])
    p=np.column_stack([np.interp(t,ar,z[:,i]) for i in (0,1)])
    prev=p-np.roll(p,1,axis=0);nex=np.roll(p,-1,axis=0)-p
    tangent=prev+nex;tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    l=p-tangent*np.linalg.norm(prev,axis=1)[:,None]/3;r=p+tangent*np.linalg.norm(nex,axis=1)[:,None]/3
    return np.stack([l,p,r],axis=1).tolist()
def raster(polys):
    rows=[[] for _ in range(H)]
    for p in polys:
        for A,B in zip(p,np.roll(p,-1,axis=0)):
            if A[1]==B[1]:continue
            if A[1]>B[1]:A,B=B,A
            for y in range(max(0,math.ceil(A[1]-.5)),min(H,math.ceil(B[1]-.5))):
                rows[y].append(A[0]+(y+.5-A[1])*(B[0]-A[0])/(B[1]-A[1]))
    v=np.zeros((H,W),bool)
    for y,r in enumerate(rows):
        r.sort()
        if len(r)%2:raise RuntimeError("Odd contour crossings")
        for l,h in zip(r[::2],r[1::2]):
            x=max(0,min(W,math.ceil(l-.5)));z=max(0,min(W,math.ceil(h-.5)));v[y,x:z]=True
    return v
def crossing(loops):
    bins={}
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for j,p in enumerate(loops):
        for i,(a,b) in enumerate(zip(p,np.roll(p,-1,axis=0))):
            seen=set()
            for y in range(math.floor(min(a[1],b[1])/4),math.floor(max(a[1],b[1])/4)+1):
                for x in range(math.floor(min(a[0],b[0])/4),math.floor(max(a[0],b[0])/4)+1):
                    k=(x,y);ls=bins.setdefault(k,[])
                    for jj,ii,c,d,N in ls:
                        if (jj,ii) in seen:continue
                        seen.add((jj,ii))
                        if j==jj and (abs(i-ii)<=1 or abs(i-ii)==N-1):continue
                        if cross(a,b,c)*cross(a,b,d)<-1e-12 and cross(c,d,a)*cross(c,d,b)<-1e-12:return True
                    ls.append((j,i,a,b,len(p)))
    return False
results=[]
for g in q["groups"][:2]:
    i=1 if g["name"]=="silver-monogram" else 2;ref=source==i;curves=g["curves"]
    attempts=[];chosen=None
    for sigma in (3.5,2.8,2.2,1.7,1.2):
        c=[smooth(l,sigma) for l in curves];p=[sample(l,.65) for l in c];pred=raster(p)
        iou=float((ref&pred).sum()/(ref|pred).sum());cr=crossing(p)
        row={"sigmaPixels":sigma,"directOriginalRasterIoU":iou,"crossings":cr,"knots":sum(map(len,c))};attempts.append(row);print(g["name"],json.dumps(row),flush=True)
        if iou>=.985 and not cr:
            chosen={**g,"curves":c,"check":{**g["check"],"iou":iou},"fairing":row,"attempts":attempts};break
    if chosen is None:raise RuntimeError("No smooth contour meets original-art parity")
    results.append(chosen)
out={"sourceSha256":q["sourceSha256"],"groups":results,"creativeApproval":False}
(root/"fair-v11d.json").write_text(json.dumps(out,separators=(",",":")));print("FAIR_PASS",json.dumps([g["fairing"] for g in results]),flush=True)
