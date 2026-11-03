import { chromium } from 'playwright';
const b = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const p = await b.newPage({ viewport: { width: 1600, height: 1000 } });
p.on('pageerror', e=>console.log('ERR', e.message));
await p.goto('http://127.0.0.1:8124/?capture=1',{waitUntil:'networkidle'}); await p.waitForFunction(()=>window.__ready,null,{timeout:90000});
await p.waitForTimeout(1200);
await p.addStyleTag({content:'*{transition:none!important} #loading{display:none}'});
await p.evaluate(()=>{__changlu.start();__changlu.freeze();__changlu.setProgress(1);__changlu.settle(70);__changlu.advance(1/24);__changlu.launch();});
for (const [sec,name] of [[1.2,'finale_12'],[2.6,'finale_26'],[5.5,'finale_55'],[8.2,'finale_82']]) {
  const frames = Math.round(sec*24) - (name==='finale_12'?0:(name==='finale_26'?29:(name==='finale_55'?62:132)));
  if (frames>0) await p.evaluate((n)=>{for(let i=0;i<n;i++)__changlu.advance(1/24)}, frames);
  await p.screenshot({path:`qa/${name}.png`});
}
console.log('FINALE SHOTS DONE');
await b.close();
