import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 800, height: 600 } });
await page.goto('http://127.0.0.1:8123/qa/zone/index.html?glb=/assets/vehicles/rocket.glb&cam=40,30,60&target=0,30,0&fov=40', { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 60000 });
const o = await page.evaluate(() => { const s=window.__scene; let min=[1e9,1e9,1e9], max=[-1e9,-1e9,-1e9]; s.traverse(m=>{ if(!m.isMesh) return; m.geometry.computeBoundingBox(); const b=m.geometry.boundingBox; const w=m.matrixWorld; for(const c of [b.min,b.max]){ const v=c.clone().applyMatrix4(w); for(let i=0;i<3;i++){min[i]=Math.min(min[i],v.getComponent(i));max[i]=Math.max(max[i],v.getComponent(i));}} }); return {min,max}; });
console.log(JSON.stringify(o)); await browser.close();
