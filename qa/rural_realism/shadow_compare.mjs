import { chromium } from 'playwright';
import fs from 'node:fs';
const output = 'qa/rural_realism/shadows';
fs.mkdirSync(output, {recursive:true});
const browser = await chromium.launch({headless:true,executablePath:process.env.CHROME || 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
const page = await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
await page.goto('http://127.0.0.1:18371/?capture=1', {waitUntil:'networkidle'});
await page.waitForFunction(() => window.__ready);
await page.waitForTimeout(1600);
await page.evaluate(() => {
  __changlu.start(); __changlu.freeze(); __changlu.setProgress(.1); __changlu.settle(80);
  document.querySelectorAll('#landing,#loading,#chapter,#scrollHint,#hotspot,#toast,#hud,#timeline,#travelMeta').forEach(e=>e.style.display='none');
  __changlu.camera.position.set(7.4,2,57.7); __changlu.camera.lookAt(2.2,1.1,52);
  __changlu.camera.fov=44; __changlu.camera.updateProjectionMatrix();
});
for (const [label,normal,bias] of [['n05',.05,-.00015],['n15',.15,-.00015],['n30',.3,-.00015],['bias',.05,-.001]]) {
  await page.evaluate(({normal,bias}) => {
    const a=__changlu;
    const light=a.scene.children.find(x=>x.isDirectionalLight && x.castShadow);
    light.shadow.normalBias=normal; light.shadow.bias=bias;
    a.renderer.shadowMap.needsUpdate=true;
    a.paper.render();
  },{normal,bias});
  await page.screenshot({path:`${output}/${label}.png`});
}
await browser.close();
