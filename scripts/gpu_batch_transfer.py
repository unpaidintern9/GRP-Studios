"""One-shot GPU transport. Only short-lived job-specific HTTPS URLs, no account keys.
Run inside the pinned service image on an authorized NVIDIA host. No listening server.
"""
import hashlib, os, pathlib, subprocess, tempfile, urllib.request, urllib.parse

MAX_INPUT=400_000_000
MAX_OUTPUT=24_000_000
def checked_url(name):
    value=os.environ[name]
    u=urllib.parse.urlsplit(value)
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.fragment:
        raise RuntimeError("Expected private HTTPS transfer URL")
    return value
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise RuntimeError("Redirect refused")
def main():
    expected=os.environ["GRP_INPUT_SHA256"]
    if len(expected)!=64 or any(c not in "0123456789abcdef" for c in expected):
        raise RuntimeError("Invalid input digest")
    opener=urllib.request.build_opener(NoRedirect())
    with tempfile.TemporaryDirectory(prefix="grp-gpu-") as d:
        src=pathlib.Path(d)/"input.bin"; dst=pathlib.Path(d)/"output.zip"
        h=hashlib.sha256(); size=0
        with opener.open(checked_url("GRP_INPUT_URL"),timeout=30) as response, src.open("xb") as out:
            while True:
                b=response.read(1024*1024)
                if not b:break
                size+=len(b)
                if size>MAX_INPUT:raise RuntimeError("Input too large")
                h.update(b);out.write(b)
        if h.hexdigest()!=expected:raise RuntimeError("Input checksum mismatch")
        env={**os.environ,"GRP_RENDER_DEVICE":"OPTIX"}
        for k in ("GRP_INPUT_URL","GRP_OUTPUT_URL","GRP_INPUT_SHA256"):env.pop(k,None)
        with src.open("rb") as stdin,dst.open("xb") as stdout:
            subprocess.run(["/usr/local/bin/node","/opt/studio/plugins/blender/clip-batch-runner.mjs"],stdin=stdin,stdout=stdout,env=env,check=True,timeout=540)
        if not 100<dst.stat().st_size<=MAX_OUTPUT:raise RuntimeError("Archive size invalid")
        body=dst.read_bytes()
        if not body.startswith(b"PK\x03\x04"):raise RuntimeError("Archive invalid")
        request=urllib.request.Request(checked_url("GRP_OUTPUT_URL"),data=body,method="PUT",headers={"Content-Type":"application/zip"})
        with opener.open(request,timeout=60) as response:
            if response.status not in (200,201,204):raise RuntimeError("Upload failed")
        print("GRP_OUTPUT_SHA256="+hashlib.sha256(body).hexdigest(),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        # Exceptions from HTTP clients may contain signed URLs; never print them.
        raise SystemExit("GPU batch failed: "+type(e).__name__) from None
