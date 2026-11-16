import * as THREE from 'three';

// Repeated coaches in the supplied GLBs share meshes. Batch their visible
// instances together and retire each car only after it is inside the portal.
function consist(group, axis) {
  group.updateWorldMatrix(true,true);
  const bounds=new THREE.Box3().setFromObject(group,true);
  const origin=group.position[axis], ends=[bounds.min[axis]-origin,bounds.max[axis]-origin];
  const inverse=group.matrixWorld.clone().invert(), batches=new Map();
  const model=group.children[0];
  for(const car of model.children) {
    const box=new THREE.Box3().setFromObject(car);
    car.traverse(mesh=>{
      if(!mesh.isMesh) return;
      const key=mesh.geometry.uuid+mesh.material.uuid;
      if(!batches.has(key)) batches.set(key,{geometry:mesh.geometry,material:mesh.material,parts:[]});
      batches.get(key).parts.push({matrix:inverse.clone().multiply(mesh.matrixWorld),
        lo:box.min[axis]-origin,hi:box.max[axis]-origin});
    });
  }
  group.remove(model);
  for(const batch of batches.values()){
    const mesh=new THREE.InstancedMesh(batch.geometry,batch.material,batch.parts.length*(axis==='x'?5:1));
    mesh.name='Passing '+batch.geometry.name;mesh.frustumCulled=false;mesh.castShadow=mesh.receiveShadow=true;
    const name=batch.material.name;
    if (/CRH baked|silver_white|CRH coach|CRH durable|wordmark|CRH pearl/.test(name)){
      if(batch.material.map)batch.material.map.anisotropy=8;
      if(/wordmark|CRH coach frames|CRH durable|CRH coach windows/.test(name)){
        mesh.userData.noNormal=true;mesh.castShadow=mesh.receiveShadow=false;
        batch.material.polygonOffset=true;batch.material.polygonOffsetFactor=-1;
        batch.material.polygonOffsetUnits=-1;
      }
    }
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);batch.mesh=mesh;group.add(mesh);
  }
  group.userData.ends=ends;
  const transform=new THREE.Matrix4();
  return {ends, place(centre, lineOrigin, limit, offsets) {
    group.position[axis]=lineOrigin+centre;
    for(const {parts,mesh} of batches.values()){
      let count=0;
      for(const dx of offsets){
        for(const p of parts){
          if(centre+dx+p.lo>limit || centre+dx+p.hi < -limit) continue;
          transform.copy(p.matrix);
          // The green train's nose is local -Z and the viaduct runs along +X.
          if(dx) transform.elements[14]-=dx;
          mesh.setMatrixAt(count++,transform);
        }
      }
      mesh.count=count;mesh.visible=count>0;mesh.instanceMatrix.needsUpdate=true;
    }
  }};
}

export function railway(zones) {
  const green=consist(zones.city.train,'x'), outbound=consist(zones.rail.hsr,'z'), inbound=consist(zones.rail.harmony,'z');
  const pitch=green.ends[1]-green.ends[0]+13;
  const approach=108+Math.max(outbound.ends[1],inbound.ends[1]), speed=32;
  const finish=(2*approach+20)/speed;
  let cityTime=0, bridgeTime=0,cityActive=false,bridgeActive=false;
  // Integrate a 1.8-second smooth start; clocks run before the island is visible.
  const runningTime=t=>t<1.8?1.8*((t/1.8)**3-.5*(t/1.8)**4):t-.9;
  const single=[0], copies=[];
  return {
    get bridgeComplete(){return runningTime(bridgeTime)>=finish;},
    get clocks(){return {cityTime,bridgeTime};},
    reset(){cityTime=bridgeTime=0;cityActive=bridgeActive=false;},
    update(dt,mode,p,reduced){
      const map=mode==='overview',travel=mode==='travel'||mode==='approach';
      const cityRange=p>=.405&&p<.715,bridgeRange=p>=.629&&p<.93;
      if(travel&&!reduced){
        if(cityRange){
          if(!cityActive){cityTime=p>=.504?3:0;cityActive=true;}
          cityTime+=dt;
        }else{cityTime=0;cityActive=false;}
        if(bridgeRange){
          if(!bridgeActive){bridgeTime=p>=.715?3:0;bridgeActive=true;}
          bridgeTime+=dt;
        }else{bridgeTime=0;bridgeActive=false;}
      }
      if(!zones.city.group.visible && !zones.rail.group.visible) return;
      if(zones.city.group.visible){
        const distance=runningTime(cityTime)*6.9, lap=Math.floor(distance/pitch);
        copies.length=0;
        for(let n=-2;n<=Math.min(lap,2);n++) copies.push(n*pitch);
        green.place(map||reduced?0:distance%pitch-green.ends[1]-18,0,135,map||reduced?single:copies);
      }
      if(zones.rail.group.visible){
        // Reset the next pair only while both full consists are behind the tunnels.
        // The background keeps moving even while a ticket is being read.
        const phase=runningTime(bridgeTime)%(finish+.6);
        const z=map||reduced ? 42 : approach-speed*phase;
        outbound.place(z,zones.rail.spec.center,118,single);
        inbound.place(-z,zones.rail.spec.center,118,single);
      }
    }
  };
}
