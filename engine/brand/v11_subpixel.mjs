/* V11 precision curves from the original RGBA alpha isocontour.
 * The two sub-four-pixel raster pinholes are discarded, not genuine counters.
 * No native mesh fill or creative approval is inferred from mask parity.
 */
const NAMES=["silver-monogram","gold-r","silver-wordmark","gold-descriptor"],OUTER=[2,1,6,16],HOLES=[0,0,1,7];
const plus=(a,b)=>[a[0]+b[0],a[1]+b[1]],minus=(a,b)=>[a[0]-b[0],a[1]-b[1]],scale=(a,k)=>[a[0]*k,a[1]*k],dot=(a,b)=>a[0]*b[0]+a[1]*b[1],norm=a=>Math.hypot(a[0],a[1]),unit=a=>scale(a,1/Math.max(norm(a),1e-12)),dist=(a,b)=>norm(minus(a,b));
const area=p=>p.reduce((s,a,i)=>{let b=p[(i+1)%p.length];return s+a[0]*b[1]-a[1]*b[0]},0)/2;
function contains(p,q){let hit=false;for(let i=0,j=q.length-1;i<q.length;j=i++){let a=q[i],b=q[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])hit=!hit}return hit}
function alphaContours(W,H,rgba,mask,id){
 let graph=new Map(),points=new Map(),box=[W,H,0,0];
 for(let i=0;i<mask.length;i++)if(mask[i]===id){let x=i%W,y=(i/W)|0;box=[Math.min(box[0],x),Math.min(box[1],y),Math.max(box[2],x),Math.max(box[3],y)]}
 function val(x,y){if(x<0||x>=W||y<0||y>=H)return 0;let i=y*W+x,a=rgba[4*i+3];return a<128||mask[i]===id?a:0}
 function join(a,b){for(let [k,v] of [[a,b],[b,a]]){if(!graph.has(k))graph.set(k,[]);graph.get(k).push(v)}}
 for(let y=box[1]-2;y<=box[3]+1;y++)for(let x=box[0]-2;x<=box[2]+1;x++){
  let z=[val(x,y),val(x+1,y),val(x+1,y+1),val(x,y+1)],p=z.map(v=>v>=127.5);if(p.every(v=>v===p[0]))continue;
  let edges=[],corners=[[x+.5,y+.5],[x+1.5,y+.5],[x+1.5,y+1.5],[x+.5,y+1.5]];
  let keys=[x+','+y+',h',(x+1)+','+y+',v',x+','+(y+1)+',h',x+','+y+',v'];
  for(let i=0;i<4;i++){let j=(i+1)%4;if(p[i]===p[j])continue;let t=(127.5-z[i])/(z[j]-z[i]);points.set(keys[i],plus(corners[i],scale(minus(corners[j],corners[i]),t)));edges.push(keys[i])}
  if(edges.length===2)join(...edges);else if(edges.length===4){let c=z.reduce((a,b)=>a+b,0)/4>=127.5;if(c===p[0]){join(edges[0],edges[1]);join(edges[2],edges[3])}else{join(edges[0],edges[3]);join(edges[1],edges[2])}}else throw Error("Invalid cell");
 }
 const seen=new Set(),loops=[],removed=[];
 for(let [start,adj] of graph){if(adj.length!==2)throw Error("Nonmanifold contour");if(seen.has(start))continue;let c=start,prev=null,p=[];
  do{if(seen.has(c))throw Error("Crossing");seen.add(c);p.push(points.get(c));let n=graph.get(c).find(k=>k!==prev);prev=c;c=n}while(c!==start);
  if(p.length<3||Math.abs(area(p))<4){removed.push(Math.abs(area(p)));continue}loops.push(p)
 }
 const oriented=loops.map(p=>{let hole=loops.filter(q=>q!==p&&contains(p[0],q)).length%2;return (area(p)>0)===!hole?p:p.slice().reverse()});
 if(oriented.filter(p=>area(p)>0).length!==OUTER[id-1]||oriented.filter(p=>area(p)<0).length!==HOLES[id-1])throw Error("Unexpected real topology "+NAMES[id-1]+" "+JSON.stringify(oriented.map(area)));
 return {loops:oriented,removed};
}
function nearby(p,i,d,span){let j=i,last=p[i],sum=0;for(let k=0;k<p.length-1;k++){j=(j+d+p.length)%p.length;let q=p[j],ds=dist(last,q);if(sum+ds>=span&&ds>0)return plus(last,scale(minus(q,last),(span-sum)/ds));sum+=ds;last=q}return last}
function fitClosed(p,tol){
 let N=p.length,angles=p.map((b,i)=>dot(unit(minus(b,nearby(p,i,-1,3))),unit(minus(nearby(p,i,1,3),b)))),corners=[];
 for(let i of Array.from({length:N},(_,i)=>i).filter(i=>angles[i]<.70).sort((a,b)=>angles[a]-angles[b]))if(corners.every(j=>Math.min((i-j+N)%N,(j-i+N)%N)>6))corners.push(i);
 if(corners.length<2)corners=[0,Math.floor(N/2)];corners.sort((a,b)=>a-b);
 const sharp=new Set(corners.filter(i=>angles[i]<.70));
 let q=p.map((b,i)=>{if(sharp.has(i))return b;let a=nearby(p,i,-1,2),c=nearby(p,i,1,2),t=unit(minus(c,a)),v=minus(plus(a,scale(t,dot(minus(b,a),t))),b);return plus(b,scale(v,Math.min(.28,.16/Math.max(norm(v),1e-9))))});
 const tangent=i=>unit(minus(nearby(q,i,1,3),nearby(q,i,-1,3)));
 function fit(a,t0,t1,depth=0){
  let p0=a[0],p3=a[a.length-1],n=a.length,L=dist(p0,p3);
  if(n<3||depth>20)return [[p0,plus(p0,scale(t0,L/3)),plus(p3,scale(t1,L/3)),p3]];
  const u=[0];for(let i=1;i<n;i++)u.push(u[i-1]+dist(a[i],a[i-1]));let arc=u[n-1];if(arc<1e-9)return [[p0,p0,p3,p3]];for(let i=0;i<n;i++)u[i]/=arc;
  let c00=0,c01=0,c11=0,x0=0,x1=0;
  for(let i=0;i<n;i++){let t=u[i],v=1-t,b0=v*v*v,b1=3*t*v*v,b2=3*t*t*v,b3=t*t*t,A=scale(t0,b1),B=scale(t1,b2),D=minus(a[i],plus(scale(p0,b0+b1),scale(p3,b2+b3)));c00+=dot(A,A);c01+=dot(A,B);c11+=dot(B,B);x0+=dot(A,D);x1+=dot(B,D)}
  let det=c00*c11-c01*c01,aa=Math.abs(det)>1e-10?(x0*c11-x1*c01)/det:arc/3,bb=Math.abs(det)>1e-10?(c00*x1-c01*x0)/det:arc/3;if(Math.min(aa,bb)<arc*.001||Math.max(aa,bb)>arc*.9)aa=bb=arc/3;
  let p1=plus(p0,scale(t0,aa)),p2=plus(p3,scale(t1,bb)),worst=0,j=1;
  for(let i=1;i<n-1;i++){let t=u[i],v=1-t,b=plus(plus(scale(p0,v*v*v),scale(p1,3*t*v*v)),plus(scale(p2,3*t*t*v),scale(p3,t*t*t))),err=dist(a[i],b);if(err>worst){worst=err;j=i}}
  if(worst<=tol)return [[p0,p1,p2,p3]];
  let mid=unit(minus(a[Math.min(n-1,j+3)],a[Math.max(0,j-3)]));return [...fit(a.slice(0,j+1),t0,scale(mid,-1),depth+1),...fit(a.slice(j),mid,t1,depth+1)];
 }
 let seg=[];for(let k=0;k<corners.length;k++){let i=corners[k],j=corners[(k+1)%corners.length],a=j>i?q.slice(i,j+1):[...q.slice(i),...q.slice(0,j+1)];
  if(a.length<2)continue;let t0=sharp.has(i)?unit(minus(nearby(q,i,1,2),q[i])):tangent(i),t1=sharp.has(j)?unit(minus(nearby(q,j,-1,2),q[j])):scale(tangent(j),-1);seg.push(...fit(a,t0,t1))}
 return seg.map((s,i)=>[seg[(i+seg.length-1)%seg.length][2],s[0],s[1]]);
}
function sample(c){let p=[];for(let i=0;i<c.length;i++){let [,a,b]=c[i],[d,e]=c[(i+1)%c.length],n=Math.max(8,Math.ceil((dist(a,b)+dist(b,d)+dist(d,e))/.4));for(let j=0;j<n;j++){let t=j/n,u=1-t;p.push(plus(plus(scale(a,u*u*u),scale(b,3*u*u*t)),plus(scale(d,3*u*t*t),scale(e,t*t*t))))}}return p}
function crossings(loops){
 let bins=new Map();const orient=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
 for(let l=0;l<loops.length;l++){let p=loops[l];for(let i=0;i<p.length;i++){let a=p[i],b=p[(i+1)%p.length],s={a,b,l,i},seen=new Set();for(let y=Math.floor(Math.min(a[1],b[1])/4);y<=Math.floor(Math.max(a[1],b[1])/4);y++)for(let x=Math.floor(Math.min(a[0],b[0])/4);x<=Math.floor(Math.max(a[0],b[0])/4);x++){let k=x+','+y,list=bins.get(k)||[];for(let q of list){if(seen.has(q))continue;seen.add(q);if(q.l===l&&(Math.abs(q.i-i)<=1||Math.abs(q.i-i)===p.length-1))continue;if(orient(a,b,q.a)*orient(a,b,q.b)<-1e-12&&orient(q.a,q.b,a)*orient(q.a,q.b,b)<-1e-12)return true}list.push(s);bins.set(k,list)}}}return false;
}
function parity(loops,W,H,mask,id){
 let rows=Array.from({length:H},()=>[]);for(let p of loops)for(let i=0;i<p.length;i++){let a=p[i],b=p[(i+1)%p.length];if(a[1]===b[1])continue;if(a[1]>b[1])[a,b]=[b,a];for(let y=Math.max(0,Math.ceil(a[1]-.5));y<Math.min(H,Math.ceil(b[1]-.5));y++)rows[y].push(a[0]+(y+.5-a[1])*(b[0]-a[0])/(b[1]-a[1]))}
 let pred=new Uint8Array(W*H);for(let y=0;y<H;y++){let r=rows[y].sort((a,b)=>a-b);if(r.length%2)throw Error("Odd crossing count");for(let i=0;i<r.length;i+=2){let a=Math.max(0,Math.ceil(r[i]-.5)),b=Math.min(W,Math.ceil(r[i+1]-.5));if(b>a)pred.fill(1,y*W+a,y*W+b)}}
 let inter=0,union=0,fp=0,fn=0;for(let i=0;i<pred.length;i++){let t=mask[i]===id,p=pred[i]===1;if(t&&p)inter++;if(t||p)union++;if(p&&!t)fp++;if(t&&!p)fn++}return {iou:inter/union,fp,fn};
}
function reconstructSubpixel(image,mask){
 const {W,H,raw}=image,groups=[];
 for(let id=1;id<=4;id++){
  let {loops,removed}=alphaContours(W,H,raw,mask,id),attempts=[],best=null;
  for(let tol of [.50,.35,.24,.16,.10]){
   let curves=loops.map(p=>fitClosed(p,tol)),polys=curves.map(sample),topology=polys.every((q,j)=>Math.sign(area(q))===Math.sign(area(loops[j]))&&Math.abs(area(q)-area(loops[j]))/Math.abs(area(loops[j]))<.018)&&!crossings(polys);
   let check={tolerance:tol,knots:curves.reduce((n,p)=>n+p.length,0),topology,...parity(polys,W,H,mask,id)};attempts.push(check);
   if(topology&&check.iou>=.992){best={curves,check};break}
  }
  if(!best)throw Error("No acceptable fitted curve for "+NAMES[id-1]+" "+JSON.stringify(attempts));
  groups.push({name:NAMES[id-1],outer:OUTER[id-1],holes:HOLES[id-1],removedSubpixelAreas:removed,sourceVertices:loops.reduce((a,p)=>a+p.length,0),...best,attempts});
 }
 return {version:1,width:W,height:H,method:"alpha-isocontour-127.5; corner-aware adaptive cubic fit; source-raster parity and strict crossing check",groups,nativeFillVerified:false,creativeApproval:false};
}
export {reconstructSubpixel};
