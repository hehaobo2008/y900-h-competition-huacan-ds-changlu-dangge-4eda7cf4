import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import sharp from 'sharp';
const root = process.cwd();
const out = path.join(root, 'docs/boards'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME || chromium.executablePath() });
const page = await browser.newPage({ viewport: { width: 2400, height: 1500 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(root, 'docs/boards.html')).href, { waitUntil: 'load' });
const offlineBytes = fs.statSync(path.join(root, 'dist', '山河织路-离线单文件.html')).size;
await page.locator('[data-offline-size]').evaluate((el, bytes) => {
  el.textContent = (bytes / 1024 ** 2).toFixed(1) + ' MiB';
}, offlineBytes);
await page.waitForTimeout(1200);
const n = await page.locator('.board').count();
const rendered=[];
for (let i = 0; i < n; i++) {
  // Rasterise each board at the top of its own viewport. Scrolling a long
  // composited sheet can leave a whole unpainted tile in a captured PNG.
  await page.evaluate(async index=>{
    document.querySelectorAll('.board').forEach((board,k)=>{board.style.display=k===index?'':'none';});
    scrollTo(0,0);await document.fonts.ready;
    await Promise.all([...document.images].filter(img=>img.offsetWidth).map(img=>img.decode()));
    await new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done)));
  },i);
  const dest=path.join(out,`board_0${i+1}.png`);
  await page.locator('.board').nth(i).screenshot({path:dest});
  rendered.push({input:dest,left:0,top:i*1500});
  console.log('board', i+1);
}
await sharp({create:{width:2400,height:n*1500,channels:3,background:'#f3ecdf'}})
  .composite(rendered).png().toFile(path.join(root,'qa/boards_overview.png'));
await browser.close();
