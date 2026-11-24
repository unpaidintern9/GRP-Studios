import {test} from "node:test";
import {TEMPLATE,INPUTS,FRAMES,validateEnvelope,canStart,validReceipt} from "../plugins/blender/review-contract.mjs";
test("fixed private review contract",()=>{
let count=0;
function ok(v){if(!v)throw Error("Assertion failed");count++}
function rejects(fn){let failed=false;try{fn()}catch{failed=true}ok(failed)}
const payload={template:TEMPLATE,assets:INPUTS.map(x=>({name:x.name,base64:"A".repeat(4*Math.ceil(x.bytes/3))}))};
ok(validateEnvelope(payload)===payload);
rejects(()=>validateEnvelope({...payload,cmd:"blender"}));
rejects(()=>validateEnvelope({...payload,template:"other"}));
rejects(()=>validateEnvelope({...payload,assets:payload.assets.slice(0,1)}));
rejects(()=>validateEnvelope({...payload,assets:[...payload.assets].reverse()}));
rejects(()=>validateEnvelope({...payload,assets:[{...payload.assets[0],name:"../../private"},payload.assets[1]]}));
rejects(()=>validateEnvelope({...payload,assets:[{...payload.assets[0],base64:"bad"},payload.assets[1]]}));
ok(canStart(null)&&canStart(undefined));
for(const state of ["running","cancelled","failed","succeeded"])ok(!canStart({state}));
const receipt={status:"unapproved-lookdev",version:"4.5.17 LTS",engine:"Cycles CPU",fps:24,totalFrames:120,resolution:[1920,1080],keyframes:FRAMES.map(frame=>({frame,file:"frame-"+String(frame).padStart(3,"0")+".png",sha256:"a".repeat(64)}))};
ok(validReceipt(receipt));ok(!validReceipt({...receipt,resolution:[640,360]}));ok(!validReceipt({...receipt,keyframes:receipt.keyframes.slice(0,3)}));ok(!validReceipt({...receipt,version:"4.5.16"}));ok(!validReceipt({...receipt,status:"approved"}));

console.log(count+" review assertions passed");
});
