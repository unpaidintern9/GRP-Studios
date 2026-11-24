import test from "node:test";
import assert from "node:assert/strict";
import {planGpu} from "../plugins/blender/gpu-plan.mjs";
import {validSegmentReceipt} from "../plugins/blender/clip-plan.mjs";
const q={id:"NVIDIA GeForce RTX 5090",cloud:"SECURE",availability:"LOW",count:1,hourlyUsd:1.39};
const base={tier:"pro",budgetCents:100,maxSeconds:600,quotes:[q]};
test("secure one GPU within explicit ceiling",()=>assert.equal(planGpu(base).ceilingCents,44));
test("refuse missing inventory, over-budget and unapproved community",()=>{
 assert.equal(planGpu({...base,quotes:[{...q,availability:"NONE"}]}),null);
 assert.equal(planGpu({...base,budgetCents:30}),null);
 assert.equal(planGpu({...base,quotes:[{...q,cloud:"COMMUNITY"}]}),null);
});
test("ultra prefers available multi-GPU quote, falls back to single",()=>{
 const a={...base,tier:"ultra",budgetCents:200,quotes:[q,{...q,count:4}]};
 assert.equal(planGpu(a).count,4);assert.equal(planGpu({...a,budgetCents:60}).count,1);
});
test("GPU receipts require real named device and never pass CPU gate",()=>{
 const r={status:"native-segment-complete",segment:0,frameStart:1,frameEnd:7,nativeFrameCount:7,resolution:[1920,1080],fps:24,samples:12,engine:"Cycles OptiX",version:"4.5.17",geometrySha256:"a".repeat(64),frameHashes:Array.from({length:7},(_,i)=>({frame:i+1,file:"frame-"+String(i+1).padStart(3,"0")+".png",sha256:"b".repeat(64)}))};
 assert.equal(validSegmentReceipt(r,0,"Cycles OptiX"),false);
 r.devices=[{type:"OPTIX",name:"RTX 5090",id:"GPU-1"}];
 assert.equal(validSegmentReceipt(r,0,"Cycles OptiX"),true);
 assert.equal(validSegmentReceipt(r,0),false);
});
