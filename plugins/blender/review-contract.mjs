// One fixed private lookdev job. Not a general remote execution interface.
export const TEMPLATE="gold-light-v02-review-v1";
export const V04_TEMPLATE="gold-light-v04-lookdev-v2";
export const V04_FRAMES=Object.freeze([1,11,20,39,78]);
export const V03_TEMPLATE="gold-light-v03-motion-v1";
export const CLIP_TEMPLATE="gold-light-v02-clip-v1";
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
 if(!payload||Object.getPrototypeOf(payload)!==Object.prototype||Object.keys(payload).sort().join(",")!=="assets,template"||![TEMPLATE,CLIP_TEMPLATE,V03_TEMPLATE,V04_TEMPLATE].includes(payload.template)) throw Error("Invalid fixed review template");
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

export function validClipReceipt(r,engine="Cycles CPU"){if(!["Cycles CPU","Cycles OptiX"].includes(engine))return false;const v=r?.video;return r?.status==="unapproved-five-second-clip"&&r.engine===engine&&(engine==="Cycles CPU"||Array.isArray(r.devices)&&r.devices.length>0&&r.devices.every(d=>d.type==="OPTIX"&&typeof d.name==="string"&&d.name.length>0&&typeof d.id==="string"&&d.id.length>0))&&/^4\.5\.17(?:\s|$)/.test(r.version)&&r.nativeFrameCount===105&&r.totalFrames===120&&r.fps===24&&r.resolution?.join(",")==="1920,1080"&&v?.file==="GRP-Gold-Light-V02-5s.mp4"&&v.codec==="h264"&&v.durationSeconds===5&&v.frames===120&&v.fps===24&&v.width===1920&&v.height===1080&&v.audio===false&&Number.isSafeInteger(v.bytes)&&v.bytes>100&&/^[0-9a-f]{64}$/.test(v.sha256)&&r.originalEndHoldSha256===INPUTS[1].sha256&&r.keyframes?.length===4&&r.keyframes.every((x,i)=>x.frame===FRAMES[i]&&x.file==="frame-"+String(x.frame).padStart(3,"0")+".png"&&/^[0-9a-f]{64}$/.test(x.sha256));}

export function validV03Receipt(r){const v=r?.video;return r?.status==="native-v03-motion-study"&&r.engine==="Cycles CPU"&&/^4\.5\.17(?:\s|$)/.test(r.version)&&r.referenceSha256==="2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26"&&/^[a-f0-9]{64}$/.test(r.geometrySha256)&&r.resolution?.join(",")==="640,360"&&r.fps===10&&r.frameCount===50&&r.sampledMasterFrames?.length===50&&r.sampledMasterFrames.every((x,i)=>x===1+Math.round(i*24/10))&&v?.file==="GRP-V03-motion-review.mp4"&&v.durationSeconds===5&&v.frames===50&&v.fps===10&&v.codec==="h264"&&v.audio===false&&Number.isSafeInteger(v.bytes)&&v.bytes>100&&/^[a-f0-9]{64}$/.test(v.sha256)}

export function validV04Receipt(r){return r?.status==="unapproved-v04-lookdev"&&r.engine==="Cycles CPU"&&/^4\.5\.17(?:\s|$)/.test(r.version)&&r.referenceSha256==="2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26"&&/^[a-f0-9]{64}$/.test(r.geometrySha256)&&r.resolution?.join(",")==="1920,1080"&&r.samples===24&&r.creativeApproval===false&&r.meshes?.length===4&&new Set(r.meshes.map(x=>x.name)).size===4&&["gold-r","silver-monogram","silver-wordmark","gold-descriptor"].every(n=>r.meshes.some(x=>x.name===n&&Number.isFinite(x.depth)&&x.depth>((n==="gold-r"||n==="silver-monogram") ? .4 : .04)&&Number.isInteger(x.faces)&&x.faces>0))&&r.keyframes?.length===V04_FRAMES.length&&r.keyframes.every((x,i)=>x.frame===V04_FRAMES[i]&&x.file==="frame-"+String(x.frame).padStart(3,"0")+".png"&&/^[a-f0-9]{64}$/.test(x.sha256))}
