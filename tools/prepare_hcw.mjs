import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const hcw='L:/harmonyprojectdevelopment/HCW';
const previous=path.join(hcw,'test/out/hchhb_loading_cache_20261112');
const stage=path.join(hcw,'test/out/hchhb_loading_fast_final_20261112');
const output=path.join(stage,'website');
const prefix='assets/experiences/aa384c92ca76/';
const read=file=>JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const baseline=read(path.join(project,'tmp/fastfix-baseline/production-live.json'));
const remote=read(path.join(project,'tmp/fastfix-baseline/production-files-live.json')).files;
const oldManifest=read(path.join(previous,'site-files.json'));
const oldDeployment=read(path.join(previous,'production-after.json'));
const runtime=path.join(project,'deployment/cloudflare/dist');
const runtimeFiles=read(path.join(project,'deployment/cloudflare/deployment-files.json'));
const require=createRequire('C:/Users/HC/AppData/Local/npm-cache/_npx/f53f07989cdda700/node_modules/wrangler/package.json');
const blake=require('blake3-wasm').hash;
if(baseline.deployment!==oldDeployment.deployment||baseline.name!=='web'||baseline.production_branch!=='main'||!baseline.domains.includes('harmonyconnectwindows.com'))throw Error('Wrong production baseline');
if(fs.existsSync(output))throw Error('Use a fresh stage; existing release artifacts are immutable');
const oldPaths=oldManifest.filter(f=>f.path!=='_headers').map(f=>'/'+f.path).sort();
if(JSON.stringify(oldPaths)!==JSON.stringify(Object.keys(remote).sort()))throw Error('Production file list differs from saved baseline');
for(const file of oldManifest){
  const data=fs.readFileSync(path.join(previous,'website',file.path));
  if(sha(data)!==file.sha256)throw Error('Saved baseline changed: '+file.path);
  if(file.path!=='_headers'&&blake(data.toString('base64')+path.extname(file.path).slice(1)).toString('hex').slice(0,32)!==remote['/'+file.path])throw Error('Cloudflare bytes differ: '+file.path);
}
fs.cpSync(path.join(previous,'website'),output,{recursive:true});
const target=path.join(output,prefix);
for(const file of runtimeFiles){
  const data=fs.readFileSync(path.join(runtime,file.path));
  if(sha(data)!==file.sha256)throw Error('Verified runtime changed: '+file.path);
  const dest=path.join(target,file.path);
  fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,data);
}
const gate=fs.readFileSync(path.join(hcw,'test/out/hchhb_site_20261111/frame-entry.js'),'utf8');
const frameHead='<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer"><style>html:not([data-hcw-frame="allowed"]){display:none}</style><script>'+gate+'</script>';
const html=fs.readFileSync(path.join(runtime,'index.html'),'utf8');
if(html.split('<meta charset="utf-8">').length!==2||html.split('<script src="./app.js"></script>').length!==2)throw Error('Unexpected document markers');
// HTML revalidates, while Pages serves JS with a four-hour browser cache.
// Version BOTH script URLs so existing visitors receive the repaired loader.
const appVersion=sha(fs.readFileSync(path.join(runtime,'app.js'))).slice(0,16);
const bootstrap="(function(){'use strict';if(document.documentElement.dataset.hcwFrame!=='allowed')return;var script=document.createElement('script');script.src='./app.js?v="+appVersion+"';script.async=false;document.body.appendChild(script);})();\n";
const bootstrapURL='./frame-bootstrap.js?v='+sha(bootstrap).slice(0,16);
fs.writeFileSync(path.join(target,'frame-bootstrap.js'),bootstrap);
const gated=html.replace('<meta charset="utf-8">','<meta charset="utf-8">'+frameHead).replace('<script src="./app.js"></script>','<script src="'+bootstrapURL+'"></script>');
if(gated.replace(frameHead,'').replace(bootstrapURL,'./app.js')!==html)throw Error('Gate changed experience content');
fs.writeFileSync(path.join(target,'index.html'),gated);
const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(item=>item.isDirectory()?walk(path.join(dir,item.name)):[path.join(dir,item.name)]);
const files=walk(output).map(file=>({path:path.relative(output,file).replaceAll('\\','/'),bytes:fs.statSync(file).size,sha256:sha(fs.readFileSync(file))})).sort((a,b)=>a.path.localeCompare(b.path));
if(files.some(f=>f.bytes>25*1024*1024))throw Error('Cloudflare file limit exceeded');
const current=new Map(files.map(f=>[f.path,f]));
for(const file of oldManifest)if(!file.path.startsWith(prefix)&&current.get(file.path)?.sha256!==file.sha256)throw Error('Unrelated website file changed: '+file.path);
const changed=files.filter(f=>oldManifest.find(old=>old.path===f.path)?.sha256!==f.sha256).map(f=>f.path);
if(changed.some(name=>!name.startsWith(prefix)))throw Error('Change escaped experience directory');
// Preserve the local source so a later HCW website build cannot restore the old story.
const source=path.join(hcw,'website',prefix);
fs.cpSync(source,path.join(stage,'source-before'),{recursive:true});
fs.cpSync(target,source,{recursive:true});
const status={scope:'hchhb-asset-loading-only',publicDeploymentAllowed:false,productionBaseline:baseline.deployment,productionBranch:'main',url:'https://harmonyconnectwindows.com/#HCHHB',prefix:'/'+prefix,files:files.length,changed,unchanged:oldManifest.length-changed.filter(name=>oldManifest.some(f=>f.path===name)).length,appVersionUnchanged:true,protectedFiles:['version.json','modules.txt','pc_version.txt','site-release.json','updates/index.html']};
for(const [name,data] of Object.entries({'site-files.json':files,'release-status.json':status,'production-baseline.json':baseline,'production-files.json':remote}))fs.writeFileSync(path.join(stage,name),JSON.stringify(data,null,2)+'\n');
console.log(JSON.stringify({stage,files:files.length,changed:changed.length,unchanged:status.unchanged,url:status.url}));
