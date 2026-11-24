"""V10 reference-led, seven-second shot choreography. Pure Python; no bpy.

Time is seconds from frame 1. Only the camera and lighting travel. The Earth
is a locked composition revealed by a layer dissolve; it never rises.
"""
from bisect import bisect_right
from math import atan, cos, degrees, hypot, isfinite, radians, sin, sqrt

FPS = 24
TOTAL = 168
REFERENCE_SHA256 = '2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26'
# Nonlinear adaptation of the actual 12-frame, 4.8-second square reference.
# This restores the early macro-to-monogram beat rather than stretching V09.
REFERENCE_BEATS = (
    (0.00, 0.00, 'gold ignition'),
    (0.40, 0.48, 'diagonal silver bevel'),
    (0.80, 0.92, 'gold R bowl and leg'),
    (1.20, 1.38, 'recognizable R'),
    (1.60, 1.95, 'complete monogram, low angle'),
    (2.00, 2.43, 'monogram settle and floor glints'),
    (2.40, 2.95, 'wordmark resolves'),
    (2.80, 3.50, 'gold arc across stage'),
    (3.20, 4.02, 'reflective full lockup'),
    (3.60, 4.65, 'earth horizon replaces stage'),
    (4.00, 5.15, 'warm sunrise glint'),
    (4.40, 5.70, 'tagline and settled lockup'),
)
# Camera anchors: sec, silver->R->mark->full, normalized view height multiplier,
# yaw, pitch, lens(mm), roll. Explicit nonzero macro obliquity, rapid initial
# pullback, stable 52mm hero camera. Span uses actual logo group bounds.
CAMERA = (
    (0.00, 0.00, 0.38, -33.0, 14.0, 72.0, -23.0),
    (0.30, 0.00, 0.38, -31.0, 13.0, 72.0, -22.0),
    (0.48, 0.06, 0.47, -29.0, 12.0, 70.0, -20.0),
    (0.92, 0.97, 0.98, -20.0,  9.0, 62.0, -11.0),
    (1.38, 1.05, 1.40, -13.0,  7.0, 59.0,  -6.0),
    (1.95, 1.96, 2.05,  -7.0,  7.0, 55.0,  -2.0),
    (2.43, 2.08, 2.35,  -4.0,  6.0, 54.0,  -1.0),
    (2.95, 2.90, 2.90,  -1.0,  4.0, 52.0,   0.0),
    (3.50, 3.00, 3.05,   0.0,  3.0, 52.0,   0.0),
    (4.02, 3.00, 3.05,   0.0,  3.0, 52.0,   0.0),
    (7.00, 3.00, 3.05,   0.0,  3.0, 52.0,   0.0),
)

def clamp(x):
    return min(1.0, max(0.0, x))


def smooth(a, b, t):
    """Quintic ramp, zero velocity and acceleration at both ends."""
    if not b > a:
        raise ValueError('Invalid timing interval')
    u = clamp((t-a)/(b-a))
    return u*u*u*(10+u*(-15+6*u))


def pulse(a, b, c, d, t):
    return smooth(a, b, t)*(1-smooth(c, d, t))


def pchip(knots, t):
    """Shape-preserving cubic interpolation without arbitrary overshoot."""
    if len(knots) < 2 or any(b[0] <= a[0] for a,b in zip(knots, knots[1:])):
        raise ValueError('Knots must increase strictly')
    if t <= knots[0][0]: return knots[0][1]
    if t >= knots[-1][0]: return knots[-1][1]
    i = bisect_right([k[0] for k in knots], t)-1
    h = [b[0]-a[0] for a,b in zip(knots,knots[1:])]
    d = [(b[1]-a[1])/dt for a,b,dt in zip(knots,knots[1:],h)]
    def m(j):
        if j == 0 or j == len(knots)-1 or d[j-1]*d[j] <= 0: return 0.0
        w1=2*h[j]+h[j-1]; w2=h[j]+2*h[j-1]
        return (w1+w2)/(w1/d[j-1]+w2/d[j])
    a,p=knots[i]; b,q=knots[i+1]; dt=b-a; u=(t-a)/dt
    return ((2*u**3-3*u*u+1)*p+(u**3-2*u*u+u)*dt*m(i)
            +(-2*u**3+3*u*u)*q+(u**3-u*u)*dt*m(i+1))


