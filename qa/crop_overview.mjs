import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const exe = 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
const src = resolve('qa/overview_clean.png');
const out = resolve('qa/overview_crop.png');

const browser = await chromium.launch({ executablePath: exe });
const page = await browser.newPage();
await page.goto('file:///' + src.replace(/\\/g, '/'));
const box = await page.evaluate(async () => {
  const img = document.querySelector('img');
  await img.decode();
  const c = document.createElement('canvas');
  c.width = img.naturalWidth; c.height = img.naturalHeight;
  const g = c.getContext('2d');
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, c.width, c.height).data;
  // sample corners for paper colour
  const px = (x, y) => { const i = (y * c.width + x) * 4; return [d[i], d[i + 1], d[i + 2]]; };
  const bg = px(4, 4);
  let x0 = c.width, y0 = c.height, x1 = 0, y1 = 0, n = 0;
  for (let y = 0; y < c.height; y++) {
    for (let x = 0; x < c.width; x++) {
      const i = (y * c.width + x) * 4;
      const dr = d[i] - bg[0], dg = d[i + 1] - bg[1], db = d[i + 2] - bg[2];
      if (dr * dr + dg * dg + db * db > 22 * 22) {
        n++;
        if (x < x0) x0 = x; if (x > x1) x1 = x;
        if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
    }
  }
  return { w: c.width, h: c.height, bg, n, x0, y0, x1, y1 };
});
await browser.close();
console.log(JSON.stringify(box));

const pad = 10;
const x = Math.max(0, box.x0 - pad);
const y = Math.max(0, box.y0 - pad);
const w = Math.min(box.w - x, box.x1 - box.x0 + 1 + pad * 2);
const h = Math.min(box.h - y, box.y1 - box.y0 + 1 + pad * 2);
// crop must be even for some encoders
const we = w - (w % 2), he = h - (h % 2);
console.log({ x, y, we, he, ratio: (we / he).toFixed(3) });
execFileSync('node_modules/ffmpeg-static/ffmpeg.exe', [
  '-y', '-hide_banner', '-loglevel', 'error',
  '-i', src, '-vf', `crop=${we}:${he}:${x}:${y}`, '-frames:v', '1', out,
], { stdio: 'inherit' });
console.log('WROTE', out);
