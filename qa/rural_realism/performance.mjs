import { chromium } from 'playwright';
import fs from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME || 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
const page=await browser.newPage({viewport:{width:1600,height:900},deviceScaleFactor:1});
await page.goto('http://127.0.0.1:18371/?capture=1',{waitUntil:'networkidle'});
await page.waitForFunction(()=>window.__ready);
await page.waitForTimeout(1600);
await page.evaluate(()=>{__changlu.start();__changlu.setProgress(.1);__changlu.settle(80);});
await page.waitForTimeout(2000);
const result=await page.evaluate(async()=>{
  const gl=__changlu.renderer.getContext(), ext=gl.getExtension('WEBGL_debug_renderer_info');
  const times=[];
  let last=performance.now(), start=last;
  while(performance.now()-start<6000) {
    await new Promise(requestAnimationFrame);
    const now=performance.now(); times.push(now-last); last=now;
  }
  const sorted=[...times].sort((a,b)=>a-b);
  return {durationMs:last-start,frames:times.length,fps:times.length/((last-start)/1000),
    frameMsP50:sorted[Math.floor(sorted.length*.5)],frameMsP95:sorted[Math.floor(sorted.length*.95)],
    viewport:[1600,900],pixelRatio:devicePixelRatio,
    vendor:ext && gl.getParameter(ext.UNMASKED_VENDOR_WEBGL),renderer:ext && gl.getParameter(ext.UNMASKED_RENDERER_WEBGL),
    userAgent:navigator.userAgent};
});
const target=process.argv[2] || 'qa/rural_realism/performance.json';
fs.writeFileSync(target,JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
await browser.close();
