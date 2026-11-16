import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';import {chromium} from 'playwright';import sharp from 'sharp';
import {flightPose,orbitalPose,SWITCH_TIME,RADIUS,DURATION} from '../prototypes/earth-home/choreography.js';
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const checks=[],errors=[],metrics={};const check=(ok,name)=>{assert(ok,name);checks.push(name)};const out='qa/earth-preview-v3';fs.mkdirSync(out,{recursive:true});
try{
 const speeds=[];
 for(let t=2;t<=9;t+=.25){const a=flightPose(t),b=flightPose(t+.01);speeds.push({time:t,rocket:(b.rocket-a.rocket)/.01,camera:(b.camera-a.camera)/.01});}
 check(speeds.every(s=>s.rocket>s.camera),'Rocket climbs faster than the observer throughout the visible ascent');
 check(flightPose(9.21).fade===0&&SWITCH_TIME>9.21,'Rocket vanishes before any world change or downward turn');
 const orbit=[];for(let t=SWITCH_TIME;t<DURATION;t+=1/60)orbit.push(orbitalPose(t,16/9,900));
 check(orbit.every((s,i)=>i===0||s.altitude>=orbit[i-1].altitude-1e-7),'Observer keeps rising throughout the look back');
 check(orbit.every((s,i)=>i===0||s.pitch<=orbit[i-1].pitch+1e-7),'Look back turns in one continuous direction');
 check(orbit.every((s,i)=>i===0||Math.abs(s.pitch-orbit[i-1].pitch)*180/Math.PI<.65),'No abrupt per-frame camera rotation at 60 Hz');
 const speedAt=t=>{const a=orbitalPose(t,16/9,900),b=orbitalPose(t+.01,16/9,900);return(b.altitude-a.altitude)/.01;};
 check(speedAt(16)>speedAt(14)*8&&speedAt(17)>speedAt(16),'Pullback clearly accelerates after the gentle surface reveal');
 check(orbitalPose(20,16/9,900).altitude>20000&&DURATION===26,'Full Earth arrives early in the 26-second cut');
 check(speedAt(21.8)<.01,'Pullback settles smoothly before the final hold');
 metrics.speeds=speeds;metrics.pullback={early:speedAt(14),building:speedAt(16),fast:speedAt(17),settled:speedAt(21.8)};
 for(const [name,width,height] of [['desktop',1600,900],['phone',390,844],['compact',320,568]]){
  const p=await browser.newPage({viewport:{width,height}});p.on('pageerror',e=>errors.push(e.message));await p.route(/^https?:/,r=>r.abort());
  await p.goto(pathToFileURL(path.resolve('dist/回望地球-独立小样.html')).href);
  await p.waitForFunction(()=>window.__earthPreview?.ready||window.__prototypeError,null,{timeout:120000});
  check(await p.evaluate(()=>!!window.__earthPreview?.ready&&!window.__prototypeError),name+' loads fully offline');
  check(await p.evaluate(()=>{const w=__earthPreview.world,m=w.clouds.material;return m.uniforms.cloudMap.value.image.width===8192&&w.scene.getObjectByName('Cloud underside')&&w.earth.material.uniforms.cloudMap.value===m.uniforms.cloudMap.value}),name+' satellite cloud atlas and cloud shadows load offline');
  const snapshots=[];
  for(const t of [0,4,6,8,9.21,9.39,9.4,11,13,14.5,16,18,20,21.8,24,26]){
   await p.evaluate(t=>__earthPreview.seek(t),t);
   const s=await p.evaluate(()=>{
    const a=__earthPreview,{earth}=a.world,camera=a.camera;camera.updateMatrixWorld();
    const centre=earth.position.clone().project(camera);
    const right=camera.position.clone().setFromMatrixColumn(camera.matrixWorld,0).multiplyScalar(6436);
    const up=camera.position.clone().setFromMatrixColumn(camera.matrixWorld,1).multiplyScalar(6436);
    const project=v=>{v.project(camera);return {x:(v.x+1)*innerWidth/2,y:(1-v.y)*innerHeight/2,z:v.z}};
    let covered=0;
    for(let y=-.9;y<=.91;y+=.3)for(let x=-.9;x<=.91;x+=.3){
     const d=camera.position.clone().set(x,y,.5).unproject(camera).sub(camera.position).normalize();
     const b=camera.position.dot(d),c=camera.position.lengthSq()-6371**2;
     if(b<0&&b*b>=c)covered++;
    }
    const r=document.querySelector('#previewWords').getBoundingClientRect(),line=document.querySelector('#homeLine').getBoundingClientRect(),control=document.querySelector('.preview-controls').getBoundingClientRect();
    return {...a.metrics,time:a.time,far:camera.far,quaternion:camera.quaternion.toArray(),radius:earth.scale.x,centre:centre.toArray(),groundCoverage:covered/49,bounds:[project(earth.position.clone().sub(right)),project(earth.position.clone().add(right)),project(earth.position.clone().add(up)),project(earth.position.clone().sub(up))],textTop:r.top,textBottom:r.bottom,lineTop:line.top,lineBottom:line.bottom,control:{left:control.left,right:control.right,top:control.top,bottom:control.bottom},scroll:document.documentElement.scrollWidth,oldVisible:Object.values(__changlu.zones).some(z=>z.group.visible)};
   });snapshots.push(s);
   if(name==='desktop'||[0,14.5,24].includes(t))await p.screenshot({path:out+'/'+(name==='desktop'?'':name+'-')+t+'.png'});
  }
  const last=snapshots.at(-1),before=snapshots.find(s=>s.time===9.39),after=snapshots.find(s=>s.time===9.4);
  const dot=before.quaternion.reduce((n,v,i)=>n+v*after.quaternion[i],0);
  check(2*Math.acos(Math.min(1,Math.abs(dot)))*180/Math.PI<.03,name+' hidden world switch preserves viewing direction');
  check(snapshots.filter(s=>s.stage==='orbit').every(s=>!s.oldPropsVisible&&!s.oldVisible&&s.radius===RADIUS),name+' old islands disappear and the full-sized Earth remains constant');
  check(snapshots.find(s=>s.time===14.5).groundCoverage>.72,name+' ground fills the view before the globe pulls away');
  check(last.far>60000&&last.centre[2]<1,name+' Earth stays visible at final altitude');
  check(last.bounds.every(v=>v.x>0&&v.x<width&&v.y>45&&v.y<last.textTop-4),name+' final Earth fits above ending text');
  check(last.lineTop>last.textBottom&&last.lineBottom<last.control.top-3,name+' ending caption stays clear of controls');
  check(last.control.left>=0&&last.control.right<=width&&last.control.bottom<=height&&last.scroll===width,name+' controls fit without overflow');
  if(name==='desktop'){
   const images=[];
   for(const t of [9.399,9.4]){await p.evaluate(t=>__earthPreview.seek(t),t);images.push(await sharp(await p.screenshot()).removeAlpha().raw().toBuffer());}
   let diff=0;for(let i=0;i<images[0].length;i++)diff+=Math.abs(images[0][i]-images[1][i]);
   const average=diff/images[0].length/255;metrics.switchDifference=average;
   check(average<.018,'No brightness flash at the off-screen scene switch');
  }
  await p.locator('#replayPreview').click();await p.waitForTimeout(350);await p.locator('#playPreview').click();
  check(await p.evaluate(()=>__earthPreview.time<1&&__earthPreview.metrics.stage==='launch'&&__changlu.zones.future.group.visible),'Replay restores the launch scene');
  await p.locator('[data-time="23"]').click();check(await p.locator('#previewWords').textContent()==='这里，是家。',name+' chapter seek reaches the ending');
  await p.locator('#playPreview').click();await p.waitForTimeout(300);await p.locator('#playPreview').click();
  check(await p.evaluate(()=>__earthPreview.time>23&&__earthPreview.time<24),name+' play and pause operate');
  metrics[name]=snapshots;await p.close();
 }
 check(!errors.length,'No runtime errors');
 fs.writeFileSync(out+'/results.json',JSON.stringify({checks:checks.length,passed:checks,metrics,errors},null,2));console.log('PASS',checks.length,'prototype checks');
}catch(e){for(const c of browser.contexts())for(const p of c.pages())await p.screenshot({path:out+'/failure.png'}).catch(()=>{});throw e;}finally{await browser.close()}
