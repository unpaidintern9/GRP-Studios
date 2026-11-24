import bpy,json,time,hashlib
from pathlib import Path
s=bpy.context.scene
p=bpy.context.preferences.addons["cycles"].preferences
p.compute_device_type="OPTIX";p.get_devices()
dev=[d for d in p.devices if d.type=="OPTIX"]
if not dev:raise RuntimeError("No OptiX GPU; CPU fallback refused")
for d in p.devices:d.use=d.type=="OPTIX"
s.cycles.device="GPU";s.cycles.denoiser="OPTIX";s.cycles.use_denoising=True
s.cycles.samples=96;s.cycles.adaptive_threshold=.015
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=168
s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB"
s.render.use_persistent_data=True
root=Path("/tmp/grp-v09/final");root.mkdir(exist_ok=True)
frames=root/"frames";frames.mkdir(exist_ok=True)
s["creative_status"]="V09d review candidate, not approved"
s.frame_set(145);bpy.ops.wm.save_as_mainfile(filepath=str(root/"gold-light-v09d.blend"))
receipt={"creativeApproval":False,"engine":"Cycles OptiX","version":bpy.app.version_string,"devices":[{"name":d.name,"type":d.type} for d in dev],"resolution":[1920,1080],"fps":24,"nativeFrames":168,"samples":96,"contours":json.loads(Path("/tmp/grp-v09/contour-d-receipt.json").read_text()),"frames":[]}
for f in range(1,169):
    t=time.monotonic();s.frame_set(f);dst=frames/f"frame-{f:03}.png";s.render.filepath=str(dst);bpy.ops.render.render(write_still=True)
    receipt["frames"].append({"frame":f,"bytes":dst.stat().st_size,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),"seconds":round(time.monotonic()-t,3)})
    (root/"render-progress.json").write_text(json.dumps(receipt))
    print("V09_FRAME_COMPLETE",f,flush=True)
(root/"render-receipt.json").write_text(json.dumps(receipt,indent=2))
print("V09_RENDER_PASS",flush=True)
