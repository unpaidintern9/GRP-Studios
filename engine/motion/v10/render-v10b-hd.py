import bpy,sys,time,json,hashlib
from pathlib import Path
s=bpy.context.scene;root=Path("/tmp/grp-v10/review-hd");root.mkdir(exist_ok=False);frames=root/"frames";frames.mkdir()
src=Path(bpy.data.filepath);p=bpy.context.preferences.addons["cycles"].preferences;p.compute_device_type="OPTIX";p.get_devices()
dev=[d for d in p.devices if d.type=="OPTIX"]
if not dev:raise RuntimeError("OptiX unavailable")
for d in p.devices:d.use=d.type=="OPTIX"
s.cycles.device="GPU";s.cycles.denoiser="OPTIX";s.cycles.use_denoising=True;s.cycles.samples=32;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.035
s.render.use_persistent_data=True;s.render.engine="CYCLES";s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=168
s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.render.image_settings.color_depth="8"
# Preserve both real render layers; the current proof has no final creative approval.
r={"mode":"native HD review proof","creative_approval":False,"blend_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"engine":"Cycles OptiX","devices":[{"name":d.name,"type":d.type} for d in dev],"version":bpy.app.version_string,"resolution":[1920,1080],"fps":24,"native_frames":168,"samples":32,"frames":[]}
for f in range(1,169):
    t=time.monotonic();s.frame_set(f);dst=frames/f"frame-{f:03d}.png";s.render.filepath=str(dst);bpy.ops.render.render(write_still=True)
    if not dst.is_file() or dst.stat().st_size<1000:raise RuntimeError("Frame missing")
    r["frames"].append({"frame":f,"bytes":dst.stat().st_size,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),"seconds":round(time.monotonic()-t,3)})
    tmp=root/"progress.tmp";tmp.write_text(json.dumps(r));tmp.replace(root/"render-progress.json")
    print("V10B_NATIVE_FRAME_COMPLETE",f,flush=True)
(root/"render-receipt.json").write_text(json.dumps(r,indent=2))
print("V10B_RENDER_PASS",flush=True)
