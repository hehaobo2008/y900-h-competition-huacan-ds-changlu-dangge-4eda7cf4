import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
import {crossings} from '../src/journey.js';

// Include the first visible frame of the incoming island. Sampling only after
// arriving in the middle of a flight misses texture uploads and new GPU programs.
const browser = await chromium.launch({executablePath:process.env.CHROME || chromium.executablePath(),
  args:['--enable-webgl','--ignore-gpu-blocklist']});
try {
  const page = await browser.newPage({viewport:{width:1600,height:900},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(process.env.CAPTURE_URL || 'http://127.0.0.1:8137/');
  await page.waitForFunction(() => window.__ready, null, {timeout:120000});
  const readyMs=await page.evaluate(()=>Math.round(performance.now()));
  await page.locator('#loading').waitFor({state:'hidden'});
  await page.evaluate(()=>__changlu.automaticLetters(false));
  await page.locator('#startBtn').click();
  if(process.argv.includes('--skip')) await page.locator('#skipIntro').click();
  await page.waitForFunction(()=>__changlu.state.mode==='travel');
  await page.evaluate(()=>__changlu.freeze());
  const flights=[];
  for (const [start,end] of crossings) {
    const row = await page.evaluate(async ({start,end}) => {
      const app=__changlu, samples=[];
      app.setProgress(start-.014);app.advance(1/60);
      const frame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
      for(let i=0;i<12;i++) await frame();
      let previous=await frame();
      const firstPrograms=app.renderer.info.programs.length;
      for(let i=0;i<100;i++){
        const p=start-.014+(end-start+.014)*i/99;
        const cpu=performance.now();app.setProgress(p);app.advance(1/60);
        const cpuMs=performance.now()-cpu;
        const now=await frame();
        samples.push({p:+p.toFixed(4),ms:+(now-previous).toFixed(1),cpuMs:+cpuMs.toFixed(1)});
        previous=now;
      }
      const ms=samples.map(s=>s.ms).sort((a,b)=>a-b);
      const gl=app.renderer.getContext(),dbg=gl.getExtension('WEBGL_debug_renderer_info');
      return {start,end,gpu:dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),
        p50Ms:ms[50],p95Ms:ms[95],worst:samples.reduce((a,b)=>a.ms>b.ms?a:b),
        over100:samples.filter(s=>s.ms>100).length,newPrograms:app.renderer.info.programs.length-firstPrograms};
    },{start,end});
    console.log(JSON.stringify(row));flights.push(row);
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(process.argv[2] || 'qa/edition/departures.json',JSON.stringify({readyMs,skippedPrologue:process.argv.includes('--skip'),viewport:[1600,900],flights,errors},null,2)+'\n');
}finally{await browser.close();}
