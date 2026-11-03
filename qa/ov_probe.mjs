import { chromium } from 'playwright';
const b=await chromium.launch({headless:true,executablePath:'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
const c=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
const p=await c.newPage();
await p.goto('http://127.0.0.1:8124/?ovp=1&v='+Date.now(),{waitUntil:'networkidle'});
await p.waitForFunction(()=>window.__ready,null,{timeout:120000});
const data=await p.evaluate(()=>{
  const THREE=window.__changlu.scene.children[0].constructor; // not reliable
  const out={zones:{},cands:[]};
  const C=window.__changlu.camera;
  for(const [id,z] of Object.entries(window.__changlu.zones)){
    z.group.updateMatrixWorld(true);
    let min=[1e9,1e9,1e9],max=[-1e9,-1e9,-1e9];
    z.group.traverse(o=>{ if(o.isMesh){o.geometry.computeBoundingBox(); const bb=o.geometry.boundingBox.clone(); bb.applyMatrix4(o.matrixWorld); min=[Math.min(min[0],bb.min.x),Math.min(min[1],bb.min.y),Math.min(min[2],bb.min.z)]; max=[Math.max(max[0],bb.max.x),Math.max(max[1],bb.max.y),Math.max(max[2],bb.max.z)];}});
    out.zones[id]={min,max,center:min.map((v,i)=>(v+max[i])/2)};
  }
  return out;
});
console.log(JSON.stringify(data));
await b.close();
