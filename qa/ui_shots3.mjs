import { chromium } from 'playwright';

const b = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
p.on('pageerror', (e) => console.log('PAGEERR', e.message));
p.on('console', (m) => { if (m.type() === 'error') console.log('CERR', m.text().slice(0, 200)); });
await p.goto('http://127.0.0.1:8124/?capture=1&v=' + Date.now(), { waitUntil: 'networkidle' });
await p.waitForFunction(() => window.__ready, null, { timeout: 120000 });
await p.waitForTimeout(1500);

async function settle(prog, steps = 90) {
  await p.evaluate(({ prog, steps }) => {
    const c = window.__changlu;
    c.freeze();
    c.start();
    c.setProgress(prog);
    c.settle(steps);
    document.querySelector('#loading').style.display = 'none';
    document.querySelector('#toast').style.display = 'none';
  }, { prog, steps });
  await p.waitForTimeout(500);
}

await settle(0.545);
await p.screenshot({ path: 'qa/ui3_city.png' });
await settle(0.79);
await p.screenshot({ path: 'qa/ui3_rail.png' });
await settle(0.95);
await p.screenshot({ path: 'qa/ui3_future.png' });

await p.evaluate(() => {
  const c = window.__changlu;
  c.setProgress(1);
  c.advance(1 / 24);
  c.settle(60);
});
await p.waitForTimeout(700);
await p.screenshot({ path: 'qa/ui3_finale_prompt.png' });

await p.evaluate(() => {
  const c = window.__changlu;
  c.launch();
  for (let i = 0; i < 60; i++) c.advance(1 / 24);
});
await p.waitForTimeout(300);
await p.screenshot({ path: 'qa/ui3_launch.png' });

await p.evaluate(() => {
  const c = window.__changlu;
  c.scrollTo(.35);
  c.advance(1 / 24);
  c.settle(60);
  c.overview();
  for (let i = 0; i < 140; i++) c.advance(1 / 24);
});
await p.waitForTimeout(300);
await p.screenshot({ path: 'qa/ui3_overview.png' });
await b.close();
