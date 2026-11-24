import { DurableObject } from "cloudflare:workers";
import { INPUTS,TEMPLATE,JOB_KEY,OUTPUT_KEY,JOB_TIMEOUT_MS,MAX_ARCHIVE_BYTES } from "../../plugins/blender/review-contract.mjs";
import { operation,permitValid,PREFLIGHT_KEY,STATUS_KEY,PERMIT_KEY } from "./queue-review-contract.mjs";
const now=()=>new Date().toISOString();
const sha=async b=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",b)),x=>x.toString(16).padStart(2,"0")).join("");
const to64=b=>{let s="";for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return btoa(s)};
async function bounded(stream,limit){if(!stream)throw Error("Missing output stream");const r=stream.getReader();let chunks=[],size=0;try{while(true){const {done,value}=await r.read();if(done)break;size+=value.length;if(size>limit)throw Error("Output exceeds limit");chunks.push(value)}const all=new Uint8Array(size);let p=0;for(const b of chunks){all.set(b,p);p+=b.length}return all}finally{r.releaseLock()}}
export class OnDemandGoldLightRenderer extends DurableObject {
 async #assets(){const assets=[];for(const s of INPUTS){const o=await this.env.MEDIA.get(s.key);if(!o||o.size!==s.bytes)throw Error("Source size mismatch");const b=new Uint8Array(await o.arrayBuffer());if(await sha(b)!==s.sha256)throw Error("Source digest mismatch");assets.push({name:s.name,base64:to64(b)})}return assets}
 async #receipt(key,body){await this.env.MEDIA.put(key,JSON.stringify(body),{httpMetadata:{contentType:"application/json"}})}
 async #state(){return await this.ctx.storage.get("review-v3")}
 async status(){return (await this.#state())??{state:"not-started",template:TEMPLATE}}
 async #finish(next){const result=await this.ctx.storage.transaction(async tx=>{const s=await tx.get("review-v3");if(s?.state!=="running")return s;const v={...s,...next,finishedAt:now()};await tx.put("review-v3",v);return v});if(result)await this.#receipt(STATUS_KEY,result);return result}
 async #stop(){const c=this.ctx.container;if(!c)return false;try{await c.destroy();return !c.running}catch(e){return !c.running}}
 async alarm(){await this.#finish({state:"failed",detail:"Deadline reached"});if(!await this.#stop())await this.ctx.storage.setAlarm(Date.now()+15000)}
 async operate(body){
  const op=operation(body);if(!op)throw Error("Invalid fixed operation");
  if(op==="preflight"){const c=this.ctx.container;if(!c?.images?.base||c.running)throw Error("On-demand container not idle/configured");await this.#assets();const receipt={status:"pass",template:TEMPLATE,image:c.images.base,sourceCount:INPUTS.length,running:false,renderEnabled:this.env.STUDIO_QUEUE_RENDER_ENABLED==="true",at:now()};await this.#receipt(PREFLIGHT_KEY,receipt);return receipt}
  if(op==="cancel"){const s=await this.#state();if(s?.state!=="running")return this.status();await this.#finish({state:"cancelled",detail:"Operator cancellation"});if(await this.#stop())await this.ctx.storage.deleteAlarm();return this.status()}
  if(this.env.STUDIO_QUEUE_RENDER_ENABLED!=="true")throw Error("Queue render disabled");
  const permit=await this.env.MEDIA.get(PERMIT_KEY);if(!permit||!permitValid(await permit.json(),body.nonce,Date.now()))throw Error("Missing or expired private permit");
  const claimed=await this.ctx.storage.transaction(async tx=>{if(await tx.get("review-v3"))return false;await tx.put("review-v3",{id:JOB_KEY,template:TEMPLATE,state:"running",createdAt:now(),deadline:Date.now()+JOB_TIMEOUT_MS});return true});if(!claimed)return this.status();
  try{await this.ctx.storage.setAlarm(Date.now()+JOB_TIMEOUT_MS);await this.#receipt(STATUS_KEY,await this.#state())}catch(e){await this.#finish({state:"failed",detail:"Safety setup failed"});throw e}
  // Await from the queue invocation rather than relying on waitUntil to keep a long render alive.
  const abort=new AbortController();const timer=setTimeout(()=>abort.abort(),JOB_TIMEOUT_MS-1000);let next={state:"failed",detail:"Render did not complete"};
  try{
   const assets=await this.#assets();const c=this.ctx.container;
   if(!c)throw Error("Container binding missing");
   if(!c.images?.base)throw Error("Container base image missing from Worker version");
   if(c.running)throw Error("Container already running");
   if((await this.#state())?.state!=="running")throw Error("Review claim no longer running");
   if(abort.signal.aborted)throw Error("Review deadline expired before start");
   // Independent in-container lifetime limit even if the Worker is interrupted.
   c.start({image:c.images.base,instance:"standard-4",enableInternet:false,entrypoint:["/usr/bin/timeout","--signal=KILL","600s","/bin/sleep","infinity"]});
   await c.setInactivityTimeout(JOB_TIMEOUT_MS);
   const proc=await c.exec(["/usr/local/bin/node","/opt/studio/plugins/blender/review-runner.mjs"],{stdin:new Response(JSON.stringify({template:TEMPLATE,assets})).body,stdout:"pipe",stderr:"pipe",cwd:"/opt/studio",user:"10001:10001",signal:abort.signal});
   const [archive,stderr,exit]=await Promise.all([bounded(proc.stdout,MAX_ARCHIVE_BYTES),bounded(proc.stderr,64000),proc.exitCode]);
   if(exit!==0||archive.length<100||archive[0]!==80||archive[1]!==75||archive[2]!==3||archive[3]!==4)throw Error("Render process failed: "+new TextDecoder().decode(stderr).slice(-500));
   if(abort.signal.aborted||(await this.#state())?.state!=="running")throw Error("Review no longer active");
   const digest=await sha(archive);const stored=await this.env.MEDIA.put(OUTPUT_KEY,archive,{onlyIf:{etagDoesNotMatch:"*"},httpMetadata:{contentType:"application/zip"},customMetadata:{sha256:digest,template:TEMPLATE,review:"unapproved"}});if(!stored)throw Error("Existing artifact not overwritten");
   const readback=await this.env.MEDIA.get(OUTPUT_KEY);if(!readback||readback.size!==archive.length||await sha(await readback.arrayBuffer())!==digest)throw Error("Output checksum mismatch");
   next={state:"succeeded",artifactKey:OUTPUT_KEY,sha256:digest,bytes:archive.length,creativeStatus:"unapproved-lookdev"};
  }catch(e){console.error("Private review failure",String(e).slice(0,600));next={state:"failed",detail:String(e).slice(0,600)}}
  finally{clearTimeout(timer);const stopped=await this.#stop();if(stopped)await this.ctx.storage.deleteAlarm();else next={state:"failed",detail:"Container shutdown not verified; alarm retained"};await this.#finish(next)}
  return this.status();
 }
}
