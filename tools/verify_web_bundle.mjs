import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright';

const root=path.resolve(process.cwd(),'dist');
const files=JSON.parse(fs.readFileSync('deployment-files.json','utf8'));
for(const file of files){
  const data=fs.readFileSync(path.join(root,file.path));
  assert.equal(createHash('sha256').update(data).digest('hex'),file.sha256,file.path);
}
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.woff':'font/woff','.glb':'model/gltf-binary'};
const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const file=path.resolve(root,'.'+(pathname.endsWith('/')?pathname+'index.html':pathname));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
try{
  const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url())});
  await page.goto('http://127.0.0.1:'+server.address().port+'/');
  await page.waitForFunction(()=>window.__ready||window.__error,null,{timeout:120000});
  assert(await page.evaluate(()=>!!window.__ready&&!window.__error),'Page boots');
  await page.waitForFunction(()=>getComputedStyle(document.querySelector('#loading')).visibility==='hidden');
  await page.evaluate(()=>{const a=__changlu;a.freeze();a.start();a.setProgress(1);a.settle(24);a.showEnd();a.render()});
  assert.equal(await page.locator('#earthTitle').textContent(),'这次，家是地球');
  assert(await page.evaluate(()=>__changlu.ending.world.clouds.material.uniforms.cloudMap.value.image.width===8192),'Full-resolution clouds');
  assert.deepEqual(errors,[]);
  console.log('Web bundle verified: '+files.length+' exact runtime files, all assets load, live Earth ending ready.');
}finally{await browser.close();await new Promise(done=>server.close(done));}
