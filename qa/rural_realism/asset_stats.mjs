import fs from 'node:fs';
const files=['assets/zones/rural.glb','assets/vehicles/rickshaw.glb',
  'assets/vegetation/grass_bermuda_01.glb','assets/vegetation/weed_plant_02.glb',
  'assets/vegetation/rural_broadleaf.glb'];
const results=[];
for(const file of files){
  const b=fs.readFileSync(file);
  const json=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());
  let triangles=0,vertices=0,primitives=0;
  for(const mesh of json.meshes||[]) for(const p of mesh.primitives){
    primitives++;
    vertices+=json.accessors[p.attributes.POSITION].count;
    triangles+=(p.indices===undefined ? json.accessors[p.attributes.POSITION].count : json.accessors[p.indices].count)/3;
  }
  results.push({file,bytes:b.length,meshes:(json.meshes||[]).length,primitives,vertices,
    triangles,materials:(json.materials||[]).length,embeddedImages:(json.images||[]).length});
}
fs.writeFileSync('qa/rural_realism/asset_stats.json',JSON.stringify(results,null,2));
console.log(JSON.stringify(results,null,2));
