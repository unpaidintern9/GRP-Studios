// Separate deployment candidate, machine-token operator only. No website,
// public media route, or OAuth claim. All render tools disabled by default.
import { createMcpHandler } from "agents/mcp/server";
import { z } from "zod";
import { createServer } from "../../mcp/server.mjs";
import { previewGuard } from "./preview-auth.mjs";
export { GoldLightRenderer } from "./review-do.mjs";

export default {
 async fetch(request,env,ctx){
  const denied=await previewGuard(request,env);if(denied)return denied;
  const handler=createMcpHandler(()=>{
   const server=createServer({mode:"remote"});
   const stub=()=>env.REVIEW_RENDERER.getByName("gold-light-v02-singleton");
   const register=(name,description,readOnly,fn)=>server.registerTool(name,{description,inputSchema:z.object({}).strict(),annotations:{readOnlyHint:readOnly,destructiveHint:false,openWorldHint:false}},async()=>{
    try{return {content:[{type:"text",text:JSON.stringify(await fn())}]}}
    catch(e){return {isError:true,content:[{type:"text",text:"Private review operation unavailable"}]}}
   });
   register("gold_light_review_status","Read one private Gold Light review job's actual state. Does not start compute.",true,()=>stub().status());
   if(env.STUDIO_RENDER_ENABLED==="true"){
    register("start_gold_light_review","Start one explicitly authorized four-frame private Blender review. Uses billable CPU container time. No retries.",false,()=>stub().startReview());
    register("cancel_gold_light_review","Cancel the one private review and stop its container.",false,()=>stub().cancelReview());
   }
   return server;
  });
  const response=await handler(request,env,ctx);const headers=new Headers(response.headers);headers.set("Cache-Control","no-store");
  return new Response(response.body,{status:response.status,statusText:response.statusText,headers});
 }
};
