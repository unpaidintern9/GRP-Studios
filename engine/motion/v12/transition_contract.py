"""V12 fixed-world transition. Native frames, bottom-up normalized screen Y.

Earth is lit and revealed behind the stage BEFORE that part of the stage
becomes transparent. No translated globe, scale animation, or simultaneous
whole-layer dissolve. Sample both envelopes for every native frame.
"""
FPS=24
TOTAL=168
FEATHER=.16
EARTH_START,EARTH_END=97,134
STAGE_START,STAGE_END=105,142

def ease(a,b,t):
    if b<=a:raise ValueError("Invalid interval")
    u=max(0.,min(1.,(t-a)/(b-a)))
    return u**3*(10+u*(-15+6*u))

def head(f,a,b,top=.46):
    return -FEATHER/2+(top+FEATHER)*ease(a,b,f)

def reveal(y,h):
    return ease(0,1,(h+FEATHER/2-y)/FEATHER)

def cues(f):
    if not 1<=f<=TOTAL:raise ValueError("Native frame outside contract")
    return {"earth_head":head(f,EARTH_START,EARTH_END),
            "stage_head":head(f,STAGE_START,STAGE_END),
            "stage_tail":1-ease(130,STAGE_END,f),
            "sunrise":.22*ease(108,130,f)+.78*ease(130,145,f)-.77*ease(145,162,f)-.03*ease(162,168,f),
            "tagline":ease(142,158,f),
            "ground_glints":1-ease(116,140,f)}

def pixel(f,y):
    c=cues(f)
    e=reveal(y,c["earth_head"])
    keep=(1-reveal(y,c["stage_head"]))*c["stage_tail"]
    # Stage alpha is composited over the Earth, not the reverse.
    return {"earth_alpha":e,"stage_keep":keep,
            "visible_earth":e*(1-keep),"uncovered":(1-e)*(1-keep)}

def validate():
    for f in range(1,169):
        c=cues(f)
        assert all(0<=c[n]<=1+1e-9 for n in ("sunrise","tagline","stage_tail","ground_glints"))
        for y in (0,.025,.05,.10,.15,.195,.25,.4):
            q=pixel(f,y)
            assert all(-1e-9<=v<=1+1e-9 for v in q.values())
            if y<=.195 and f>1:
                p=pixel(f-1,y)
                assert q["visible_earth"]+1e-9>=p["visible_earth"]
                assert abs(q["visible_earth"]-p["visible_earth"])<.15
            if y<=.195:
                assert q["uncovered"]<.12
    for y in (0,.05,.1,.15,.195):
        assert pixel(97,y)["visible_earth"]==0
        assert pixel(142,y)["visible_earth"]==1
    return {"earthFrames":[EARTH_START,EARTH_END],"stageFrames":[STAGE_START,STAGE_END],
            "finalHorizonY":.195,"transitionSeconds":(STAGE_END-EARTH_START)/FPS,
            "totalFrames":TOTAL,"creativeApproval":False}
