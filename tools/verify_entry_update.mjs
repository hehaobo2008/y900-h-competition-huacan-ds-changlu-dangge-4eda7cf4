// Verify the cache-only release against actual HTTPS responses. Full runtime
// coverage is recorded separately for the byte-identical app and model set.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright';
const url=process.argv[2],stage=process.argv[3];
assert(url&&stage);
const prefix='/assets/experiences/aa384c92ca76/';
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
const responses=[],oldRequests=[],errors=[];
try{
 const page=await browser.newPage();
 for(const file of ['app.js','frame-bootstrap.js'])await page.route('**/'+file,route=>{
  oldRequests.push(route.request().url());
  return route.fulfill({contentType:'application/javascript',body:'window.__staleScript=true;'});
 });
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{
  const u=new URL(r.url());
  if(u.pathname===prefix+'app.js'||u.pathname===prefix+'frame-bootstrap.js')responses.push(r);
 });
 await page.goto(url,{waitUntil:'commit',timeout:60000});
 await page.waitForSelector('iframe[title="山河织路互动作品"]',{timeout:120000});
 const frame=await (await page.$('iframe')).contentFrame();
 await frame.waitForFunction(()=>window.__assetTransfer?.loaded>0,null,{timeout:180000});
 assert.equal(await frame.evaluate(()=>!!window.__staleScript),false);
 assert.equal(await frame.evaluate(()=>window.__error),null);
 assert.deepEqual(oldRequests,[],'Old cached script URLs must never be used');
 assert.equal(responses.length,2);
 const scripts=[];
 for(const response of responses){
  const u=new URL(response.url()),file=path.basename(u.pathname),bytes=await response.body();
  assert.equal(response.status(),200);
  assert.deepEqual(bytes,fs.readFileSync(path.join(stage,'website',prefix.slice(1),file)));
  const sha256=createHash('sha256').update(bytes).digest('hex');
  assert.equal(u.searchParams.get('v'),sha256.slice(0,16));
  scripts.push({url:response.url(),bytes:bytes.length,sha256});
 }
 assert.deepEqual(errors,[]);
 const report={url,checkedAt:new Date().toISOString(),scope:'cache-only entry update; identical runtime covered by full-runtime-production-qa',versionedScriptsVerified:true,staleScriptsNeverRequested:true,scripts,transfer:await frame.evaluate(()=>window.__assetTransfer),errors};
 fs.writeFileSync(path.join(stage,'online-entry-update.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
}finally{await browser.close()}
