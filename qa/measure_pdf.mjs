import { chromium } from 'playwright';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const b = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
for (const [src, w, h] of [['docs/flow.html',1123,794],['docs/design.html',794,1123]]) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.goto(pathToFileURL(path.join(process.cwd(), src)).href, { waitUntil: 'load' });
  await p.waitForTimeout(300);
  const r = await p.evaluate(() => {
    const mm = 96/25.4;
    const pages = [...document.querySelectorAll('.page')];
    return pages.map((pg, i) => {
      const pr = pg.getBoundingClientRect();
      const f = pg.querySelector('footer')?.getBoundingClientRect();
      const kids = [...pg.children].filter(e => e.tagName !== 'FOOTER').map(e => ({ c: e.className || e.tagName, bottom: +(e.getBoundingClientRect().bottom - pr.top).toFixed(1) }));
      return { page: i+1, h: +pr.height.toFixed(1), footerTop: f ? +(f.top - pr.top).toFixed(1) : null, last: kids[kids.length-1], over: kids.filter(k => f && k.bottom > f.top - 6) };
    });
  });
  console.log(src, JSON.stringify(r));
  await p.close();
}
await b.close();
