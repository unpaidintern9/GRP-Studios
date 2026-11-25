// Runs only inside the dedicated isolated container. Reads one bounded JSON
// envelope from stdin, produces one bounded private ZIP on stdout. No network,
// shell strings, arbitrary file paths, or caller-provided executable arguments.
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile, stat, rm } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { INPUTS, MAX_REQUEST_BYTES, MAX_ARCHIVE_BYTES, CLIP_TEMPLATE, V03_TEMPLATE, V04_TEMPLATE, V05_TEMPLATE, validV05Receipt, validV04Receipt, validV03Receipt, validReceipt, validClipReceipt, validateEnvelope } from "./review-contract.mjs";

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
 const clip=input.template===CLIP_TEMPLATE,v03=input.template===V03_TEMPLATE,v04=input.template===V04_TEMPLATE,v05=input.template===V05_TEMPLATE;
 const render=path.join(work,v05?"gold-light-v05":v04?"gold-light-v04":v03?"gold-light-v03":"gold-light-v02",clip?"clip":"lookdev");
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
  if(v05){
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_v05.py"],475000);
   run("python3",["engine/motion/gold_light_v05_post.py"],65000);
  }else if(v04){
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_v04.py"],500000);
  }else if(v03){
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_v03.py"],430000);
   run("python3",["engine/motion/gold_light_v03_post.py"],65000);
  }else if(clip){
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_clip.py"],440000);
   run("python3",["engine/motion/gold_light_post.py"],90000);
  }else{
   run("/opt/blender/blender",["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--threads","4","--python","engine/motion/gold_light_v02.py","--","--review"],450000);
  }
  const receiptName=v05?"v05-receipt.json":v04?"v04-receipt.json":v03?"motion-receipt.json":clip?"clip-receipt.json":"lookdev-receipt.json";
  const receipt=JSON.parse(await readFile(path.join(render,receiptName),"utf8"));
  if(!(v05?validV05Receipt(receipt):v04?validV04Receipt(receipt):v03?validV03Receipt(receipt):clip?validClipReceipt(receipt):validReceipt(receipt)))throw Error("Unexpected Blender receipt");
  if(clip||v03||v05){const b=await readFile(path.join(render,receipt.video.file));if(b.length!==receipt.video.bytes||sha(b)!==receipt.video.sha256)throw Error("Video hash mismatch");}
  for(const x of receipt.keyframes??[]){
   const b=await readFile(path.join(render,x.file));
   if(b.length<24||!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))||b.readUInt32BE(16)!==1920||b.readUInt32BE(20)!==1080||sha(b)!==x.sha256)throw Error("Invalid keyframe");
  }
  if(v04){run("python3",["-c","from PIL import Image,ImageDraw; import sys,pathlib; p=pathlib.Path(sys.argv[1]); frames=(1,11,20,39,78); c=Image.new('RGB',(960,870),(8,12,19)); d=ImageDraw.Draw(c); [(c.paste(Image.open(p/f'frame-{f:03d}.png').convert('RGB').resize((480,270),Image.Resampling.LANCZOS),((i%2)*480,(i//2)*290)),d.text(((i%2)*480+8,(i//2)*290+272),f'Native frame {f} / {(f-1)/24:.2f}s',fill=(220,220,220))) for i,f in enumerate(frames)]; c.save(p/'lookdev-contact.jpg',quality=88)",render],30000);}
  const names=v05?[receiptName,"gold-light-v05.blend",receipt.video.file]:v04?[receiptName,"gold-light-v04.blend",...receipt.keyframes.map(x=>x.file),"lookdev-contact.jpg"]:v03?[receiptName,"gold-light-v03.blend",receipt.video.file]:[receiptName,clip?"gold-light-v02.blend":"gold-light-v02-lookdev.blend",...receipt.keyframes.map(x=>x.file),...(clip?[receipt.video.file,"native-receipt.json"]:[])];
  // Private ZIP contains only the fixed output allowlist. No source PNGs,
  // credentials, logs, or arbitrary directory contents.
  run("python3",["-c","import sys,zipfile,pathlib; out,root,*names=sys.argv[1:]; z=zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED); [z.write(pathlib.Path(root)/n,n,compress_type=zipfile.ZIP_STORED if n=='lookdev-contact.jpg' else zipfile.ZIP_DEFLATED) for n in names]; z.close()",archive,render,...names],30000);
  const st=await stat(archive);if(st.size<100||st.size>MAX_ARCHIVE_BYTES)throw Error("Archive size outside limit");
  const bytes=await readFile(archive);
  process.stdout.write(bytes);
 }finally{await rm(work,{recursive:true,force:true})}
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
