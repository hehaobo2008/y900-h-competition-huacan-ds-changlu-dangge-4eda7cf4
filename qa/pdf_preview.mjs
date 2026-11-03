import { chromium } from 'playwright';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const root=process.cwd();
const b=await chromium.launch({headless:true, executablePath:'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
for (const [src,w,h,prefix] of [['docs/flow.html',1123,794,'flow'],['docs/design.html',794,1123,'design']]) {
  const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1});
  await p.goto(pathToFileURL(path.join(root,src)).href,{waitUntil:'load'}); await p.waitForTimeout(600);
  const n=await p.locator('.page').count();
  for(let i=0;i<n;i++) await p.locator('.page').nth(i).screenshot({path:`qa/pdf_${prefix}_${i+1}.png`});
  console.log(prefix,n);
  await p.close();
}
await b.close();
