import bpy,sys,json,pathlib
sys.path.insert(0,"/tmp/grp-v09/repo/engine/motion")
from gold_light_v06_contours import mask,sampled
from gold_light_v02 import CENTER,UNITS_PER_PIXEL
root=pathlib.Path('/tmp/grp-v09')
W,H=1536,934
raw=(root/'official-mask.bin').read_bytes()
names=("silver-monogram","gold-r","silver-wordmark","gold-descriptor")
base={}
for idx,name in enumerate(names,1):
    base[name]=[sum(1<<x for x,v in enumerate(raw[y*W:(y+1)*W]) if v==idx) for y in range(H)]
def pix(v):return (v.x/UNITS_PER_PIXEL+CENTER[0],CENTER[1]-v.y/UNITS_PER_PIXEL)
def measure():
    out={}
    for name in names:
        c=bpy.data.objects[name].data
        curves=[[(pix(p.handle_left),pix(p.co),pix(p.handle_right)) for p in sp.bezier_points] for sp in c.splines]
        m=mask([sampled(a) for a in curves],W,H);b=base[name]
        out[name]=sum((x&y).bit_count() for x,y in zip(m,b))/sum((x|y).bit_count() for x,y in zip(m,b))
    return out
report={}
for name,path in [('v08',root/'gold-light-v08.blend'),('v09e',root/'preview/gold-light-v09e.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(path))
    report[name]=measure()
(root/'source-parity.json').write_text(json.dumps(report,indent=2))
print("SOURCE_PARITY",json.dumps(report),flush=True)
