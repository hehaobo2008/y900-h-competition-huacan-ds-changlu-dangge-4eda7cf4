import {chromium} from 'playwright';
import fs from 'node:fs';
const dir='qa/rural_realism/lights';fs.mkdirSync(dir,{recursive:true});
const b=await chromium.launch({headless:true,executablePath:process.env.CHROME || 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
const p=await b.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
await p.goto('http://127.0.0.1:18371/?capture=1',{waitUntil:'networkidle'});
await p.waitForFunction(()=>window.__ready);
await p.waitForTimeout(1600);
await p.evaluate(()=>{
  __changlu.start();__changlu.freeze();__changlu.setProgress(.1);__changlu.settle(80);
  document.querySelectorAll('#landing,#loading,#chapter,#scrollHint,#hotspot,#toast,#hud,#timeline,#travelMeta').forEach(e=>e.style.display='none');
  __changlu.camera.position.set(7.4,2,57.7);__changlu.camera.lookAt(2.2,1.1,52);
  __changlu.camera.fov=44;__changlu.camera.updateProjectionMatrix();
});
for(const [name,hemi,fill,exposure] of [['current',1.05,.55,1.15],['fill',1.4,.8,1.15],['bright',1.4,.8,1.28],['soft',1.25,.7,1.24]]){
  await p.evaluate(({hemi,fill,exposure})=>{
    const a=__changlu, lights=a.scene.children.filter(x=>x.isLight);
    lights.find(x=>x.isHemisphereLight).intensity=hemi;
    lights.find(x=>x.isDirectionalLight&&!x.castShadow).intensity=fill;
    a.renderer.toneMappingExposure=exposure;a.paper.render();
  },{hemi,fill,exposure});
  await p.screenshot({path:`${dir}/${name}.png`});
}
await b.close();
