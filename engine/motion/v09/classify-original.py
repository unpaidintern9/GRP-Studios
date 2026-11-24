from PIL import Image
from collections import deque
import pathlib
p=pathlib.Path('/tmp/grp-v09');im=Image.open(p/'source-full.png').convert('RGBA')
W,H=im.size;assert (W,H)==(1536,934)
raw=im.tobytes();n=W*H;seen=bytearray(n);out=bytearray(n);counts=[0]*5
for i in range(n):
    if seen[i] or raw[4*i+3]<128:continue
    q=[i];seen[i]=1;gold=0;miny=H;maxy=0
    for j in q:
        x=j%W;y=j//W;gold+=raw[4*j]-raw[4*j+2]>40;miny=min(miny,y);maxy=max(maxy,y)
        for k in (j-1 if x else -1,j+1 if x+1<W else -1,j-W if y else -1,j+W if y+1<H else -1):
            if k>=0 and not seen[k] and raw[4*k+3]>=128:seen[k]=1;q.append(k)
    if len(q)<32:continue
    assert not(miny<555<=maxy)
    g=gold/len(q);assert g<=.3 or g>=.7
    idx=(4 if g>=.7 else 3) if miny>=555 else (2 if g>=.7 else 1)
    counts[idx]+=1
    for j in q:out[j]=idx
assert counts[1:]==[2,1,6,16],counts
(p/'official-mask.bin').write_bytes(out)
print('ORIGINAL_MASK_PASS',counts)
