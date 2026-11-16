import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import ffmpegPath from 'ffmpeg-static';
import fs from 'node:fs';
import path from 'node:path';
import { letters } from '../src/letters.js';

const FPS = 24, DUR = 102, W = 1920, H = 1080;
const preview = process.env.PREVIEW === '1';
const out = path.resolve('dist', '山河织路-演示片.mp4');
const production = path.resolve('production');
const master = path.join(production, 'film_master.mp4');
const delivery = path.join(production, 'film_delivery.mp4');
const staging = preview ? null : fs.mkdtempSync(path.join(production, '.film-'));

const chapters = [
  { num: '壹', year: '1980s', title: '田埂晨', t0: 11.2, t1: 14.4, dark: false },
  { num: '贰', year: '1990s', title: '街市暮', t0: 20.2, t1: 23.4, dark: false },
  { num: '叁', year: '2010s', title: '城夜雨', t0: 36.0, t1: 41.5, dark: true },
  { num: '肆', year: '2020s', title: '山河速', t0: 48.4, t1: 56.9, dark: false },
  { num: '伍', year: '未来', title: '星河远', t0: 62.4, t1: 68.0, dark: true },
].map((chapter, i) => ({ ...chapter, byline: letters[i].distance, setting:letters[i].setting, line: letters[i].routeLine }));
function win(t, a, b, f = 0.7) { return Math.max(0, Math.min(1, (t - a) / f, (b - t) / f)); }
function captionAt(t) {
  for (const c of chapters) {
    const o = win(t, c.t0, c.t1);
    if(o>0 && c.num==='肆' && t<54.9) return {...c,byline:'山河大桥',setting:'',line:'',o:Math.min(o,win(t,c.t0,54.9,.5))};
    if(o>0 && c.num==='肆') return {...c,setting:'',o:Math.min(o,win(t,54.9,c.t1,.4))};
    if (o > 0) return { ...c, o };
  }
  return null;
}

const KP = [
  [0,.10],[11.8,.10],[14.2,.197],[15.4,.200],[20.8,.270],
  [22.05,.315],[27.4,.315],[29.9,.405],[31.1,.405],[35.7,.504],
  [37.2,.545],[39.2,.553],[41.3,.597],[43.3,.629],[48.0,.715],
  [50.5,.79],[53.8,.806],[56,.847],[57,.847],[62,.930],
  [64,.937],[66,.948],[68.5,.961],[70.5,.968],[72.2,.974],[73.4,.983],[74.8,1.0],[102,1.0],
];
function progressAt(t) {
  for (let i = 0; i < KP.length - 1; i++) {
    const [a, pa] = KP[i], [b, pb] = KP[i + 1];
    if (t >= a && t <= b) {
      const u = (t - a) / Math.max(1e-6, b - a);
      const e = u * u * (3 - 2 * u);
      return pa + (pb - pa) * e;
    }
  }
  return 1;
}

// Edited inserts are live views of the same scene and materials as the visitor's route.
const inserts = [
  [11.5, 12.8, .1, [1.6,1.8,54.8], [-4.55,1.72,48.6], 51],
  [27.6, 28.9, .315, [1.75,2.05,-448.5], [-4.15,2.38,-455.85], 55],
  [39.5, 41.5, .554, [2.8,3.05,-816.7], [1.7,11.4,-841.9], 55],
  [51.7, 53.7, .79, [-45,47,-1192], [2.4,32,-1256], 47],
  [70.8, 72.1, .972, [140,10.5,-1714], [128,9.4,-1728], 55],
];
function insertAt(t) {
  const shot = inserts.find(([start,end]) => t >= start && t < end);
  return shot && { p:shot[2], from:shot[3], look:shot[4], fov:shot[5] - 2*(t-shot[0])/(shot[1]-shot[0]) };
}

