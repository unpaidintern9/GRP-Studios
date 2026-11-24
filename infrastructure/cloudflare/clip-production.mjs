// Explicitly authorized, one-at-a-time, checkpointed production execution.
// The owner permit is required before each step, and no step retries automatically.
import {INPUTS,MAX_ARCHIVE_BYTES} from "../../plugins/blender/review-contract.mjs";
import {CLIP,SEGMENTS,STEP_MS,CLIP_PREFIX,CLIP_PERMIT,CLIP_STATUS,CLIP_ARCHIVE,segmentKey,clipOperation,validClipPermit} from "../../plugins/blender/clip-plan.mjs";
const KEY="clip-production-v1";
const now=()=>new Date().toISOString();
const digest=async b=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",b)),x=>x.toString(16).padStart(2,"0")).join("");
const to64=b=>{let s="";for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return btoa(s)};
async function bounded(stream,limit){if(!stream)throw Error("Missing output");const r=stream.getReader();let arr=[],n=0;try{while(true){const {done,value}=await r.read();if(done)break;n+=value.length;if(n>limit)throw Error("Output limit");arr.push(value)}const b=new Uint8Array(n);let p=0;for(const a of arr){b.set(a,p);p+=a.length}return b}finally{r.releaseLock()}}
async function publish(env,s){await env.MEDIA.put(CLIP_STATUS,JSON.stringify(s),{httpMetadata:{contentType:"application/json"}});return s}
async function stop(ctx){const c=ctx.container;if(!c)return false;try{await c.destroy();return !c.running}catch{return !c.running}}
async function permit(env,nonce){const o=await env.MEDIA.get(CLIP_PERMIT);const p=o?await o.json():null;if(!validClipPermit(p,nonce,Date.now()))throw Error("Missing or expired production permit");return p}
async function terminal(ctx,env,state,detail){const s=await ctx.storage.transaction(async tx=>{const v=await tx.get(KEY);if(!v||v.state!=="running")return v;const next={...v,state,detail,finishedAt:now(),activeStep:null};await tx.put(KEY,next);return next});return s?publish(env,s):null}
async function assets(env){const result=[];for(const s of INPUTS){const o=await env.MEDIA.get(s.key);if(!o||o.size!==s.bytes)throw Error("Original missing");const b=new Uint8Array(await o.arrayBuffer());if(await digest(b)!==s.sha256)throw Error("Original checksum mismatch");result.push({name:s.name,base64:to64(b)})}return result}
function inputStream(header,env,parts){
 const b=new TextEncoder().encode(JSON.stringify(header));const len=new Uint8Array(4);new DataView(len.buffer).setUint32(0,b.length);
 const iterator=(async function*(){yield len;yield b;for(const p of parts){const o=await env.MEDIA.get(segmentKey(p.index));if(!o||o.size!==p.bytes)throw Error("Missing private segment");const r=o.body.getReader();try{while(true){const x=await r.read();if(x.done)break;yield x.value}}finally{r.releaseLock()}}})();
 return new ReadableStream({async pull(c){try{const x=await iterator.next();if(x.done)c.close();else c.enqueue(x.value)}catch(e){c.error(e)}},async cancel(){await iterator.return()}});
}
export async function clipAlarm(ctx,env){
 const s=await ctx.storage.get(KEY);if(!s||(s.activeStep===null&&!s.stopPending))return false;
 if(s.state==="running")await terminal(ctx,env,"failed","Production step deadline reached");
 const stopped=await stop(ctx);
 await ctx.storage.transaction(async tx=>{const v=await tx.get(KEY);if(v)await tx.put(KEY,{...v,stopPending:!stopped})});
 if(!stopped)await ctx.storage.setAlarm(Date.now()+15000);
 return true;
}
export async function operateClip(ctx,env,body){
 const op=clipOperation(body);if(!op)throw Error("Invalid clip operation");
 if(op==="clip-cancel"){const s=await ctx.storage.get(KEY);if(!s||s.nonceHash!==await digest(new TextEncoder().encode(body.nonce)))throw Error("Wrong production cancellation permit");const result=await terminal(ctx,env,"cancelled","Owner cancelled");if(await stop(ctx))await ctx.storage.deleteAlarm();return result}
 if(env.STUDIO_QUEUE_RENDER_ENABLED!=="true")throw Error("Production disabled");
 const p=await permit(env,body.nonce);
 const nonceHash=await digest(new TextEncoder().encode(body.nonce));
 if(op==="clip-start"){
  const review=await ctx.storage.get("review-v3");if(review?.state!=="succeeded")throw Error("Native quality review has not succeeded");
  const s=await ctx.storage.transaction(async tx=>{if(await tx.get(KEY))return null;const v={template:CLIP,state:"running",nonceHash,createdAt:now(),expiresAt:p.expiresAt,maxComputeMs:p.maxComputeMs,spentMs:0,next:0,activeStep:null,segments:[],completedNativeFrames:0};await tx.put(KEY,v);return v});
  if(!s)return await ctx.storage.get(KEY);await publish(env,s);await env.RENDER_QUEUE.send({operation:"clip-step",template:CLIP,nonce:body.nonce,segment:0});return s;
 }
 const step=body.segment,started=Date.now();
 const s=await ctx.storage.transaction(async tx=>{const v=await tx.get(KEY);if(v?.state!=="running"||v.nonceHash!==nonceHash||v.next!==step||v.activeStep!==null||p.maxComputeMs!==v.maxComputeMs||p.expiresAt!==v.expiresAt)return null;if(v.spentMs+STEP_MS>v.maxComputeMs||Date.now()+STEP_MS>v.expiresAt){const exhausted={...v,state:"budget-exhausted",finishedAt:now(),detail:"Insufficient authorized remaining step budget"};await tx.put(KEY,exhausted);return exhausted}const next={...v,activeStep:step,stepDeadline:Date.now()+STEP_MS};await tx.put(KEY,next);return next});
 if(!s)return await ctx.storage.get(KEY);await publish(env,s);if(s.state!=="running")return s;
 let output=null,failure=null,stopped=false;
 const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),STEP_MS-1000);
 try{
  await ctx.storage.setAlarm(started+STEP_MS);
  const original=await assets(env),c=ctx.container;if(!c?.images?.clip||c.running||abort.signal.aborted)throw Error("Unsafe clip container state");
  const assembly=step===SEGMENTS;
  const parts=assembly?s.segments:[];
  if(assembly&&(parts.length!==SEGMENTS||parts.some((x,i)=>x.index!==i)))throw Error("Incomplete assembly manifest");
  const h=assembly?{template:CLIP,mode:"assemble",assets:original,segments:parts}:{template:CLIP,mode:"segment",assets:original,segment:step};
  c.start({image:c.images.clip,instance:"standard-4",enableInternet:false,entrypoint:["/usr/bin/timeout","--signal=KILL","600s","/bin/sleep","infinity"]});
  await c.setInactivityTimeout(STEP_MS);
  const process=await c.exec(["/usr/local/bin/node","/opt/studio/plugins/blender/clip-batch-runner.mjs"],{stdin:inputStream(h,env,parts),stdout:"pipe",stderr:"pipe",cwd:"/opt/studio",user:"10001:10001",signal:abort.signal});
  const [bytes,err,exit]=await Promise.all([bounded(process.stdout,MAX_ARCHIVE_BYTES),bounded(process.stderr,64000),process.exitCode]);
  if(exit!==0||bytes.length<100||bytes[0]!==80||bytes[1]!==75||bytes[2]!==3||bytes[3]!==4)throw Error("Native batch failed: "+new TextDecoder().decode(err).slice(-600));
  if(abort.signal.aborted||(await ctx.storage.get(KEY))?.state!=="running")throw Error("Production no longer active");
  const key=assembly?CLIP_ARCHIVE:segmentKey(step),hash=await digest(bytes);
  const stored=await env.MEDIA.put(key,bytes,{onlyIf:{etagDoesNotMatch:"*"},httpMetadata:{contentType:"application/zip"},customMetadata:{sha256:hash,template:CLIP,stage:String(step)}});
  if(!stored)throw Error("Existing archive not overwritten");const readback=await env.MEDIA.get(key);if(!readback||readback.size!==bytes.length||await digest(await readback.arrayBuffer())!==hash)throw Error("Private batch readback mismatch");
  output={index:step,sha256:hash,bytes:bytes.length};
 }catch(e){failure=String(e).slice(0,700);console.error("Clip step failed",step,failure)}
 finally{clearTimeout(timer);stopped=await stop(ctx);if(stopped)await ctx.storage.deleteAlarm()}
 if(!output||!stopped){if(!stopped){await ctx.storage.transaction(async tx=>{const v=await tx.get(KEY);if(v)await tx.put(KEY,{...v,stopPending:true})});await ctx.storage.setAlarm(Date.now()+15000)}return terminal(ctx,env,"failed",stopped?(failure??"Missing output"):"Container shutdown unverified; safety alarm retained");}
 const next=await ctx.storage.transaction(async tx=>{const v=await tx.get(KEY);if(v?.state!=="running"||v.activeStep!==step)return v;const x={...v,spentMs:v.spentMs+Math.max(0,Date.now()-started),activeStep:null,next:step+1};if(step<SEGMENTS){x.segments=[...v.segments,output];x.completedNativeFrames=x.segments.length*7}else{Object.assign(x,{state:"succeeded",finishedAt:now(),artifactKey:CLIP_ARCHIVE,sha256:output.sha256,bytes:output.bytes,creativeStatus:"unapproved-five-second-clip"})}await tx.put(KEY,x);return x});
 await publish(env,next);
 if(next.state==="running"){try{await permit(env,body.nonce);await env.RENDER_QUEUE.send({operation:"clip-step",template:CLIP,nonce:body.nonce,segment:next.next})}catch(e){return terminal(ctx,env,"failed","Next step not submitted: "+String(e).slice(0,250))}}
 return next;
}
