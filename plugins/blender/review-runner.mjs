// Runs only inside the dedicated isolated container. Reads one bounded JSON
// envelope from stdin, produces one bounded private ZIP on stdout. No network,
// shell strings, arbitrary file paths, or caller-provided executable arguments.
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile, stat, rm } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { INPUTS, MAX_REQUEST_BYTES, MAX_ARCHIVE_BYTES, CLIP_TEMPLATE, validReceipt, validClipReceipt, validateEnvelope } from "./review-contract.mjs";

const root=fileURLToPath(new URL("../../",import.meta.url));
const sha=b=>createHash("sha256").update(b).digest("hex");
const blob=b=>createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");
const work=path.join(root,"private");

const archive=path.join(work,"lookdev.zip");
function run(cmd,args,timeout){
 const p=spawnSync(cmd,args,{cwd:root,timeout,killSignal:"SIGKILL",stdio:["ignore","pipe","pipe"],maxBuffer:4000000,env:{PATH:"/usr/local/bin:/usr/bin:/bin",HOME:"/tmp",BLENDER_BIN:"/opt/blender/blender"}});
 if(p.error||p.status!==0){console.error("Stage failed:",cmd,p.error?.message??p.status);console.error(p.stderr?.toString().slice(-2000));throw Error("Render stage failed")}
}
async function main(){
 let parts=[],size=0;
 for await(const chunk of process.stdin){size+=chunk.length;if(size>MAX_REQUEST_BYTES)throw Error("Input too large");parts.push(chunk)}
 const input=validateEnvelope(JSON.parse(Buffer.concat(parts).toString("utf8")));
 const clip=input.template===CLIP_TEMPLATE;
 const render=path.join(work,"gold-light-v02",clip?"clip":"lookdev");
 // Verify all assets before any render or filesystem mutation.
 const source=input.assets.map((a,i)=>{
  const b=Buffer.from(a.base64,"base64"),e=INPUTS[i];
  if(b.length!==e.bytes||b.toString("base64")!==a.base64||sha(b)!==e.sha256||blob(b)!==e.blob)throw Error("Exact asset verification failed");
  return b;
 });
 await mkdir(work,{recursive:false});
 try {
  await mkdir(path.join(work,"brand"));
  for(let i=0;i<INPUTS.length;i++)await writeFile(path.join(work,"brand",INPUTS[i].name),source[i],{flag:"wx"});
  run(process.execPath,["engine/brand/prepare_gold_light.mjs"],30000);
  if(clip){
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_clip.py"],440000);
   run("python3",["engine/motion/gold_light_post.py"],90000);
  }else{
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_v02.py","--","--review"],450000);
  }
  const receiptName=clip?"clip-receipt.json":"lookdev-receipt.json";
  const receipt=JSON.parse(await readFile(path.join(render,receiptName),"utf8"));
  if(!(clip?validClipReceipt(receipt):validReceipt(receipt)))throw Error("Unexpected Blender receipt");
  if(clip){const b=await readFile(path.join(render,receipt.video.file));if(b.length!==receipt.video.bytes||sha(b)!==receipt.video.sha256)throw Error("Video hash mismatch");}
  for(const x of receipt.keyframes){
   const b=await readFile(path.join(render,x.file));
   if(b.length<24||!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))||b.readUInt32BE(16)!==1920||b.readUInt32BE(20)!==1080||sha(b)!==x.sha256)throw Error("Invalid keyframe");
  }
  const names=[receiptName,clip?"gold-light-v02.blend":"gold-light-v02-lookdev.blend",...receipt.keyframes.map(x=>x.file),...(clip?[receipt.video.file,"native-receipt.json"]:[])];
  // Private ZIP contains only the fixed output allowlist. No source PNGs,
  // credentials, logs, or arbitrary directory contents.
  run("python3",["-c","import sys,zipfile,pathlib; out,root,*names=sys.argv[1:]; z=zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED); [z.write(pathlib.Path(root)/n,n) for n in names]; z.close()",archive,render,...names],30000);
  const st=await stat(archive);if(st.size<100||st.size>MAX_ARCHIVE_BYTES)throw Error("Archive size outside limit");
  const bytes=await readFile(archive);
  process.stdout.write(bytes);
 }finally{await rm(work,{recursive:true,force:true})}
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