const browser = await chromium.launch({ executablePath: process.env.CHROME || chromium.executablePath(), args: ['--enable-webgl','--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
await page.addInitScript(() => {
  let seed = 71949;
  Math.random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
});
await page.goto(new URL('?capture=1', process.env.CAPTURE_URL || 'http://127.0.0.1:8137/').href, { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 120000 });
await page.waitForTimeout(1700);
await page.evaluate(() => {
  const st = document.createElement('style');
  st.textContent = `
    #loading,#chapter,#scrollHint,#toast{display:none!important}
    .film-landscape #hud,.film-landscape #timeline,.film-landscape #travelMeta{visibility:hidden!important}
    .film-intro #travelMeta{visibility:visible!important}
    *{transition:none!important;animation:none!important}
    #vcap{position:absolute;left:clamp(40px,7.2vw,132px);bottom:16.5vh;z-index:26;pointer-events:none;opacity:0;max-width:560px}
    #vcap{padding:18px 32px 18px 22px;background:linear-gradient(90deg,rgba(247,239,223,.91),rgba(247,239,223,.72) 75%,transparent)}
    #vcap.dark{background:linear-gradient(90deg,rgba(15,29,39,.86),rgba(15,29,39,.56) 75%,transparent)}
    #vcap .vtop{display:flex;align-items:baseline;gap:14px;margin-bottom:9px}
    #vcap .vnum{font-size:21px;letter-spacing:.1em;color:#a8332a;border-left:2px solid #a8332a;padding-left:12px;line-height:1}
    #vcap .vyear{font-family:var(--sans);font-size:16px;letter-spacing:.07em;color:rgba(35,31,25,.8)}
    #vcap .vtitle{font-size:clamp(40px,4.2vw,58px);letter-spacing:.12em;line-height:1.08;margin:0 0 10px;color:#231f19;text-shadow:0 0 30px rgba(243,236,223,.7)}
    #vcap .vline{font-size:22px;letter-spacing:.04em;line-height:1.6;color:#403c34}
    #vcap .vsetting{font:16px/1.6 var(--sans);margin-bottom:3px;color:#544839}
    #vcap.dark .vsetting{color:#dfded2}
    #vcap.dark .vnum{color:#ff8a6a;border-color:#ff8a6a}
    #vcap.dark .vyear{color:rgba(243,236,223,.7)}
    #vcap.dark .vtitle{color:#f3ecdf;text-shadow:0 2px 30px rgba(0,0,0,.55)}
    #vcap.dark .vline{color:rgba(243,236,223,.78);text-shadow:0 2px 18px rgba(0,0,0,.6)}
    #vhint{position:absolute;left:50%;bottom:11vh;transform:translateX(-50%);z-index:27;pointer-events:none;opacity:0;
      background:rgba(20,17,13,.82);color:#f3ecdf;font-family:var(--sans);font-size:19px;letter-spacing:.12em;padding:12px 22px;border-radius:2px}
  `;
  document.head.appendChild(st);
  const cap = document.createElement('div'); cap.id = 'vcap'; document.getElementById('app').appendChild(cap);
  const hint = document.createElement('div'); hint.id = 'vhint'; hint.textContent = '轻滑前行　　轻点票面翻阅'; document.getElementById('app').appendChild(hint);
  window.__changlu.automaticLetters(false); window.__changlu.freeze();
});
async function capFrame(p, cap, hintOp, zoom, cut, filmTime) {
  await page.evaluate(({ dt, p, cap, hintOp, zoom, cut, sec }) => {
    const a = window.__changlu;
    if (p != null && !a.state.modal) a.setProgress(cut ? cut.p : p);
    if (cut) {
      a.step(dt);
      const c=a.camera, pos=c.position.clone(), q=c.quaternion.clone(), f=c.fov;
      c.position.set(...cut.from); c.lookAt(...cut.look); c.fov=cut.fov;
      c.updateProjectionMatrix(); c.updateMatrixWorld(); a.paper.render();
      c.position.copy(pos); c.quaternion.copy(q); c.fov=f;
      c.updateProjectionMatrix(); c.updateMatrixWorld();
    } else a.advance(dt);
    const el = document.getElementById('vcap');
    if (cap) {
      el.className = cap.dark ? 'dark' : '';
      el.innerHTML = `<div class="vtop"><span class="vnum">${cap.num}</span><span class="vyear">${cap.year} · ${cap.byline}</span></div><div class="vtitle">${cap.title}</div><div class="vsetting">${cap.setting}</div><div class="vline">${cap.line}</div>`;
      el.style.opacity = cap.o.toFixed(3);
    } else el.style.opacity = '0';
    document.body.classList.toggle('film-landscape', document.body.dataset.mode === 'travel' && !document.getElementById('ticketLayer').classList.contains('show'));
    document.body.classList.toggle('film-intro',hintOp>0);
    document.getElementById('vhint').style.opacity = hintOp.toFixed(3);
    document.getElementById('gl').style.transform = zoom ? `scale(${zoom})` : 'none';
  }, { dt: 1 / FPS, p, cap, hintOp, zoom, cut, sec:filmTime });
}

const score = path.resolve('production', 'score.wav');
const ff = preview ? null : spawn(ffmpegPath, [
  '-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-i', score,
  '-map', '0:v:0', '-map', '1:a:0',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
  '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
  '-shortest', '-movflags', '+faststart', path.join(staging, 'master.mp4'),
], { stdio: ['pipe', 'inherit', 'inherit'] });
const ffDone = ff ? new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c)))) : null;

