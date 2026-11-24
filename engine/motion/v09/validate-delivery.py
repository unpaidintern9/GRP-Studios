import json,pathlib,subprocess,hashlib,statistics
from PIL import Image,ImageChops,ImageStat
root=pathlib.Path('/tmp/grp-v09/final')
video=root/'GRP-V09-1080p-OptiX.mp4'
probe=json.loads((root/'probe.json').read_text())
streams=probe['streams'];v=[s for s in streams if s['codec_type']=='video']
assert len(v)==1 and not any(s['codec_type']=='audio' for s in streams)
s=v[0]
assert s['codec_name']=='h264' and s['width']==1920 and s['height']==1080
assert s['avg_frame_rate']=='24/1' and int(s['nb_read_frames'])==168
assert abs(float(probe['format']['duration'])-7)<.001
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
r=json.loads((root/'render-receipt.json').read_text())
assert r['devices']==[{'name':'NVIDIA L40S','type':'OPTIX'}]
assert r['nativeFrames']==168 and len(r['frames'])==168 and r['samples']==96
assert [f['frame'] for f in r['frames']]==list(range(1,169))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
frames=root/'frames';previous=None;delta=[];means=[]
for f in r['frames']:
    p=frames/f"frame-{f['frame']:03}.png"
    assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
    with Image.open(p) as im:
        assert im.size==(1920,1080)
        thumb=im.convert('RGB').resize((192,108),Image.Resampling.LANCZOS)
    if previous:
        diff=ImageChops.difference(thumb,previous)
        delta.append({'frame':f['frame'],'meanAbsRgbDelta':sum(ImageStat.Stat(diff).mean)/3})
    means.append({'frame':f['frame'],'meanRgb':sum(ImageStat.Stat(thumb).mean)/3})
    previous=thumb
r.update({'technicalStatus':'PASS','creativeApproval':False,'sourceCommit':'f7f943c2817ce4048eb70584f470cd8d280f7457','video':{'file':video.name,'bytes':video.stat().st_size,'sha256':sha(video),'codec':s['codec_name'],'fps':24,'frames':168,'durationSeconds':7,'audio':False},'blend':{'file':'gold-light-v09d.blend','bytes':(root/'gold-light-v09d.blend').stat().st_size,'sha256':sha(root/'gold-light-v09d.blend')},'originalSourceParity':json.loads((root.parent/'source-parity.json').read_text()),'decodeValidation':'ffmpeg -xerror complete','motionDiagnostics':{'meanAbsRgbDelta':statistics.mean(x['meanAbsRgbDelta'] for x in delta),'largestDeltas':sorted(delta,key=lambda x:x['meanAbsRgbDelta'],reverse=True)[:8],'minimumMeanRgb':min(means,key=lambda x:x['meanRgb']),'note':'Diagnostic only; intended lighting changes and holds may produce large or small frame deltas.'}})
(root/'final-receipt.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:r[k] for k in ('technicalStatus','creativeApproval','video','blend','motionDiagnostics')},indent=2))
