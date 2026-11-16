import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=path.join(root,'dist');
const checkout=path.join(root,'deployment','cloudflare');
const output=path.join(checkout,'dist');
const files=[
  'index.html','style.css','app.js',
  ...['rural','town','city','rail','future'].map(n=>`assets/zones/${n}.glb`),
  ...['rickshaw','car','green_train','hsr','harmony','rocket','future_metro'].map(n=>`assets/vehicles/${n}.glb`),
  ...fs.readdirSync(path.join(source,'assets','painted')).map(n=>`assets/painted/${n}`),
  ...['cloud','glow','star','smoke','shadow','grain','ink','seal'].map(n=>`assets/textures/${n}.png`),
  ...['shanhe-titles.woff','mashanzheng-OFL.txt','zcoolqingkehuangyou-OFL.txt'].map(n=>`assets/fonts/${n}`),
  ...['earth.jpg','clouds.jpg','CLOUDS-CREDIT.txt','EARTH-CREDIT.txt'].map(n=>`assets/earth/${n}`),
];
const transport=JSON.parse(fs.readFileSync(path.join(source,'asset-manifest.json'),'utf8'));
files.push('asset-manifest.json',...new Set(Object.values(transport.assets).flatMap(a=>a.chunks.map(p=>p.file))));
const manifest=[];
for(const relative of files){
  const input=path.join(source,relative),destination=path.join(output,relative);
  const data=fs.readFileSync(input);
  if(data.length>25*1024*1024)throw new Error(`Cloudflare Pages file exceeds 25 MiB: ${relative}`);
  fs.mkdirSync(path.dirname(destination),{recursive:true});
  fs.writeFileSync(destination,data);
  manifest.push({path:relative,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')});
}
fs.writeFileSync(path.join(checkout,'deployment-files.json'),JSON.stringify(manifest,null,2)+'\n');
fs.writeFileSync(path.join(checkout,'.gitignore'),'.wrangler/\nnode_modules/\n');
fs.writeFileSync(path.join(checkout,'README.md'),'# 山河织路 · Cloudflare 发布包\n\n正式作品的静态网页发布目录，包含五幕三维场景、票根互动与「这次，家是地球」尾声。\n\n由主项目的 tools/prepare_cloudflare.mjs 从经过验收的 dist 复制。deployment-files.json 记录逐文件校验值。只发布本目录下 dist 内的网页与运行素材；离线单文件、影片和历史小样不上传。\n');
console.log(JSON.stringify({checkout,files:files.length,totalBytes:manifest.reduce((n,f)=>n+f.bytes,0),largest:manifest.reduce((a,b)=>a.bytes>b.bytes?a:b)}));
