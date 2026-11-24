// One fixed private lookdev job. Not a general remote execution interface.
export const TEMPLATE="gold-light-v02-review-v1";
export const FRAMES=Object.freeze([18,36,76,114]);
export const INPUTS=Object.freeze([
  {
    "name": "grp-mark-reverse.png",
    "blob": "8c8b9cad7ad96ffae49f778b78d09f7ce29b82cb",
    "sha256": "09e4f7d89229d47bcd23e884950d90b8d8b2624ca3073267129a6764dba6b265",
    "bytes": 304742
  },
  {
    "name": "grp-full-reverse.png",
    "blob": "84bba8beaba9ec557d05f5426e958233f00d3605",
    "sha256": "57640212bfc8173a8cb5c2b740129ba365898c95846db1156035c3efe1ccdf76",
    "bytes": 562827
  }
].map(x=>Object.freeze({...x,key:"brand/originals/"+x.blob+"/"+x.name})));
export const MAX_REQUEST_BYTES=1500000;
export const MAX_ARCHIVE_BYTES=24000000;
export const JOB_TIMEOUT_MS=600000;
export const JOB_KEY="gold-light-v02-review-v1";
export const OUTPUT_KEY="reviews/"+JOB_KEY+"/lookdev.zip";
export function validateEnvelope(payload) {
 if(!payload||Object.getPrototypeOf(payload)!==Object.prototype||Object.keys(payload).sort().join(",")!=="assets,template"||payload.template!==TEMPLATE) throw Error("Invalid fixed review template");
 if(!Array.isArray(payload.assets)||payload.assets.length!==INPUTS.length)throw Error("Expected two inputs");
 for(let i=0;i<INPUTS.length;i++){
  const v=payload.assets[i],expected=INPUTS[i];
  if(!v||Object.keys(v).sort().join(",")!=="base64,name"||v.name!==expected.name||
    typeof v.base64!=="string"||v.base64.length!==4*Math.ceil(expected.bytes/3)||!/^[A-Za-z0-9+/]+={0,2}$/.test(v.base64))throw Error("Invalid fixed input");
 }
 return payload;
}
export function canStart(state){return state===undefined||state===null}
export function validReceipt(r) {
 return !!r&&r.status==="unapproved-lookdev"&&/^4\.5\.17(?:\s|$)/.test(r.version)&&r.engine==="Cycles CPU"&&r.fps===24&&r.totalFrames===120&&
 Array.isArray(r.resolution)&&r.resolution.join(",")==="1920,1080"&&Array.isArray(r.keyframes)&&r.keyframes.length===FRAMES.length&&
 r.keyframes.every((x,i)=>x.frame===FRAMES[i]&&x.file==="frame-"+String(x.frame).padStart(3,"0")+".png"&&/^[0-9a-f]{64}$/.test(x.sha256));
}
