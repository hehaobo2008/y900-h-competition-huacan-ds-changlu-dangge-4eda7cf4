import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

// These poses are world-space metres in the actual five-island app.
const stage = process.argv[2] || 'baseline';
const base = process.env.CAPTURE_URL || 'http://127.0.0.1:18371/';
const out = path.join('qa', 'rural_realism', stage);
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROME || 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe',
  args: ['--use-angle=default', '--enable-webgl', '--ignore-gpu-blocklist'],
});
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.goto(base + '?capture=1', { waitUntil: 'networkidle', timeout: 90000 });
await page.waitForFunction(() => window.__ready || window.__error, null, { timeout: 90000 });
if (await page.evaluate(() => window.__error)) throw new Error(await page.evaluate(() => window.__error));
// boot() schedules its landing transition after __ready; finish it first.
await page.waitForTimeout(1600);
await page.evaluate(() => {
  __changlu.start(); __changlu.freeze(); __changlu.setProgress(.1); __changlu.settle(80);
  document.body.classList.add('photo');
  document.querySelectorAll('#landing,#loading,#chapter,#scrollHint,#hotspot,#toast,#hud,#timeline,#travelMeta')
    .forEach(e => { if (e) e.style.display = 'none'; });
});
const views = [
  ['01_overview', [260, 260, 350], [0, 0, 0], 44],
  ['02_road', [0, 1.7, 74], [0, 1.55, 30], 52],
  ['03_cart_front', [7.4, 2.0, 57.7], [2.2, 1.1, 52], 44],
  ['04_cart_side', [-4.3, 1.4, 53.8], [2.2, 1.05, 52], 44],
  ['05_courtyard', [-10, 1.7, 8], [-24, 2.2, -2], 48],
  ['06_water', [30, 1.8, -12], [48, 1, -38], 48],
  ['07_wheel_detail', [4.55, 1.05, 53.6], [3.15, .68, 52], 42],
  ['08_cart_rear', [1.0, 1.65, 56], [2.2, .95, 52], 46],
  ['09_house_detail', [-22, 1.7, 7.6], [-24, 1.55, 1.6], 45],
];
for (const [name, pos, look, fov] of views) {
  await page.evaluate(({ pos, look, fov }) => {
    const a = window.__changlu;
    a.camera.position.set(...pos);
    a.camera.fov = fov; a.camera.updateProjectionMatrix();
    a.camera.lookAt(...look); a.camera.updateMatrixWorld();
    a.paper.render();
  }, { pos, look, fov });
  await page.screenshot({ path: path.join(out, name + '.png') });
}
const info = await page.evaluate(() => {
  const a = window.__changlu;
  const gl = a.renderer.getContext();
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  const vehicle = a.zones.rural.vehicle;
  a.renderer.info.autoReset = false;
  a.renderer.info.reset();
  a.paper.render();
  return {
    userAgent: navigator.userAgent,
    webgl: gl.getParameter(gl.VERSION),
    vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : null,
    renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : null,
    size: [a.renderer.domElement.width, a.renderer.domElement.height],
    pixelRatio: a.renderer.getPixelRatio(),
    cameraNearFar: [a.camera.near, a.camera.far],
    cartPosition: vehicle.position.toArray(),
    cartRotationY: vehicle.rotation.y,
    calls: a.renderer.info.render.calls,
    triangles: a.renderer.info.render.triangles,
  };
});
fs.writeFileSync(path.join(out, 'capture.json'), JSON.stringify({ info, errors, views }, null, 2));
console.log(JSON.stringify({ output: out, info, errors }, null, 2));
await browser.close();
