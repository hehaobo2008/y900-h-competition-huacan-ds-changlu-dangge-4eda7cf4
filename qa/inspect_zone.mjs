import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
page.on('pageerror', e => console.log('ERR', e.message));
await page.goto('http://127.0.0.1:8123/qa/zone/index.html?glb=/assets/zones/rural.glb&cam=90,48,120&target=-15,4,-10&fov=38', { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 60000 });
const out = await page.evaluate(() => {
  const THREE = window.__THREE;
  const scene = window.__scene, camera = window.__camera;
  const big = [];
  scene.traverse(o => {
    if (!o.isMesh) return;
    o.geometry.computeBoundingSphere();
    const bs = o.geometry.boundingSphere.clone().applyMatrix4(o.matrixWorld);
    if (bs.radius > 30) big.push({ name: o.name, mat: o.material?.name, r: +bs.radius.toFixed(1), c: bs.center.toArray().map(v=>+v.toFixed(1)) });
  });
  return { cam: camera.position.toArray(), target: {x: camera.position.x}, big };
});
console.log(JSON.stringify(out, null, 1));
await browser.close();
