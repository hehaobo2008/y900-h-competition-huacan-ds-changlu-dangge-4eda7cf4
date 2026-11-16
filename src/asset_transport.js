import {gunzipSync} from 'three/addons/libs/fflate.module.js';
import {ASSET} from './assets.js';

const jobs=new Map(),parts=new Map(),partWaiters=[],wholeWaiters=[];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const hash=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
const checked=async(bytes,item)=>bytes.byteLength===item.bytes&&await hash(bytes)===item.sha256;
const stats=window.__assetTransfer={strategy:'whole-file-first',loaded:0,total:0,assets:0,completed:0,directRequests:0,cached:0,resumed:0,fallbacks:0,retries:0,active:0,activeParts:0,maxActiveParts:0,ready:false,recovered:[]};
let metadataPromise,cachePromise,cacheIndexPromise,partSlots=0,wholeSlots=0;

async function assetCache(){
  if(!cachePromise)cachePromise=Promise.resolve().then(()=>caches.open('shanhe-assets-v1')).catch(()=>null);
  return cachePromise;
}
async function cacheIndex(){
  if(!cacheIndexPromise)cacheIndexPromise=assetCache().then(async cache=>new Set((await cache?.keys()||[]).map(r=>r.url))).catch(()=>new Set());
  return cacheIndexPromise;
}
async function deleteCache(url){
  try{const index=await cacheIndex();if(!index.has(url))return;await (await assetCache())?.delete(url);index.delete(url)}catch{}
}
async function readCache(url,item){
  try{
    if(!(await cacheIndex()).has(url))return null;
    const cache=await assetCache(),response=await cache?.match(url);
    if(response){const bytes=await response.arrayBuffer();if(await checked(bytes,item))return bytes;await deleteCache(url)}
  }catch{/* Storage is optional. */}
  return null;
}
async function saveCache(url,bytes){
  try{const cache=await assetCache();if(!cache)return false;await cache.put(url,new Response(bytes));(await cacheIndex()).add(url);return true}
  catch{return false}
}

