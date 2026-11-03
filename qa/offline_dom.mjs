import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 900, height: 600 } });
page.on('pageerror', e => console.log('PAGEERR', e.message));
const url = pathToFileURL('H:/appdata/H/competition/huacan-ds/changlu-dangge/qa/offline_test.html').href;
await page.goto(url, { waitUntil: 'load' });
console.log(await page.evaluate(() => {
  const els = [...document.querySelectorAll('#gl')];
  return { count: els.length, tags: els.map(e=>[e.tagName, e.constructor.name, typeof e.addEventListener, e.outerHTML?.slice(0,80)]), first: document.querySelector('#gl')?.constructor?.name, htmlStart: document.documentElement.outerHTML.slice(0,300) };
}));
await browser.close();
