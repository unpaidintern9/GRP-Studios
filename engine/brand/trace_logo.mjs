// Native-resolution RGBA8 logo trace; pure functions, no network or repository dependency.
function decodePng(a,inflate){
 const u=i=>a[i]*16777216+(a[i+1]<<16)+(a[i+2]<<8)+a[i+3];
 if(a.length<33||![137,80,78,71,13,10,26,10].every((x,i)=>a[i]===x))throw Error("Not PNG");
 const W=u(16),H=u(20);if(W<1||W>4096||H<1||H>4096||a[24]!==8||a[25]!==6||a[26]||a[27]||a[28])throw Error("Expected RGBA8 PNG");
 let z=[];for(let i=8;i<a.length;){let n=u(i);if(i+12+n>a.length)throw Error("Truncated PNG");if(String.fromCharCode(...a.slice(i+4,i+8))==="IDAT")for(let j=i+8;j<i+8+n;j++)z.push(a[j]);i+=n+12}
 let out=inflate(Uint8Array.from(z),W*H*4+H);if(out.length!==W*H*4+H)throw Error("Inflated length");
 let raw=new Uint8Array(W*H*4),stride=W*4,k=0;
 function pa(a,b,c){let p=a+b-c,u=Math.abs(p-a),v=Math.abs(p-b),w=Math.abs(p-c);return u<=v&&u<=w?a:v<=w?b:c}
 for(let y=0;y<H;y++){let f=out[k++];if(f>4)throw Error("Invalid PNG filter");for(let x=0;x<stride;x++){let i=y*stride+x,l=x>=4?raw[i-4]:0,u=y?raw[i-stride]:0,ul=y&&x>=4?raw[i-stride-4]:0;raw[i]=(out[k++]+(f===1?l:f===2?u:f===3?(l+u)>>1:f===4?pa(l,u,ul):0))&255}}
 return {W,H,raw}
}
function classify({W,H,raw}){
 const mask=new Uint8Array(W*H),seen=new Uint8Array(W*H),q=new Int32Array(W*H),components=[];let discarded=0;
 for(let i=0;i<mask.length;i++){
  if(seen[i]||raw[4*i+3]<128)continue;
  let head=0,tail=1;q[0]=i;seen[i]=1;let gold=0,minx=W,miny=H,maxx=0,maxy=0;
  while(head<tail){let j=q[head++],x=j%W,y=Math.floor(j/W),p=j*4;gold+=raw[p]-raw[p+2]>40?1:0;minx=Math.min(minx,x);miny=Math.min(miny,y);maxx=Math.max(maxx,x);maxy=Math.max(maxy,y);
   for(let k of [x?j-1:-1,x+1<W?j+1:-1,y?j-W:-1,y+1<H?j+W:-1])if(k>=0&&!seen[k]&&raw[k*4+3]>=128){seen[k]=1;q[tail++]=k}}
  if(tail<32){discarded+=tail;continue}
  if(miny<555&&maxy>=555)throw Error("Unexpected crossing");
  let fraction=gold/tail;if(fraction>.3&&fraction<.7)throw Error("Ambiguous color");
  const id=miny>=555?(fraction>=.7?4:3):(fraction>=.7?2:1);
  for(let k=0;k<tail;k++)mask[q[k]]=id;
  components.push({id,area:tail,bbox:[minx,miny,maxx+1,maxy+1],goldFraction:fraction});
 }
 return {mask,components,discarded}
}
function trace(mask,W,H,id,epsilon=.65,smoothingPasses=0){
 if(!Number.isInteger(smoothingPasses)||smoothingPasses<0||smoothingPasses>3)throw Error('Invalid smoothing passes');
 let maxDisplacement=0;
 function smooth(points){let a=points;for(let pass=0;pass<smoothingPasses;pass++){a=a.map((p,i)=>{let x=0,y=0;for(let k=-2;k<=2;k++){const q=a[(i+k+a.length)%a.length],w=[1,4,6,4,1][k+2]/16;x+=q[0]*w;y+=q[1]*w;}return [x,y]});}for(let i=0;i<a.length;i++)maxDisplacement=Math.max(maxDisplacement,Math.hypot(a[i][0]-points[i][0],a[i][1]-points[i][1]));return a;}
 const pitch=W+1,E=new Map(),delta=[1,pitch,-1,-pitch];let count=0,minx=W,miny=H,maxx=0,maxy=0;
 const add=(v,d)=>E.set(v,(E.get(v)||0)|(1<<d));
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){let i=y*W+x;if(mask[i]!==id)continue;count++;minx=Math.min(minx,x);miny=Math.min(miny,y);maxx=Math.max(maxx,x);maxy=Math.max(maxy,y);let v=y*pitch+x;if(!y||mask[i-W]!==id)add(v,0);if(x===W-1||mask[i+1]!==id)add(v+1,1);if(y===H-1||mask[i+W]!==id)add(v+pitch+1,2);if(!x||mask[i-1]!==id)add(v+pitch,3)}
 const area=ps=>ps.reduce((a,p,i)=>{let q=ps[(i+1)%ps.length];return a+p[0]*q[1]-q[0]*p[1]},0)/2;
 function simplify(pts){
  let lo=0,hi=0;for(let i=1;i<pts.length;i++){if(pts[i][0]<pts[lo][0]||pts[i][0]===pts[lo][0]&&pts[i][1]<pts[lo][1])lo=i;if(pts[i][0]>pts[hi][0]||pts[i][0]===pts[hi][0]&&pts[i][1]>pts[hi][1])hi=i}
  let chain=pts.slice(lo).concat(pts.slice(0,lo));let split=(hi-lo+pts.length)%pts.length;chain.push(chain[0]);
  function rdp(l,r){if(r<=l+1)return [chain[l],chain[r]];let [ax,ay]=chain[l],[bx,by]=chain[r],dx=bx-ax,dy=by-ay,dd=dx*dx+dy*dy,best=epsilon*epsilon,mid=-1;
   for(let i=l+1;i<r;i++){let [x,y]=chain[i],t=dd?Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/dd)):0,e=(x-ax-t*dx)**2+(y-ay-t*dy)**2;if(e>best){best=e;mid=i}}
   return mid<0?[chain[l],chain[r]]:rdp(l,mid).slice(0,-1).concat(rdp(mid,r));
  }
  return rdp(0,split).slice(0,-1).concat(rdp(split,chain.length-1).slice(0,-1));
 }
 let loops=[],tiny=0;
 while(E.size){let start=E.keys().next().value,v=start,d=Math.log2(E.get(v)&-E.get(v)),pts=[],guard=0;
  do{pts.push([v%pitch,Math.floor(v/pitch)]);let b=E.get(v)&~(1<<d);if(b)E.set(v,b);else E.delete(v);v+=delta[d];if(v===start)break;let bits=E.get(v)||0;let nd=[(d+1)%4,d,(d+3)%4,(d+2)%4].find(t=>bits&(1<<t));if(nd===undefined||++guard>100000)throw Error("Invalid contour");d=nd}while(true);
  if(Math.abs(area(pts))<4){tiny+=Math.abs(area(pts));continue}
  let simple=simplify(smooth(pts));if(simple.length<3||Math.sign(area(simple))!==Math.sign(area(pts)))throw Error("Contour simplification");loops.push(simple)
 }
 let xs=Array.from({length:H},()=>[]);
 for(let ps of loops)for(let i=0;i<ps.length;i++){let [x1,y1]=ps[i],[x2,y2]=ps[(i+1)%ps.length];if(y1===y2)continue;if(y1>y2){[x1,x2]=[x2,x1];[y1,y2]=[y2,y1]}for(let y=Math.max(0,Math.ceil(y1-.5));y<Math.min(H,Math.ceil(y2-.5));y++)xs[y].push(x1+(y+.5-y1)*(x2-x1)/(y2-y1))}
 let pred=new Uint8Array(W*H);for(let y=0;y<H;y++){let a=xs[y].sort((a,b)=>a-b);if(a.length%2)throw Error("Odd crossings");for(let k=0;k<a.length;k+=2)for(let x=Math.max(0,Math.ceil(a[k]-.5));x<Math.min(W,Math.ceil(a[k+1]-.5));x++)pred[y*W+x]=1}
 let inter=0,union=0,fp=0,fn=0;for(let i=0;i<pred.length;i++){let t=mask[i]===id,p=pred[i]===1;if(t&&p)inter++;if(t||p)union++;if(p&&!t)fp++;if(t&&!p)fn++}
 return {id,count,bbox:[minx,miny,maxx+1,maxy+1],loops,tiny,maxDisplacement,iou:inter/union,fp,fn,vertices:loops.reduce((s,l)=>s+l.length,0),outer:loops.filter(l=>area(l)>0).length,holes:loops.filter(l=>area(l)<0).length};
}
function buildGeometry(full,mark){
 if(full.W!==1536||full.H!==934||mark.W!==1536||mark.H!==579)throw Error("Source dimensions mismatch");
 const f=classify(full),m=classify(mark);let same=0,total=0;
 for(let i=0;i<555*full.W;i++){if(f.mask[i]||m.mask[i]){total++;if(f.mask[i]===m.mask[i])same++}}
 if(same!==total)throw Error("Monogram mismatch");
 const names=["silver-monogram","gold-r","silver-wordmark","gold-descriptor"],expected=[2,1,6,16];
 const groups=names.map((name,i)=>{const components=f.components.filter(c=>c.id===i+1);let g=trace(f.mask,full.W,full.H,i+1,.16,i<2?3:1);
 if(components.length!==expected[i]||g.outer!==expected[i]||g.iou<.985)throw Error("Candidate validation: "+JSON.stringify({name,n:components.length,outer:g.outer,iou:g.iou}));
 return {...g,name,components:components.length}});
 return {version:1,width:full.W,height:full.H,monogramAgreement:same/total,discardedSmallPixels:f.discarded,groups}
}
export { decodePng, classify, trace, buildGeometry };
