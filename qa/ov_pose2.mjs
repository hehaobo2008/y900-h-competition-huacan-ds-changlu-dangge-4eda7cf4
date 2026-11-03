import { chromium } from 'playwright';
const b=await chromium.launch({headless:true,executablePath:'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
const c=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
const p=await c.newPage();
await p.goto('http://127.0.0.1:8124/?ovt2=1&v='+Date.now(),{waitUntil:'networkidle'});
await p.waitForFunction(()=>window.__ready,null,{timeout:120000});
await p.evaluate(()=>{window.__changlu.start(); window.__changlu.freeze(); window.__changlu.overview(); window.__changlu.settle(100);});
await p.waitForTimeout(1300);
await p.evaluate(()=>{document.querySelectorAll('#landing,#hud,#timeline,#chapter,#hotspot,#toast,.ov-labels').forEach(e=>e.style.display='none');});
const poses=[
 {n:'D',pos:[900,700,600],look:[0,0,-500],fov:68},
 {n:'E',pos:[1100,900,900],look:[0,0,-700],fov:60},
 {n:'G',pos:[1530,1190,1020],look:[0,0,-820],fov:42},
 {n:'H',pos:[900,700,600],look:[0,0,-820],fov:56},
];
for(const q of poses){
 await p.evaluate((q)=>{
  const C=window.__changlu.camera; C.up.set(0,1,0); C.position.set(...q.pos); C.fov=q.fov; C.lookAt(...q.look); C.updateProjectionMatrix(); C.updateMatrixWorld(true);
  const sc=window.__changlu.scene; sc.fog.near=1200; sc.fog.far=7000;
  window.__changlu.paper.render();
 },q);
 await p.waitForTimeout(200);
 const proj=await p.evaluate(()=>{
  const C=window.__changlu.camera; const V=C.position.constructor; const out=[];
  for(const [id,z] of Object.entries(window.__changlu.zones)){
   z.group.updateMatrixWorld(true); let mn=[1e9,1e9,1e9],mx=[-1e9,-1e9,-1e9];
   z.group.traverse(o=>{if(o.isMesh){o.geometry.computeBoundingBox();const bb=o.geometry.boundingBox.clone();bb.applyMatrix4(o.matrixWorld);mn=[Math.min(mn[0],bb.min.x),Math.min(mn[1],bb.min.y),Math.min(mn[2],bb.min.z)];mx=[Math.max(mx[0],bb.max.x),Math.max(mx[1],bb.max.y),Math.max(mx[2],bb.max.z)];}});
   let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
   for(let i=0;i<8;i++){const v=new V(i&1?mx[0]:mn[0],i&2?mx[1]:mn[1],i&4?mx[2]:mn[2]).project(C);const sx=(v.x*.5+.5)*390,sy=(-v.y*.5+.5)*844;x0=Math.min(x0,sx);x1=Math.max(x1,sx);y0=Math.min(y0,sy);y1=Math.max(y1,sy);}
   out.push({id,x0:+x0.toFixed(0),x1:+x1.toFixed(0),y0:+y0.toFixed(0),y1:+y1.toFixed(0)});
  }
  return out;
 });
 console.log(q.n, JSON.stringify(proj));
 await p.screenshot({path:`qa/ovpose_${q.n}.png`});
}
await b.close();
