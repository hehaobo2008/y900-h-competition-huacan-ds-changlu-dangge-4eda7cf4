import * as THREE from 'three';
const points=[[-12,10,23],[11,11,-480],[-6,24,-848],[-3,38,-1260],[102,15,-1760]];
export function createOpeningLights(scene,texture){
  const group=new THREE.Group();group.name='Opening era lights';group.userData.noNormal=true;scene.add(group);
  const lamps=points.map(p=>{
    const lamp=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,color:'#e99b51',transparent:true,
      opacity:0,depthTest:false,depthWrite:false,fog:false,toneMapped:false,blending:THREE.AdditiveBlending}));
    lamp.position.set(...p);lamp.scale.setScalar(100);lamp.renderOrder=6;group.add(lamp);return lamp;
  });
  return {
    update(t,still=false){
      group.visible=true;
      const fade=still?1:1-THREE.MathUtils.smoothstep(t,5.6,6.7);
      lamps.forEach((lamp,i)=>lamp.material.opacity=.9*fade*(still?1:THREE.MathUtils.smoothstep(t,2.7+i*.42,3.3+i*.42)));
    },
    dispose(){scene.remove(group);lamps.forEach(lamp=>lamp.material.dispose())}
  };
}
