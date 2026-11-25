"""Dimensioned, inset rounded crown; silhouette does not grow outward.

All x/y points remain within the validated original/fair outline. Front and
back surfaces are a height field of the distance to that outline. Small
serifs therefore round into their own stroke, rather than receiving an
unbounded miter. This is a look-development candidate, not a new logo.
"""
import math
HALF_SIDE=.055
CROWN_WIDTH=.115
CROWN_RISE=.135

def crown(distance,width=CROWN_WIDTH,rise=CROWN_RISE):
    if not all(math.isfinite(v) for v in (distance,width,rise)) or width<=0 or rise<=0:
        raise ValueError("Invalid rounded crown")
    t=max(0.,min(1.,distance/width))
    return rise*math.sqrt(max(0.,t*(2-t)))

def surface_z(distance):
    return HALF_SIDE+crown(distance)

def validate():
    assert crown(0)==0
    assert crown(CROWN_WIDTH)==CROWN_RISE
    assert crown(2*CROWN_WIDTH)==CROWN_RISE
    a=[surface_z(CROWN_WIDTH*i/1000) for i in range(1001)]
    assert all(x<=y for x,y in zip(a,a[1:]))
    assert abs(a[-1]-.19)<1e-12
    # At the flat crest, the roundover approaches zero derivative.
    assert (crown(CROWN_WIDTH)-crown(CROWN_WIDTH-1e-6))/1e-6<1e-4
    return {"sideHalfDepth":HALF_SIDE,"crownWidth":CROWN_WIDTH,"crownRise":CROWN_RISE,
            "maxDepth":2*a[-1],"outwardSilhouetteGrowth":0,"creativeApproval":False}
