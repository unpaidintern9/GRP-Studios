"""Reference-led V11 motion contract. One-based native frames at 24fps.
The owner GIF supplies 12 discrete poses, not continuous motion. Preserve the
7-second native delivery; interpolate shot choreography, not source pixels.
"""
from math import isfinite
FPS=24
TOTAL=168
ANCHORS=(1,15,29,43,57,71,85,99,113,127,141,155)
# Frame, region, square-safe width, center, yaw, pitch, roll, focal length.
# Macro composition may crop deliberately; full monogram/lockup may not.
SHOTS=(
 (1,"silver",2.80,.47,.52,-46,13,-24,85),
 (8,"silver",2.80,.48,.51,-42,12,-22,82),
 (15,"silver",2.80,.50,.50,-34,10,-18,76),
 (21,"gold",1.95,.54,.50,-34,9,-15,72),
 (29,"gold",1.37,.49,.46,-24,7,-7,67),
 (36,"gold",1.09,.50,.48,-17,5,-3,61),
 (43,"gold",.84,.52,.48,-10,4,0,57),
 (50,"gold",.76,.54,.51,-14,5,0,54),
 (57,"mark",.86,.50,.56,-20,7,0,52),
 (64,"mark",.80,.50,.56,-13,6,0,52),
 (71,"mark",.74,.50,.55,-7,4,0,52),
 (78,"mark",.71,.50,.58,-3,2,0,52),
 (85,"lockup",.72,.50,.50,0,0,0,52),
 (99,"lockup",.72,.50,.50,0,0,0,52),
 (113,"lockup",.72,.50,.50,0,0,0,52),
 (127,"lockup",.72,.50,.50,0,0,0,52),
 (141,"lockup",.72,.50,.50,0,0,0,52),
 (155,"lockup",.72,.50,.50,0,0,0,52),
 (168,"lockup",.72,.50,.50,0,0,0,52),
)
def ease(a,b,f):
    if b<=a or not all(isfinite(v) for v in (a,b,f)):raise ValueError("Invalid cue")
    t=max(0.,min(1.,(f-a)/(b-a)))
    return t*t*t*(10+t*(-15+6*t))
def pulse(a,b,c,d,f):
    return ease(a,b,f)*(1-ease(c,d,f))
def cues(f):
    if not 1<=f<=TOTAL:raise ValueError("Invalid native frame")
    earth=ease(113,127,f)
    return {
      "ignition":(1-ease(3,13,f)),
      "mark":ease(7,15,f),
      "wordmark":ease(71,85,f),
      "stage":ease(43,57,f)*(1-earth),
      "earth":earth,
      "silver_sweep":pulse(6,14,18,25,f),
      "gold_sweep":pulse(17,27,36,49,f),
      "floor_glints":ease(47,57,f)*(1-earth),
      "upper_sweep":pulse(87,96,103,113,f),
      "transition_glint":pulse(109,119,127,137,f),
      "sunrise":.24*ease(113,127,f)+.76*ease(127,141,f)-.79*ease(141,155,f)-.04*ease(155,168,f),
      "tagline":ease(141,155,f)
    }
def frames_for(name):
    return [(f,cues(f)[name]) for f in range(1,TOTAL+1)]
def native_checkpoints():
    return tuple(sorted(set(ANCHORS+(8,21,36,50,64,78,91,106,118,123,134,148,168))))
def assert_contract():
    assert TOTAL/FPS==7
    assert all(a[0]<b[0] for a,b in zip(SHOTS,SHOTS[1:]))
    assert all(s[1:]==SHOTS[-1][1:] for s in SHOTS if s[0]>=85)
    for f in range(1,TOTAL+1):
        q=cues(f)
        assert all(-1e-9<=v<=1+1e-9 for v in q.values())
        if f>=57:assert abs(q["stage"]+q["earth"]-1)<1e-9
        if f>1:assert abs(q["earth"]-cues(f-1)["earth"])<.14
    assert cues(71)["wordmark"]==0 and cues(85)["wordmark"]==1
    assert cues(113)["earth"]==0 and cues(127)["earth"]==1
    assert abs(cues(141)["sunrise"]-1)<1e-9 and cues(155)["tagline"]==1
    assert cues(113)["upper_sweep"]==0
    return {"nativeFrames":TOTAL,"fps":FPS,"referenceAnchors":ANCHORS,"checkpoints":native_checkpoints(),"cameraLockedFrom":85,"earthTransition":[113,127],"taglineVisibleBy":155,"creativeApproval":False}
if __name__=="__main__":
    import json
    print(json.dumps(assert_contract(),indent=2))
