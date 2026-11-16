import * as THREE from 'three';

// Each oak or pine reuses its source mesh. Keep off-camera branches out of the
// drawing batch, with room for cast shadows and their image in the water below.
export function prepareWoodland(zones) {
  const groups=[],combined=new THREE.Matrix4(),local=new THREE.Matrix4(),sphere=new THREE.Sphere();
  for(const id of ['town','city','rail','future']){
    const group=zones[id].group;
    group.traverse(mesh=>{
      if(!mesh.isInstancedMesh || !/^Q (bark|leaves) /.test(mesh.material.name))return;
      const source=mesh.instanceMatrix.array.slice(),total=mesh.count,centres=new Float32Array(total*4);
      mesh.geometry.computeBoundingSphere();
      for(let i=0;i<total;i++){
        mesh.getMatrixAt(i,local);combined.multiplyMatrices(mesh.matrixWorld,local);
        sphere.copy(mesh.geometry.boundingSphere).applyMatrix4(combined);
        const p=sphere.center;centres.set([p.x,p.y,p.z,sphere.radius+18],i*4);
      }
      mesh.computeBoundingSphere();
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      let farMesh=null;
      if(mesh.geometry.userData.distantWood){
        const bytes=Uint8Array.from(atob(mesh.geometry.userData.distantWood),c=>c.charCodeAt(0));
        const geometry=new THREE.BufferGeometry();
        for(const [name,attribute] of Object.entries(mesh.geometry.attributes))geometry.setAttribute(name,attribute);
        geometry.setIndex(new THREE.BufferAttribute(new Uint16Array(bytes.buffer),1));
        geometry.boundingSphere=mesh.geometry.boundingSphere.clone();
        farMesh=new THREE.InstancedMesh(geometry,mesh.material,total);
        farMesh.name=mesh.name+' distant branches';
        farMesh.matrix.copy(mesh.matrix);farMesh.matrixAutoUpdate=false;
        farMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
        farMesh.boundingSphere=mesh.boundingSphere.clone();
        farMesh.castShadow=mesh.castShadow;farMesh.receiveShadow=mesh.receiveShadow;farMesh.count=0;
      }
      groups.push({group,mesh,farMesh,source,centres,total,mask:new Uint8Array(total).fill(1)});
    });
  }
  for(const {mesh,farMesh} of groups)if(farMesh)mesh.parent.add(farMesh);
  const frustum=new THREE.Frustum(),projection=new THREE.Matrix4();
  return camera=>{
    camera.updateMatrixWorld();
    frustum.setFromProjectionMatrix(projection.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));
    const planes=frustum.planes;
    for(const {group,mesh,farMesh,source,centres,total,mask} of groups){
      if(!group.visible)continue;
      let changed=false;
      for(let i=0;i<total;i++){
        const j=i*4,x=centres[j],y=centres[j+1],z=centres[j+2],radius=centres[j+3];
        let inside=1;
        // Left and right only. Keep tall trees above the frame for reflections.
        for(let side=0;side<2;side++){
          const p=planes[side],n=p.normal;
          if(n.x*x+n.z*z+p.constant+Math.max(n.y*y,n.y*(2-y)) < -radius){inside=0;break;}
        }
        if(inside && farMesh){
          const dx=x-camera.position.x,dy=y-camera.position.y,dz=z-camera.position.z;
          const threshold=(radius-18)*camera.projectionMatrix.elements[5]*(mask[i]===2?7:8.4);
          if(dx*dx+dy*dy+dz*dz>threshold*threshold)inside=2;
        }
        if(mask[i]!==inside){mask[i]=inside;changed=true;}
      }
      if(!changed)continue;
      let count=0,farCount=0;
      for(let i=0;i<total;i++)if(mask[i]){
        const distant=mask[i]===2,batch=distant?farMesh:mesh,index=distant?farCount++:count++;
        batch.instanceMatrix.array.set(source.subarray(i*16,i*16+16),index*16);
      }
      for(const [batch,n] of [[mesh,count],[farMesh,farCount]])if(batch){
        batch.count=n;
        batch.instanceMatrix.clearUpdateRanges();
        if(n)batch.instanceMatrix.addUpdateRange(0,n*16);
        batch.instanceMatrix.needsUpdate=true;
      }
    }
  };
}
