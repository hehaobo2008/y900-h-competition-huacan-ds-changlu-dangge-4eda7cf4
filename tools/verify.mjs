import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
import {letters,endingText} from '../src/letters.js';
import {travelTime,progressAtTime,crossings,hermite} from '../src/journey.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),dist=path.join(root,'dist');
const subset=process.argv.includes('--layout-only')?'layout':process.argv.includes('--arrivals-only')?'arrivals':process.argv.includes('--homecoming-only')?'homecoming':process.argv.includes('--recovery-only')?'recovery':'all';
const out=path.join(root,'qa','tickets');fs.mkdirSync(out,{recursive:true});
assert(fs.existsSync(path.join(dist,'app.js')),'Run npm run build first');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.woff':'font/woff','.png':'image/png','.webp':'image/webp','.glb':'model/gltf-binary'};
const server=http.createServer((req,res)=>{
  const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/^\/nested\//,'/');
  const file=path.resolve(dist,'.'+(name.endsWith('/')?name+'index.html':name));
  if(!file.startsWith(dist+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return}
  res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const base='http://127.0.0.1:'+server.address().port;
const executablePath=[process.env.CHROME,chromium.executablePath(),'C:/Program Files/Google/Chrome/Application/chrome.exe'].find(p=>p&&fs.existsSync(p));
const browser=await chromium.launch({headless:true,...(executablePath?{executablePath}:{}),args:['--enable-webgl','--ignore-gpu-blocklist']});
const checks=[],errors=[],metrics={};
function check(ok,name){assert(ok,name);checks.push(name)}
async function open(options={},url=base+'/'){
  const context=await browser.newContext({viewport:{width:1600,height:900},deviceScaleFactor:1,...options});
  if(url.startsWith('file:'))await context.route(/^https?:/,r=>r.abort());
  const p=await context.newPage();
  p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  await p.goto(url,{waitUntil:'networkidle'});
  await p.waitForFunction(()=>window.__ready||window.__error,null,{timeout:120000});
  check(await p.evaluate(()=>window.__ready&&!window.__error),'World loaded '+url.split('/').at(-1));
  await p.waitForFunction(()=>getComputedStyle(document.querySelector('#loading')).visibility==='hidden');
  await p.evaluate(()=>__changlu.freeze());
  return p;
}
async function step(p,seconds){await p.evaluate(seconds=>{const a=__changlu;let left=seconds;while(left>1e-8){const dt=Math.min(1/60,left);a.step(dt);left-=dt}a.render()},seconds)}
async function place(p,progress){await p.evaluate(t=>{__changlu.setProgress(t);__changlu.settle(24);__changlu.step(0)},progress)}
async function shot(p,name){await p.evaluate(()=>__changlu.render());await p.waitForTimeout(750);await p.screenshot({path:path.join(out,name+'.png')})}
async function start(p){
  const touch=await p.evaluate(()=>matchMedia('(pointer:coarse)').matches);
  await p.locator('#startBtn')[touch?'tap':'click']();await p.locator('#skipIntro')[touch?'tap':'click']();
  await step(p,.01);await mode(p,'travel');
}
async function close(p){await p.context().close()}
async function showTicket(p,t){await place(p,t);await driveToStop(p)}
async function advanceWheel(p,delta=120){await p.evaluate(d=>window.dispatchEvent(new WheelEvent('wheel',{deltaY:d,bubbles:true,cancelable:true})),delta)}
async function mode(p,m){check(await p.evaluate(()=>__changlu.state.mode)===m,'Mode '+m)}
async function fits(p,selector,name){
  await p.waitForTimeout(750); // Measure the settled face, after its CSS flip/size transition.
  check(await p.locator(selector).evaluate(n=>{const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=-1&&r.right<=innerWidth+1&&r.top>=-1&&r.bottom<=innerHeight+1}),name+' fits viewport');
}
async function replay(p){
  await p.locator('#againBtn').click();await mode(p,'prologue');
  check(await p.evaluate(()=>!__changlu.state.replyDraft&&__changlu.state.keptLetter===null&&!__changlu.scene.getObjectByName('Five lights on the way home')&&!__changlu.camera.view?.enabled),'Replay clears draft, kept quote, lights and framing');
  await p.locator('#skipIntro').click();await step(p,.01);
}
async function ending(p,message){
  check(await p.locator('#earthTitle').innerText()==='这次，家是地球','Earth ending uses the chosen final line');
  check(await p.locator('#endCard').getAttribute('data-ending')==='earth','Ending keeps the live Earth visible');
  await p.locator('#endRecord summary').click();
  check(await p.locator('#endAnswer').innerText()===endingText,'Journey record preserves the third-person story');
  if(message)check(await p.locator('#endWish').innerText()===message&&await p.locator('#endRecipient').innerText()==='旅途留言','Visitor text stays a separate inscription');
  else check(await p.locator('#endReply').isHidden(),'Blank message stays blank');
  check(await p.locator('#endTickets .home-ticket').count()===5,'All five paper objects remain in the journey record');
  await fits(p,'.end-record-panel','Journey record');
  await p.locator('#endRecord summary').click();
}
async function opening(p){
  await p.locator('#startBtn').click();await mode(p,'prologue');
  await advanceWheel(p,900);await step(p,1.6);
  check(await p.locator('#introWords').innerText()==='外婆、妈妈、宁宁，\n三代人的回家路。','Third-person three-generation opening');
  check(await p.evaluate(()=>Object.values(__changlu.info().visible).every(Boolean)),'Five islands shown together in opening');
  await shot(p,'opening-1');await step(p,2.9);await shot(p,'opening-2');
  check(await p.evaluate(()=>__changlu.scene.getObjectByName('Opening era lights').children.length)===5,'Opening has five era lights');
  await step(p,5.2);await mode(p,'travel');
  check(await p.evaluate(()=>Math.abs(__changlu.state.progress-.1)<1e-6&&!__changlu.scene.getObjectByName('Opening era lights')),'Opening reaches first composition and disposes its lights');
  check(await p.locator('#walkBtn,#bookScrim,#arrivalBookmark,#finale').count()===0,'No walk controller, bookmark or extra finale popup');
}
async function driveToStop(p,rate=1/60){
  return p.evaluate(dt=>{
    const a=__changlu,log=[];
    for(let f=0;f<Math.ceil(90/dt)&&!(a.state.modal&&a.state.storyStop?.phase!=='revealing');f++){
      if(f%3===0)window.dispatchEvent(new WheelEvent('wheel',{deltaY:1400,cancelable:true}));
      a.step(dt);log.push({p:a.state.progress,v:a.state.metreSpeed,phase:a.state.storyStop?.phase||'travel',visible:!!a.state.modal,time:f*dt});
    }
    const stopped=a.state.progress;
    // Continue the SAME arriving wheel burst without an artificial idle gap.
    for(let i=0;i<20;i++){window.dispatchEvent(new WheelEvent('wheel',{deltaY:1500,cancelable:true}));a.step(.02);}
    const ignoredArrival=a.state.progress===stopped&&a.state.target===stopped&&!!a.state.modal;
    a.paper.render();return {p:a.state.progress,modal:a.state.modal?.id,reading:a.state.reading,ignoredArrival,log};
  },rate);
}
async function arrivals(p){
  const anchors=[.128,.342,.572,.812,1];metrics.stops=[];
  // No progress jumps: stress the entire journey with sustained large wheel input.
  for(let i=0;i<5;i++){
    const trip=await driveToStop(p,i===2?.1:1/60),approach=trip.log.filter(s=>s.phase==='approach'||s.phase==='revealing');
    check(trip.modal==='ticketLayer'&&trip.reading===i,'Continuous wheel reaches ticket '+i+' in order');
    check(Math.abs(trip.p-anchors[i])<1e-7&&trip.log.every(s=>s.p<=anchors[i]+1e-7),'Ticket '+i+' cannot be overrun, including low frame rate');
    check(approach.length>=8&&approach.at(-1).v<.06,'Ticket '+i+' decelerates before stopping');
    const duration=approach.at(-1).time-approach[0].time;
    const atFraction=f=>approach[Math.floor((approach.length-1)*f)].v/approach[0].v;
    check(duration>=3.5&&duration<=5.3,'Ticket '+i+' has a visible multi-second slowdown');
    check(atFraction(.2)>.86&&atFraction(.5)>.44&&atFraction(.5)<.59,'Ticket '+i+' retains speed early and reaches half speed near halfway');
    const peak=approach.findIndex(s=>s.v===Math.max(...approach.map(s=>s.v))),tail=approach.slice(peak);
    check(tail.every((s,j)=>j===0||s.v<=tail[j-1].v+.001),'Ticket '+i+' slows continuously from peak speed');
    const firstReveal=trip.log.find(s=>s.phase==='revealing');
    check(firstReveal?.v>0.2&&firstReveal.p<anchors[i],'Ticket '+i+' starts appearing while the camera is moving');
    check(trip.log.at(-1).time-firstReveal.time>=1.35&&trip.log.at(-1).time-firstReveal.time<=1.6,'Ticket '+i+' reveal overlaps the final slowdown');
    check(trip.log.at(-1).v<.01,'Ticket '+i+' settles as the reveal finishes');
    check(!trip.log.some(s=>s.phase==='waiting'),'Ticket '+i+' opens at arrival without a background-animation gate');
    if(i===3){
      const before=await p.evaluate(()=>__changlu.zones.rail.hsr.position.z);await step(p,.4);
      check(await p.evaluate(()=>__changlu.zones.rail.hsr.position.z)!==before,'Trains keep moving behind the open ticket');
    }
    metrics.stops.push({index:i,anchor:trip.p,rate:i===2?10:60,approach:approach.filter((_,j)=>j%3===0)});
    await shot(p,'stop-front-'+i);
    check(trip.ignoredArrival,'Ticket '+i+' ignores the arriving gesture without queueing');
    await step(p,1.2);
    if(i===2||i===3){
      const visual=await p.locator('#railTicketFace').textContent();
      check(visual.includes(letters[i].rail.service)&&visual.includes(letters[i].rail.className)&&visual.includes(letters[i].rail.seat),'Rail face has service, seat and class');
      check(await p.locator('#ticketFront .ticket-stub').isHidden(),'Rail ticket has no cinema stub');
      check(await p.locator('#railTicketFace svg').evaluate(n=>getComputedStyle(n).stroke==='none'),'Rail type is not thickened by icon styles');
    }
    await p.locator('#ticketFront').focus();
    if(i===1)await p.keyboard.press('r');else await p.locator('#ticketFront').click();
    check(await p.locator('#ticketLayer').getAttribute('data-side')==='back'&&await p.locator('#cardBody').innerText()===letters[i].body,'One click or R flips ticket '+i);
    await shot(p,'stop-back-'+i);await step(p,.5);
    check(await p.evaluate(()=>__changlu.state.progress)===trip.p,'Ticket '+i+' stays readable until a fresh action');
    if(i===0){
      await p.keyboard.press('Shift+Tab');check(await p.locator('#shelveTicket').evaluate(n=>n===document.activeElement),'Focus wraps backwards');
      await p.keyboard.press('Tab');check(await p.locator('#keepLetter').evaluate(n=>n===document.activeElement),'Focus wraps forwards');
      await p.locator('#keepLetter').click();
    }
    if(i<4){
      await p.mouse.move(100,450);await p.waitForTimeout(200);await p.mouse.wheel(0,240);await p.waitForTimeout(50);await step(p,1);
      const continued=await p.evaluate(()=>({modal:!!__changlu.state.modal,stop:!!__changlu.state.storyStop,p:__changlu.state.progress}));
      check(!continued.modal&&!continued.stop&&continued.p>trip.p&&travelTime(continued.p)-travelTime(trip.p)<2.29,'Fresh wheel continues past ticket '+i+' without replaying a burst');
      await step(p,2);check(await p.locator('#ticketLayer').evaluate(n=>!n.classList.contains('show')),'Ticket '+i+' does not immediately repeat');
    }else{
      check(await p.locator('#ticketComposer').isVisible(),'Boarding message stays in the same ticket');
      await p.locator('#wishInput').fill('等星河归来，再聚一桌。');
      await p.locator('#wishInput').dispatchEvent('keydown',{key:'Enter',isComposing:true,bubbles:true});
      check(await p.evaluate(()=>__changlu.state.mode)==='travel','IME confirmation cannot launch');
      await p.locator('#wishInput').press('Home');await p.locator('#wishInput').press('End');
      check(await p.evaluate(()=>!__changlu.state.jumping),'Editing keys do not travel');
      await p.locator('#prevLetter').click();await p.locator('#nextLetter').click();
      check(await p.locator('#wishInput').inputValue()==='等星河归来，再聚一桌。','Draft survives archive navigation');
      check(await p.evaluate(()=>__changlu.state.collected.size)===5,'All five tickets read');
      await p.locator('#skipFinale').click();await mode(p,'ended');await ending(p,'等星河归来，再聚一桌。');
      check(await p.locator('#endQuote').textContent()===letters[0].excerpt,'Kept quote remains separate');
    }
  }
  await replay(p);await p.locator('#autoBtn').click();await step(p,30);
  check(await p.evaluate(()=>__changlu.state.modal?.id==='ticketLayer'&&__changlu.state.resumeAfterTicket),'Autoplay also stops at the node');
  await p.locator('#ticketFront').click();await p.locator('#cardClose').click();
  check(await p.evaluate(()=>__changlu.state.auto&&!__changlu.state.glideSpeed),'Continue resumes autoplay from rest');
  await step(p,1);check(await p.evaluate(()=>__changlu.state.progress)>.128,'Autoplay proceeds after reading');
  await advanceWheel(p,201);await step(p,.15);
  const incoming=await p.evaluate(()=>__changlu.state.metreSpeed);await p.locator('#memoryBtn').click();
  const speeds=await p.evaluate(()=>{const out=[];for(let i=0;i<110;i++){__changlu.step(1/60);out.push(__changlu.state.metreSpeed)}return out});
  check(speeds[0]>incoming*.9&&speeds.every((v,i)=>i===0||v<=speeds[i-1]+1e-6)&&Math.abs(speeds.at(-1))<1e-6,'Manual archive opening still brakes smoothly');
  await p.locator('#ticketFront').focus();await p.keyboard.press('Enter');
  check(await p.locator('#ticketLayer').getAttribute('data-side')==='back','Keyboard flips archive ticket');
  await p.keyboard.press('Escape');check(await p.locator('#memoryBtn').evaluate(n=>n===document.activeElement),'Archive restores focus');
  await p.evaluate(()=>__changlu.automaticLetters(false));const movement=[];
  for(const at of [.13,.34,.555,.775,.945]){
    await place(p,at);await advanceWheel(p);const target=await p.evaluate(()=>__changlu.state.target);
    await step(p,3);const end=await p.evaluate(()=>__changlu.state.progress),a=hermite('pos',at),b=hermite('pos',end);
    movement.push({at,effort:travelTime(target)-travelTime(at),actual:Math.hypot(...b.map((x,i)=>x-a[i]))});
  }
  check(movement.every(m=>Math.abs(m.effort-2.28)<.0001),'Equal wheel effort outside stops in all five scenes');
  check(movement.every(m=>m.actual>2.18&&m.actual<2.29),'Camera ground distance remains consistent');metrics.wheel=movement;
  const arc=p=>{let length=0,previous=hermite('pos',p);for(let i=1;i<=80;i++){const next=hermite('pos',progressAtTime(travelTime(p)+i*.001));length+=Math.hypot(...next.map((x,j)=>x-previous[j]));previous=next}return length/.08};
  metrics.crossings=crossings.map(([a,b])=>({start:arc(a),middle:arc((a+b)/2),end:arc(b)}));
  check(metrics.crossings.every(c=>c.start<1.03&&c.middle>10&&c.end<1.03),'Crossing acceleration remains gradual');
  await p.evaluate(()=>__changlu.automaticLetters(true));await p.locator('#overviewBtn').click();await step(p,2.5);
  await p.locator('.ov-label[data-zone="rail"]').click();
  check(await p.evaluate(()=>__changlu.state.mode==='approach'&&__changlu.state.progress>.7),'Overview directly approaches selected island');
  await step(p,2.2);await driveToStop(p);
  check(await p.evaluate(()=>__changlu.state.reading)===3,'Direct entry still reaches its ticket');
  await p.locator('#ticketFront').click();await p.locator('#cardClose').click();
}
async function backgroundTraffic(p){
  await p.evaluate(()=>__changlu.automaticLetters(false));
  for(const [label,start,arrival,key,axis] of [['green',.400,.504,'city','x'],['high-speed',.625,.715,'rail','z']]){
    for(const wheelGap of [3,18]){
      await place(p,start);
      const traffic=await p.evaluate(({arrival,key,axis,wheelGap})=>{
        const a=__changlu,groups=key==='city'?[a.zones.city.train]:[a.zones.rail.hsr,a.zones.rail.harmony];
        const sample=()=>groups.map(g=>({position:g.position[axis],count:g.children.reduce((n,m)=>n+(m.isInstancedMesh&&m.visible?m.count:0),0)}));
        let before=null;
        for(let i=0;i<20000&&a.state.progress<arrival;i++){
          if(i%wheelGap===0)window.dispatchEvent(new WheelEvent('wheel',{deltaY:wheelGap===3?1400:120,cancelable:true}));
          a.step(1/60);
          if(!before&&a.state.progress>arrival-.018)before=sample();
        }
        const entering=sample();a.setProgress(arrival);
        for(let i=0;i<30;i++)a.step(1/60);
        return {before,entering,later:sample(),p:a.state.progress};
      },{arrival,key,axis,wheelGap});
      check(traffic.before?.every((g,i)=>g.position!==traffic.entering[i].position),label+' already moving before entry at wheel gap '+wheelGap);
      check(traffic.entering.every(g=>g.count>0),label+' visible on island entry at wheel gap '+wheelGap);
      const changes=traffic.later.map((g,i)=>g.position-traffic.entering[i].position);
      check(changes.every(d=>Math.abs(d)>1),label+' moves while the camera is held');
      if(key==='rail')check(changes[0]*changes[1]<0,'High-speed trains move in opposite directions');
      metrics[label+'Traffic'+wheelGap]=traffic;
    }
  }
  await p.locator('#overviewBtn').click();await step(p,2);
  await p.locator('.ov-label[data-zone="rail"]').click();await step(p,.4);
  const before=await p.evaluate(()=>__changlu.zones.rail.hsr.position.z);await step(p,.6);
  check(await p.evaluate(()=>({mode:__changlu.state.mode,z:__changlu.zones.rail.hsr.position.z})).then(s=>s.mode==='approach'&&s.z!==before),'Direct approach includes train pre-roll');
  await step(p,1.2);
  await place(p,.625);await place(p,.812);
  await p.evaluate(()=>{__changlu.state.presented.delete(3);__changlu.automaticLetters(true)});
  await step(p,.1);
  check(await p.evaluate(()=>__changlu.state.modal?.id==='ticketLayer'&&__changlu.state.reading===3),'Bridge ticket appears immediately at its position');
  check(await p.evaluate(()=>[__changlu.zones.rail.hsr,__changlu.zones.rail.harmony].every(g=>g.children.some(m=>m.isInstancedMesh&&m.count>0))),'Ticket is readable while both trains are still passing');
  await p.locator('#ticketFront').click();await p.locator('#cardClose').click();
}
async function fullFlight(p,name='desktop'){
  await place(p,1);await step(p,.6);
  await p.locator('#launchBtn').waitFor({state:'visible'});
  check(await p.locator('#launchBtn').isVisible()&&await p.locator('#ticketLayer').getAttribute('data-side')==='front','Launch is available from unflipped boarding pass: '+JSON.stringify(await p.evaluate(()=>({mode:__changlu.state.mode,modal:__changlu.state.modal?.id,p:__changlu.state.progress,stop:__changlu.state.storyStop?.phase,landing:document.querySelector('#landing').className,side:document.querySelector('#ticketLayer').dataset.side}))));
  const before=await p.evaluate(()=>__changlu.camera.position.toArray());
  await p.locator('#launchBtn').click();await mode(p,'finale');
  check(await p.evaluate(p=>__changlu.camera.position.distanceTo(__changlu.camera.position.clone().fromArray(p))<.001,before),'Launch begins at the current camera position');
  let time=0;const samples=[];
  for(const t of [2,6,8.9,9.39,9.4,14.5,18,21.8,24]){
    await step(p,t-time);time=t;
    samples.push(await p.evaluate(()=>{
      const a=__changlu,r=a.zones.future.rocket,c=a.activeCamera,w=a.ending.world;c.updateMatrixWorld();
      const low=r.position.clone().set(0,0,0),high=low.clone().set(0,60,0);r.localToWorld(low).project(c);r.localToWorld(high).project(c);
      const right=c.position.clone().setFromMatrixColumn(c.matrixWorld,0).multiplyScalar(6436),up=c.position.clone().setFromMatrixColumn(c.matrixWorld,1).multiplyScalar(6436);
      const bounds=[right,right.clone().negate(),up,up.clone().negate()].map(v=>{v.project(c);return{x:(v.x+1)*innerWidth/2,y:(1-v.y)*innerHeight/2}});
      return {...a.ending.metrics,dx:Math.abs(high.x-low.x)*innerWidth/2,quaternion:c.quaternion.toArray(),sceneVisible:a.scene.visible,
        surfaceWidth:w.earth.material.uniforms.surface.value.image.width,cloudWidth:w.clouds.material.uniforms.cloudMap.value.image.width,
        radius:w.earth.scale.x,near:c.near,bounds,titleTop:document.querySelector('#earthTitle').getBoundingClientRect().top,
        width:innerWidth,height:innerHeight,pixelRatio:a.renderer.getPixelRatio(),canvas:[a.renderer.domElement.width,a.renderer.domElement.height]};
    }));
  }
  check(samples[1].rocketHeight>samples[0].rocketHeight&&samples[2].rocketHeight>samples[1].rocketHeight,'Rocket keeps gaining height before it disappears');
  check(samples.slice(0,3).every(x=>x.dx<1),'Rocket projects vertically during ascent');
  check(samples[3].rocketOpacity===0&&samples[4].stage==='orbit','Rocket disappears before the orbital world begins');
  const dot=samples[3].quaternion.reduce((n,x,i)=>n+x*samples[4].quaternion[i],0);
  check(2*Math.acos(Math.min(1,Math.abs(dot)))*180/Math.PI<.03,'Looking direction stays continuous at the hidden scene switch');
  check(samples.slice(4).every(x=>!x.sceneVisible&&x.radius===6371),'Original scenery leaves the frame and Earth never changes scale');
  check(samples.slice(4).every(x=>x.near>=Math.min(500,x.cameraHeight*.01)-1e-5),'Orbital depth precision keeps clouds clear of the ground');
  check(samples.every(x=>x.surfaceWidth===5400&&x.cloudWidth===8192),'Original surface and 8K cloud maps stay at full resolution');
  check(samples.every(x=>x.pixelRatio>=1.5&&x.canvas[0]>=x.width*1.5),'Ending renders above native CSS resolution');
  const last=samples.at(-1);
  check(last.bounds.every(v=>v.x>0&&v.x<last.width&&v.y>20&&v.y<last.titleTop-4),name+' full Earth stays clear of the ending line');
  check(await p.locator('#earthTitle').evaluate(n=>+getComputedStyle(n).opacity)>.99,'Final line fades in after the pullback');
  await shot(p,name+'-earth');metrics[name+'Flight']={samples};
  await step(p,2.1);await mode(p,'ended');await ending(p,'');await shot(p,name+'-ending');
  await p.locator('#endOverviewBtn').click();await step(p,.1);
  check(await p.evaluate(()=>__changlu.scene.visible&&!__changlu.ending.active),'Overview restores the miniature world and releases cinematic control');
  await p.locator('#ovBack').click();await mode(p,'ended');
  check(await p.evaluate(()=>__changlu.ending.inOrbit&&!__changlu.scene.visible),'Returning from overview restores the final Earth view');
  check(await p.locator('#againBtn').evaluate(n=>!n.closest('[inert]')),'Returning from overview leaves ending usable');
  await replay(p);
  check(await p.evaluate(()=>__changlu.scene.visible&&!__changlu.ending.active&&__changlu.sky.mat.uniforms.upperAtmosphere.value===0),'Replay restores the original sky and world');
}
async function mobile(p,name,{touch=false,flight=false}={}){
  await start(p);await showTicket(p,.116);
  await fits(p,'#ticketLayer',name+' front');await shot(p,name+'-front');
  if(touch){
    await step(p,1.3); // The app clock is frozen; let the arrival guard finish before a NEW swipe.
    const driver=await p.context().newCDPSession(p),b=await p.locator('#ticketFront').boundingBox(),x=b.x+b.width*.5,y=b.y+b.height*.7;
    await driver.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
    for(const offset of [15,40,75,100])await driver.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-offset}]});
    await driver.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    await p.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
    await step(p,1);await p.waitForTimeout(550);
    check(await p.evaluate(()=>__changlu.state.progress>.128&&!__changlu.state.modal&&document.querySelector('#ticketLayer').dataset.side==='front'),'A fresh upward swipe continues without accidentally flipping the ticket');
    await p.locator('#memoryBtn').tap();await step(p,1.8);await p.waitForTimeout(550);
  }
  await p.locator('#ticketFront').tap();await p.waitForTimeout(750);await fits(p,'#ticketLayer',name+' back');
  check(await p.locator('#ticketLayer').getAttribute('data-side')==='back'&&await p.locator('#ticketFront').getAttribute('aria-hidden')==='true'&&await p.evaluate(()=>__changlu.state.modal?.id)==='ticketLayer'&&await p.locator('#cardTitle').innerText()===letters[0].backText,name+' touch flips directly to prose');
  await shot(p,name+'-back');await p.locator('#cardClose').tap();
  for(const [idx,at] of [[1,.325],[2,.55],[3,.79]]){
    await showTicket(p,at);await fits(p,'#ticketLayer',name+' rail ticket '+idx);await shot(p,name+'-rail-'+idx);
    check(await p.locator(idx===1?'#objectTicketFace':'#railTicketFace').isVisible(),name+' distinct ticket '+idx+' visible');
    if(touch&&idx===1){
      await step(p,1.3);
      const driver=await p.context().newCDPSession(p),box=await p.locator('#ticketFront').boundingBox(),x=box.x+box.width/2,y=box.y+box.height*.8;
      await driver.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
      for(const offset of [16,42,70,100])await driver.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-offset}]});
      await driver.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await p.waitForTimeout(80);await step(p,1);
      check(await p.evaluate(()=>!__changlu.state.modal&&__changlu.state.progress>.342),'Fresh upward swipe continues without a button or accidental flip');
      await p.waitForTimeout(600);await p.locator('#memoryBtn').tap();await step(p,1.8);
    }
    await p.locator('#ticketFront').tap();await fits(p,'#ticketLayer',name+' rail reverse '+idx);await p.locator('#cardClose').tap();
  }
  await place(p,1);await step(p,.6);
  await fits(p,'#ticketLayer',name+' boarding front');await shot(p,name+'-boarding-front');await p.locator('#ticketFront').tap();await p.waitForTimeout(750);
  await fits(p,'#ticketLayer',name+' boarding reverse');
  await p.locator('#wishInput').fill('等星河归来，再聚一桌。');await p.waitForTimeout(250);
  check(await p.locator('#wishInput').evaluate(n=>{const r=n.getBoundingClientRect(),b=document.querySelector('#ticketBack').getBoundingClientRect();return r.top>=b.top&&r.bottom<=b.bottom}),name+' focused input is fully visible inside ticket');
  check(await p.evaluate(()=>document.documentElement.scrollWidth===innerWidth),name+' no horizontal page overflow');
  await fits(p,'#launchBtn',name+' launch');await shot(p,name+'-boarding');
  await p.locator('[data-wish]').nth(1).tap();const message=letters[4].replies[1];
  check(await p.locator('#wishInput').inputValue()===message,name+' preset fills same message field');
  await p.locator('#skipFinale').tap();await mode(p,'ended');await ending(p,message);await replay(p);
  if(flight)await fullFlight(p,name);
  await place(p,1);await step(p,.6);await p.locator('#skipFinale').tap();await mode(p,'ended');await ending(p,'');
}
async function deployment(){
  const p=await open({viewport:{width:1280,height:800},reducedMotion:'reduce'},base+'/nested/');
  await p.locator('#startBtn').click();await step(p,20);await mode(p,'prologue');
  check(await p.locator('#skipIntro').innerText()==='进入长卷 →','Reduced motion offers a static readable introduction');
  await p.locator('#skipIntro').click();await place(p,1);await step(p,.6);
  await p.locator('#ticketFront').click();await p.locator('#wishInput').fill('归来仍有一盏灯');await p.locator('#launchBtn').click();
  await mode(p,'ended');await ending(p,'归来仍有一盏灯');
  check(await p.evaluate(()=>__changlu.zones.future.rocket.position.y)===7,'Reduced motion omits moving launch');
  await close(p);
  const offline=await open({viewport:{width:1280,height:800}},pathToFileURL(path.join(dist,'山河织路-离线单文件.html')).href);
  check(await offline.evaluate(()=>Object.values(__changlu.sky.plates).every(t=>t.image.width>0)),'Offline textures decode without network');
  await start(offline);await showTicket(offline,.325);await offline.locator('#ticketFront').click();
  check(await offline.locator('#cardBody').innerText()===letters[1].body,'Offline one-click ticket text works');
  await offline.locator('#cardClose').click();await place(offline,1);await step(offline,.6);
  await offline.locator('#ticketFront').click();await offline.locator('#wishInput').fill('离线也有归途');await offline.locator('#skipFinale').click();await ending(offline,'离线也有归途');
  await shot(offline,'offline-ending');await close(offline);
}
async function recovery(){
  const c=await browser.newContext();await c.route('**/assets/zones/rural.glb',r=>r.fulfill({status:404,body:'Missing'}));const p=await c.newPage();
  await p.goto(base+'/');await p.waitForFunction(()=>!!window.__error);
  check(await p.locator('#retryBtn').evaluate(n=>n===document.activeElement&&!n.closest('[inert]')),'Missing model has focused retry');await c.close();
  const g=await browser.newContext();await g.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type.startsWith('webgl')?null:get.call(this,type,...args)}});
  const q=await g.newPage();await q.goto(base+'/');await q.waitForFunction(()=>!!window.__error);
  check(await q.locator('#errorScreen').isVisible(),'WebGL failure shows recovery screen');await g.close();
}
try{
  if(subset!=='recovery'){
    if(subset!=='layout'){
    const p=await open();
    if(subset!=='homecoming'){await opening(p);await arrivals(p);await backgroundTraffic(p);console.log('PASS five gradual arrivals, fresh-gesture continuation, archive, background trains, message and replay')}
    else await start(p);
    if(subset!=='arrivals'){await fullFlight(p);console.log('PASS live Earth ending, source resolution, transitions and replay')}
    await close(p);
    }
    for(const [name,width,height,flight] of [
      ['phone',390,844,true],['small-phone',360,640,false],['compact-phone',320,568,true],['landscape',844,390,false],['short-landscape',568,320,true]
    ].filter(r=>!process.argv.includes('--desktop-only')&&(subset==='all'||subset==='layout'||subset==='homecoming'||r[0]==='phone')&&(!process.argv.includes('--small-only')||['compact-phone','short-landscape'].includes(r[0])))){
      const phone=await open({viewport:{width,height},isMobile:true,hasTouch:true});
      if(subset==='homecoming'){await start(phone);await fullFlight(phone,name);}
      else await mobile(phone,name,{touch:name==='phone',flight:flight&&subset!=='arrivals'});
      await close(phone);console.log('PASS '+name+' touch, reading and endpoint');
    }
    if(subset==='all'||subset==='homecoming'){await deployment();console.log('PASS nested, reduced-motion and offline')}
  }
  if(subset==='all'||subset==='recovery')await recovery();
  check(errors.length===0,'No runtime or console errors: '+errors.join('\n'));
  fs.writeFileSync(path.join(out,subset==='all'?'results.json':subset+'-results.json'),JSON.stringify({checks:checks.length,passed:checks,runtimeErrors:errors,metrics},null,2));
  console.log('PASS '+checks.length+' checks; report and screenshots: '+out);
}catch(error){
  console.error('Runtime errors:',errors);
  for(const c of browser.contexts())for(const p of c.pages())await p.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});
  throw error;
}finally{await browser.close();await new Promise(done=>server.close(done))}
