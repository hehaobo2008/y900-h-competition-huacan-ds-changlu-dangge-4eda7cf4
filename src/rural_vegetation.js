import * as THREE from 'three';

// Poly Haven's model contains individual plant variants. Their local meshes
// are instanced by variant; catalogue translations are intentionally ignored.
export function addRuralVegetation(parent, grass, weed, tree, ground, walkable) {
  let seed = 1983;
  const rand = () => { seed = (1664525*seed+1013904223) >>> 0; return seed/4294967296; };
  const roadX = y => 3*Math.sin((y+145)/52)+1.2*Math.sin((y+20)/19);
  const grassVariants = [];
  grass.scene.traverse(o => { if (o.isMesh && /medium_[a-f]$/.test(o.name)) grassVariants.push(o); });
  const weedVariants = [];
  weed.scene.traverse(o => { if (o.isMesh && /_LOD0$/.test(o.name)) weedVariants.push(o); });
  const plants = new THREE.Group();
  plants.name = 'Rural_Verge_Plants';
  parent.add(plants);
  const shopTree = tree.scene;
  const height = 5.0;
  shopTree.name = 'Village_Broadleaf_Tree';
  // This source's origin is in the centre of its unit-height mesh.
  shopTree.scale.setScalar(height);
  shopTree.position.set(-6,ground(-6,-55)+height*.50122,55);
  shopTree.rotation.y = .45;
  shopTree.traverse(o => {
    if (!o.isMesh) return;
    o.castShadow = true; o.receiveShadow = true;
    o.material.metalness = 0;
    o.material.roughness = .9;
  });
  plants.add(shopTree);
  const grassPoses = grassVariants.map(() => []);
  const weedPoses = weedVariants.map(() => []);
  for (let y = -81; y < -21; y += 2.1) {
    for (const side of [-1,1]) {
      if (rand() < .17) continue;
      const cy = y + (rand()-.5)*1.4;
      const cx = roadX(cy) + side*(2.9+rand()*2.2);
      for (let n=0;n<12;n++) {
        const x = cx+(rand()-.5)*1.15, yy = cy+(rand()-.5)*1.4;
        if (!walkable(x,-yy)) continue;
        const variant = Math.floor(rand()*grassPoses.length);
        grassPoses[variant].push([x,ground(x,yy)+.025,-yy,rand()*Math.PI*2,.8+rand()*.9]);
      }
      if (weedPoses.length && rand() < .34 && walkable(cx,-cy)) {
        const variant = Math.floor(rand()*weedPoses.length);
        weedPoses[variant].push([cx,ground(cx,cy)+.02,-cy,rand()*Math.PI*2,.8+rand()*.65]);
      }
    }
  }
  const dummy = new THREE.Object3D();
  function batch(variants, poses) {
    variants.forEach((source,i) => {
      if (!poses[i].length) return;
      const mesh = new THREE.InstancedMesh(source.geometry, source.material, poses[i].length);
      mesh.name = 'Verge_' + source.name;
      mesh.castShadow = false;
      mesh.receiveShadow = true;
      poses[i].forEach(([x,y,z,angle,scale],index) => {
        dummy.position.set(x,y,z); dummy.rotation.set(0,angle,0); dummy.scale.setScalar(scale);
        dummy.updateMatrix(); mesh.setMatrixAt(index,dummy.matrix);
      });
      mesh.instanceMatrix.needsUpdate = true;
      mesh.computeBoundingSphere();
      plants.add(mesh);
    });
  }
  batch(grassVariants, grassPoses);
  batch(weedVariants, weedPoses);
  return plants;
}
