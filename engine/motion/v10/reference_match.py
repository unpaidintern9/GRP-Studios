#!/usr/bin/env python3
"""Inspect exact private reference vs a native render. No creative PASS is inferred."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageOps

REFERENCE_SHA = '2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26'
FPS = 24
BEATS = (
    'Concentrated horizontal white-gold ignition',
    'Diagonal silver bevel macro; hot moving reflection',
    'Gold R bowl and curved leg; warm moving reflection',
    'Gold R reads as a complete sculptural shape',
    'Full metallic monogram at three-quarter angle; reflective stage',
    'Smaller monogram on reflective obsidian stage',
    'Complete original lockup; warm reflected floor light',
    'Upper diagonal traveling glint; stable lockup',
    'Full lockup and atmospheric stage; prepare transition',
    'Floor transitions into wide luminous night-Earth horizon',
    'Earth sunrise flare peaks; centered full lockup',
    'Flare settles; readable SEE BEYOND THE NOISE tagline',
)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def anchors(reference, total=168):
    if sha(reference) != REFERENCE_SHA:
        raise ValueError('Incorrect reference GIF digest')
    im = Image.open(reference)
    if im.n_frames != len(BEATS):
        raise ValueError('Unexpected reference panel count')
    times, panels, t = [], [], 0
    for i in range(im.n_frames):
        im.seek(i)
        times.append(t)
        panels.append(im.convert('RGBA').copy())
        t += im.info['duration']
    if times != list(range(0, 4800, 400)) or t != 4800:
        raise ValueError('Unexpected reference timing')
    rows = [dict(panel=i+1, source_ms=ms, target_frame=1+(ms*total+t//2)//t,
                 target_seconds=round(((ms*total+t//2)//t)/FPS, 6), beat=BEATS[i])
            for i,ms in enumerate(times)]
    return rows,panels,t

def probe(video):
    raw = subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-count_frames','-of','json',str(video)])
    p=json.loads(raw)
    v=[s for s in p['streams'] if s['codec_type']=='video']
    if len(v)!=1:
        raise ValueError('Exactly one video stream required')
    v=v[0];count=int(v.get('nb_read_frames',v.get('nb_frames','0')))
    if (v['width'],v['height'],v['r_frame_rate'],v['codec_name'])!=(1920,1080,'24/1','h264'):
        raise ValueError('Wrong output video format')
    if len(p['streams'])!=1 or count!=168 or abs(float(p['format']['duration'])-7)>0.001:
        raise ValueError('Expected silent seven-second, 168-frame master')
    return {'frames':count,'duration':float(p['format']['duration']),'width':1920,'height':1080,'fps':FPS,'codec':'h264','audio':False}

def decode(video,index):
    # Exact ordinal selection rather than nearest-keyframe seeking.
    png=subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-vf',f'select=eq(n\\,{index})','-frames:v','1','-f','image2pipe','-vcodec','png','-'])
    from io import BytesIO
    with Image.open(BytesIO(png)) as im:
        return im.convert('RGB')

def build(reference,video,outdir):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    specs=probe(video);rows,panels,duration=anchors(reference,specs['frames'])
    cw,ch=760,342
    sheet=Image.new('RGB',(cw*2,ch*6),(13,16,21));d=ImageDraw.Draw(sheet)
    for i,(row,ref) in enumerate(zip(rows,panels)):
        frame=decode(video,row['target_frame']-1)
        x=(i%2)*cw;y=(i//2)*ch
        ref=ImageOps.contain(ref,(270,270));candidate=ImageOps.contain(frame,(480,270))
        sheet.paste(ref,(x,y+27),ref);sheet.paste(candidate,(x+274,y+27))
        d.text((x+6,y+6),f"{row['panel']:02d} | GIF {row['source_ms']/1000:.1f}s",fill=(225,229,237))
        d.text((x+278,y+6),f"Render f{row['target_frame']:03d} | {row['target_seconds']:.2f}s",fill=(225,229,237))
        d.text((x+6,y+305),row['beat'],fill=(231,188,109))
    path=outdir/'reference-vs-render.jpg';sheet.save(path,quality=94)
    manifest={'reference_sha256':sha(reference),'reference_ms':duration,'reference_dimensions':list(panels[0].size),'reference_panels':len(panels),'mapping':'uniform 4.8s to 7.0s; frame 1 is t=0','video_sha256':sha(video),'technical_format':specs,'anchors':rows,'creative_approval':False,'note':'Square reference kept undistorted; render kept 16:9. Matching these frames does not prove matching in-between motion.'}
    (outdir/'reference-comparison.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

def main():
    p=argparse.ArgumentParser();p.add_argument('reference');p.add_argument('video');p.add_argument('outdir');a=p.parse_args()
    print(json.dumps(build(a.reference,a.video,a.outdir),indent=2))

if __name__=='__main__':main()
