// Account-authenticated queue only. No paid operations, secret output, or public route.
export const GPU_PREFLIGHT_KEY="gpu/control/runpod-preflight.json";
export function gpuPreflightOperation(body){
 return !!body&&typeof body==="object"&&!Array.isArray(body)&&Object.keys(body).sort().join(",")==="operation"&&body.operation==="gpu-preflight";
}
export async function runGpuPreflight(env,request=fetch){
 const receipt={at:new Date().toISOString(),status:"failed",operation:"read-only-runpod-preflight"};
 const key=env.RUNPOD_API_KEY;
 if(typeof key!=="string"||!key.trim())return {...receipt,detail:"RUNPOD_API_KEY missing"};
 const get=async path=>{
  const r=await request("https://api.runpod.io/v2"+path,{method:"GET",headers:{Authorization:"Bearer "+key,Accept:"application/json"},redirect:"error",signal:AbortSignal.timeout(15000)});
  if(!r.ok)return {httpStatus:r.status};
  return {httpStatus:r.status,data:await r.json()};
 };
 try{
  const balance=await get("/billing/balance");
  if(balance.httpStatus!==200)return {...receipt,detail:"Balance read failed",httpStatus:balance.httpStatus};
  if(!Number.isFinite(balance.data?.balanceAmount)||!["PREPAID","POSTPAID"].includes(balance.data?.billingMode))return {...receipt,detail:"Unexpected balance response"};
  const pods=await get("/pods?includeClusterPods=true&limit=100");
  if(pods.httpStatus!==200)return {...receipt,detail:"Pods read failed",httpStatus:pods.httpStatus};
  if(!Array.isArray(pods.data?.pods)||typeof pods.data?.pagination?.hasNextPage!=="boolean")return {...receipt,detail:"Unexpected pod list"};
  return {...receipt,status:"pass",balanceUsd:balance.data.balanceAmount,billingMode:balance.data.billingMode,podsOnPage:pods.data.pods.length,additionalPodsPossible:pods.data.pagination.hasNextPage};
 }catch{return {...receipt,detail:"Runpod connection or response failed"}}
}
export async function publishGpuPreflight(env){
 const receipt=await runGpuPreflight(env);
 await env.MEDIA.put(GPU_PREFLIGHT_KEY,JSON.stringify(receipt),{httpMetadata:{contentType:"application/json"}});
 return receipt;
}
