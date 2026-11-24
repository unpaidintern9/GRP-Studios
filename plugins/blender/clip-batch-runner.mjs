// Fixed native chunk/assembly runner; binary-framed private inputs and ZIP output.
import {createHash} from "node:crypto";
import {mkdir,readFile,writeFile,stat,rm} from "node:fs/promises";
import {spawnSync} from "node:child_process";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {INPUTS,CLIP_TEMPLATE,MAX_REQUEST_BYTES,MAX_ARCHIVE_BYTES,validateEnvelope,validClipReceipt} from "./review-contract.mjs";
import {SEGMENTS,range,validSegmentReceipt} from "./clip-plan.mjs";
const root=fileURLToPath(new URL("../../",import.meta.url));
const work=path.join(root,"private"),out=path.join(work,"gold-light-v02","clip");
const sha=b=>createHash("sha256").update(b).digest("hex");
const blob=b=>createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");
const iter=process.stdin[Symbol.asyncIterator]();let rem=Buffer.alloc(0);
async function take(n){const result=Buffer.alloc(n);let offset=0;while(offset<n){if(!rem.length){const next=await iter.next();if(next.done)throw Error("Truncated input");rem=Buffer.from(next.value)}const len=Math.min(rem.length,n-offset);rem.copy(result,offset,0,len);rem=rem.subarray(len);offset+=len}return result}
async function eof(){if(rem.length)throw Error("Unexpected trailing input");const p=await iter.next();if(!p.done)throw Error("Unexpected trailing input")}
function run(cmd,args,timeout){const p=spawnSync(cmd,args,{cwd:root,timeout,killSignal:"SIGKILL",stdio:["ignore","pipe","pipe"],maxBuffer:8000000,env:{PATH:"/usr/local/bin:/usr/bin:/bin",HOME:"/tmp",BLENDER_BIN:"/opt/blender/blender"}});if(p.error||p.status!==0){console.error("Stage failed:",cmd,p.error?.message??p.status);console.error(p.stderr?.toString().slice(-2500));throw Error("Production stage failed")}}
function verifyPng(b){if(b.length<24||!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))||b.readUInt32BE(16)!==1920||b.readUInt32BE(20)!==1080)throw Error("Native frame format mismatch")}
async function main(){
 const headerSize=(await take(4)).readUInt32BE(0);if(headerSize<2||headerSize>MAX_REQUEST_BYTES)throw Error("Header size");
 const h=JSON.parse((await take(headerSize)).toString("utf8"));
 const mode=h.mode,segment=h.segment;
 if(h.template!==CLIP_TEMPLATE||!["segment","assemble"].includes(mode))throw Error("Unsupported production mode");
 if(mode==="segment"){range(segment);if(Object.keys(h).sort().join(",")!=="assets,mode,segment,template")throw Error("Unexpected segment fields")}
 else if(Object.keys(h).sort().join(",")!=="assets,mode,segments,template"||!Array.isArray(h.segments)||h.segments.length!==SEGMENTS||h.segments.some((x,i)=>Object.keys(x).sort().join(",")!=="bytes,index,sha256"||x.index!==i||!Number.isSafeInteger(x.bytes)||x.bytes<100||x.bytes>MAX_ARCHIVE_BYTES||!/^[a-f0-9]{64}$/.test(x.sha256)))throw Error("Invalid assembly manifest");
 const assets=validateEnvelope({template:CLIP_TEMPLATE,assets:h.assets}).assets.map((a,i)=>{const b=Buffer.from(a.base64,"base64"),e=INPUTS[i];if(b.length!==e.bytes||b.toString("base64")!==a.base64||sha(b)!==e.sha256||blob(b)!==e.blob)throw Error("Original asset hash mismatch");return b});
 await mkdir(work);
 try{
  await mkdir(path.join(work,"brand"));for(let i=0;i<assets.length;i++)await writeFile(path.join(work,"brand",INPUTS[i].name),assets[i],{flag:"wx"});
  let files,zipRoot;
  if(mode==="segment"){
   await eof();run(process.execPath,["engine/brand/prepare_gold_light.mjs"],30000);
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_clip.py","--","--segment",String(segment)],450000);
   const r=JSON.parse(await readFile(path.join(out,"native-receipt.json"),"utf8"));if(!validSegmentReceipt(r,segment))throw Error("Segment receipt mismatch");
   const [first,last]=range(segment);
   files=["native-receipt.json"];for(let n=first;n<=last;n++){const f="frame-"+String(n).padStart(3,"0")+".png";const b=await readFile(path.join(out,"frames",f));verifyPng(b);if(sha(b)!==r.frameHashes[n-first].sha256)throw Error("Frame digest mismatch");await writeFile(path.join(out,f),b,{flag:"wx"});files.push(f)}if(segment===0)files.push("gold-light-v02.blend");
   zipRoot=out;
  }else{
   const dir=path.join(work,"segments");await mkdir(dir);for(const m of h.segments){const b=await take(m.bytes);if(sha(b)!==m.sha256)throw Error("Archive hash mismatch");await writeFile(path.join(dir,"segment-"+String(m.index).padStart(2,"0")+".zip"),b,{flag:"wx"})}await eof();
   await writeFile(path.join(dir,"manifest.json"),JSON.stringify(h.segments),{flag:"wx"});await mkdir(path.dirname(out),{recursive:true});
   run("python3",["engine/motion/gold_light_assemble.py"],90000);run("python3",["engine/motion/gold_light_post.py"],150000);
   const r=JSON.parse(await readFile(path.join(out,"clip-receipt.json"),"utf8"));if(!validClipReceipt(r))throw Error("Final clip receipt invalid");
   const video=await readFile(path.join(out,r.video.file));if(sha(video)!==r.video.sha256||video.length!==r.video.bytes)throw Error("Video digest mismatch");
   files=["clip-receipt.json","native-receipt.json","gold-light-v02.blend",r.video.file,...r.keyframes.map(x=>x.file)];zipRoot=out;
  }
  const archive=path.join(work,"output.zip");run("python3",["-c","import sys,zipfile,pathlib; out,root,*names=sys.argv[1:]; z=zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED); [z.write(pathlib.Path(root)/n,n) for n in names]; z.close()",archive,zipRoot,...files],30000);
  const s=await stat(archive);if(s.size<100||s.size>MAX_ARCHIVE_BYTES)throw Error("Output archive size limit");process.stdout.write(await readFile(archive));
 }finally{await rm(work,{recursive:true,force:true})}
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
