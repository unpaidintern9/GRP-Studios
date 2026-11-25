"""Native V11 checkpoint and HD review render. No compute provisioning."""
import bpy,sys,time,json,hashlib,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from motion_contract import native_checkpoints,assert_contract
p=argparse.ArgumentParser();p.add_argument("--mode",choices=["checkpoints","review-hd"],required=True);p.add_argument("--output",required=True);p.add_argument("--blend-sha",required=True);p.add_argument("--frames",help="Optional comma-separated diagnostic frames, checkpoint mode only")
a=p.parse_args(sys.argv[sys.argv.index("--")+1:]);contract=assert_contract()
s=bpy.context.scene;src=Path(bpy.data.filepath);digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if tuple(bpy.app.version)!=(4,5,17) or digest(src)!=a.blend_sha:raise RuntimeError("Unverified scene or Blender")
if (s.frame_start,s.frame_end,s.render.fps,s.render.fps_base)!=(1,168,24,1):raise RuntimeError("Wrong timing")
if set(v.name for v in s.view_layers)!={"BrandStage","Earth"}:raise RuntimeError("Wrong layers")
prefs=bpy.context.preferences.addons["cycles"].preferences;prefs.compute_device_type="OPTIX";prefs.get_devices()
devices=[d for d in prefs.devices if d.type=="OPTIX"]
if not devices:raise RuntimeError("No OptiX, refuse CPU fallback")
for d in prefs.devices:d.use=d.type=="OPTIX"
s.cycles.device="GPU";s.cycles.denoiser="OPTIX";s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True;s.render.use_persistent_data=True
w,h,samples,threshold=(1280,720,24,.04) if a.mode=="checkpoints" else (1920,1080,48,.025)
s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100;s.cycles.samples=samples;s.cycles.adaptive_threshold=threshold;s.render.engine="CYCLES"
s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.render.image_settings.color_depth="8"
root=Path(a.output).resolve();root.mkdir(parents=True,exist_ok=False);frames=root/"frames";frames.mkdir()
if a.frames and a.mode!="checkpoints":raise RuntimeError("HD review must render every frame")
targets=tuple(int(f) for f in a.frames.split(",")) if a.frames else native_checkpoints() if a.mode=="checkpoints" else range(1,169)
if not targets or any(f<1 or f>168 for f in targets) or len(set(targets))!=len(targets):raise RuntimeError("Invalid frames")
receipt={"mode":a.mode,"creative_approval":False,"blend_sha256":a.blend_sha,"engine":"Cycles OptiX","blender":bpy.app.version_string,"devices":[{"name":d.name,"type":d.type} for d in devices],"resolution":[w,h],"fps":24,"native_frames":168,"samples":samples,"frames":[]}
for f in targets:
    t=time.monotonic();s.frame_set(f);dst=frames/f"frame-{f:03d}.png";s.render.filepath=str(dst)
    bpy.ops.render.render(write_still=True)
    if not dst.is_file() or dst.stat().st_size<1000:raise RuntimeError("Missing native frame")
    receipt["frames"].append({"frame":f,"bytes":dst.stat().st_size,"sha256":digest(dst),"seconds":round(time.monotonic()-t,3)})
    tmp=root/"progress.tmp";tmp.write_text(json.dumps(receipt));tmp.replace(root/"render-progress.json")
    print("V11_NATIVE_FRAME_COMPLETE",f,flush=True)
(root/"render-receipt.json").write_text(json.dumps(receipt,indent=2));print("V11_NATIVE_RENDER_PASS",a.mode,flush=True)
