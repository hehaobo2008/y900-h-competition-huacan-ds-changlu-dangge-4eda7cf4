import { chromium } from 'playwright';

const exe = 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
const browser = await chromium.launch({ executablePath: exe });
const errs = [];

async function run(w, h, tag, full = true) {
  const ctx = await browser.newContext({
    viewport: { width: w, height: h }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errs.push(tag + ' PAGEERR ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(tag + ' CERR ' + m.text().slice(0, 200)); });
  await page.goto('http://127.0.0.1:8124/?final=' + tag + '&v=' + Date.now(), { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__ready, null, { timeout: 120000 });
  await page.waitForTimeout(1500);

  const metrics = () => page.evaluate(() => {
    const box = (s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return { x: +r.x.toFixed(0), y: +r.y.toFixed(0), w: +r.width.toFixed(0), h: +r.height.toFixed(0), op: +cs.opacity, disp: cs.display }; };
    return {
      vw: innerWidth, vh: innerHeight, scrollW: document.documentElement.scrollWidth,
      dark: document.body.classList.contains('dark-scene'),
      mode: window.__changlu.state.mode, chapter: window.__changlu.state.chapter,
      pr: window.__changlu.renderer.getPixelRatio(), bloom: window.__changlu.paper.bloom.enabled,
      landing: box('#landing'), start: box('#startBtn'), hud: box('#hud'),
      buttons: [...document.querySelectorAll('.hud-actions button')].map(e => { const r = e.getBoundingClientRect(); return { w: +r.width.toFixed(0), h: +r.height.toFixed(0) }; }),
      card: box('#card'), close: box('#cardClose'), ovBack: box('#ovBack'), finale: box('#finale'), end: box('#endCard'),
      labels: [...document.querySelectorAll('.ov-label')].map(e => { const r = e.getBoundingClientRect(); return { t: e.textContent.trim().slice(0, 2), x: +r.x.toFixed(0), y: +r.y.toFixed(0), w: +r.width.toFixed(0) }; }),
      sound: window.__changlu.soundInfo(),
    };
  });

  console.log(tag + '_landing ' + JSON.stringify(await metrics()));
  await page.screenshot({ path: `qa/final_${tag}_landing.png` });
  await page.tap('#startBtn');
  await page.waitForTimeout(1800);
  await page.evaluate(() => window.__changlu.scrollTo(.545));
  await page.waitForTimeout(3000);
  console.log(tag + '_city ' + JSON.stringify(await metrics()));
  await page.screenshot({ path: `qa/final_${tag}_city.png` });

  await page.evaluate(() => window.__changlu.showCard());
  await page.waitForTimeout(600);
  console.log(tag + '_card ' + JSON.stringify(await metrics()));
  await page.screenshot({ path: `qa/final_${tag}_card.png` });
  await page.evaluate(() => window.__changlu.hideCard());

  await page.evaluate(() => window.__changlu.overview());
  await page.waitForTimeout(3200);
  console.log(tag + '_overview ' + JSON.stringify(await metrics()));
  await page.screenshot({ path: `qa/final_${tag}_overview.png` });
  if (full) {
    const first = page.locator('.ov-label').first();
    if (await first.count()) { await first.tap(); await page.waitForTimeout(2600); console.log(tag + '_labelJump ' + JSON.stringify(await metrics())); }
  }
  await page.evaluate(() => { if (window.__changlu.state.mode === 'overview') window.__changlu.exitOverview(); window.__changlu.scrollTo(1); });
  await page.waitForTimeout(3000);
  console.log(tag + '_finale ' + JSON.stringify(await metrics()));
  await page.screenshot({ path: `qa/final_${tag}_finale.png` });
  const launch = page.locator('#launchBtn');
  if (await launch.isVisible()) { await launch.tap(); await page.waitForTimeout(2600); await page.screenshot({ path: `qa/final_${tag}_launch.png` }); }
  await page.waitForTimeout(8200);
  console.log(tag + '_end ' + JSON.stringify(await metrics()));
  await page.screenshot({ path: `qa/final_${tag}_end.png` });
  await ctx.close();
}

await run(390, 844, 'p', true);
await run(844, 390, 'l', false);
console.log('ERRORS ' + JSON.stringify(errs));
await browser.close();
