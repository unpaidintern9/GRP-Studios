"""Private fixed post-production. Validate exact native frames and official hold.
Run using the system Python and FFmpeg in the dedicated renderer image.
"""
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image
from fractions import Fraction
from math import isclose

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"private/gold-light-v02/clip"
FRAMES=OUT/"frames"
ORIGINAL=ROOT/"private/brand/grp-full-reverse.png"
SHA="57640212bfc8173a8cb5c2b740129ba365898c95846db1156035c3efe1ccdf76"
WIDTH,HEIGHT=1920,1080

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args,timeout=30):
    return subprocess.run(args,check=True,capture_output=True,text=True,timeout=timeout).stdout

def main():
    native=json.loads((OUT/"native-receipt.json").read_text())
    if native["nativeFrameCount"]!=105 or native["resolution"]!=[WIDTH,HEIGHT]:
        raise RuntimeError("Native frame receipt mismatch")
    if sha(ORIGINAL)!=SHA:
        raise RuntimeError("Original lockup digest mismatch")
    # Match the final camera's centered horizontal sensor framing:
    # 36 mm sensor, 48 mm lens, camera distance 13.1; same XY source scale
    # and center as gold_light_v02.py. Preserve original aspect and alpha.
    raw=Image.open(ORIGINAL).convert("RGBA")
    if raw.size!=(1536,934):
        raise RuntimeError("Original artwork dimensions mismatch")
    scale=WIDTH*(6.0/932.0)*48/(36*13.1)
    size=(round(raw.width*scale),round(raw.height*scale))
    rgba=raw.resize(size,Image.Resampling.LANCZOS)
    hold=Image.new("RGBA",(WIDTH,HEIGHT),(4,6,10,255))
    hold.alpha_composite(rgba,(round(WIDTH/2-744*scale),round(HEIGHT/2-453.5*scale)))
    hold=hold.convert("RGB")
    for frame in range(1,106):
        path=FRAMES/f"frame-{frame:03d}.png"
        image=Image.open(path).convert("RGB")
        if image.size!=(WIDTH,HEIGHT):
            raise RuntimeError(f"Frame {frame} is not native 1080p")
        # Ease the final physical-light reveal into the exact original lockup.
        if frame>=96:
            t=(frame-95)/11
            weight=t*t*(3-2*t)
            Image.blend(image,hold,weight).save(path)
    for frame in range(106,121):
        hold.save(FRAMES/f"frame-{frame:03d}.png")
    if len(list(FRAMES.glob("frame-*.png")))!=120:
        raise RuntimeError("Missing or extra timeline frames")
    dst=OUT/"GRP-Gold-Light-V02-5s.mp4"
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-n",
         "-framerate","24","-start_number","1","-i",str(FRAMES/"frame-%03d.png"),
         "-frames:v","120","-an","-c:v","libx264","-preset","fast","-crf","17",
         "-pix_fmt","yuv420p","-movflags","+faststart",str(dst)],timeout=65)
    data=json.loads(run(["ffprobe","-v","error","-count_frames",
        "-show_streams","-show_format","-of","json",str(dst)],timeout=30))
    streams=data["streams"]
    if len(streams)!=1:
        raise RuntimeError("Expected one silent video stream")
    v=streams[0]
    if (v["codec_name"],v["width"],v["height"],v["pix_fmt"])!=("h264",WIDTH,HEIGHT,"yuv420p"):
        raise RuntimeError("Encoded video does not match delivery contract")
    if Fraction(v["avg_frame_rate"])!=24 or int(v["nb_read_frames"])!=120 or not isclose(float(data["format"]["duration"]),5.0,abs_tol=.001):
        raise RuntimeError("Encoded duration/frame count mismatch")
    if sha(FRAMES/"frame-106.png")!=sha(FRAMES/"frame-120.png"):
        raise RuntimeError("Final hold is not stable")
    # Decode the complete MP4, not merely the header.
    run(["ffmpeg","-nostdin","-v","error","-i",str(dst),"-f","null","-"],timeout=30)
    review=[18,36,76,114]
    for f in review:
        (OUT/f"frame-{f:03d}.png").write_bytes((FRAMES/f"frame-{f:03d}.png").read_bytes())
    receipt={**native,"status":"unapproved-five-second-clip","video":{
      "file":dst.name,"sha256":sha(dst),"bytes":dst.stat().st_size,
      "codec":"h264","durationSeconds":5,"frames":120,"fps":24,
      "width":WIDTH,"height":HEIGHT,"audio":False},"originalEndHoldSha256":SHA,
      "keyframes":[{"frame":f,"file":f"frame-{f:03d}.png","sha256":sha(OUT/f"frame-{f:03d}.png")} for f in review]}
    (OUT/"clip-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
if __name__=="__main__":
    main()
