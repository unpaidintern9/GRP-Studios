"""Pure reference-timed camera plan; distances use actual contour bounds."""
from math import sqrt

WORDMARK_KEYS = ((1, 0), (50, 0), (53, 0), (59, 1), (120, 1))
SHIFT_KEYS = ((1, 1), (50, 1), (59, 0), (120, 0))


def face_shot(frame, target, height, coverage, lens, offset, roll):
    # 36 mm horizontal sensor, 16:9 frame; projected vertical extent is
    # approximately height*lens/(distance*20.25) before bevel/foreshortening.
    if height <= 0 or coverage <= 0 or lens <= 0:
        raise ValueError('Invalid framing inputs')
    x, y, z = target
    dx, dy = (v * height for v in offset)
    distance = height * lens / (20.25 * coverage)
    if dx*dx + dy*dy >= distance*distance:
        raise ValueError('Camera offset exceeds optical distance')
    return (frame, (x+dx, y+dy, z+sqrt(distance*distance-dx*dx-dy*dy)), target, lens, roll)


def shot_plan(silver, gold, floor_y, shift, anchor):
    sl, sh, sb, st = silver
    lo, hi, b, t = gold
    h = t-b
    rx = (lo+hi)/2
    mid = (max(st,t)+min(sb,b))/2+shift
    sx, sy = anchor
    return [
        face_shot(1, (sx,sy,.20), h, 2.7, 50, (-.26,.13), -10),
        face_shot(11, (sx+.03*h,sy-.06*h,.20), h, 2.4, 50, (-.25,.10), -25),
        face_shot(20, (rx-.08*h,b+shift+.69*h,.20), h, 1.28, 52, (.15,.09), -14),
        face_shot(30, (rx-.13*h,b+shift+.50*h,.20), h, .86, 50, (.11,.05), -4),
        (39,(-2.7,floor_y+1.25,12.8),(0,mid-.26,0),48,-2),
        (49,(-1.7,floor_y+1.65,15.5),(0,mid-.34,0),47,-1),
        (59,(-1.0,floor_y+2.40,18.2),(0,-.25,0),47,0),
        (69,(-.55,floor_y+2.60,18.8),(0,-.22,0),47,0),
        (78,(-.25,floor_y+2.75,19.3),(0,-.18,0),47,0),
        (98,(.10,floor_y+2.90,19.7),(0,-.18,0),47,0),
        (110,(0,floor_y+2.9,19.8),(0,-.18,0),47,0),
        (120,(0,floor_y+2.9,19.8),(0,-.18,0),47,0),
    ]
