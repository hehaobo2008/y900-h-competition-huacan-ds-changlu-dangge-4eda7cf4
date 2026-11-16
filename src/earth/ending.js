import * as THREE from 'three';
import {launchExhaust} from '../launch_exhaust.js';
import {makeEarthWorld,makeStars,softenSky} from './world.js';
import {DURATION,SWITCH_TIME,RADIUS,smooth,flightPose,orbitalPose} from './choreography.js';

export {DURATION,SWITCH_TIME};
const origin=new THREE.Vector3(102,0,-1760),north=new THREE.Vector3(-.6,0,-.8);

export async function createEarthEnding({renderer,scene,camera,paper,sky,rocket,smokeTexture,glowTexture}){
 softenSky(sky.mat);
 const world=await makeEarthWorld(renderer,sky),stars=makeStars();
 stars.visible=false;scene.add(stars);
 const point=new THREE.Sprite(new THREE.SpriteMaterial({map:glowTexture,color:'#fff0cd',transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false,fog:false}));
 point.position.set(0,10,0);point.userData.noNormal=true;point.name='Rocket distant light';rocket?.add(point);
 const materials=[];
 rocket?.traverse(o=>{if(o.isMesh)for(const m of (Array.isArray(o.material)?o.material:[o.material])){
  if(m&&!materials.some(r=>r.m===m))materials.push({m,opacity:m.opacity,transparent:m.transparent});
 }});
 const caption=document.querySelector('#earthCaption'),title=document.querySelector('#earthTitle'),line=document.querySelector('#earthLine');
 let active=false,time=0,exhaust=null,initial=null,metrics={};
 function poseOrbit(t){
  const size=renderer.getSize(new THREE.Vector2()),pose=orbitalPose(t,size.x/size.y,size.y),c=world.camera;
  const radial=new THREE.Vector3(0,Math.cos(pose.arc),0).addScaledVector(north,Math.sin(pose.arc));
  const forward=north.clone().multiplyScalar(Math.cos(pose.arc)).add(new THREE.Vector3(0,-Math.sin(pose.arc),0));
  c.position.copy(radial).multiplyScalar(RADIUS+pose.altitude);
  const direction=forward.clone().multiplyScalar(Math.cos(pose.pitch)).addScaledVector(radial,Math.sin(pose.pitch));
  c.up.copy(radial).multiplyScalar(Math.cos(pose.pitch)).addScaledVector(forward,-Math.sin(pose.pitch)).normalize();
  c.lookAt(c.position.clone().add(direction));c.fov=pose.fov;c.updateProjectionMatrix();c.updateMatrixWorld();
  return pose;
 }
 function resize(width,height){
  if(!active)return;
  world.resize(width,height);
  if(time>=SWITCH_TIME)poseOrbit(time);
 }
 function update(t){
  if(!active)return;
  time=Math.min(DURATION,Math.max(0,t));
  const flight=flightPose(Math.min(time,SWITCH_TIME)),orbit=time>=SWITCH_TIME;
  scene.visible=!orbit;stars.visible=!orbit;
  if(!orbit){
   if(rocket){
    rocket.position.copy(origin).setY(flight.rocket);rocket.scale.setScalar(1);rocket.rotation.set(0,0,0);rocket.visible=flight.fade>0;
    for(const {m,opacity} of materials)m.opacity=opacity*flight.fade;
    exhaust?.update(time);
    const jets=rocket.getObjectByName('Engine exhaust');if(jets)jets.material.uniforms.power.value=smooth(0,.8,time)*flight.fade;
    point.scale.setScalar(90);point.material.opacity=smooth(6,8,time)*flight.fade*.8;
   }
   const blend=smooth(0,1.2,time);
   camera.clearViewOffset();camera.position.copy(origin).add(new THREE.Vector3(.6*flight.range,flight.camera,.8*flight.range));
   camera.position.lerp(initial.position,1-blend);camera.up.set(0,1,0);camera.lookAt(origin.x,flight.rocket+30,origin.z);
   camera.quaternion.slerp(initial.quaternion,1-blend);
   camera.far=160000;camera.fov=THREE.MathUtils.lerp(initial.fov,52,blend);camera.updateProjectionMatrix();camera.updateMatrixWorld();
   sky.group.visible=true;sky.group.position.copy(camera.position);
   sky.mat.uniforms.vacuumFade.value=smooth(7,12.7,time);sky.mat.uniforms.upperAtmosphere.value=smooth(2.5,4.6,time);
   stars.position.copy(camera.position);stars.material.opacity=smooth(7,12.7,time)*.55;
   scene.fog.near=8000;scene.fog.far=50000;
   paper.paperPass.uniforms.ink.value=THREE.MathUtils.lerp(initial.ink,.14,smooth(0,3,time));
   paper.paperPass.uniforms.grainAmount.value=.025;
   metrics={stage:'launch',time,rocketHeight:flight.rocket,cameraHeight:flight.camera,rocketOpacity:flight.fade,oldPropsVisible:true};
  }else{
   if(rocket)rocket.visible=false;
   const pose=poseOrbit(time);
   metrics={stage:'orbit',time,cameraHeight:pose.altitude,rocketOpacity:0,oldPropsVisible:false,planetRadius:RADIUS};
  }
  renderer.toneMappingExposure=1.04;
  const show=time>=21.9;caption.hidden=!show;caption.setAttribute('aria-hidden',String(!show));
  title.style.opacity=String(smooth(21.9,23.2,time));line.style.opacity=String(smooth(23.1,24.5,time));
 }
 function render(){
  if(!active)return;
  if(time>=SWITCH_TIME)world.render(orbitalPose(time,world.camera.aspect,renderer.getSize(new THREE.Vector2()).y).altitude,smooth(7,12.7,time));
  else paper.render();
 }
 function begin(){
  if(active)reset();
  initial={position:camera.position.clone(),quaternion:camera.quaternion.clone(),fov:camera.fov,far:camera.far,
   pixelRatio:renderer.getPixelRatio(),exposure:renderer.toneMappingExposure,
   ink:paper.paperPass.uniforms.ink.value,grain:paper.paperPass.uniforms.grainAmount.value};
  active=true;time=0;
  const size=renderer.getSize(new THREE.Vector2());
  // Supersample the light orbital scene instead of stretching a 720p recording.
  renderer.setPixelRatio(Math.min(2,Math.max(1.5,devicePixelRatio)));
  renderer.setSize(size.x,size.y,false);paper.setSize(size.x,size.y);world.resize(size.x,size.y);
  for(const {m} of materials){m.transparent=true;m.needsUpdate=true;}
  if(rocket)exhaust=launchExhaust(rocket,scene,smokeTexture);
  update(0);
 }
 function reset(){
  if(!active)return;
  active=false;time=0;exhaust?.dispose();exhaust=null;scene.visible=true;stars.visible=false;point.material.opacity=0;
  sky.mat.uniforms.vacuumFade.value=0;sky.mat.uniforms.upperAtmosphere.value=0;
  for(const {m,opacity,transparent} of materials){m.opacity=opacity;m.transparent=transparent;m.needsUpdate=true;}
  if(rocket){rocket.position.set(102,7,-1760);rocket.rotation.set(0,0,0);rocket.scale.setScalar(1);}
  camera.up.set(0,1,0);camera.clearViewOffset();camera.far=initial.far;camera.updateProjectionMatrix();
  renderer.toneMappingExposure=initial.exposure;
  renderer.setPixelRatio(initial.pixelRatio);
  const size=renderer.getSize(new THREE.Vector2());renderer.setSize(size.x,size.y,false);paper.setSize(size.x,size.y);
  paper.paperPass.uniforms.ink.value=initial.ink;paper.paperPass.uniforms.grainAmount.value=initial.grain;
  caption.hidden=true;caption.setAttribute('aria-hidden','true');
  document.querySelector('#endRecord').open=false;
 }
 // Upload full-resolution maps and compile the orbital view behind the loading
 // screen. The small target only saves warm-up work; texture sizes stay intact.
 const output=world.paper.composer.renderToScreen;
 world.paper.composer.renderToScreen=false;world.resize(160,90);poseOrbit(18);
 world.render(orbitalPose(18,16/9,900).altitude);
 await renderer.compileAsync?.(world.scene,world.camera);
 world.paper.composer.renderToScreen=output;renderer.setRenderTarget(null);
 return {begin,update,render,reset,resize,world,
  get active(){return active},get inOrbit(){return active&&time>=SWITCH_TIME},
  get camera(){return active&&time>=SWITCH_TIME?world.camera:camera},
  get pixelRatio(){return Math.min(2,Math.max(1.5,devicePixelRatio))},
  get metrics(){return {...metrics}}
 };
}
