import { chromium } from 'playwright';
const b=await chromium.launch({headless:true,executablePath:'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
const c=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
const p=await c.newPage();
await p.goto('http://127.0.0.1:8124/?ovt3=1&v='+Date.now(),{waitUntil:'networkidle'});
await p.waitForFunction(()=>window.__ready,null,{timeout:120000});
await p.evaluate(()=>{window.__changlu.start(); window.__changlu.freeze(); window.__changlu.overview(); window.__changlu.settle(120);});
await p.waitForTimeout(1300);
await p.evaluate(()=>{
  document.querySelectorAll('#landing,#hud,#timeline,#chapter,#hotspot,#toast').forEach(e=>e.style.display='none');
  const C=window.__changlu.camera; C.up.set(0,1,0); C.position.set(178,2974,-310); C.fov=50; C.lookAt(0,20,-800); C.updateProjectionMatrix(); C.updateMatrixWorld(true);
  const sc=window.__changlu.scene; sc.fog.near=1200; sc.fog.far=7000;
  const V=C.position.constructor;
  document.querySelectorAll('.ov-label').forEach((el,i)=>{
    const z=window.__changlu.zones[el.dataset.zone]; const v=new V(0,50,z.center??0); // placeholder
  });
  window.__changlu.paper.render();
});
// use real zone centers
const pos=await p.evaluate(()=>{
  const C=window.__changlu.camera; const V=C.position.constructor;
  const centers=[]; const zs={rural:-1,town:-420,city:-840,rail:-1260,future:-1680};
  document.querySelectorAll('.ov-label').forEach(el=>{
    const z=window.__changlu.zones[el.dataset.zone];
    const v=new V(z.group.position.x, 50, z.group.position.z - 840).project(C); // group position may be 0
    centers.push({id:el.dataset.zone, x:((v.x*.5+.5)*390).toFixed(0), y:((-v.y*.5+.5)*844).toFixed(0)});
  });
  return centers;
});
console.log(JSON.stringify(pos));
await p.screenshot({path:'qa/ovpose_P.png'});
await b.close();
