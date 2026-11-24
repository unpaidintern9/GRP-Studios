"""Encode exact native 24fps sequence with no interpolated or repeated holds."""
import hashlib,json,subprocess
from pathlib import Path
from fractions import Fraction
OUT=Path(__file__).resolve().parents[2]/"private/gold-light-v05/lookdev"
def main():
    r=json.loads((OUT/"v05-receipt.json").read_text());frames=OUT/"frames"
    files=sorted(frames.glob("frame-*.png"))
    if len(files)!=120 or [p.name for p in files]!=[f"frame-{i:03d}.png" for i in range(1,121)] or [hashlib.sha256(p.read_bytes()).hexdigest() for p in files]!=r["frameHashes"]:raise RuntimeError("Native frame evidence mismatch")
    dst=OUT/"GRP-V05-motion-proof.mp4"
    subprocess.run(["ffmpeg","-nostdin","-v","error","-n","-framerate","24","-start_number","1","-i",str(frames/"frame-%03d.png"),"-frames:v","120","-an","-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(dst)],check=True,timeout=35)
    d=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(dst)],timeout=15));v=d["streams"][0]
    if len(d["streams"])!=1 or v["codec_name"]!="h264" or (v["width"],v["height"])!=(768,432) or Fraction(v["avg_frame_rate"])!=24 or int(v["nb_read_frames"])!=120 or abs(float(d["format"]["duration"])-5)>.001:raise RuntimeError("Video export mismatch")
    subprocess.run(["ffmpeg","-nostdin","-v","error","-i",str(dst),"-f","null","-"],check=True,timeout=15)
    r["video"]={"file":dst.name,"bytes":dst.stat().st_size,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),"durationSeconds":5,"frames":120,"fps":24,"codec":"h264","audio":False}
    (OUT/"v05-receipt.json").write_text(json.dumps(r,indent=2))
if __name__=="__main__":main()
