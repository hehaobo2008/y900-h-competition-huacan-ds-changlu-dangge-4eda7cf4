import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import ffmpegPath from 'ffmpeg-static';
import fs from 'node:fs';
import path from 'node:path';

const FPS = 24, DUR = 102, W = 1920, H = 1080;
const preview = process.env.PREVIEW === '1';
const out = path.resolve('dist', '山河织路-演示片.mp4');

const chapters = [
  { id: 'rural', num: '壹', year: '1980s', title: '田埂晨', line: '路是走出来的。', t0: 5.6, t1: 11.8, dark: false },
  { id: 'town', num: '贰', year: '1990s', title: '街市暮', line: '路通向更大的世界。', t0: 19.6, t1: 23.4, dark: false },
  { id: 'city', num: '叁', year: '2010s', title: '城夜雨', line: '路把远方变成日常。', t0: 33.6, t1: 39.8, dark: true },
  { id: 'rail', num: '肆', year: '2020s', title: '山河速', line: '路让山河彼此相拥。', t0: 47.6, t1: 54.0, dark: true },
  { id: 'future', num: '伍', year: '未来', title: '星河远', line: '路从脚下，通向星辰。', t0: 61.6, t1: 68.0, dark: true },
];
function win(t, a, b, f = 0.7) { return Math.max(0, Math.min(1, (t - a) / f, (b - t) / f)); }
function captionAt(t) {
  for (const c of chapters) {
    const o = win(t, c.t0, c.t1);
    if (o > 0) return { ...c, o };
  }
  return null;
}

const KP = [
  [0,0],[5.4,.045],[8,.10],[11.5,.10],[18.6,.215],
  [19,.25],[22,.315],[25.5,.315],[32.6,.43],
  [33,.47],[36,.545],[39.5,.545],[46.6,.65],
  [47,.69],[50.5,.79],[55,.79],[60.6,.86],
  [61,.90],[64,.95],[68.5,.95],[74.8,1.0],[102,1.0],
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

const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.log('PAGEERR', e.message));
page.on('console', m => { if (m.type() === 'error') console.log('CERR', m.text().slice(0, 200)); });
await page.goto('http://127.0.0.1:8124/?capture=1', { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 120000 });
await page.waitForTimeout(1700);
await page.evaluate(() => {
  const st = document.createElement('style');
  st.textContent = `
    #loading,#chapter,#scrollHint,#toast{display:none!important}
    *{transition:none!important;animation:none!important}
    #vcap{position:absolute;left:clamp(40px,7.2vw,132px);bottom:16.5vh;z-index:26;pointer-events:none;opacity:0;max-width:560px}
    #vcap .vtop{display:flex;align-items:baseline;gap:14px;margin-bottom:9px}
    #vcap .vnum{font-size:21px;letter-spacing:.1em;color:#a8332a;border-left:2px solid #a8332a;padding-left:12px;line-height:1}
    #vcap .vyear{font-family:var(--sans);font-size:10px;letter-spacing:.24em;color:rgba(35,31,25,.55)}
    #vcap .vtitle{font-size:clamp(40px,4.2vw,58px);letter-spacing:.12em;line-height:1.08;margin:0 0 10px;color:#231f19;text-shadow:0 0 30px rgba(243,236,223,.7)}
    #vcap .vline{font-size:13px;letter-spacing:.14em;line-height:1.9;color:rgba(35,31,25,.7);text-shadow:0 0 22px rgba(243,236,223,.8)}
    #vcap.dark .vnum{color:#ff8a6a;border-color:#ff8a6a}
    #vcap.dark .vyear{color:rgba(243,236,223,.7)}
    #vcap.dark .vtitle{color:#f3ecdf;text-shadow:0 2px 30px rgba(0,0,0,.55)}
    #vcap.dark .vline{color:rgba(243,236,223,.78);text-shadow:0 2px 18px rgba(0,0,0,.6)}
    #vhint{position:absolute;left:50%;bottom:11vh;transform:translateX(-50%);z-index:27;pointer-events:none;opacity:0;
      background:rgba(20,17,13,.82);color:#f3ecdf;font-family:var(--sans);font-size:11px;letter-spacing:.16em;padding:11px 20px;border-radius:2px}
  `;
  document.head.appendChild(st);
  const cap = document.createElement('div'); cap.id = 'vcap'; document.getElementById('app').appendChild(cap);
  const hint = document.createElement('div'); hint.id = 'vhint'; hint.textContent = '滚动 / 触摸上滑 · 前进　　拖动 · 回望　　点击拾光 · 停留'; document.getElementById('app').appendChild(hint);
  window.__changlu.freeze();
});
async function capFrame(p, cap, hintOp, zoom) {
  await page.evaluate(({ dt, p, cap, hintOp, zoom }) => {
    if (p != null) window.__changlu.scrollTo(p);
    window.__changlu.advance(dt);
    const el = document.getElementById('vcap');
    if (cap) {
      el.className = cap.dark ? 'dark' : '';
      el.innerHTML = `<div class="vtop"><span class="vnum">${cap.num}</span><span class="vyear">${cap.year}</span></div><div class="vtitle">${cap.title}</div><div class="vline">${cap.line}</div>`;
      el.style.opacity = cap.o.toFixed(3);
    } else el.style.opacity = '0';
    document.getElementById('vhint').style.opacity = hintOp.toFixed(3);
    document.getElementById('gl').style.transform = zoom ? `scale(${zoom})` : 'none';
  }, { dt: 1 / FPS, p, cap, hintOp, zoom });
}

