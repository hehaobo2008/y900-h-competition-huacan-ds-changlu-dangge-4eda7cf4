import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';

const hash=data=>createHash('sha256').update(data).digest('hex');
const mime={'.glb':'model/gltf-binary','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'};
// Small, content-addressed transfers also work on hosts that ignore Range.
// Compression is lossless: the client checks the original file's SHA-256.
export function buildAssetTransport(dist){
  const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>
    e.isDirectory()?(e.name==='transfer'?[]:walk(path.join(dir,e.name))):[path.join(dir,e.name)]);
  const assets={},parts=new Map();
  const folder=path.join(dist,'assets','transfer');
  fs.mkdirSync(folder,{recursive:true});
  for(const file of walk(path.join(dist,'assets')).filter(f=>mime[path.extname(f)])){
    const source=fs.readFileSync(file),packed=gzipSync(source,{level:9});
    const compressed=packed.length<source.length*.95,body=compressed?packed:source;
    const chunks=[];
    for(let offset=0;offset<body.length;offset+=128*1024){
      const data=body.subarray(offset,offset+128*1024),sha256=hash(data);
      const relative='assets/transfer/'+sha256+'.bin';
      fs.writeFileSync(path.join(dist,relative),data);
      chunks.push({file:relative,bytes:data.length,sha256});parts.set(relative,data.length);
    }
    assets['/'+path.relative(dist,file).replaceAll('\\','/')]={
      bytes:source.length,sha256:hash(source),mime:mime[path.extname(file)],
      encoding:compressed?'gzip':'identity',chunks,
    };
  }
  const manifest={version:1,assets};
  fs.writeFileSync(path.join(dist,'asset-manifest.json'),JSON.stringify(manifest));
  console.log('Lossless asset transport:',Object.keys(assets).length,'assets,',parts.size,'parts,',
    (Array.from(parts.values()).reduce((a,b)=>a+b,0)/1048576).toFixed(1)+' MiB');
  return manifest;
}
