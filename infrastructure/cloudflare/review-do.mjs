import { DurableObject } from "cloudflare:workers";
import { INPUTS,TEMPLATE,JOB_KEY,OUTPUT_KEY,JOB_TIMEOUT_MS,MAX_ARCHIVE_BYTES,canStart } from "../../plugins/blender/review-contract.mjs";

const now=()=>new Date().toISOString();
const sha=async b=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",b)),x=>x.toString(16).padStart(2,"0")).join("");
const to64=b=>{let s="";for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return btoa(s)};
const terminal=s=>["succeeded","failed","cancelled"].includes(s);
const get=ctx=>ctx.storage.get("review");
const finish=async(ctx,next)=>ctx.storage.transaction(async tx=>{
 const current=await tx.get("review");
 if(current?.state!=="running")return false;
 await tx.put("review",{...current,...next,finishedAt:now()});return true;
});
export class GoldLightRenderer extends DurableObject {
 async status(){return (await get(this.ctx))??{id:JOB_KEY,template:TEMPLATE,state:"not-started"}}
 async startReview(){
  // Deliberately single-use; a new render requires a new reviewed template
  // version. No automatic retries, no queue consumers.
  if(this.env.STUDIO_RENDER_ENABLED!=="true")throw Error("Rendering disabled");
  const claimed=await this.ctx.storage.transaction(async tx=>{
   const state=await tx.get("review");
   if(!canStart(state))return false;
   await tx.put("review",{id:JOB_KEY,template:TEMPLATE,state:"running",createdAt:now(),deadline:Date.now()+JOB_TIMEOUT_MS});return true;
  });
  if(!claimed)return this.status();
  try{await this.ctx.storage.setAlarm(Date.now()+JOB_TIMEOUT_MS)}
  catch(e){await finish(this.ctx,{state:"failed",detail:"Could not establish shutdown alarm"});throw e}
  this.ctx.waitUntil(this.runReview());
  return this.status();
 }
 async cancelReview(){
  await this.ctx.storage.transaction(async tx=>{
   const state=await tx.get("review");
   if(state?.state==="running")await tx.put("review",{...state,state:"cancelled",finishedAt:now(),detail:"Cancelled by operator"});
  });
  if(this.ctx.container?.running)await this.ctx.container.destroy();
  return this.status();
 }
 async alarm(){
  const state=await get(this.ctx);
  if(state?.state==="running")await finish(this.ctx,{state:"failed",detail:"Hard review deadline expired"});
  if(this.ctx.container?.running)await this.ctx.container.destroy();
 }
 async runReview(){
  const c=this.ctx.container;
  const abort=new AbortController();
  const timer=setTimeout(()=>abort.abort(),JOB_TIMEOUT_MS-1000);
  let output=null, failure=null;
  try{
   const assets=[];
   for(const spec of INPUTS){
    const obj=await this.env.MEDIA.get(spec.key);
    if(!obj||obj.size!==spec.bytes)throw Error("Private original missing or wrong size");
    const b=new Uint8Array(await obj.arrayBuffer());
    if(await sha(b)!==spec.sha256)throw Error("Private original hash mismatch");
    assets.push({name:spec.name,base64:to64(b)});
   }
   if(abort.signal.aborted||(await get(this.ctx))?.state!=="running")throw Error("Review no longer active");
   if(c.running)throw Error("Unexpected active container");
   c.start({enableInternet:false});
   await c.setInactivityTimeout(60000);
   const input=new Response(JSON.stringify({template:TEMPLATE,assets})).body;
   const process=await c.exec(["/usr/local/bin/node","/opt/studio/plugins/blender/review-runner.mjs"],{
    stdin:input,stdout:"pipe",stderr:"pipe",cwd:"/opt/studio",user:"10001:10001",signal:abort.signal
   });
   // Read bounded stdout and stderr concurrently; never buffer unbounded
   // process output or expose private logs.
   async function bounded(stream,limit){const r=stream.getReader();let chunks=[],size=0;try{while(true){const {done,value}=await r.read();if(done)break;size+=value.length;if(size>limit)throw Error("Output exceeds limit");chunks.push(value)}const all=new Uint8Array(size);let p=0;for(const b of chunks){all.set(b,p);p+=b.length}return all}finally{r.releaseLock()}}
   const [archive,stderr,exit]=await Promise.all([bounded(process.stdout,MAX_ARCHIVE_BYTES),bounded(process.stderr,64000),process.exitCode]);
   if(exit!==0||archive.length<100||archive[0]!==80||archive[1]!==75||archive[2]!==3||archive[3]!==4)throw Error("Review process did not return an accepted ZIP");
   if(abort.signal.aborted||(await get(this.ctx))?.state!=="running")throw Error("Review no longer active");
   const digest=await sha(archive);
   const stored=await this.env.MEDIA.put(OUTPUT_KEY,archive,{onlyIf:{etagDoesNotMatch:"*"},httpMetadata:{contentType:"application/zip"},customMetadata:{sha256:digest,template:TEMPLATE,review:"unapproved"}});
   if(!stored)throw Error("Review object already exists; no overwrite");
   const readback=await this.env.MEDIA.get(OUTPUT_KEY);
   if(!readback||readback.size!==archive.length||await sha(await readback.arrayBuffer())!==digest)throw Error("Private output readback mismatch");
   output={state:"succeeded",artifactKey:OUTPUT_KEY,sha256:digest,bytes:archive.length,creativeStatus:"unapproved-lookdev"};
  }catch(e){failure="Private render failed; inspect dedicated container logs and state";console.error("Review error:",String(e).slice(0,300))}
  finally{
   clearTimeout(timer);
   // Success is recorded only after explicit container teardown. If destroy
   // fails, leave the safety alarm armed and report failure.
   let stopped=false;
   try{if(c?.running)await c.destroy();stopped=!c?.running}catch(e){console.error("Container stop failed")}
   if(stopped){await this.ctx.storage.deleteAlarm();await finish(this.ctx,output??{state:"failed",detail:failure??"No output"})}
   else{await finish(this.ctx,{state:"failed",detail:"Container shutdown unverified; safety alarm retained"})}
  }
 }
}
