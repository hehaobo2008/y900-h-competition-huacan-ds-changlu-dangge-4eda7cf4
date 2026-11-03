import { chromium } from 'playwright';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const b=await chromium.launch({headless:true,executablePath:'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
for(const [src,w,h,tag] of [['docs/design.html',900,1273,'design'],['docs/flow.html',1600,1130,'flow']]){
 const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1});
 await p.goto(pathToFileURL(path.resolve(src)).href,{waitUntil:'load'});
 await p.waitForTimeout(500);
 await p.emulateMedia({media:'print'});
 const secs=p.locator('section.page');
 const n=await secs.count();
 for(let i=0;i<n;i++) await secs.nth(i).screenshot({path:`qa/${tag}_page_${i+1}.png`});
 console.log(tag,n);
 await p.close();
}
await b.close();
