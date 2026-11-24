"""Private storyboard comparison; no aesthetic or native-render certification."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageChops, ImageStat

REF_SHA='2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26'

FPS=24
# Fixed owner-directed beat alignment, independent of candidate appearance.
# 7s: flare .6, macro to 2, reveal to 3.2, sweep to 4.5, horizon to 5.8.
SEVEN_SECOND_TIMES=(0,.6,1.1,1.6,2,2.7,3.2,3.8,4.5,5.1,5.5,5.8)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def beat_indices(seconds):
    if seconds not in (5,7):raise ValueError('Unsupported duration')
    times=tuple(i*.4 for i in range(12)) if seconds==5 else SEVEN_SECOND_TIMES
    return [round(t*FPS) for t in times]

def validate_probe(d,seconds):
    streams=d['streams']
    if len(streams)!=1:raise ValueError('Expected exactly one silent video stream')
    v=streams[0]
    if v.get('codec_type')!='video' or v.get('codec_name')!='h264' or (v.get('width'),v.get('height'))!=(1920,1080) or v.get('avg_frame_rate')!='24/1' or v.get('sample_aspect_ratio') not in ('1:1',None) or abs(float(d['format']['duration'])-seconds)>.001:raise ValueError('Export mismatch')

def compare(ref,video,out,seconds=5):
    indices=beat_indices(seconds);count=seconds*FPS
    if sha(ref)!=REF_SHA:raise ValueError('Wrong storyboard')
    im=Image.open(ref)
    if im.n_frames!=12:raise ValueError('Wrong storyboard frame count')
    refs=[]
    for i in range(12):
        im.seek(i)
        if im.info.get('duration')!=400:raise ValueError('Wrong storyboard cadence')
        refs.append(im.convert('RGB'))
    d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    validate_probe(d,seconds)
    raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(video),'-vf','scale=320:180','-pix_fmt','rgb24','-f','rawvideo','-'])
    stride=320*180*3
    if len(raw)!=count*stride:raise ValueError('Decoded frame count mismatch')
    frames=[Image.frombytes('RGB',(320,180),raw[i*stride:(i+1)*stride]) for i in range(count)]
    delta=[round(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3,4) for a,b in zip(frames,frames[1:])]
    sheet=Image.new('RGB',(3*336,4*420+222),(15,19,27));draw=ImageDraw.Draw(sheet);beats=[]
    for i,ref_frame in enumerate(refs):
        idx=indices[i];x=(i%3)*336;y=(i//3)*420
        draw.text((x+8,y+4),f'{i*.4:.1f}s storyboard | video {idx/FPS:.3f}s',fill='white')
        thumb=ImageOps.contain(ref_frame,(320,180))
        sheet.paste(thumb,(x+(336-thumb.width)//2,y+22+(180-thumb.height)//2))
        sheet.paste(frames[idx],(x+8,y+226))
        draw.text((x+8,y+207),'Full 16:9 frame (not stretched to square)',fill='white')
        beats.append({'referenceSeconds':i*.4,'videoFrame':idx+1,'videoSeconds':idx/24})
    for col,idx in enumerate((indices[-1],(indices[-1]+count-1)//2,count-1)):
        x=col*336;y=4*420
        draw.text((x+8,y+4),f'Closing hold | {idx/FPS:.3f}s',fill='white')
        sheet.paste(frames[idx],(x+8,y+22))
    out.mkdir(parents=True,exist_ok=False)
    sheet.save(out/'comparison.jpg',quality=92)
    receipt={'referenceSha256':REF_SHA,'videoSha256':sha(video),'decodedFrames':count,'durationSeconds':seconds,'fps':FPS,'size':[1920,1080],'audio':False,'beats':beats,'closingHoldFrames':[indices[-1]+1,(indices[-1]+count-1)//2+1,count],'adjacentFrameMeanAbsoluteRgbDelta':delta,'creativeApproval':False,'note':'Delta is diagnostic only; decoded frame count does not establish native rendering, reference similarity, or motion quality.'}
    (out/'comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reference',type=Path);p.add_argument('video',type=Path);p.add_argument('private_output',type=Path);p.add_argument('--seconds',type=int,choices=(5,7),default=5);a=p.parse_args();compare(a.reference,a.video,a.private_output,a.seconds)
