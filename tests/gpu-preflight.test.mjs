import test from "node:test";
import assert from "node:assert/strict";
import {gpuPreflightOperation,runGpuPreflight} from "../infrastructure/cloudflare/gpu-preflight.mjs";
test("fixed operation only",()=>{
 assert.equal(gpuPreflightOperation({operation:"gpu-preflight"}),true);
 assert.equal(gpuPreflightOperation({operation:"gpu-preflight",url:"https://example.com"}),false);
});
test("missing key fails before network",async()=>{
 assert.equal((await runGpuPreflight({},()=>{throw Error("unexpected")})).status,"failed");
});
test("read only, fixed origin, no secret or pod details in receipt",async()=>{
 let calls=0;const receipt=await runGpuPreflight({RUNPOD_API_KEY:"test-token"},async(url,opts)=>{
  calls++;assert.equal(opts.method,"GET");assert.equal(opts.redirect,"error");assert.equal(opts.headers.Authorization,"Bearer test-token");assert.ok(url.startsWith("https://api.runpod.io/v2/"));
  return Response.json(calls===1?{balanceAmount:10,billingMode:"PREPAID"}:{pods:[{id:"private-pod",env:{SECRET:"test-token"}}],pagination:{hasNextPage:false}});
 });assert.equal(calls,2);assert.equal(receipt.status,"pass");assert.equal(receipt.balanceUsd,10);assert.equal(receipt.podsOnPage,1);assert.ok(!JSON.stringify(receipt).includes("test-token"));assert.ok(!JSON.stringify(receipt).includes("private-pod"));
});
test("permission error fails closed without response body",async()=>{
 const receipt=await runGpuPreflight({RUNPOD_API_KEY:"test-token"},async()=>new Response("test-token",{status:403}));
 assert.equal(receipt.status,"failed");assert.equal(receipt.httpStatus,403);assert.ok(!JSON.stringify(receipt).includes("test-token"));
});
