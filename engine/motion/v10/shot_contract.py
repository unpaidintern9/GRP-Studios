"""Measured square-reference framing, independent of Blender. One-based frames.
Coordinates are bottom-up, in the centered square-safe crop; width is a
fraction of that crop, not of the full 16:9 image. Macro crops intentional.
"""
FPS=24
TOTAL=168
ANCHORS=tuple(range(1,156,14))
# frame, region, width fraction, center x/y, yaw/pitch/roll degrees, mm lens.
# Approximate visual annotations of the exact reference, not pixel identity.
SHOTS=(
 (1,"silver",2.80,.50,.50,-27,11,-22,65),
 (15,"silver",2.80,.50,.50,-27,11,-22,65),
 (29,"gold",1.35,.49,.47,19,8,-9,58),
 (43,"gold",.96,.52,.46,11,5,0,55),
 (57,"mark",.88,.50,.57,-18,7,0,52),
 (71,"mark",.74,.50,.56,-6,4,0,52),
 (85,"lockup",.72,.50,.48,0,0,0,52),
 (99,"lockup",.72,.50,.48,0,0,0,52),
 (113,"lockup",.72,.50,.48,0,0,0,52),
 (127,"lockup",.72,.50,.48,0,0,0,52),
 (141,"lockup",.72,.50,.48,0,0,0,52),
 (155,"lockup",.72,.50,.48,0,0,0,52),
 (168,"lockup",.72,.50,.48,0,0,0,52),
)
WORDMARK=((1,0),(71,0),(85,1),(168,1))
FLOOR=((1,0),(43,0),(57,1),(113,1),(127,0),(168,0))
EARTH=((1,0),(113,0),(127,1),(168,1))
SUN=((1,0),(113,0),(127,.25),(141,1),(155,.24),(168,.20))
TAG=((1,0),(141,0),(155,1),(168,1))
SQUARE=1080/1920
def widescreen(x,y):
    return (.5+(x-.5)*SQUARE,y)
def projected_width(square_width):
    return square_width*SQUARE
def bounds_ok(b,region,tolerance=.012):
    if region in ("silver","gold"):return True
    return b[0]>=.5-SQUARE/2-tolerance and b[1]<=.5+SQUARE/2+tolerance and b[2]>=-tolerance and b[3]<=1+tolerance
