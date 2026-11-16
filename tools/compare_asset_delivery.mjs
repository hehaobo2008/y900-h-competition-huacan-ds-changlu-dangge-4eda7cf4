// Same browser settings, empty caches and identical real HTTPS asset URLs.
// Only the local app bundle changes. This is an asset-delivery comparison,
// not a substitute for the final production entry test.
import fs from 'node:fs';
import path from 'node:path';
import {chromium} from 'playwright';
const out=path.resolve('qa/asset-comparison');fs.mkdirSync(out,{recursive:true});
const html=fs.readFileSync('src/index.html','utf8')
 .replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="https://harmonyconnectwindows.com/assets/experiences/aa384c92ca76/">')
 .replace('<script src="./app.js"></script>','');
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const results=[];
try{
 for(const [name,file] of [
  ['previous-parts','L:/harmonyprojectdevelopment/HCW/test/out/hchhb_loading_cache_20261112/website/assets/experiences/aa384c92ca76/app.js'],
  ['candidate-whole','dist/app.js']]){
  const context=await browser.newContext(),page=await context.newPage({viewport:{width:1280,height:800}});
  await page.goto('http://127.0.0.1:18176/not-a-page',{waitUntil:'domcontentloaded'});
  await page.setContent(html,{waitUntil:'domcontentloaded'});
  const start=Date.now(),requests=[];
  page.on('request',r=>{if(r.url().includes('harmonyconnectwindows.com')&&r.resourceType()==='fetch')requests.push(r.url())});
  await page.addScriptTag({content:fs.readFileSync(file,'utf8')});
  const timer=setInterval(async()=>{
   try{console.log(name+' '+JSON.stringify(await page.evaluate(()=>({transfer:window.__assetTransfer,ready:window.__ready,error:window.__error}))))}catch{}
  },20000);
  let error=null;
  try{await page.waitForFunction(()=>window.__ready||window.__error,null,{timeout:900000})}catch(e){error=e.message}
  clearInterval(timer);
  const result={name,seconds:(Date.now()-start)/1000,requests:requests.length,error,...await page.evaluate(()=>({ready:!!window.__ready,error:window.__error,transfer:window.__assetTransfer,protocols:[...new Set(performance.getEntriesByType('resource').filter(e=>e.name.includes('harmonyconnectwindows.com')).map(e=>e.nextHopProtocol))]}))};
  results.push(result);console.log('RESULT '+JSON.stringify(result));
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));
  await context.close();
 }
}finally{await browser.close()}
