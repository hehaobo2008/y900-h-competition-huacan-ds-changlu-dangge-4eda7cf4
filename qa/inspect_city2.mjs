import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
page.on('pageerror', e => console.log('ERR', e.message));
await page.goto('http://127.0.0.1:8123/qa/zone/index.html?glb=/assets/zones/city.glb&cam=42,8,-30&target=40,25,-10&fov=45&night=0&post=0', { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 60000 });
await page.screenshot({ path: 'qa/city_nopost.png' });
await page.evaluate(() => {
  const scene = window.__scene;
  scene.background = new (scene.background.constructor)('#222222');
  scene.traverse(o => { if (o.isMesh) {
    const m = o.material?.name || '';
    if (!['CityWarm','CityCool','CityPale','SignsNeon','NeonPink','NeonCyan','CityLamp'].includes(m)) o.visible = false;
  }});
});
await page.waitForTimeout(300);
await page.screenshot({ path: 'qa/city_windows_only.png' });
await browser.close();
