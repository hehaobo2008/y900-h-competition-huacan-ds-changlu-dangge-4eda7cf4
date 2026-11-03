import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.log('PAGEERR', e.message));
page.on('console', m => { if (m.type()==='error') console.log('CERR', m.text().slice(0,300)); });
await page.goto('http://127.0.0.1:8124/', { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 60000 });
await page.waitForTimeout(1500);
await page.click('#startBtn');
await page.waitForTimeout(1600);
for (const [t, name] of [[0.10,'h5_rural'],[0.315,'h5_town'],[0.545,'h5_city_train'],[0.56,'h5_city'],[0.79,'h5_rail'],[0.95,'h5_future']]) {
  await page.evaluate((tt) => { window.__changlu.setProgress(tt); window.__changlu.settle(70); }, t);
  await page.waitForTimeout(350);
  await page.screenshot({ path: `qa/${name}.png` });
  console.log('shot', name);
}
await page.evaluate(() => { window.__changlu.overview(); window.__changlu.settle(80); });
await page.waitForTimeout(1200);
await page.screenshot({ path: 'qa/h5_overview.png' });
console.log('shot overview');
await browser.close();
