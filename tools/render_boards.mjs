import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const root = process.cwd();
const out = path.join(root, 'docs/boards'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 2400, height: 1500 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(root, 'docs/boards.html')).href, { waitUntil: 'load' });
await page.waitForTimeout(1200);
const n = await page.locator('.board').count();
for (let i = 0; i < n; i++) {
  await page.locator('.board').nth(i).screenshot({ path: path.join(out, `board_0${i+1}.png`) });
  console.log('board', i+1);
}
await page.screenshot({ path: path.join(root, 'qa/boards_overview.png'), fullPage: true });
await browser.close();
