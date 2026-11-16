import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const url=process.argv[2];
assert(url&&(new URL(url).protocol==='https:'||new URL(url).hostname==='127.0.0.1'),'Provide HTTPS or a local verification URL.');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=process.env.HCW_QA_OUTPUT||path.join(root,'qa','deployment');
fs.mkdirSync(output,{recursive:true});
const direct=process.env.HCW_QA_DIRECT==='1';
const proxy=!direct&&new URL(url).protocol==='https:'&&(process.env.HTTPS_PROXY||process.env.HTTP_PROXY);
const browser=await chromium.launch({
  executablePath:process.env.CHROME||'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args:direct?['--no-proxy-server']:[],
  ...(proxy?{proxy:{server:proxy}}:{}),
});
const errors=[],failedRequests=[],transferResponses=[];
const protocols=new Set();
const navigationRetries=[];
async function navigate(page,target,options={}){
  for(let attempt=0;attempt<3;attempt++){
    try{return await page.goto(target,{waitUntil:'commit',timeout:60000,...options})}
    catch(error){if(attempt===2)throw error;navigationRetries.push({target,error:error.message});await new Promise(resolve=>setTimeout(resolve,500))}
  }
}
const pending=new Map();
let page,monitor;
const started=Date.now();
try{
  page=await browser.newPage({viewport:{width:1920,height:1080}});
  const network=await page.context().newCDPSession(page);
  await network.send('Network.enable');
  network.on('Network.responseReceived',({response})=>{
    if(response.url.includes('/assets/experiences/aa384c92ca76/'))protocols.add(response.protocol);
  });
  page.on('request',r=>pending.set(r,r.url()));
  page.on('requestfinished',r=>pending.delete(r));
  page.on('requestfailed',r=>pending.delete(r));
  const embedded=new URL(url).hash==='#HCHHB';
  const prefix='/assets/experiences/aa384c92ca76/';
  const hostChecks={};
  if(embedded){
    const requested=[];
    page.on('request',r=>requested.push(r.url()));
    await navigate(page,new URL('/',url).href);
    await page.waitForSelector('.site-header',{timeout:60000});
    hostChecks.homepageVisible=await page.locator('.site-header').count()===1;
    hostChecks.downloads=await page.locator('.download-grid h3').allTextContents();
    hostChecks.noExperienceRequests=requested.every(u=>!u.includes(prefix));
    assert(hostChecks.homepageVisible&&hostChecks.noExperienceRequests);
    assert.deepEqual(hostChecks.downloads,['Windows','HarmonyOS']);
    console.log('Original homepage and downloads verified.');
  }
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400&&new URL(r.url()).origin===new URL(url).origin){
    if(r.request().resourceType()==='fetch'&&r.url().includes(prefix+'assets/'))transferResponses.push(`${r.status()} ${r.url()}`);
    else errors.push(`${r.status()} ${r.url()}`);
  }});
  page.on('requestfailed',r=>{if(r.url().includes(prefix)&&r.failure()?.errorText!=='net::ERR_ABORTED')failedRequests.push({url:r.url(),type:r.resourceType(),error:r.failure()?.errorText})});
  if(embedded)await page.goto('about:blank');
  const response=await navigate(page,url);
  assert.equal(response.status(),200,'Deployed homepage returns HTTP 200');
  let experience=page;
  if(embedded){
    await page.waitForSelector('iframe[title="山河织路互动作品"]',{timeout:120000});
    experience=await (await page.$('iframe')).contentFrame();
    console.log('Experience frame created: '+experience.url());
    assert.equal(page.url(),url,'Keep the requested hash entry');
    assert.equal(await page.locator('.site-header').count(),0);
    assert.equal(await experience.locator('meta[name="robots"]').getAttribute('content',{timeout:120000}),'noindex,nofollow,noarchive');
    console.log('Exact HCHHB entry mounted. Loading experience assets.');
  }
  monitor=setInterval(async()=>{
    try{console.log('Load progress: '+JSON.stringify(await experience.evaluate(()=>({status:document.querySelector('#loadStatus')?.textContent,transfer:window.__assetTransfer,ready:window.__ready,error:window.__error}))))}catch{}
  },20000);
  await experience.waitForFunction(()=>window.__ready||window.__error,null,{timeout:600000});
  clearInterval(monitor);
  assert(await experience.evaluate(()=>!!window.__ready&&!window.__error),'All scene assets load');
  const transfer=await experience.evaluate(()=>window.__assetTransfer);
  assert(transfer?.ready&&transfer.loaded===transfer.total,'Every original asset passed its SHA-256 check');
  const loadedSeconds=(Date.now()-started)/1000;
  console.log('All scene assets loaded. Checking the live Earth ending.');
  await experience.waitForFunction(()=>getComputedStyle(document.querySelector('#loading')).visibility==='hidden');
  await page.screenshot({path:path.join(output,'online-cover.png')});
  await experience.locator('#startBtn').click();
  await experience.waitForFunction(()=>__changlu.state.started);
  const scenes=[];
  for(const [name,progress] of [['rural',.13],['town',.35],['city',.55],['rail',.77],['future',.95]]){
    const result=await experience.evaluate(({name,progress})=>{
      const a=__changlu;a.freeze();a.start();a.setProgress(progress);a.settle(24);a.render();
      return {name,children:a.zones[name].group.children.length,ready:!!a.zones[name].group};
    },{name,progress});
    assert(result.ready&&result.children>0);scenes.push(result);
    await page.screenshot({path:path.join(output,'online-'+name+'.png')});
  }
  await experience.evaluate(()=>{const a=__changlu;a.freeze();a.start();a.setProgress(1);a.settle(24);a.showEnd();a.render()});
  const ending=await experience.evaluate(()=>({
    title:document.querySelector('#earthTitle').textContent,
    cloudsWidth:__changlu.ending.world.clouds.material.uniforms.cloudMap.value.image.width,
    videos:document.querySelectorAll('video').length,
  }));
  assert.equal(ending.title,'这次，家是地球');
  assert.equal(ending.cloudsWidth,8192,'Original cloud texture is served');
  assert.equal(ending.videos,0,'Ending is rendered live');
  await page.waitForTimeout(1400);
  await page.screenshot({path:path.join(output,'online-earth.png')});
  await page.setViewportSize({width:390,height:844});
  await experience.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>{__changlu.render();resolve()}))));
  await page.screenshot({path:path.join(output,'online-earth-mobile.png')});
  if(embedded)assert.equal((await page.locator('iframe').boundingBox()).width,390);
  await page.setViewportSize({width:1920,height:1080});
  const warmStart=Date.now();
  await page.reload({waitUntil:'commit'});
  let warmFrame=page;
  if(embedded){await page.waitForSelector('iframe[title="山河织路互动作品"]',{timeout:120000});warmFrame=await (await page.$('iframe')).contentFrame()}
  await warmFrame.waitForFunction(()=>window.__ready||window.__error,null,{timeout:120000});
  assert(await warmFrame.evaluate(()=>!!window.__ready&&!window.__error));
  const warm={seconds:(Date.now()-warmStart)/1000,transfer:await warmFrame.evaluate(()=>window.__assetTransfer)};
  assert.equal(warm.transfer.directRequests,0,'Repeat visit reuses verified original assets');
  assert.equal(warm.transfer.cached,49);
  if(embedded){
    await page.evaluate(()=>location.hash='download');
    await page.waitForSelector('.site-header');
    assert.equal(await page.locator('iframe').count(),0);
    hostChecks.leaveExperience=true;
    await page.goto(new URL(prefix,url).href,{waitUntil:'commit'});
    await page.waitForFunction(()=>document.title==='页面未找到');
    assert.equal(await page.title(),'页面未找到');
    assert(await page.evaluate(()=>typeof window.__changlu==='undefined'));
    hostChecks.directDirectoryBlocked=true;
  }
  assert.deepEqual(errors,[],'No browser or HTTP errors');
  assert.deepEqual(failedRequests.filter(r=>!(r.type==='fetch'&&r.url.includes(prefix+'assets/'))),[],'No failed entry or styling requests');
  const report={url,checkedAt:new Date().toISOString(),status:response.status(),loadedSeconds,warm,protocols:[...protocols],navigationRetries,hostChecks,transfer,scenes,ending,errors,recoveredTransferResponses:transferResponses,failedRequests};
  fs.writeFileSync(path.join(output,'online-results.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}catch(error){
  fs.writeFileSync(path.join(output,'last-failure.json'),JSON.stringify({message:error.message,url:page?.url(),frames:page?.frames().map(f=>f.url()),pending:[...pending.values()],errors,failedRequests},null,2)+'\n');
  throw error;
}finally{clearInterval(monitor);await browser.close()}
