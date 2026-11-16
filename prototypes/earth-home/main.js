import '../../src/bootstrap.js';
import * as THREE from 'three';
import {ASSET} from '../../src/assets.js';
import {launchExhaust} from '../../src/launch_exhaust.js';
import {makeEarthWorld,makeStars,softenSky} from './planet.js';
import {DURATION,SWITCH_TIME,RADIUS,clamp,smooth,flightPose,orbitalPose} from './choreography.js';

const $=s=>document.querySelector(s),origin=new THREE.Vector3(102,0,-1760),north=new THREE.Vector3(-.6,0,-.8);
let time=0,playing=false,ready=false,previous=performance.now(),a,world,exhaust,launchStars,point;
const rocketMaterials=[];
let debug={};
async function prepare(){
 while(!window.__ready||getComputedStyle($('#loading')).visibility!=='hidden')await new Promise(requestAnimationFrame);
 a=window.__changlu;a.freeze();a.start();a.automaticLetters(false);
 a.state.mode='travel';a.state.finaleShown=true;a.state.progress=a.state.target=1;a.state.modal=null;a.settle(24);
 softenSky(a.sky.mat);
 const textures=new THREE.TextureLoader();
 const [smoke,glow]=await Promise.all([textures.loadAsync(ASSET('/assets/textures/smoke.png')),textures.loadAsync(ASSET('/assets/textures/glow.png'))]);
 exhaust=launchExhaust(a.zones.future.rocket,a.scene,smoke);
 a.zones.future.rocket.traverse(o=>{if(o.isMesh&&o.material?.isMeshStandardMaterial&&!rocketMaterials.some(r=>r.m===o.material)){
  const m=o.material;rocketMaterials.push({m,opacity:m.opacity});m.transparent=true;m.needsUpdate=true;
 }});
 point=new THREE.Sprite(new THREE.SpriteMaterial({map:glow,color:'#fff0cd',transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false,fog:false}));
 point.position.set(0,10,0);point.userData.noNormal=true;point.name='Rocket distant light';a.zones.future.rocket.add(point);
 launchStars=makeStars();a.scene.add(launchStars);
 world=await makeEarthWorld(a.renderer,a.sky);
 // Compile the orbital view before playback, so the hidden scene switch has no
 // first-frame shader compilation pause.
 setOrbitCamera(17);world.render(orbitalPose(17,innerWidth/innerHeight,innerHeight).altitude);
 a.renderer.compileAsync&&await a.renderer.compileAsync(world.scene,world.camera);
 $('#previewLoading').hidden=true;ready=true;draw(0);
 window.__earthPreview={
  seek(t){playing=false;time=clamp(t,0,DURATION);draw(time)},
  play(){if(time>=DURATION)time=0;playing=true;},
  get time(){return time},get ready(){return ready},duration:DURATION,
  get camera(){return time<SWITCH_TIME?a.camera:world.camera},get world(){return world},
  get metrics(){return {...debug}}
 };
}
function setOrbitCamera(t){
 const pose=orbitalPose(t,innerWidth/innerHeight,innerHeight),camera=world.camera;
 const radial=new THREE.Vector3(0,Math.cos(pose.arc),0).addScaledVector(north,Math.sin(pose.arc));
 const forward=north.clone().multiplyScalar(Math.cos(pose.arc)).add(new THREE.Vector3(0,-Math.sin(pose.arc),0));
 camera.position.copy(radial).multiplyScalar(RADIUS+pose.altitude);
 const direction=forward.clone().multiplyScalar(Math.cos(pose.pitch)).addScaledVector(radial,Math.sin(pose.pitch));
 camera.up.copy(radial).multiplyScalar(Math.cos(pose.pitch)).addScaledVector(forward,-Math.sin(pose.pitch)).normalize();
 camera.lookAt(camera.position.clone().add(direction));camera.fov=pose.fov;camera.updateProjectionMatrix();camera.updateMatrixWorld();
 return pose;
}
function draw(t){
 const flight=flightPose(Math.min(t,SWITCH_TIME)),rocket=a.zones.future.rocket;
 if(t<SWITCH_TIME){
  a.step(0);a.camera.clearViewOffset();a.state.finaleShown=true;
  rocket.position.copy(origin).setY(flight.rocket);rocket.scale.setScalar(1);rocket.rotation.set(0,0,0);rocket.visible=flight.fade>0;
  for(const {m,opacity} of rocketMaterials)m.opacity=opacity*flight.fade;
  exhaust.update(t);rocket.getObjectByName('Engine exhaust').material.uniforms.power.value=smooth(0,.8,t)*flight.fade;
  point.scale.setScalar(90);point.material.opacity=smooth(6,8,t)*flight.fade*.8;
  const camera=a.camera;camera.position.copy(origin).add(new THREE.Vector3(.6*flight.range,flight.camera,.8*flight.range));
  camera.up.set(0,1,0);camera.lookAt(origin.x,flight.rocket+30,origin.z);
  camera.far=160000;camera.fov=52;camera.updateProjectionMatrix();camera.updateMatrixWorld();
  const space=smooth(7,12.7,t);
  a.sky.group.visible=true;a.sky.group.position.copy(camera.position);a.sky.mat.uniforms.vacuumFade.value=space;a.sky.mat.uniforms.upperAtmosphere.value=smooth(2.5,4.6,t);
  launchStars.position.copy(camera.position);launchStars.material.opacity=space*.55;
  a.scene.fog.near=8000;a.scene.fog.far=50000;
  a.paper.paperPass.uniforms.ink.value=.14;a.paper.paperPass.uniforms.grainAmount.value=.04;
  a.paper.render();
  const bottom=origin.clone().setY(flight.rocket).project(camera),top=origin.clone().setY(flight.rocket+60).project(camera);
  debug={stage:'launch',rocketHeight:flight.rocket,cameraHeight:flight.camera,rocketPixels:Math.abs(top.y-bottom.y)*innerHeight/2,rocketOpacity:flight.fade,pitch:flight.pitch*180/Math.PI,oldPropsVisible:true};
 }else{
  // All former islands, buildings, vehicles, sprites and stage scenery leave
  // the rendered world while the camera still looks upward.
  for(const z of Object.values(a.zones))z.group.visible=false;
  rocket.visible=false;launchStars.visible=false;
  const pose=setOrbitCamera(t);world.render(pose.altitude,smooth(7,12.7,t));
  debug={stage:'orbit',rocketHeight:flight.rocket,cameraHeight:pose.altitude,rocketPixels:0,rocketOpacity:0,pitch:pose.pitch*180/Math.PI,oldPropsVisible:false,planetRadius:RADIUS};
 }
 if(t<SWITCH_TIME)launchStars.visible=true;
 $('#previewWords').textContent=t<5?'从这里，去往更远的地方。':'这里，是家。';
 $('#previewWords').classList.toggle('home',t>=5);
 $('#previewWords').style.opacity=String(t<5?smooth(.2,1.2,t)*(1-smooth(3.1,4.4,t)):smooth(21.9,23.2,t));
 $('#homeLine').style.opacity=String(smooth(23.1,24.5,t));
 $('#timeRange').value=String(t);$('#timeReadout').textContent=String(Math.floor(t)).padStart(2,'0')+' / '+DURATION+' 秒';
 $('#playPreview').textContent=playing?'暂停':'播放';
 $('#phaseLabel').textContent=t<3?'点火':t<10?'目送火箭远去':t<14.6?'地表浮现':t<21.9?'拉远回望':'这里，是家';
}
$('#playPreview').onclick=()=>{if(!ready)return;if(time>=DURATION)time=0;playing=!playing;draw(time)};
$('#replayPreview').onclick=()=>{if(!ready)return;time=0;playing=true;draw(0)};
$('#timeRange').oninput=e=>{if(!ready)return;time=+e.target.value;playing=false;draw(time)};
for(const b of document.querySelectorAll('[data-time]'))b.onclick=()=>{if(!ready)return;time=+b.dataset.time;playing=false;draw(time)};
addEventListener('resize',()=>{if(ready)requestAnimationFrame(()=>{world.resize(innerWidth,innerHeight);draw(time)})});
function frame(now){
 const dt=Math.min(.1,(now-previous)/1000);previous=now;
 if(ready&&playing){time=Math.min(DURATION,time+dt);if(time>=DURATION)playing=false;draw(time);}
 requestAnimationFrame(frame);
}
requestAnimationFrame(frame);prepare().catch(error=>{console.error(error);$('#previewLoading').textContent='小样加载失败：'+error.message;window.__prototypeError=error.message;});
