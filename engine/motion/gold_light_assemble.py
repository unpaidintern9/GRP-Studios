"""Assemble only the 15 immutable native segment archives. No arbitrary extraction."""
import hashlib,json,zipfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"private/gold-light-v02/clip"
PARTS=ROOT/"private/segments"
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    device=os.environ.get("GRP_RENDER_DEVICE","CPU")
    if device not in ("CPU","OPTIX"):raise RuntimeError("Invalid render device")
    engine="Cycles OptiX" if device=="OPTIX" else "Cycles CPU"
    manifest=json.loads((PARTS/"manifest.json").read_text())
    if len(manifest)!=15:raise RuntimeError("Expected 15 fixed segments")
    OUT.mkdir(exist_ok=False)
    frames=OUT/"frames";frames.mkdir()
    geometry=None; total_seconds=0; all_hashes=[]; first_receipt=None
    for i,m in enumerate(manifest):
        if m["index"]!=i:raise RuntimeError("Segment order mismatch")
        p=PARTS/f"segment-{i:02d}.zip"
        raw=p.read_bytes()
        if len(raw)!=m["bytes"] or sha(raw)!=m["sha256"]:raise RuntimeError("Segment digest mismatch")
        a,b=i*7+1,i*7+7
        names=[f"frame-{n:03d}.png" for n in range(a,b+1)]
        expected={"native-receipt.json",*names}
        if i==0:expected.add("gold-light-v02.blend")
        with zipfile.ZipFile(p) as z:
            if len(z.infolist())!=len(expected) or set(z.namelist())!=expected:raise RuntimeError("Unexpected segment entries")
            if sum(x.file_size for x in z.infolist())>64_000_000:raise RuntimeError("Oversize segment")
            r=json.loads(z.read("native-receipt.json"))
            if r["status"]!="native-segment-complete" or r["segment"]!=i or r["frameStart"]!=a or r["frameEnd"]!=b or r["nativeFrameCount"]!=7 or r["resolution"]!=[1920,1080] or r["fps"]!=24 or r["samples"]!=12 or r["engine"]!=engine or not r["version"].startswith("4.5.17"):raise RuntimeError("Native segment receipt mismatch")
            if device=="OPTIX" and (not r.get("devices") or any(d.get("type")!="OPTIX" or not d.get("name") or not d.get("id") for d in r["devices"])):raise RuntimeError("Missing OptiX device evidence")
            if geometry is None:geometry=r["geometrySha256"];first_receipt=r
            if geometry!=r["geometrySha256"]:raise RuntimeError("Geometry changed across segments")
            if len(r["frameHashes"])!=7:raise RuntimeError("Segment hash count mismatch")
            for n,h in zip(names,r["frameHashes"]):
                data=z.read(n)
                if h["file"]!=n or h["frame"]!=int(n[6:9]) or sha(data)!=h["sha256"]:raise RuntimeError("Native frame hash mismatch")
                (frames/n).write_bytes(data);all_hashes.append(h)
            if i==0:(OUT/"gold-light-v02.blend").write_bytes(z.read("gold-light-v02.blend"))
            total_seconds+=r["renderSeconds"]
    if len(list(frames.glob("frame-*.png")))!=105:raise RuntimeError("Native frame coverage incomplete")
    receipt={**first_receipt,"status":"native-sequence-complete","segment":None,"frameStart":1,"frameEnd":105,"nativeFrameCount":105,"frameHashes":all_hashes,"renderSeconds":round(total_seconds,3)}
    (OUT/"native-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
if __name__=="__main__":main()
