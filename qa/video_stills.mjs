import { chromium } from 'playwright';

const W = 1920, H = 1080;
const chapters = [
  { id: 'rural', num: '壹', year: '1980s', title: '田埂晨', line: '路是走出来的。', t0: 5.6, t1: 11.8, dark: false },
  { id: 'town', num: '贰', year: '1990s', title: '街市暮', line: '路通向更大的世界。', t0: 19.6, t1: 23.4, dark: false },
  { id: 'city', num: '叁', year: '2010s', title: '城夜雨', line: '路把远方变成日常。', t0: 33.6, t1: 39.8, dark: true },
  { id: 'rail', num: '肆', year: '2020s', title: '山河速', line: '路让山河彼此相拥。', t0: 47.6, t1: 54.0, dark: true },
  { id: 'future', num: '伍', year: '未来', title: '星河远', line: '路从脚下，通向星辰。', t0: 61.6, t1: 68.0, dark: true },
];
const win = (t, a, b, f = 0.7) => Math.max(0, Math.min(1, (t - a) / f, (b - t) / f));
const captionAt = (t) => { for (const c of chapters) { const o = win(t, c.t0, c.t1); if (o > 0) return { ...c, o }; } return null; };
const KP = [[0,0],[5.4,.045],[8,.10],[11.5,.10],[18.6,.215],[19,.25],[22,.315],[25.5,.315],[32.6,.43],[33,.47],[36,.545],[39.5,.545],[46.6,.65],[47,.69],[50.5,.79],[55,.79],[60.6,.86],[61,.90],[64,.95],[68.5,.95],[74.8,1.0],[102,1.0]];
function progressAt(t) {
  for (let i = 0; i < KP.length - 1; i++) {
    const [a, pa] = KP[i], [b, pb] = KP[i + 1];
    if (t >= a && t <= b) { const u = (t - a) / (b - a); const e = u * u * (3 - 2 * u); return pa + (pb - pa) * e; }
  }
  return 1;
}

const b = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
p.on('pageerror', (e) => console.log('PAGEERR', e.message));
await p.goto('http://127.0.0.1:8124/?capture=1&stills=1&v=' + Date.now(), { waitUntil: 'networkidle' });
await p.waitForFunction(() => window.__ready, null, { timeout: 120000 });
await p.waitForTimeout(1500);
await p.evaluate(() => {
  const st = document.createElement('style');
  st.textContent = `
    #loading,#chapter,#scrollHint,#toast{display:none!important}
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
  `;
  document.head.appendChild(st);
  const cap = document.createElement('div'); cap.id = 'vcap'; document.getElementById('app').appendChild(cap);
  window.__changlu.freeze(); window.__changlu.start();
});

async function at(t, name, steps = 110) {
  const p0 = progressAt(t);
  const cap = captionAt(t);
  await p.evaluate(({ p0, cap, steps }) => {
    const c = window.__changlu;
    c.setProgress(p0);
    c.settle(steps);
    c.advance(1 / 24);
    const el = document.getElementById('vcap');
    if (cap) {
      el.className = cap.dark ? 'dark' : '';
      el.innerHTML = `<div class="vtop"><span class="vnum">${cap.num}</span><span class="vyear">${cap.year}</span></div><div class="vtitle">${cap.title}</div><div class="vline">${cap.line}</div>`;
      el.style.opacity = cap.o.toFixed(3);
    } else el.style.opacity = 0;
  }, { p0, cap, steps });
  await p.waitForTimeout(250);
  await p.screenshot({ path: `qa/vstill_${name}.png` });
  console.log('still', name, p0.toFixed(3));
}

for (const [t, name] of [[8,'08'],[12,'12'],[17,'17'],[22,'22'],[30,'30'],[37,'37'],[42,'42'],[52,'52'],[58,'58'],[65,'65'],[70,'70'],[76,'76'],[84,'84']]) {
  if (t === 22) {
    await p.evaluate(() => window.__changlu.showCard());
  }
  await at(t, name);
  if (t === 22) await p.evaluate(() => window.__changlu.hideCard());
}

// finale prompt / launch
await at(77, '77');
await p.evaluate(() => { window.__changlu.launch(); });
await p.waitForTimeout(2600);
await p.evaluate(() => document.getElementById('vcap').style.opacity = 0);
await p.screenshot({ path: 'qa/vstill_80.png' });
await p.evaluate(() => { for (let i = 0; i < 200; i++) window.__changlu.advance(1 / 24); });
await p.screenshot({ path: 'qa/vstill_88.png' });

// overview
await p.evaluate(() => { window.__changlu.setProgress(0.9); window.__changlu.settle(30); window.__changlu.overview(); for (let i = 0; i < 160; i++) window.__changlu.advance(1 / 24); });
await p.waitForTimeout(400);
await p.screenshot({ path: 'qa/vstill_92.png' });

// end
await p.evaluate(() => { window.__changlu.exitOverview(); window.__changlu.showEnd(); });
await p.waitForTimeout(1500);
await p.screenshot({ path: 'qa/vstill_98.png' });
await b.close();
