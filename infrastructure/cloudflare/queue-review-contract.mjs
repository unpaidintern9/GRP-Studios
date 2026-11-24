export const TEMPLATE="gold-light-v02-review-v1";
export const QUEUE="grp-studios-render-queue";
export const PREFLIGHT_KEY="reviews/control/preflight-v3.json";
export const STATUS_KEY="reviews/control/status-v3.json";
export const PERMIT_KEY="reviews/control/permit-v3.json";
export function operation(body){
 if(!body||typeof body!=="object"||Array.isArray(body))return null;
 if(Object.keys(body).sort().join(",")==="operation,template"&&body.template===TEMPLATE&&["preflight","cancel"].includes(body.operation))return body.operation;
 if(Object.keys(body).sort().join(",")==="nonce,operation,template"&&body.template===TEMPLATE&&body.operation==="render"&&typeof body.nonce==="string"&&/^[a-f0-9]{64}$/.test(body.nonce))return "render";
 return null;
}
export function permitValid(p,nonce,now){
 return !!p&&Object.keys(p).sort().join(",")==="expiresAt,nonce,template"&&p.template===TEMPLATE&&p.nonce===nonce&&Number.isSafeInteger(p.expiresAt)&&p.expiresAt>now&&p.expiresAt<=now+600000;
}