const total = Math.round((preview ? 99 : DUR) * FPS);
const previewTimes = new Set([2, 8, 12, 17, 22, 26, 30, 37, 42, 52, 58, 65, 70, 76, 80, 84, 91, 98].map(t => Math.round(t * FPS)));
const t0 = Date.now();
for (let i = 0; i < total; i++) {
  const t = i / FPS;
  if(i===Math.round(1.5*FPS)) await page.evaluate(()=>window.__changlu.prologue());
  // Time elides between the broadside insert and the reverse shot of the tail.
  if(i===Math.round(53.7*FPS)) await page.evaluate(()=>{for(let j=0;j<200;j++)__changlu.step(1/24);});
  if (i === Math.round(22.05 * FPS)) await page.evaluate(() => window.__changlu.receiveLetter());
  if (i === Math.round(23.6 * FPS)) await page.evaluate(() => document.getElementById('ticketFront').click());
  if (i === Math.round(25.4 * FPS)) await page.evaluate(() => document.getElementById('keepLetter').click());
  if (i === Math.round(27.4 * FPS)) await page.evaluate(() => window.__changlu.hideCard());
  if (i === Math.round(75.6 * FPS)) await page.evaluate(() => document.getElementById('ticketFront').click());
  if (i === Math.round(76.5 * FPS)) await page.evaluate(() => document.querySelector('[data-wish]').click());
  if (i === Math.round(78.2 * FPS)) await page.evaluate(() => document.getElementById('launchBtn').click());
  if (i === Math.round(99.3 * FPS)) await page.evaluate(() => window.__changlu.showEnd());
  const p = t >= 11.2 ? progressAt(t) : null;
  const cap = (t >= 22.05 && t <= 27.6) ? null : (t >= 5.6 ? captionAt(t) : null);
  const hintOp = 0;
  const zoom = t < 1.5 ? 1 + .008*t/1.5 : null;
  if (preview && !previewTimes.has(i)) {
    await page.evaluate(({ dt, p }) => {
      if (p != null) window.__changlu.scrollTo(p);
      window.__changlu.step(dt);
    }, { dt: 1 / FPS, p });
    continue;
  }
  await capFrame(p, cap, hintOp, zoom, insertAt(t),t);
  if (preview) {
    await page.screenshot({ path: `qa/video_preview_${String(t.toFixed(1)).padStart(5,'0')}.png` });
    continue;
  }
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 120 === 0) console.log('frame', i, '/', total, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
await browser.close();
if (errors.length) throw Error(errors.join('\n'));
if (ff) {
  ff.stdin.end(); await ffDone;
  const newMaster = path.join(staging,'master.mp4'), newDelivery = path.join(staging,'delivery.mp4');
  const encode = spawn(ffmpegPath, ['-hide_banner','-loglevel','error','-y','-i',newMaster,
    '-c:v','libx264','-preset','medium','-crf','22','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',newDelivery], {stdio:'inherit'});
  await new Promise((resolve,reject) => encode.once('close',code => code ? reject(Error('delivery encode ' + code)) : resolve()));
  fs.renameSync(newMaster,master); fs.renameSync(newDelivery,delivery);
  fs.copyFileSync(delivery,out);
  fs.rmdirSync(staging);
  console.log('VIDEO',out,fs.statSync(out).size);
}
