import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const browser = await chromium.launch({
  executablePath: process.env.CHROME || chromium.executablePath(),
  args: ['--enable-webgl', '--ignore-gpu-blocklist'],
});
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
try {
  await page.goto(process.env.CAPTURE_URL || 'http://127.0.0.1:8137/', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__ready);
  await page.evaluate(()=>{__changlu.start();__changlu.automaticLetters(false);});
  const hardware = await page.evaluate(() => {
    const gl = __changlu.renderer.getContext();
    const debug = gl.getExtension('WEBGL_debug_renderer_info');
    return { gpu: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
      browser: navigator.userAgent, viewport: [innerWidth, innerHeight], dpr: devicePixelRatio };
  });
  const chapters = [], crossings = [];
  const stops=[['rural',.1],['town',.315],['city',.545],['rail',.79],['future',.95]];
  const flights=[['rural-town',.223],['town-city',.438],['city-rail',.658],['rail-future',.874]];
  for (const [chapter, progress] of [...stops,...flights]) {
    const moving=chapter.includes('-');
    await page.evaluate(p => { __changlu.setProgress(p); __changlu.settle(80); }, progress);
    await page.waitForTimeout(700);
    if(moving) await page.locator('#autoBtn').click();
    const sample = await page.evaluate(() => new Promise(resolve => {
      const elapsed = [];
      let start, previous;
      function measure(now) {
        if (start === undefined) { start = previous = now; requestAnimationFrame(measure); return; }
        elapsed.push(now - previous);
        previous = now;
        if (now - start < 4000) { requestAnimationFrame(measure); return; }
        elapsed.sort((a,b) => a - b);
        const rounded = number => Number(number.toFixed(1));
        resolve({ frames: elapsed.length, seconds: rounded((now - start)/1000),
          fps: rounded(elapsed.length * 1000 / (now - start)), medianMs: rounded(elapsed[Math.floor(elapsed.length / 2)]),
          p95Ms: rounded(elapsed[Math.floor(elapsed.length * .95)]),
          letterInReach:document.querySelector('#memoryBtn').checkVisibility() && !document.querySelector('#memoryBtn').closest('[inert]'),lastProgress:__changlu.state.progress });
      }
      requestAnimationFrame(measure);
    }));
    (moving ? crossings : chapters).push({chapter,progress,...sample});
    if(moving) await page.locator('#autoBtn').click();
  }
  for (const row of [...chapters,...crossings]) assert(row.letterInReach,row.chapter+' has an accessible archive entry');
  for (const row of crossings) assert(row.lastProgress>row.progress+.007,row.chapter+' advances during frame-time sample');
  const limits = await page.evaluate(() => [.44,.95].map(p => {
    __changlu.setProgress(p); __changlu.settle(5);
    const {rail,city}=__changlu.zones;
    const span=(object,offset)=>object.userData.ends.map(end=>+(offset+end).toFixed(3));
    return {hsr:span(rail.hsr,rail.hsr.position.z+1260),harmony:span(rail.harmony,rail.harmony.position.z+1260),
      green:span(city.train,city.train.position.x)};
  }));
  assert(limits.every(({hsr,harmony,green})=>[hsr,harmony].every(([lo,hi])=>hi-lo>265&&hi-lo<275)&&green[1]-green[0]>206&&green[1]-green[0]<218),'Native train lengths match the revised consists');
  assert.deepEqual(errors, []);
  const avenueSurfaces=await page.evaluate(()=>{
    const a=__changlu,city=a.zones.city;
    const sample=()=>({wet:city.road.visible,dry:city.asphalt.filter(o=>o.visible).length,originals:city.asphalt.length});
    a.setProgress(.55);a.settle(75);const street=sample();
    a.overview();a.settle(120);return {street,overview:sample()};
  });
  assert(avenueSurfaces.street.wet && avenueSurfaces.street.dry===0);
  assert(!avenueSurfaces.overview.wet && avenueSurfaces.overview.dry===avenueSurfaces.overview.originals && avenueSurfaces.overview.dry>0);
  const report = {hardware,chapters,crossings,bridgeOffsetsMetres:limits,avenueSurfaces,errors};
  fs.writeFileSync('qa/edition/performance.json', JSON.stringify(report,null,2) + '\n');
  console.log(JSON.stringify(report));
} finally { await browser.close(); }
