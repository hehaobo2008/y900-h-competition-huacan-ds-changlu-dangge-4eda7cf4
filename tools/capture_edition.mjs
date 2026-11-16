import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const out = path.resolve(process.argv[2] || 'qa/edition/final');
const base = process.env.CAPTURE_URL || 'http://127.0.0.1:8137/';
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROME || chromium.executablePath(), args: ['--enable-webgl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
const juryNames={cover:'desktop-cover',card:'desktop-memory',wish:'desktop-wish',end:'desktop-ending'};
async function shot(name){
  await page.screenshot({path:path.join(out,name+'.jpg'),type:'jpeg',quality:94});
  if(process.argv.includes('--jury') && juryNames[name])
    await page.screenshot({path:path.resolve('qa/optimized',juryNames[name]+'.png')});
}
// Positions in the shipped world, shared by every revision. The route frames
// below also exercise the actual authored camera at each chapter entrance.
const views = [
  ['rural', .1, [7.1, 2.05, 56.3], [1.1, 1.23, 51.3], 44],
  ['town', .315, [-.8, 1.85, -450.2], [4.6, 1.32, -457.1], 47],
  ['city', .545, [-4.4, 3.2, -809], [3, 13.5, -854], 51],
  ['rail', .79, [-14, 40.2, -1202], [2.4, 35.2, -1220], 43],
  ['future', .95, [149, 22, -1694], [98, 32, -1760], 45],
];
try {
  await page.goto(new URL('?capture=1', base).href, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__ready || window.__error, null, {timeout: 90000});
  if (await page.evaluate(() => window.__error)) throw Error(await page.evaluate(() => window.__error));
  await page.waitForFunction(() => document.body.dataset.mode === 'landing');
  await page.waitForTimeout(750);
  await shot('cover');
  await page.evaluate(() => { __changlu.start(); __changlu.automaticLetters(false); __changlu.freeze(); });
  const clean = await page.addStyleTag({content: '#app > :not(#world), #world > :not(canvas){display:none!important}'});
  for (const [id, p, pos, target, fov] of views) {
    await page.evaluate(({id,p}) => {
      const a=__changlu; a.state.time=12; a.setProgress(p);
      if (id==='rail' || id==='city') for(let frame=0;frame<(id==='rail'?82:112);frame++) a.step(1/24);
      a.settle(100);
    }, {id,p});
    await shot(id + '-route');
    await page.evaluate(({pos,target,fov}) => {
      const a=__changlu; a.camera.position.set(...pos); a.camera.lookAt(...target); a.camera.fov=fov;
      a.camera.updateProjectionMatrix(); a.camera.updateMatrixWorld(); a.paper.render();
    }, {pos,target,fov});
    await shot(id);
  }
  if (process.argv.includes('--details')) {
    for (const [id,p,pos,target,fov] of [
      ['grain-table',.1,[-.4,1.68,48.45],[-3.04,1.03,46.05],44],
      ['cart-work',.1,[5.55,1.52,54.15],[2.10,1.08,51.83],43],
      ['newsstand',.315,[4.6,1.92,-451.7],[8.2,1.83,-454.7],44],
      ['city-engine',.545,[13.8,18.9,-825],[-4,16,-845],43],
      ['service-work',.95,[119.3,11.55,-1734],[112.5,8.85,-1743],44],
      ['granary-front',.1,[1.6,1.8,54.8],[-4.55,1.72,48.6],51],
      ['produce-stall',.315,[1.75,2.05,-448.5],[-4.15,2.38,-455.85],55],
      ['noodle-shop',.545,[3.7,2.16,-811.5],[10.2,2.5,-824.8],54],
      ['riverside',.79,[-62,37,-1212],[1,33,-1260],49],
      ['south-portal',.79,[7,39,-1185],[0,35.8,-1152],50],
      ['north-portal',.79,[7,39,-1333],[0,35.8,-1368],50],
      ['winter-garden',.95,[140,9.8,-1715],[128,8.8,-1728],56],
    ]) {
      await page.evaluate(({p,pos,target,fov})=>{
        const a=__changlu; a.setProgress(p); a.settle(100);
        a.camera.position.set(...pos); a.camera.lookAt(...target); a.camera.fov=fov;
        a.camera.updateProjectionMatrix(); a.camera.updateMatrixWorld(); a.paper.render();
      },{p,pos,target,fov});
      await shot(id);
    }
  }
  await page.evaluate(() => { __changlu.overview(); __changlu.settle(140); });
  await shot('overview');
  await clean.evaluate(node => node.remove());
  await page.evaluate(() => { __changlu.exitOverview(); __changlu.setProgress(.315); __changlu.advance(.001); __changlu.settle(80); __changlu.showCard(); __changlu.advance(.001); });
  await page.locator('#artifact').click(); await page.locator('#keepLetter').click(); await page.waitForTimeout(650); await shot('card');
  await page.evaluate(() => { __changlu.hideCard(); __changlu.setProgress(1); __changlu.advance(.05); __changlu.settle(100); });
  await page.locator('#knockBtn').click(); await page.locator('#knockBtn').click();
  await page.locator('[data-wish]').first().click(); await page.waitForTimeout(650); await shot('wish');
  await page.evaluate(() => { __changlu.launch(); for(let i=0;i<67;i++) __changlu.step(1/24); __changlu.paper.render(); });
  await page.waitForTimeout(600); await shot('launch');
  await page.evaluate(() => { __changlu.showEnd(); }); await page.waitForTimeout(650); await shot('end');
  fs.writeFileSync(path.join(out,'views.json'), JSON.stringify({views,errors},null,2));
  if(errors.length) throw Error(errors.join('\n'));
} finally { await browser.close(); }
