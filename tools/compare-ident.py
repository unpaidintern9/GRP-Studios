"""Private comparison only: exact storyboard, native-frame decode, no approval score."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageChops, ImageStat

REF_SHA='2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def compare(ref,video,out):
    if sha(ref)!=REF_SHA:raise ValueError('Wrong storyboard')
    im=Image.open(ref)
    if im.n_frames!=12:raise ValueError('Wrong storyboard frame count')
    refs=[]
    for i in range(12):
        im.seek(i)
        if im.info.get('duration')!=400:raise ValueError('Wrong storyboard cadence')
        refs.append(im.convert('RGB'))
    d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    streams=d['streams'];v=streams[0]
    if len(streams)!=1 or v['codec_name']!='h264' or (v['width'],v['height'])!=(1920,1080) or v['avg_frame_rate']!='24/1' or abs(float(d['format']['duration'])-5)>.001:raise ValueError('Export mismatch')
    raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(video),'-vf','scale=320:180','-pix_fmt','rgb24','-f','rawvideo','-'])
    stride=320*180*3
    if len(raw)!=120*stride:raise ValueError('Decoded frame count mismatch')
    frames=[Image.frombytes('RGB',(320,180),raw[i*stride:(i+1)*stride]) for i in range(120)]
    delta=[round(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3,4) for a,b in zip(frames,frames[1:])]
    sheet=Image.new('RGB',(3*336,4*420),(15,19,27));draw=ImageDraw.Draw(sheet);beats=[]
    for i,ref_frame in enumerate(refs):
        idx=round(i*9.6);x=(i%3)*336;y=(i//3)*420
        draw.text((x+8,y+4),f'{i*.4:.1f}s storyboard | video {idx/24:.3f}s',fill='white')
        sheet.paste(ImageOps.contain(ref_frame,(180,180)),(x+78,y+22))
        sheet.paste(frames[idx],(x+8,y+226))
        draw.text((x+8,y+207),'Full 16:9 frame (not stretched to square)',fill='white')
        beats.append({'referenceSeconds':i*.4,'videoFrame':idx+1,'videoSeconds':idx/24})
    out.mkdir(parents=True,exist_ok=False)
    sheet.save(out/'comparison.jpg',quality=92)
    receipt={'referenceSha256':REF_SHA,'videoSha256':sha(video),'decodedFrames':120,'durationSeconds':5,'fps':24,'size':[1920,1080],'audio':False,'beats':beats,'adjacentFrameMeanAbsoluteRgbDelta':delta,'creativeApproval':False,'note':'Delta is diagnostic only; not a reference-similarity or motion-quality score.'}
    (out/'comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reference',type=Path);p.add_argument('video',type=Path);p.add_argument('private_output',type=Path);a=p.parse_args();compare(a.reference,a.video,a.private_output)
