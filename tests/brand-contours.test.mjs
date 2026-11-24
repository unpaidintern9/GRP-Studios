import {test} from 'node:test';
import assert from 'node:assert/strict';
import {trace, classify} from '../engine/brand/trace_logo.mjs';

test('contour trace preserves a real enclosed counter',()=>{
 const W=24,H=24,mask=new Uint8Array(W*H);
 for(let y=2;y<22;y++)for(let x=2;x<22;x++)if(x<7||x>=17||y<7||y>=17)mask[y*W+x]=1;
 const g=trace(mask,W,H,1);
 assert.equal(g.outer,1);
 assert.equal(g.holes,1);
 assert.equal(g.iou,1);
 assert.equal(g.count,300);
});

test('whole-component classification keeps warm glyph edge pixels and ignores tiny dust',()=>{
 const W=64,H=64,raw=new Uint8Array(W*H*4);
 function pixel(x,y,c){raw.set(c,(y*W+x)*4)}
 for(let y=5;y<15;y++)for(let x=5;x<15;x++)pixel(x,y,[214,217,220,255]);
 for(let y=25;y<35;y++)for(let x=25;x<35;x++)pixel(x,y,x<27?[214,217,220,255]:[230,170,30,255]);
 pixel(50,50,[214,217,220,255]);
 const m=classify({W,H,raw});
 assert.equal(m.components.length,2);
 assert.equal(m.discarded,1);
 assert.equal(m.components[0].id,1);
 assert.equal(m.components[1].id,2);
 assert.equal(m.mask[25*W+25],2);
});
