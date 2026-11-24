// Fixed Gold Light production plan. No arbitrary code, filenames or render settings.
export const CLIP="gold-light-v02-clip-v1";
export const SEGMENTS=15;
export const STEP_MS=600000;
export const MAX_PLAN_MS=16*STEP_MS;
export const CLIP_PREFIX="clips/"+CLIP;
export const CLIP_PERMIT=CLIP_PREFIX+"/permit.json";
export const CLIP_STATUS=CLIP_PREFIX+"/status.json";
export const CLIP_ARCHIVE=CLIP_PREFIX+"/clip.zip";
export function range(i){if(!Number.isInteger(i)||i<0||i>=SEGMENTS)throw Error("Invalid clip segment");return [i*7+1,i*7+7]}
export function segmentKey(i){range(i);return CLIP_PREFIX+"/segments/"+String(i).padStart(2,"0")+".zip"}
export function clipOperation(b){
 if(!b||typeof b!=="object"||Array.isArray(b)||b.template!==CLIP||typeof b.nonce!=="string"||!/^[a-f0-9]{64}$/.test(b.nonce))return null;
 const keys=Object.keys(b).sort().join(",");
 if(keys==="nonce,operation,template"&&["clip-start","clip-cancel"].includes(b.operation))return b.operation;
 if(keys==="nonce,operation,segment,template"&&b.operation==="clip-step"&&Number.isInteger(b.segment)&&b.segment>=0&&b.segment<=SEGMENTS)return "clip-step";
 return null;
}
export function validClipPermit(p,nonce,now){
 return !!p&&Object.keys(p).sort().join(",")==="expiresAt,maxComputeMs,nonce,template"&&p.template===CLIP&&p.nonce===nonce&&Number.isSafeInteger(p.expiresAt)&&p.expiresAt>now&&p.expiresAt<=now+MAX_PLAN_MS+600000&&Number.isSafeInteger(p.maxComputeMs)&&p.maxComputeMs>=STEP_MS&&p.maxComputeMs<=MAX_PLAN_MS;
}
export function validSegmentReceipt(r,i){
 const [first,last]=range(i);
 return r?.status==="native-segment-complete"&&r.segment===i&&r.frameStart===first&&r.frameEnd===last&&r.nativeFrameCount===7&&r.resolution?.join(",")==="1920,1080"&&r.fps===24&&r.samples===12&&r.engine==="Cycles CPU"&&/^4\.5\.17(?:\s|$)/.test(r.version)&&/^[a-f0-9]{64}$/.test(r.geometrySha256)&&r.frameHashes?.length===7&&r.frameHashes.every((x,k)=>x.frame===first+k&&x.file==="frame-"+String(x.frame).padStart(3,"0")+".png"&&/^[a-f0-9]{64}$/.test(x.sha256));
}
