// Separate deployment candidate, machine-token operator only. No website,
// public media route, or OAuth claim. All render tools disabled by default.
import { createMcpHandler } from "agents/mcp/server";
import { z } from "zod";
import { createServer } from "../../mcp/server.mjs";
import { previewGuard } from "./preview-auth.mjs";
export { GoldLightRenderer } from "./review-do.mjs";
export { OnDemandGoldLightRenderer } from "./on-demand-review-do.mjs";
import { gpuPreflightOperation,publishGpuPreflight } from "./gpu-preflight.mjs";
import { clipOperation } from "../../plugins/blender/clip-plan.mjs";
import { operation, QUEUE, V03_TEMPLATE, V04_TEMPLATE } from "./queue-review-contract.mjs";

export default {
 async queue(batch,env){
  if(batch.queue!==QUEUE)throw Error("Unexpected queue");
  for(const m of batch.messages){
   if(gpuPreflightOperation(m.body)){await publishGpuPreflight(env);m.ack();continue}
   if(!operation(m.body)&&!clipOperation(m.body)){m.ack();continue}
   await env.ON_DEMAND_RENDERER.getByName(m.body.template===V04_TEMPLATE?"gold-light-v04-lookdev-v2-singleton":m.body.template===V03_TEMPLATE?"gold-light-v03-motion-singleton":"gold-light-v02-singleton").operate(m.body);
   m.ack();
  }
 },
 async fetch(request,env,ctx){
  const denied=await previewGuard(request,env);if(denied)return denied;
  const handler=createMcpHandler(()=>{
   const server=createServer({mode:"remote"});
   const stub=()=>env.ON_DEMAND_RENDERER.getByName("gold-light-v02-singleton");
   const register=(name,description,readOnly,fn)=>server.registerTool(name,{description,inputSchema:z.object({}).strict(),annotations:{readOnlyHint:readOnly,destructiveHint:false,openWorldHint:false}},async()=>{
    try{return {content:[{type:"text",text:JSON.stringify(await fn())}]}}
    catch(e){return {isError:true,content:[{type:"text",text:"Private review operation unavailable"}]}}
   });
   register("gold_light_review_status","Read one private Gold Light review job's actual state. Does not start compute.",true,()=>stub().status());
   register("gold_light_v03_motion_status","Read private V03 native motion review status; no compute.",true,async()=>{const o=await env.MEDIA.get("reviews/gold-light-v03-motion-v1/status.json");return o?o.json():{state:"not-started",template:V03_TEMPLATE}});
   register("gold_light_v04_lookdev_status","Read private V04 native HD lookdev status; no compute.",true,async()=>{const o=await env.MEDIA.get("reviews/gold-light-v04-lookdev-v2/status.json");return o?o.json():{state:"not-started",template:V04_TEMPLATE}});
   return server;
  });
  const response=await handler(request,env,ctx);const headers=new Headers(response.headers);headers.set("Cache-Control","no-store");
  return new Response(response.body,{status:response.status,statusText:response.statusText,headers});
 }
};
