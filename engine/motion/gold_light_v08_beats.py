"""Owner-approved seven-second native timing."""
from bisect import bisect_right
FPS=24
TOTAL=168
ANCHORS=((1,1),(11,15),(20,29),(30,41),(39,49),(49,65),(53,77),(59,88),(69,99),(78,109),(85,119),(88,125),(98,138),(106,150),(110,157),(120,168))
WORDMARK=((1,0),(77,0),(88,1),(168,1))
TAGLINE=((1,0),(139,0),(150,1),(168,1))
HORIZON=((1,-112),(109,-112),(119,-99),(125,-91),(138,-89),(168,-89))
def retime(frame):
    if frame<=1:return 1+(frame-1)*1.4
    if frame>=120:return 168+(frame-120)*1.1
    i=bisect_right([x[0] for x in ANCHORS],frame)-1
    a,b=ANCHORS[i];c,d=ANCHORS[i+1]
    return b+(frame-a)*(d-b)/(c-a)
def retimed_shots(shots):
    return [(retime(f),p,t,l,r) for f,p,t,l,r in shots]
