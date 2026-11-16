import fs from 'node:fs/promises';
import path from 'node:path';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, instance, meshopt, textureCompress, weld } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder, MeshoptSimplifier } from 'meshoptimizer';
import sharp from 'sharp';

// Blender exports full detail first. Retain that export for future repacks,
// including nodes carrying water or interaction anchors.
const zones=['rural','town','city','rail','future'];
const vehicles=['rickshaw','car','green_train','hsr','harmony','rocket','future_metro'];
const args=process.argv.slice(2);
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready,MeshoptSimplifier.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder
});
for(const name of args.length?args:[...zones,...vehicles]){
  if(![...zones,...vehicles].includes(name)) throw Error('Unknown asset '+name);
  const folder=zones.includes(name)?'zones':'vehicles';
  const output=path.resolve('assets',folder,name+'.glb');
  const raw=path.resolve('assets','raw',folder,name+'.glb');
  const current=await fs.readFile(output);
  const gltf=JSON.parse(current.subarray(20,20+current.readUInt32LE(12)));
  if(!gltf.extensionsUsed?.includes('EXT_meshopt_compression')) await fs.writeFile(raw,current);
  const doc=await io.read(raw);
  await doc.transform(dedup(),weld(),
    ...(['town','city','rail','future'].includes(name)?[instance({min:2})]:[]),
    ...(name==='harmony'?[]:[textureCompress({encoder:sharp,targetFormat:'webp',quality:91,effort:35})]),
    meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16,quantizeTexcoord:16}));
  for(const mesh of doc.getRoot().listMeshes())for(const prim of mesh.listPrimitives()){
    if(!prim.getMaterial()?.getName().startsWith('Q bark '))continue;
    const a=prim.getAttribute('POSITION'),pos=new Float32Array(a.getCount()*3),v=[];
    if(a.getCount()>65535)continue;
    for(let i=0;i<a.getCount();i++)pos.set(a.getElement(i,v),i*3);
    const original=new Uint32Array(prim.getIndices().getArray());
    const [far]=MeshoptSimplifier.simplifySloppy(original,pos,3,null,Math.floor(original.length*.16/3)*3,.09);
    if(far.length>=36 && far.length<original.length*.65){
      // The coarse index still points into the same uploaded vertex/UV buffers.
      prim.setExtras({...prim.getExtras(),distantWood:Buffer.from(new Uint16Array(far).buffer).toString('base64')});
    }
  }
  const tmp=output+'.tmp.glb';
  await io.write(tmp,doc);
  await fs.rename(tmp,output);
  console.log(name, (await fs.stat(output)).size);
}
