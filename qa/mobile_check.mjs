import { chromium } from 'playwright';

const exe = 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
const browser = await chromium.launch({ executablePath: exe });
const ctx = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
});
const page = await ctx.newPage();
const errs = [];
page.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errs.push('CERR ' + m.text().slice(0, 240)); });
await page.goto('http://127.0.0.1:8124/?mobile=1&v=' + Date.now(), { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__ready, null, { timeout: 120000 });
await page.waitForTimeout(1600);

const snap = async (name, extra = () => ({})) => {
  const base = await page.evaluate(() => {
    const box = (s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return { x: +r.x.toFixed(0), y: +r.y.toFixed(0), w: +r.width.toFixed(0), h: +r.height.toFixed(0), op: +cs.opacity, disp: cs.display }; };
    return {
      vw: innerWidth, vh: innerHeight,
      pr: window.__changlu.renderer.getPixelRatio(),
      bloom: window.__changlu.paper.bloom.enabled,
      scrollW: document.documentElement.scrollWidth,
      info: window.__changlu.info(),
      sound: window.__changlu.soundInfo(),
      landing: box('#landing'), hud: box('#hud'), card: box('#card'), finale: box('#finale'), end: box('#endCard'),
    };
  });
  const extraData = await page.evaluate(extra);
  const data = { name, ...base, ...extraData };
  await page.screenshot({ path: `qa/m_${name}.png` });
  console.log(JSON.stringify(data));
  return data;
};

await snap('landing');
await page.tap('#startBtn');
await page.waitForTimeout(2300);
await page.evaluate(() => window.__changlu.scrollTo(.10));
await page.waitForTimeout(2600);
await snap('rural');

// touch swipe should move the scroll target without moving the page
const before = await page.evaluate(() => window.__changlu.state.target);
await page.evaluate(() => {
  const c = document.querySelector('#gl');
  c.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 195, clientY: 620, pointerType: 'touch' }));
  window.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: 195, clientY: 520, pointerType: 'touch' }));
  window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 195, clientY: 520, pointerType: 'touch' }));
});
await page.waitForTimeout(600);
const after = await page.evaluate(() => window.__changlu.state.target);
console.log(JSON.stringify({ swipeTarget: { before: +before.toFixed(4), after: +after.toFixed(4), delta: +(after - before).toFixed(4) } }));

await page.evaluate(() => window.__changlu.showCard());
await page.waitForTimeout(700);
await snap('card');
await page.evaluate(() => window.__changlu.hideCard());

await page.evaluate(() => window.__changlu.overview());
await page.waitForTimeout(2800);
await snap('overview', () => ({ labels: [...document.querySelectorAll('.ov-label')].map(e => { const r = e.getBoundingClientRect(); return { t: e.textContent.trim(), x: +r.x.toFixed(0), y: +r.y.toFixed(0), w: +r.width.toFixed(0) }; }) }));
await page.evaluate(() => window.__changlu.exitOverview());

await page.evaluate(() => window.__changlu.scrollTo(1));
await page.waitForTimeout(2600);
await snap('finale_prompt');
await page.tap('#launchBtn');
await page.waitForTimeout(2400);
await snap('launch');

await page.waitForTimeout(6000);
await page.evaluate(() => window.__changlu.showEnd());
await page.waitForTimeout(900);
await snap('end');

console.log('ERRORS', JSON.stringify(errs));
await browser.close();
