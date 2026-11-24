"""Private asset staging: source URLs verified from Solar System Scope.
No private inputs or assets are committed. Download once outside Blender, pack
validated textures into the scene, retain provenance with private deliverables.
"""
import argparse, hashlib, json, pathlib, urllib.request
from urllib.parse import urlsplit
from PIL import Image

BASE="https://cdn.solarsystemscope.com/textures/download/"
ASSETS={"day":"8k_earth_daymap.jpg","night":"8k_earth_nightmap.jpg","clouds":"8k_earth_clouds.jpg"}
LICENSE="https://creativecommons.org/licenses/by/4.0/"
CREDIT="Earth texture maps by Solar System Scope (https://www.solarsystemscope.com/textures/), CC BY 4.0; adapted for GRP's artistic lighting and 3D composition. No affiliation or endorsement."
MAX_BYTES=24*1024*1024
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(p):
    if not 1024<p.stat().st_size<=MAX_BYTES:raise RuntimeError("Unexpected image size: "+p.name)
    with Image.open(p) as im:
        if im.format!="JPEG" or tuple(im.size)!=(8192,4096):raise RuntimeError("Expected 8192x4096 JPEG: "+p.name)
        im.verify()
    return {"file":p.name,"bytes":p.stat().st_size,"sha256":sha(p),"dimensions":[8192,4096]}
class SameHost(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,hdrs,newurl):
        u=urlsplit(newurl)
        if u.scheme!="https" or u.hostname!="cdn.solarsystemscope.com" or not u.path.startswith("/textures/download/"):
            raise RuntimeError("Unexpected asset redirect")
        return super().redirect_request(req,fp,code,msg,hdrs,newurl)
def stage(root):
    root=pathlib.Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    manifest={"provider":"Solar System Scope","source":"https://www.solarsystemscope.com/textures/","license":LICENSE,"credit":CREDIT,"assets":{}}
    opener=urllib.request.build_opener(SameHost())
    for role,name in ASSETS.items():
        dst=root/name
        if not dst.exists():
            temp=dst.with_suffix(".part")
            try:
                with opener.open(urllib.request.Request(BASE+name,headers={"User-Agent":"GRP-Studio-Asset-Staging/1.0"}),timeout=60) as response,temp.open("wb") as out:
                    size=0
                    while True:
                        data=response.read(1024*1024)
                        if not data:break
                        size+=len(data)
                        if size>MAX_BYTES:raise RuntimeError("Asset exceeds bound")
                        out.write(data)
                verify(temp);temp.replace(dst)
            finally:
                if temp.exists():temp.unlink()
        manifest["assets"][role]={**verify(dst),"url":BASE+name}
    path=root/"earth-assets.json"
    if path.exists() and json.loads(path.read_text())!=manifest:raise RuntimeError("Existing asset manifest changed")
    path.write_text(json.dumps(manifest,indent=2)+"\n")
    (root/"ATTRIBUTION.txt").write_text(CREDIT+"\n"+LICENSE+"\n")
    return manifest
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("directory");a=p.parse_args();print(json.dumps(stage(a.directory),indent=2))
