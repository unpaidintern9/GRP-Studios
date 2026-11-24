import { test } from "node:test";
import assert from "node:assert/strict";
import { CLIP_TEMPLATE, INPUTS, FRAMES, validateEnvelope, validClipReceipt } from "../plugins/blender/review-contract.mjs";
test("fixed five-second silent native clip",()=>{
 const payload={template:CLIP_TEMPLATE,assets:INPUTS.map(x=>({name:x.name,base64:"A".repeat(4*Math.ceil(x.bytes/3))}))};assert.equal(validateEnvelope(payload),payload);
 const receipt={"status":"unapproved-five-second-clip","engine":"Cycles CPU","version":"4.5.17 LTS","nativeFrameCount":105,"totalFrames":120,"fps":24,"resolution":[1920,1080],"video":{"file":"GRP-Gold-Light-V02-5s.mp4","codec":"h264","durationSeconds":5,"frames":120,"fps":24,"width":1920,"height":1080,"audio":false,"bytes":10000,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},"originalEndHoldSha256":"57640212bfc8173a8cb5c2b740129ba365898c95846db1156035c3efe1ccdf76","keyframes":[{"frame":18,"file":"frame-018.png","sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},{"frame":36,"file":"frame-036.png","sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},{"frame":76,"file":"frame-076.png","sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},{"frame":114,"file":"frame-114.png","sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]};
 assert.equal(validClipReceipt(receipt),true);
 assert.equal(validClipReceipt({...receipt,video:{...receipt.video,frames:119}}),false);
 assert.equal(validClipReceipt({...receipt,video:{...receipt.video,durationSeconds:4.96}}),false);
 assert.equal(validClipReceipt({...receipt,video:{...receipt.video,audio:true}}),false);
 assert.equal(validClipReceipt({...receipt,originalEndHoldSha256:"c".repeat(64)}),false);
});
