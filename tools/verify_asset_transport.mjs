import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {chromium} from 'playwright';

const root=process.cwd(),dist=path.join(root,'dist'),out=path.join(root,'qa','asset-delivery');
fs.mkdirSync(out,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.join(dist,'asset-manifest.json'),'utf8'));
const sha=data=>createHash('sha256').update(data).digest('hex');
for(const [assetPath,asset] of Object.entries(manifest.assets)){
 const chunks=asset.chunks.map(part=>{
  const bytes=fs.readFileSync(path.join(dist,part.file));
  assert.equal(bytes.length,part.bytes);assert.equal(sha(bytes),part.sha256);return bytes;
 });
 const joined=Buffer.concat(chunks),original=asset.encoding==='gzip'?gunzipSync(joined):joined;
 assert.equal(sha(original),asset.sha256);
 assert.deepEqual(original,fs.readFileSync(path.join(dist,assetPath.slice(1))));
}
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
const url='http://127.0.0.1:18176/';
const ready=page=>page.waitForFunction(()=>window.__ready,null,{timeout:120000});
try{
 const normal=await browser.newPage({viewport:{width:1440,height:900}});
 const normalRequests=[];let releaseCloud;
 normal.on('request',r=>{if(r.resourceType()==='fetch')normalRequests.push(new URL(r.url()).pathname)});
 await normal.route('**/assets/earth/clouds.jpg',async route=>{await new Promise(resolve=>{releaseCloud=resolve});await route.continue()});
 const coldStart=Date.now();await normal.goto(url,{waitUntil:'domcontentloaded'});
 await normal.waitForFunction(()=>window.__changlu?.zones.rural?.group?.children.length>0,null,{timeout:120000});
 assert.equal(await normal.evaluate(()=>!!window.__ready),false,'World can parse before the late Earth texture arrives');
 while(!releaseCloud)await new Promise(resolve=>setTimeout(resolve,20));
 releaseCloud();await ready(normal);
 const coldSeconds=(Date.now()-coldStart)/1000,cold=await normal.evaluate(()=>window.__assetTransfer);
 assert.equal(cold.directRequests,49);assert.equal(cold.fallbacks,0);assert.equal(cold.completed,49);
 assert.equal(normalRequests.filter(p=>p.includes('/assets/transfer/')).length,0,'Normal loading never requests 345 parts');
 await normal.unroute('**/assets/earth/clouds.jpg');
 const normalBefore=normalRequests.length,warmStart=Date.now();
 await normal.reload({waitUntil:'domcontentloaded'});await ready(normal);
 const warmSeconds=(Date.now()-warmStart)/1000,warm=await normal.evaluate(()=>window.__assetTransfer);
 assert.equal(warm.directRequests,0);assert.equal(warm.cached,49);
 assert.equal(normalRequests.slice(normalBefore).filter(p=>manifest.assets[p]).length,0,'Repeat visit uses validated whole-file cache');
 await normal.close();

 const page=await browser.newPage({viewport:{width:1440,height:900}});
 const target='/assets/vehicles/rickshaw.glb',asset=manifest.assets[target];
 const retryPart='/'+asset.chunks[0].file,fatalPart='/'+asset.chunks[3].file;
 const requests=new Map();let fail=true;
 page.on('request',r=>{if(r.resourceType()==='fetch'){const p=new URL(r.url()).pathname;requests.set(p,(requests.get(p)||0)+1)}});
 await page.route('**/assets/vehicles/rickshaw.glb',route=>route.abort('connectionreset'));
 await page.route('**/assets/vehicles/green_train.glb',route=>
  requests.get('/assets/vehicles/green_train.glb')===1
   ?route.fulfill({status:200,body:Buffer.alloc(20)}):route.continue());
 await page.route('**/assets/transfer/*.bin',route=>{
  const p=new URL(route.request().url()).pathname,n=requests.get(p);
  if(p===retryPart&&n===1)return route.abort('connectionreset');
  if(p===retryPart&&n===2)return route.fulfill({status:200,body:Buffer.alloc(20)});
  if(p===fatalPart&&fail)return route.fulfill({status:503,body:'temporary test failure'});
  return route.continue();
 });
 await page.goto(url,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__error&&window.__assetTransfer.active===0,null,{timeout:120000});
 assert.equal(requests.get(fatalPart),6);assert(await page.locator('#errorScreen').isVisible());
 const before=new Map(requests);
 fail=false;await page.locator('#retryBtn').click();await ready(page);
 assert.equal(requests.get(target),2,'A retry resumes verified parts instead of fetching the failed full file again');
 assert.equal(requests.get(retryPart),3,'Connection reset and truncated part both recovered');
 assert.equal(requests.get(fatalPart),7);
 for(const [p,count] of before)if(p!==fatalPart&&manifest.assets[p])assert.equal(requests.get(p),count,'Successful original files survive reload: '+p);
 const recovered=await page.evaluate(()=>window.__assetTransfer);
 assert(recovered.ready&&recovered.loaded===recovered.total&&recovered.maxActiveParts<=6);
 assert.equal(recovered.resumed,1);

 // Recover a damaged full-file cache and a damaged old-release part cache.
 const car='/assets/vehicles/car.glb',carAsset=manifest.assets[car];
 const seedParts=asset.chunks.map(part=>({file:part.file,data:fs.readFileSync(path.join(dist,part.file)).toString('base64')}));
 await page.evaluate(async({target,asset,car,carAsset,retryPart,seedParts})=>{
  const cache=await caches.open('shanhe-assets-v1');
  await cache.delete(new URL('.'+target,document.baseURI).href+'?sha256='+asset.sha256);
  for(const part of seedParts){const bytes=Uint8Array.from(atob(part.data),c=>c.charCodeAt(0));await cache.put(new URL(part.file,document.baseURI),new Response(bytes))}
  await cache.put(new URL('.'+retryPart,document.baseURI),new Response('damaged part'));
  await cache.put(new URL('.'+car,document.baseURI).href+'?sha256='+carAsset.sha256,new Response('damaged original'));
 },{target,asset,car,carAsset,retryPart,seedParts});
 const beforeReload=new Map(requests);
 await page.reload({waitUntil:'domcontentloaded'});await ready(page);
 assert.equal(requests.get(target),2);
 assert.equal(requests.get(retryPart),beforeReload.get(retryPart)+1);
 assert.equal(requests.get(car),beforeReload.get(car)+1);
 const cacheRecovery=await page.evaluate(()=>window.__assetTransfer);
 assert.equal(cacheRecovery.resumed,1);assert.equal(cacheRecovery.directRequests,1);
 await page.evaluate(()=>{const a=__changlu;a.freeze();a.start();a.setProgress(1);a.settle(24);a.showEnd();a.render()});
 const ending=await page.evaluate(()=>({title:document.querySelector('#earthTitle').textContent,clouds:__changlu.ending.world.clouds.material.uniforms.cloudMap.value.image.width}));
 assert.equal(ending.title,'这次，家是地球');assert.equal(ending.clouds,8192);
 await page.waitForTimeout(1400);await page.screenshot({path:path.join(out,'earth.png')});
 const report={losslessOriginals:52,coldSeconds,warmSeconds,parseOverlapsDownloads:true,normalPartRequests:0,cold,warm,exhaustedRetries:6,manualResume:true,onlyFailedFileUsesParts:true,corruptOriginalCacheRecovery:true,corruptPartCacheRecovery:true,recovered,cacheRecovery,ending};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close()}
