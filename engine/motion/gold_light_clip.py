"""Render the complete five-second GRP ident from the native scene.
The final 15-frame hold is composed from the exact verified official PNG
in the post-production stage.  No generated still interpolation.
"""
import json
import argparse
import hashlib
from pathlib import Path
import sys
import time
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from gold_light_v02 import load_geometry, create_scene, private_path, WORK

def main():
    if tuple(bpy.app.version)!=(4,5,17):
        raise RuntimeError("Expected Blender 4.5.17")
    parser=argparse.ArgumentParser()
    parser.add_argument("--segment",type=int,choices=range(15))
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    segment=args.segment
    first,last=(1,105) if segment is None else (segment*7+1,segment*7+7)
    geometry,sha=load_geometry()
    out=private_path(WORK/"clip")
    out.mkdir(exist_ok=False)
    frames=out/"frames"
    frames.mkdir()
    scene,meshes=create_scene(geometry,sha)
    # Review-quality, native 1080p path-traced animation; final 4K polish
    # is separate. Fixed sample ceiling prevents unbounded sample escalation.
    scene.cycles.samples=12
    scene.cycles.use_denoising=True
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.08
    scene.render.use_persistent_data=True
    scene.render.threads_mode="FIXED"
    scene.render.threads=4
    scene.frame_set(1)
    if segment is None or segment==0:
        bpy.ops.wm.save_as_mainfile(filepath=str(out/"gold-light-v02.blend"))
    started=time.monotonic()
    # All moving frames are genuinely rendered. The locked closing card
    # is held at its exact original artwork in post-production.
    hashes=[]
    for frame in range(first,last+1):
        scene.frame_set(frame)
        dst=frames/f"frame-{frame:03d}.png"
        scene.render.filepath=str(dst)
        bpy.ops.render.render(write_still=True)
        if not dst.is_file() or dst.stat().st_size<24:
            raise RuntimeError(f"Missing native frame {frame}")
        hashes.append({"frame":frame,"file":dst.name,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest()})
    receipt={"status":"native-sequence-complete" if segment is None else "native-segment-complete","engine":"Cycles CPU",
             "version":bpy.app.version_string,"geometrySha256":sha,
             "nativeFrameCount":last-first+1,"segment":segment,"frameStart":first,"frameEnd":last,"frameHashes":hashes,"resolution":[1920,1080],"samples":12,
             "fps":24,"totalFrames":120,"renderSeconds":round(time.monotonic()-started,3),
             "meshes":meshes}
    (out/"native-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
if __name__=="__main__":
    main()