const score = path.resolve('production', 'score.wav');
const ff = preview ? null : spawn(ffmpegPath, [
  '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-i', score,
  '-map', '0:v:0', '-map', '1:a:0',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
  '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
  '-shortest', '-movflags', '+faststart', out,
], { stdio: ['pipe', 'inherit', 'inherit'] });
const ffDone = ff ? new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c)))) : null;

const total = Math.round((preview ? 99 : DUR) * FPS);
const previewTimes = new Set([2, 8, 12, 17, 22, 26, 30, 37, 42, 52, 58, 65, 70, 76, 80, 84, 91, 98].map(t => Math.round(t * FPS)));
const t0 = Date.now();
for (let i = 0; i < total; i++) {
  const t = i / FPS;
  if (i === Math.round(5 * FPS)) {
    await page.evaluate(() => { window.__changlu.start(); window.__changlu.setProgress(.045); window.__changlu.settle(45); document.getElementById('gl').style.transform = 'none'; });
  }
  if (i === Math.round(22.6 * FPS)) await page.evaluate(() => window.__changlu.showCard());
  if (i === Math.round(27.4 * FPS)) await page.evaluate(() => window.__changlu.hideCard());
  if (i === Math.round(78.2 * FPS)) await page.evaluate(() => window.__changlu.launch());
  if (i === Math.round(90.0 * FPS)) await page.evaluate(() => {
    const z = window.__changlu.zones.future;
    if (z && z.rocket) z.rocket.position.y = 7;
    window.__changlu.overview();
  });
  if (i === Math.round(96.0 * FPS)) await page.evaluate(() => { window.__changlu.exitOverview(); window.__changlu.showEnd(); });
  const p = t >= 5.4 ? progressAt(t) : null;
  const cap = (t >= 22.5 && t <= 27.6) ? null : (t >= 5.6 ? captionAt(t) : null);
  const hintOp = t >= 6.3 && t < 9.5 ? win(t, 6.3, 9.5, 0.6) : 0;
  const zoom = t < 5 ? 1 + 0.025 * (t / 5) : null;
  if (preview && !previewTimes.has(i)) {
    await page.evaluate(({ dt, p }) => {
      if (p != null) window.__changlu.scrollTo(p);
      window.__changlu.step(dt);
    }, { dt: 1 / FPS, p });
    continue;
  }
  await capFrame(p, cap, hintOp, zoom);
  if (preview) {
    await page.screenshot({ path: `qa/video_preview_${String(t.toFixed(1)).padStart(5,'0')}.png` });
    continue;
  }
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 120 === 0) console.log('frame', i, '/', total, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
if (ff) { ff.stdin.end(); await ffDone; console.log('VIDEO', out, fs.statSync(out).size); }
await browser.close();
