import {V03_TEMPLATE,V04_TEMPLATE,V05_TEMPLATE} from "../../plugins/blender/review-contract.mjs";
export {V03_TEMPLATE,V04_TEMPLATE,V05_TEMPLATE};
export const TEMPLATE="gold-light-v02-review-v1";
export const QUEUE="grp-studios-render-queue";
export const PREFLIGHT_KEY="reviews/control/preflight-v3.json";
export const STATUS_KEY="reviews/control/status-v3.json";
export const PERMIT_KEY="reviews/control/permit-v3.json";
export function operation(body){
 if(!body||typeof body!=="object"||Array.isArray(body))return null;
 if(Object.keys(body).sort().join(",")==="operation,template"&&[TEMPLATE,V03_TEMPLATE,V04_TEMPLATE,V05_TEMPLATE].includes(body.template)&&["preflight","cancel"].includes(body.operation))return body.operation;
 if(Object.keys(body).sort().join(",")==="nonce,operation,template"&&[TEMPLATE,V03_TEMPLATE,V04_TEMPLATE,V05_TEMPLATE].includes(body.template)&&body.operation==="render"&&typeof body.nonce==="string"&&/^[a-f0-9]{64}$/.test(body.nonce))return "render";
 return null;
}
export function permitValid(p,nonce,now,template=TEMPLATE){
 return !!p&&Object.keys(p).sort().join(",")==="expiresAt,nonce,template"&&p.template===template&&p.nonce===nonce&&Number.isSafeInteger(p.expiresAt)&&p.expiresAt>now&&p.expiresAt<=now+600000;
}

export function reviewKeys(template){if(template===V05_TEMPLATE)return {status:"reviews/gold-light-v05-motion-v1/status.json",permit:"reviews/gold-light-v05-motion-v1/permit.json",preflight:"reviews/gold-light-v05-motion-v1/preflight.json",output:"reviews/gold-light-v05-motion-v1/motion.zip",image:"clip"};if(template===V04_TEMPLATE)return {status:"reviews/gold-light-v04-lookdev-v2/status.json",permit:"reviews/gold-light-v04-lookdev-v2/permit.json",preflight:"reviews/gold-light-v04-lookdev-v2/preflight.json",output:"reviews/gold-light-v04-lookdev-v2/lookdev.zip",image:"clip"};if(template===V03_TEMPLATE)return {status:"reviews/gold-light-v03-motion-v1/status.json",permit:"reviews/gold-light-v03-motion-v1/permit.json",preflight:"reviews/gold-light-v03-motion-v1/preflight.json",output:"reviews/gold-light-v03-motion-v1/motion.zip",image:"clip"};if(template!==TEMPLATE)throw Error("Unknown review template");return {status:STATUS_KEY,permit:PERMIT_KEY,preflight:PREFLIGHT_KEY,output:"reviews/gold-light-v02-review-v1/lookdev.zip",image:"base"}}
