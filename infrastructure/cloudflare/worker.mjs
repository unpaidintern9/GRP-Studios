// Read-only machine-authenticated preview. Not the final team OAuth endpoint.
import { createMcpHandler } from "agents/mcp/server";
import { createServer } from "../../mcp/server.mjs";

const handler=createMcpHandler(()=>createServer({mode:"remote"}));
async function authorized(request,env) {
  const expected=env.STUDIO_PREVIEW_TOKEN;
  if(typeof expected!=="string"||expected.length<32)return false;
  const h=request.headers.get("Authorization")||"";
  if(!h.startsWith("Bearer ")||h.length>1024)return false;
  const digest=async s=>new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s)));
  const [a,b]=await Promise.all([digest(h.slice(7)),digest(expected)]);
  let diff=0;for(let i=0;i<a.length;i++)diff|=a[i]^b[i];
  return diff===0;
}
export default {
  async fetch(request,env,ctx) {
    if(new URL(request.url).pathname!=="/mcp")return new Response("Not found",{status:404});
    // Machine-only. Reject browser-origin requests in this preview.
    if(request.headers.has("Origin")||!(await authorized(request,env)))return new Response("Unauthorized",{status:401,headers:{"Cache-Control":"no-store","WWW-Authenticate":"Bearer"}});
    return handler(request,env,ctx);
  }
};
