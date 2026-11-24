import {test} from "node:test";
import assert from "node:assert/strict";
import {operation,permitValid,TEMPLATE} from "../infrastructure/cloudflare/queue-review-contract.mjs";
test("private fixed queue admission",()=>{
 const nonce="a".repeat(64),now=100000;
 assert.equal(operation({operation:"preflight",template:TEMPLATE}),"preflight");
 assert.equal(operation({operation:"cancel",template:TEMPLATE}),"cancel");
 assert.equal(operation({operation:"render",template:TEMPLATE,nonce}),"render");
 assert.equal(operation({operation:"render",template:TEMPLATE,nonce,command:"anything"}),null);
 assert.equal(operation({operation:"render",template:TEMPLATE}),null);
 assert.equal(operation({operation:"render",template:"other",nonce}),null);
 assert.equal(operation(null),null);
 assert.equal(permitValid({template:TEMPLATE,nonce,expiresAt:now+60000},nonce,now),true);
 assert.equal(permitValid({template:TEMPLATE,nonce,expiresAt:now},nonce,now),false);
 assert.equal(permitValid({template:TEMPLATE,nonce,expiresAt:now+600001},nonce,now),false);
 assert.equal(permitValid({template:TEMPLATE,nonce:"b".repeat(64),expiresAt:now+1},nonce,now),false);
});
