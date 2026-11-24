"""Native preview and master rendering. Does not allocate compute or publish files.
Run from a verified V10 blend in an authorized, bounded Blender 4.5.17 session.
"""
import argparse, hashlib, json, sys, time
from pathlib import Path
import bpy
from mathutils import Vector
FPS=24;TOTAL=168
CHECKPOINTS=(1,15,29,43,57,71,85,99,113,118,123,127,134,141,155,168)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=["checkpoints","motion","master"],required=True)
    p.add_argument("--output",required=True);p.add_argument("--device",choices=["OPTIX","CPU"],required=True)
    p.add_argument("--approved-draft-manifest");p.add_argument("--blend-sha",required=True)
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    s=bpy.context.scene;source=Path(bpy.data.filepath)
    if tuple(bpy.app.version)!=(4,5,17) or not source.is_file() or digest(source)!=a.blend_sha:
        raise RuntimeError("Wrong Blender version or scene digest")
    if a.mode=="master":
        if not a.approved_draft_manifest:raise RuntimeError("Master requires reviewed native motion draft")
        review=json.loads(Path(a.approved_draft_manifest).read_text())
        if review.get("blend_sha256")!=a.blend_sha or review.get("native_motion_review_pass") is not True:
            raise RuntimeError("Native motion review not recorded")
    if (s.frame_start,s.frame_end,s.render.fps,s.render.fps_base)!=(1,TOTAL,FPS,1):raise RuntimeError("Scene timing mismatch")
    if set(v.name for v in s.view_layers)!={"BrandStage","Earth"}:raise RuntimeError("Unexpected render layer isolation")
    if a.device=="OPTIX":
        p=bpy.context.preferences.addons["cycles"].preferences;p.compute_device_type="OPTIX";p.get_devices()
        gpu=[d for d in p.devices if d.type=="OPTIX"]
        if not gpu:raise RuntimeError("No OptiX GPU; refuse silent CPU fallback")
        for d in p.devices:d.use=d.type=="OPTIX"
        s.cycles.device="GPU";s.cycles.denoiser="OPTIX";devices=[{"name":d.name,"type":d.type} for d in gpu]
    else:
        s.cycles.device="CPU";s.cycles.denoiser="OPENIMAGEDENOISE";devices=[{"type":"CPU"}]
    s.cycles.use_denoising=True;s.render.use_persistent_data=True
    specs={"checkpoints":(1280,720,24,.035),"motion":(960,540,12,.075),"master":(1920,1080,64,.018)}
    w,h,samples,threshold=specs[a.mode];s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.cycles.samples=samples;s.cycles.adaptive_threshold=threshold
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.render.image_settings.color_depth="8"
    s.view_settings.view_transform="AgX"
    root=Path(a.output).resolve();root.mkdir(parents=True,exist_ok=False)
    frames=root/"frames";frames.mkdir()
    if a.mode=="master":(root/"exr").mkdir()
    receipt={"mode":a.mode,"blend_sha256":a.blend_sha,"engine":"Cycles","devices":devices,"resolution":[w,h],"samples":samples,"fps":FPS,"native_frames":TOTAL,"creative_approval":False,"frames":[]}
    targets=CHECKPOINTS if a.mode=="checkpoints" else range(1,TOTAL+1)
    for f in targets:
        start=time.monotonic();s.frame_set(f);dst=frames/f"frame-{f:03}.png";s.render.filepath=str(dst)
        bpy.ops.render.render(write_still=True)
        if not dst.is_file() or dst.stat().st_size<1000:raise RuntimeError("Missing composed PNG")
        if a.mode=="master":
            s.render.image_settings.file_format="OPEN_EXR_MULTILAYER";s.render.image_settings.color_mode="RGBA";s.render.image_settings.color_depth="16"
            exr=root/"exr"/f"frame-{f:03}.exr"
            bpy.data.images["Render Result"].save_render(str(exr),scene=s)
            if not exr.is_file():raise RuntimeError("Missing scene-linear multilayer EXR")
            s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB";s.render.image_settings.color_depth="8"
        receipt["frames"].append({"frame":f,"bytes":dst.stat().st_size,"sha256":digest(dst),"seconds":round(time.monotonic()-start,3)})
        (root/"render-progress.json").write_text(json.dumps(receipt,indent=2))
        print("V10_NATIVE_FRAME_COMPLETE",f,flush=True)
    (root/"render-receipt.json").write_text(json.dumps(receipt,indent=2))
    print("V10_NATIVE_RENDER_PASS",a.mode,flush=True)
if __name__=="__main__":main()
