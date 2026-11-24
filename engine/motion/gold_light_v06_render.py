"""Finite native GPU render/export. Requires explicit OptiX and hard UTC deadline.
No implicit CPU fallback, no provider provisioning, no network transfers.
"""
import bpy, hashlib, json, os, time, sys, subprocess
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gold_light_v02 import load_geometry, private_path, WORK
from gold_light_v06 import create_scene

OUT=WORK.parent/"gold-light-v06-gpu"
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if tuple(bpy.app.version)!=(4,5,17):raise RuntimeError("Unexpected Blender version")
    if os.environ.get("GRP_RENDER_DEVICE")!="OPTIX":raise RuntimeError("Explicit GPU mode required")
    deadline=int(os.environ["GRP_DEADLINE_EPOCH"])
    if not time.time()+60<deadline<=time.time()+3600:raise RuntimeError("Invalid bounded render deadline")
    source=os.environ["GRP_SOURCE_COMMIT"]
    if len(source)!=40 or any(x not in "0123456789abcdef" for x in source):raise RuntimeError("Invalid source commit")
    g,sha=load_geometry();s,geo,pos=create_scene(g,sha)
    prefs=bpy.context.preferences.addons["cycles"].preferences;prefs.compute_device_type="OPTIX";prefs.get_devices()
    devices=[{"name":d.name,"type":d.type,"id":d.id} for d in prefs.devices if d.type=="OPTIX"]
    if not devices:raise RuntimeError("No actual OptiX device")
    for d in prefs.devices:d.use=d.type=="OPTIX"
    s.cycles.device="GPU";s.cycles.denoiser="OPTIX";s.cycles.denoising_use_gpu=True
    s.render.use_persistent_data=True;s.render.threads_mode="FIXED";s.render.threads=8
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.render.image_settings.color_depth="8"
    s["source_commit"]=source;s["creative_status"]="unapproved V06 native GPU proof"
    out=private_path(OUT);out.mkdir(parents=True,exist_ok=False);frames=out/"frames";frames.mkdir()
    s.frame_set(106);blend=out/"gold-light-v06-gpu.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    result={}
    def render(f):
        if time.time()+45>deadline:raise RuntimeError("Bounded render deadline reached")
        s.frame_set(f);p=frames/f"frame-{f:03d}.png";s.render.filepath=str(p);t=time.monotonic();bpy.ops.render.render(write_still=True)
        b=p.read_bytes()
        if b[:8]!=b"\x89PNG\r\n\x1a\n" or int.from_bytes(b[16:20],"big")!=1920 or int.from_bytes(b[20:24],"big")!=1080:raise RuntimeError("Native frame mismatch")
        result[f]={"frame":f,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"seconds":round(time.monotonic()-t,3)}
        (out/"progress.json").write_text(json.dumps({"devices":devices,"framesCompleted":len(result),"frames":result},indent=2))
        print("GRP_V06_FRAME",f,result[f],flush=True)
    for f in (11,39,78,98,106):render(f)
    estimate=max(result[f]["seconds"] for f in (39,78,98,106))*115*1.3+100
    if time.time()+estimate>deadline:raise RuntimeError("HD motion estimate exceeds authorized deadline")
    for f in range(1,121):
        if f not in result:render(f)
    if len(result)!=120:raise RuntimeError("Missing native frames")
    video=out/"GRP-V06-1080p-OptiX.mp4"
    def run(args,max_seconds):
        left=int(deadline-time.time())
        if left<1:raise RuntimeError("Deadline reached")
        return subprocess.check_output(args,timeout=min(max_seconds,left))
    run(["ffmpeg","-nostdin","-v","error","-n","-framerate","24","-start_number","1","-i",str(frames/"frame-%03d.png"),"-frames:v","120","-an","-c:v","libx264","-crf","17","-preset","fast","-pix_fmt","yuv420p","-movflags","+faststart",str(video)],90)
    d=json.loads(run(["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(video)],25));v=d["streams"][0]
    if len(d["streams"])!=1 or v["codec_name"]!="h264" or (v["width"],v["height"])!=(1920,1080) or Fraction(v["avg_frame_rate"])!=24 or int(v["nb_read_frames"])!=120 or abs(float(d["format"]["duration"])-5)>.001:raise RuntimeError("Export mismatch")
    run(["ffmpeg","-nostdin","-v","error","-i",str(video),"-f","null","-"],25)
    receipt={"status":"unapproved-native-v06-gpu-proof","version":bpy.app.version_string,"engine":"Cycles OptiX","devices":devices,"denoiser":"OPTIX","sourceCommit":source,"referenceSha256":s["reference_sha256"],"geometrySha256":sha,"geometry":geo,"resolution":[1920,1080],"samples":64,"nativeFrames":120,"fps":24,"motionBlur":True,"closingTreatment":s["closing_treatment"],"creativeApproval":False,"frames":[result[i] for i in range(1,121)],"video":{"file":video.name,"bytes":video.stat().st_size,"sha256":digest(video),"codec":"h264","durationSeconds":5,"fps":24,"frames":120,"audio":False},"blend":{"file":blend.name,"bytes":blend.stat().st_size,"sha256":digest(blend)}}
    (out/"final-receipt.json").write_text(json.dumps(receipt,indent=2))
    print("GRP_V06_NATIVE_120_EXPORT_PASS",flush=True)
if __name__=="__main__":main()
