import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
page.on('pageerror', e => console.log('ERR', e.message));
await page.goto('http://127.0.0.1:8123/qa/zone/index.html?glb=/assets/zones/city.glb&cam=0,7,140&target=0,10,0&fov=45&night=1', { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 60000 });
const out = await page.evaluate(() => {
  const scene = window.__scene; const res = [];
  const seen = new Set();
  scene.traverse(o => {
    if (!o.isMesh || !o.material) return;
    const m = o.material;
    if (!['CityWarm','CityCool','CityPale','SignsNeon','Signs','NeonPink','NeonCyan','CityLamp'].includes(m.name)) return;
    if (seen.has(m.name)) return; seen.add(m.name);
    o.geometry.computeBoundingSphere();
    res.push({ name: o.name, mat: m.name, type: m.type, emissive: m.emissive?.getHexString(), ei: m.emissiveIntensity,
      map: !!m.map, side: m.side, visible: o.visible, verts: o.geometry.attributes.position?.count,
      bs: o.geometry.boundingSphere?.center.toArray().map(v=>+v.toFixed(1)), br: +o.geometry.boundingSphere?.radius.toFixed(1) });
  });
  return res;
});
console.log(JSON.stringify(out, null, 1));
await page.screenshot({ path: 'qa/city_inspect_day.png' });
await browser.close();
