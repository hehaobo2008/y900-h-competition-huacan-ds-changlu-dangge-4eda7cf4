import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.log('PAGEERR', e.message));
await page.goto('http://127.0.0.1:8124/?capture=1', { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 90000 });
await page.waitForTimeout(1500);
await page.evaluate(() => { window.__changlu.start(); window.__changlu.freeze(); window.__changlu.setProgress(.315); window.__changlu.settle(60); document.querySelectorAll('#chapter,#scrollHint,#hotspot').forEach(e=>e.style.display='none'); });
await page.waitForTimeout(800);
const t0 = Date.now();
for (let i=0;i<12;i++) {
  await page.evaluate(([dt,p]) => { window.__changlu.scrollTo(p); window.__changlu.advance(dt); }, [1/24, .315 + .001*i]);
  const buf = await page.screenshot({ type: 'jpeg', quality: 90 });
  if (i===0) console.log('frame bytes', buf.length);
}
console.log('12 frames ms', Date.now()-t0);
await page.screenshot({ path: 'qa/bench_last.jpg', type:'jpeg', quality: 92 });
await browser.close();
