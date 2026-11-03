import { chromium } from 'playwright';
const glb = process.argv[2] || '/assets/zones/future.glb';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 640, height: 480 } });
await page.goto(`http://127.0.0.1:8123/qa/zone/index.html?glb=${glb}&cam=120,80,160&target=0,20,0&fov=45`, { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 90000 });
const o = await page.evaluate(() => {
  const s = window.__scene; s.updateMatrixWorld(true);
  let min=[1e9,1e9,1e9], max=[-1e9,-1e9,-1e9]; let n=0;
  s.traverse(m => { if(!m.isMesh || !m.geometry) return; m.geometry.computeBoundingBox(); const b=m.geometry.boundingBox; if(!b) return; n++;
    for(const c of [b.min,b.max]){ const v=c.clone().applyMatrix4(m.matrixWorld); for(let i=0;i<3;i++){min[i]=Math.min(min[i],v.getComponent(i));max[i]=Math.max(max[i],v.getComponent(i));}}});
  const names=[]; s.traverse(m=>{ if(m.isMesh && m.geometry) names.push([m.name, m.geometry.attributes.position.count, m.material?.name]); });
  const fx=[]; s.traverse(m=>{ if(m.name.startsWith('FX')) fx.push([m.name, m.position.toArray().map(v=>+v.toFixed(1))]); });
  return {min,max,n,fx,names:names.slice(0,40)};
});
console.log(JSON.stringify(o)); await browser.close();
