// Prepare only the CC0 meshes planted in the four later chapters.
import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { NodeIO } from '@gltf-transform/core';
import { prune, simplifyPrimitive, weld } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';

const source = path.resolve('assets/sources/quaternius-stylized-nature');
const target = path.resolve('assets/vegetation/trees');
await fs.mkdir(target,{recursive:true});
await MeshoptSimplifier.ready;
const io = new NodeIO();
const families = {
  town: {models:['CommonTree_1','CommonTree_2'],shadow:[75,94,54],light:[174,179,98]},
  city: {models:['CommonTree_3','CommonTree_4'],shadow:[50,78,72],light:[133,155,100]},
  river: {models:['CommonTree_5'],shadow:[61,98,77],light:[155,177,109]},
  pine: {models:['Pine_2','Pine_3','Pine_4'],shadow:[42,76,69],light:[122,151,106]},
  silver: {models:['TwistedTree_2','TwistedTree_4'],shadow:[75,116,108],light:[172,197,157]},
  copper: {models:['TwistedTree_1','TwistedTree_5'],shadow:[123,86,83],light:[213,165,121]},
};
const clamp = t => Math.max(0,Math.min(1,t));
function fillLeafClusters(primitive) {
  const pos=primitive.getAttribute('POSITION'),indices=primitive.getIndices().getArray();
  const roots=Array.from({length:pos.getCount()},(_,i)=>i);
  function root(i){while(roots[i]!==i){roots[i]=roots[roots[i]];i=roots[i];}return i;}
  for(let i=0;i<indices.length;i+=3){
    const a=root(indices[i]);roots[root(indices[i+1])]=a;roots[root(indices[i+2])]=a;
  }
  const pieces=new Map(),v=[];
  for(let i=0;i<roots.length;i++){const id=root(i);if(!pieces.has(id))pieces.set(id,[]);pieces.get(id).push(i);}
  for(const cluster of pieces.values()){
    if(cluster.length>48)continue;
    const mid=[0,0,0];
    for(const i of cluster){pos.getElement(i,v);v.forEach((n,k)=>mid[k]+=n/cluster.length);}
    for(const i of cluster){pos.getElement(i,v);pos.setElement(i,v.map((n,k)=>mid[k]+1.19*(n-mid[k])));}
  }
}
function taperRoots(primitive){
  const pos=primitive.getAttribute('POSITION'),v=[],lo=pos.getMin([]),hi=pos.getMax([]);
  // Trim the game kit's broad root flare while preserving the centreline of bent stems.
  const bins=Array.from({length:12},()=>[0,0,0]);
  const fraction=y=>clamp((y-lo[1])/(hi[1]-lo[1]));
  const bin=y=>Math.min(11,Math.floor(fraction(y)*12));
  for(let i=0;i<pos.getCount();i++){pos.getElement(i,v);const b=bins[bin(v[1])];b[0]+=v[0];b[1]+=v[2];b[2]++;}
  for(let i=0;i<pos.getCount();i++){
    pos.getElement(i,v);const b=bins[bin(v[1])],t=clamp((fraction(v[1])-.10)/.36);
    const k=.62+.38*t*t*(3-2*t);
    pos.setElement(i,[b[0]/b[2]+(v[0]-b[0]/b[2])*k,v[1],b[1]/b[2]+(v[2]-b[1]/b[2])*k]);
  }
}
async function leafPaint(input, palette) {
  const {data,info} = await sharp(input).resize(512,512).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  for(let y=0;y<info.height;y++) for(let x=0;x<info.width;x++) {
    const u=x/info.width,v=y/info.height,i=(y*info.width+x)*4;
    const brush=.5+.5*Math.sin(15*u+11*v+.9*Math.sin(19*v));
    const sweep=.5+.5*Math.sin(7*u-8*v+1.5);
    const ink=clamp(.15+.32*brush+.31*sweep+.16*(1-v)+.035*Math.sin(56*u+45*v));
    for(let k=0;k<3;k++)data[i+k]=Math.round(palette.shadow[k]+ink*(palette.light[k]-palette.shadow[k]));
  }
  return sharp(data,{raw:info}).png().toBuffer();
}
for (const [family, palette] of Object.entries(families)) {
  for(const model of palette.models) {
    const doc=await io.read(path.join(source,model+'.gltf'));
    const root=doc.getRoot(),mesh=root.listMeshes()[0];
    await doc.transform(weld());
    for(const primitive of mesh.listPrimitives()) {
      const mat=primitive.getMaterial(),leaves=mat.getName().includes('Leaves');
      mat.setNormalTexture(null).setRoughnessFactor(.91).setMetallicFactor(0);
      const tex=mat.getBaseColorTexture();
      if(leaves) {
        fillLeafClusters(primitive);
        tex.setImage(await leafPaint(tex.getImage(),palette)).setMimeType('image/png').setName('Canopy '+family);
        mat.setName('Q leaves '+family).setDoubleSided(true).setAlphaMode('MASK').setAlphaCutoff(.36);
        const pos=primitive.getAttribute('POSITION'),norm=primitive.getAttribute('NORMAL');
        const lo=pos.getMin([]),hi=pos.getMax([]),a=[],n=[],rgb=[];
        for(let i=0;i<pos.getCount();i++) {
          pos.getElement(i,a);norm.getElement(i,n);
          const h=clamp((a[1]-lo[1])/(hi[1]-lo[1]));
          const dx=(a[0]-(hi[0]+lo[0])/2)/(hi[0]-lo[0]),dz=(a[2]-(hi[2]+lo[2])/2)/(hi[2]-lo[2]);
          const v=[dx*1.25+n[0]*.22,.15+h*.8+n[1]*.12,dz*1.25+n[2]*.22],len=Math.hypot(...v);
          norm.setElement(i,v.map(j=>j/len));
          const light=clamp(.63+.29*h+.08*Math.sin(a[0]*2.1+a[2]*1.32));
          rgb.push(Math.round(255*light),Math.round(255*light),Math.round(255*(light*.89+.11)));
        }
        primitive.setAttribute('COLOR_0',doc.createAccessor().setType('VEC3').setArray(new Uint8Array(rgb)).setNormalized(true).setBuffer(pos.getBuffer()));
      } else {
        taperRoots(primitive);
        tex.setImage(await sharp(tex.getImage()).resize({width:512,height:512,fit:'inside'}).modulate({saturation:.86}).linear(.88,19).png().toBuffer()).setMimeType('image/png');
        mat.setName('Q bark '+(family==='copper'||family==='silver'?'twisted':'branched'));
      }
      simplifyPrimitive(primitive,{simplifier:MeshoptSimplifier,ratio:leaves ? .72 : .17,error:leaves ? .006 : .02});
    }
    await doc.transform(prune());
    mesh.setName(model);
    await io.write(path.join(target,model+'.glb'),doc);
  }
}
