import fs from 'node:fs';
import {chromium} from 'playwright';
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
const results=[];
try{
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 for(const phase of ['original-cold-local','original-warm-local']){
  const start=Date.now();await page.goto('http://127.0.0.1:18180/#HCHHB',{waitUntil:'commit'});
  await page.waitForSelector('iframe');const frame=await (await page.$('iframe')).contentFrame();
  await frame.waitForFunction(()=>window.__ready||window.__error,null,{timeout:120000});
  const result={phase,seconds:(Date.now()-start)/1000,...await frame.evaluate(()=>({ready:!!window.__ready,error:window.__error,resources:performance.getEntriesByType('resource').filter(r=>r.name.includes('/assets/')).map(r=>({bytes:r.transferSize,duration:r.duration}))}))};
  results.push(result);console.log(JSON.stringify({...result,resources:result.resources.length,transferred:result.resources.reduce((s,r)=>s+r.bytes,0)}));
  await page.goto('about:blank');
 }
 fs.writeFileSync('qa/asset-delivery/original-local-baseline.json',JSON.stringify(results,null,2));
}finally{await browser.close()}
