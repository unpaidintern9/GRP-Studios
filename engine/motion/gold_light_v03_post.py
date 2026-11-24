"""Encode a private native motion study; no logo compositing or reference images."""
import hashlib,json,subprocess
from pathlib import Path
from fractions import Fraction
OUT=Path(__file__).resolve().parents[2]/"private/gold-light-v03/lookdev"
def main():
    r=json.loads((OUT/"motion-receipt.json").read_text())
    frames=OUT/"frames"
    if len(list(frames.glob("frame-*.png")))!=50:raise RuntimeError("Incomplete native motion")
    dst=OUT/"GRP-V03-motion-review.mp4"
    subprocess.run(["ffmpeg","-nostdin","-v","error","-n","-framerate","10","-start_number","0","-i",str(frames/"frame-%03d.png"),"-frames:v","50","-an","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(dst)],check=True,timeout=45)
    d=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(dst)],timeout=20))
    v=d["streams"][0]
    if len(d["streams"])!=1 or v["codec_name"]!="h264" or (v["width"],v["height"])!=(640,360) or Fraction(v["avg_frame_rate"])!=10 or int(v["nb_read_frames"])!=50 or abs(float(d["format"]["duration"])-5)>.001:raise RuntimeError("Motion export mismatch")
    subprocess.run(["ffmpeg","-nostdin","-v","error","-i",str(dst),"-f","null","-"],check=True,timeout=20)
    r["video"]={"file":dst.name,"bytes":dst.stat().st_size,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),"durationSeconds":5,"frames":50,"fps":10,"codec":"h264","audio":False}
    (OUT/"motion-receipt.json").write_text(json.dumps(r,indent=2))
if __name__=="__main__":main()
