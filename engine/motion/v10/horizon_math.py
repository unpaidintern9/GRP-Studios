"""Independent camera-local horizon projection. No Blender dependency."""
from math import sqrt, isfinite

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def mul(a,k): return tuple(v*k for v in a)
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def unit(a):
    n=sqrt(dot(a,a))
    if n<=1e-12:raise ValueError('Zero vector')
    return mul(a,1/n)

def screen_ray(frame,x,row):
    """Top-down normalized image row; view frame is (xmin,xmax,ymin,ymax,z)."""
    l,r,b,t,z=frame
    if not(l<r and b<t and z<0):raise ValueError('Invalid perspective view frame')
    return unit((l+x*(r-l),t-row*(t-b),z))

def sphere_center(frame,radius,ratio,apex):
    if not(0<radius and ratio>1 and 0<apex<1):raise ValueError('Invalid horizon')
    ray=screen_ray(frame,.5,apex)
    down=unit(add((0.,-1.,0.),mul(ray,ray[1])))
    return add(mul(ray,radius*sqrt(ratio*ratio-1)),mul(down,radius))

def hit(frame,center,radius,x,row):
    ray=screen_ray(frame,x,row);p=dot(ray,center)
    return p>0 and p*p-dot(center,center)+radius*radius>=-1e-8*radius*radius

def horizon_row(frame,center,radius,x):
    if not hit(frame,center,radius,x,1.):return None
    lo,hi=0.,1.
    for _ in range(52):
        m=(lo+hi)/2
        if hit(frame,center,radius,x,m):hi=m
        else:lo=m
    return hi

def fit_horizon(frame,radius=100.,apex=.805,edge=.875):
    """Find a fixed, shallow, full-width horizon in the actual shifted camera."""
    if not .5<apex<edge<.98:raise ValueError('Invalid desired composition')
    def sample(ratio):
        c=sphere_center(frame,radius,ratio,apex)
        rows=[horizon_row(frame,c,radius,x) for x in (0.,.5,1.)]
        return c,rows
    lo,hi=1.005,1.45
    for _ in range(48):
        m=(lo+hi)/2;_,rows=sample(m)
        if any(v is None for v in rows) or max(rows[0],rows[2])>edge:hi=m
        else:lo=m
    c,rows=sample(lo)
    if any(v is None for v in rows) or abs(rows[1]-apex)>.0005 or max(rows[0],rows[2])>edge+.002 or min(rows[0],rows[2])<apex-.003:
        raise RuntimeError('Cannot fit full-width fixed horizon')
    if max(rows[0],rows[2])-min(rows[0],rows[2])>.03:raise RuntimeError('Asymmetric horizon; correct camera framing')
    return {'center':c,'radius':radius,'ratio':lo,'rows':rows,'apex':apex,'max_edge':edge,'frame':list(frame)}

def smoother(a,b,f):
    if b<=a:raise ValueError('Bad timing interval')
    u=max(0.,min(1.,(f-a)/(b-a)))
    return u**3*(10+u*(-15+6*u))

def closing_cues(f):
    earth=smoother(113,127,f)
    return {'earth':earth,'stage':1-earth,'sun':.25*smoother(113,127,f)+.75*smoother(127,141,f)-.76*smoother(141,155,f)-.04*smoother(155,168,f),'tagline':smoother(141,155,f)}