async function fetchBytes(url,cacheMode='default',headerTimeout=90000){
  const controller=new AbortController();
  // Queueing is allowed; after headers, only inactivity times out.
  let timer=setTimeout(()=>controller.abort(),headerTimeout);
  try{
    const response=await fetch(url,{cache:cacheMode,signal:controller.signal});
    if(!response.ok)throw Error('HTTP '+response.status);
    const reader=response.body.getReader(),chunks=[];let length=0;
    while(true){
      clearTimeout(timer);timer=setTimeout(()=>controller.abort(),25000);
      const {value,done}=await reader.read();if(done)break;
      chunks.push(value);length+=value.length;
    }
    const bytes=new Uint8Array(length);let offset=0;
    for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length}
    return bytes;
  }finally{clearTimeout(timer)}
}
async function metadata(){
  if(!metadataPromise)metadataPromise=(async()=>{
    for(let attempt=0;attempt<3;attempt++){
      try{
        const result=JSON.parse(new TextDecoder().decode(await fetchBytes(new URL('./asset-manifest.json',document.baseURI),'no-cache',15000)));
        if(result.version!==1||!result.assets)throw Error('Invalid asset manifest');
        return result;
      }catch(error){if(attempt===2)throw error;stats.retries++;await sleep(400*2**attempt)}
    }
  })().catch(error=>{metadataPromise=null;throw error});
  return metadataPromise;
}
async function withPartSlot(task){
  if(partSlots>=6)await new Promise(resolve=>partWaiters.push(resolve));else partSlots++;
  stats.activeParts++;stats.maxActiveParts=Math.max(stats.maxActiveParts,stats.activeParts);
  try{return await task()}
  finally{stats.activeParts--;const next=partWaiters.shift();if(next)next();else partSlots--}
}
async function wholeFile(url,asset){
  if(wholeSlots>=12)await new Promise(resolve=>wholeWaiters.push(resolve));else wholeSlots++;
  try{
    for(let attempt=0;attempt<2;attempt++){
      try{
        stats.directRequests++;const bytes=await fetchBytes(url,attempt?'reload':'default');
        if(!await checked(bytes,asset))throw Error('Stale or incomplete scene asset');
        return bytes;
      }catch(error){if(attempt===1)throw error;stats.retries++;await sleep(400)}
    }
  }finally{const next=wholeWaiters.shift();if(next)next();else wholeSlots--}
}
function partURL(part){return new URL('./'+part.file,document.baseURI).href}
async function existingPart(part){
  if(parts.has(part.sha256))return parts.get(part.sha256);
  const bytes=await readCache(partURL(part),part);if(bytes)parts.set(part.sha256,bytes);
  return bytes;
}
async function fetchPart(part){
  const existing=await existingPart(part);if(existing)return existing;
  return withPartSlot(async()=>{
    for(let attempt=0;attempt<6;attempt++){
      try{
        const bytes=await fetchBytes(partURL(part),attempt?'reload':'default',20000);
        if(!await checked(bytes,part))throw Error('Incomplete asset part');
        parts.set(part.sha256,bytes);await saveCache(partURL(part),bytes);return bytes;
      }catch(error){if(attempt===5)throw error;stats.retries++;await sleep(Math.min(4000,400*2**attempt))}
    }
  });
}
async function fromParts(asset){
  const result=await Promise.allSettled(asset.chunks.map(fetchPart));
  const failure=result.find(r=>r.status==='rejected');if(failure)throw failure.reason;
  const body=new Blob(result.map(r=>r.value));
  const bytes=asset.encoding==='gzip'
    ?typeof DecompressionStream==='function'
      ?await new Response(body.stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()
      :gunzipSync(new Uint8Array(await body.arrayBuffer()))
    :await body.arrayBuffer();
  if(!await checked(bytes,asset))throw Error('Asset integrity mismatch');
  for(const part of asset.chunks)parts.delete(part.sha256);
  return bytes;
}

export function loadAssetURL(assetPath){
  if(window.__ASSET_MAP?.[assetPath])return Promise.resolve(ASSET(assetPath));
  if(jobs.has(assetPath))return jobs.get(assetPath);
  stats.active++;stats.assets++;stats.ready=false;
  const job=(async()=>{
    const asset=(await metadata()).assets[assetPath];
    if(!asset)throw Error('Unknown scene asset: '+assetPath);
    stats.total+=asset.bytes;
    const url=ASSET(assetPath),cacheKey=url+'?sha256='+asset.sha256;
    const resumeKey=new URL('./asset-recovery/'+asset.sha256,document.baseURI).href;
    let bytes=await readCache(cacheKey,asset);
    if(bytes)stats.cached++;
    else{
      // A single metadata-only cache index avoids probing 345 bodies on a cold
      // visit. Reuse complete old-release assets, or an explicitly failed file.
      const index=await cacheIndex();
      if(index.has(resumeKey)||asset.chunks.every(part=>index.has(partURL(part)))){
        stats.resumed++;bytes=await fromParts(asset);
      }else{
        try{
          bytes=await wholeFile(url,asset);
        }catch{
          stats.fallbacks++;stats.retries++;stats.recovered.push(assetPath);
          await saveCache(resumeKey,'1');
          bytes=await fromParts(asset);
        }
      }
      // Keep recoverable pieces if storage cannot hold the assembled file.
      if(await saveCache(cacheKey,bytes)){
        await deleteCache(resumeKey);
        await Promise.all(asset.chunks.map(part=>deleteCache(partURL(part))));
      }
    }
    stats.loaded+=asset.bytes;stats.completed++;
    return URL.createObjectURL(new Blob([bytes],{type:asset.mime}));
  })().catch(error=>{error.assetTransfer=true;jobs.delete(assetPath);throw error})
    .finally(()=>{stats.active--;stats.ready=stats.active===0&&stats.completed===stats.assets});
  jobs.set(assetPath,job);return job;
}
