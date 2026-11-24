// Pure quote-based plan; no allocations or implicit spending.
export const GPU_TIERS=Object.freeze({pro:1,ultra:4,"ultra-max":8});
export function planGpu({tier="pro",budgetCents,maxSeconds,quotes,allowCommunity=false,storageReserveCents=20}) {
 const limit=GPU_TIERS[tier];
 if(!limit||!Number.isSafeInteger(budgetCents)||!Number.isSafeInteger(storageReserveCents)||storageReserveCents<0||budgetCents<=storageReserveCents||!Number.isSafeInteger(maxSeconds)||maxSeconds<60||!Array.isArray(quotes))throw Error("Invalid GPU budget or tier");
 const allowed=new Set(["NVIDIA GeForce RTX 5090","NVIDIA GeForce RTX 4090","NVIDIA RTX PRO 6000 Blackwell Server Edition","NVIDIA RTX A6000","NVIDIA L40S"]);
 const usable=quotes.filter(q=>allowed.has(q.id)&&["SECURE",...(allowCommunity?["COMMUNITY"]:[])].includes(q.cloud)&&["LOW","MEDIUM","HIGH"].includes(q.availability)&&Number.isSafeInteger(q.count)&&q.count>0&&Number.isFinite(q.hourlyUsd)&&q.hourlyUsd>0);
 const choices=usable.filter(q=>q.count<=limit).map(q=>({...q,ceilingCents:Math.ceil(q.hourlyUsd*q.count*maxSeconds/36)+storageReserveCents})).filter(q=>q.ceilingCents<=budgetCents);
 const speed={"NVIDIA GeForce RTX 5090":5,"NVIDIA RTX PRO 6000 Blackwell Server Edition":5,"NVIDIA GeForce RTX 4090":4,"NVIDIA L40S":3,"NVIDIA RTX A6000":2};
 choices.sort((a,b)=>Number(b.cloud==="SECURE")-Number(a.cloud==="SECURE")||speed[b.id]*b.count-speed[a.id]*a.count||a.ceilingCents-b.ceilingCents);
 return choices[0]??null;
}