def frame_time(frame):
    if not isinstance(frame,int) or not 1 <= frame <= TOTAL:
        raise ValueError('Frame out of range')
    return (frame-1)/FPS


def cues(t):
    if not isfinite(t): raise ValueError('Nonfinite time')
    # The foreground and horizon are complementary layers; the planet does
    # not translate. The sweep bridges the transition, rather than preceding
    # an unrelated second reveal.
    earth=smooth(4.06,4.88,t)
    return {
        'opening_flare': pulse(-.12,.16,.28,.62,t),
        'metal': smooth(.25,.62,t),
        'wordmark': smooth(2.35,2.98,t),
        'stage': 1-earth,
        'earth': earth,
        'gold_sweep': pulse(3.20,3.67,4.40,4.95,t),
        'sunrise': pulse(4.42,5.15,5.36,6.10,t)*.78+smooth(4.42,5.15,t)*.22,
        'tagline': smooth(5.38,5.85,t),
    }


def camera_channels(t):
    keys=('target','span','yaw','pitch','lens','roll')
    return {k:pchip([(r[0],r[i]) for r in CAMERA],t) for i,k in enumerate(keys,1)}


def horizon_center(depth, radius, apex=.79, lens=100.0, sensor_height=20.25):
    """Fixed sphere center in camera-local coordinates (Y up, -Z forward).

    The optical ray at normalized image-row `apex` is tangent to the sphere.
    No animated visibility/translation is needed to compose the Earth.
    """
    if not (0 < radius < depth and .5 < apex < 1 and lens > 0 and sensor_height > 0):
        raise ValueError('Invalid horizon framing')
    slope=(.5-apex)*sensor_height/lens
    return (0.0, depth*slope-radius*sqrt(1+slope*slope), -depth)


def horizon_row(x, depth=100.0, radius=95.0, apex=.79, lens=100.0):
    """Top tangent row at a normalized X position, or None off-screen."""
    cx,cy,cz=horizon_center(depth,radius,apex,lens)
    sx=(x-.5)*36.0/lens
    def intersects(row):
        sy=(.5-row)*20.25/lens
        dot=cy*sy-cz
        norm=1+sx*sx+sy*sy
        return dot>0 and dot*dot-norm*(cy*cy+cz*cz-radius*radius)>=-1e-8
    if not intersects(1.0):return None
    lo=0.;hi=1.
    for _ in range(54):
        mid=(lo+hi)/2
        if intersects(mid):hi=mid
        else:lo=mid
    return hi


def preview_frames():
    # Every reference beat, plus dense samples through the disputed horizon.
    times=[b[1] for b in REFERENCE_BEATS]+[4.18,4.34,4.50,4.75,5.0,5.85,6.5,167/24]
    return tuple(sorted({min(TOTAL,round(t*FPS)+1) for t in times}))


def shot_manifest():
    return {
        'version':'v10-shot-plan-1','fps':FPS,'frames':TOTAL,'durationSeconds':TOTAL/FPS,
        'referenceSha256':REFERENCE_SHA256,'referenceBeats':REFERENCE_BEATS,
        'cameraKnots':CAMERA,'previewFrames':preview_frames(),
        'fixedHorizon':{'depth':100.,'radius':95.,'lensMm':100.,'center':horizon_center(100,95),
                        'apexRow':.79,'edgeRow':horizon_row(0.)},
        'status':'source-plan-not-rendered','creativeApproval':False,
    }
