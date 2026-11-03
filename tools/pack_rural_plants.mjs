import { NodeIO } from '@gltf-transform/core';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const io = new NodeIO();
for (const name of ['grass_bermuda_01','weed_plant_02']) {
  const file = path.join(root,'assets','vegetation',name+'.glb');
  const doc = await io.read(file);
  const material = doc.getRoot().listMaterials()[0];
  material.getBaseColorTexture()
    .setImage(fs.readFileSync(path.join(root,'assets','vegetation','source',name,'basecolor_alpha.png')))
    .setMimeType('image/png');
  material.setAlphaMode('MASK').setAlphaCutoff(.45).setDoubleSided(true);
  await io.write(file,doc);
  console.log(name, 'packed with opacity');
}
