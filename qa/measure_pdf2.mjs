import { chromium } from 'playwright';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const b = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const p = await b.newPage({ viewport: { width: 794, height: 1123 } });
await p.goto(pathToFileURL(path.join(process.cwd(), 'docs/design.html')).href, { waitUntil: 'load' });
await p.waitForTimeout(300);
const r = await p.evaluate(() => {
  const pages=[...document.querySelectorAll('.page')];
  return [2,3,5,6].map(i=>{
    const pg=pages[i-1], pr=pg.getBoundingClientRect();
    const f=pg.querySelector('footer').getBoundingClientRect();
    const figs=[...pg.querySelectorAll('figure')].map(e=>{const b=e.getBoundingClientRect(); const im=e.querySelector('img')?.getBoundingClientRect(); return {cls:e.className, top:+(b.top-pr.top).toFixed(0), h:+b.height.toFixed(0), imgH:im?+im.height.toFixed(0):null};});
    return {page:i, footerTop:+(f.top-pr.top).toFixed(0), figs};
  });
});
console.log(JSON.stringify(r,null,1));
await b.close();
