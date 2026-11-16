import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';
import { chromium } from 'playwright';
import { crossings } from '../src/journey.js';

const code=await build({stdin:{contents:"export {Raycaster,Vector2,Vector3,Box3} from 'three';",resolveDir:process.cwd()},bundle:true,write:false,format:'iife',globalName:'Probe'});
const browser=await chromium.launch({executablePath:process.env.CHROME||chromium.executablePath(),args:['--enable-webgl','--ignore-gpu-blocklist']});
const page=await browser.newPage({viewport:{width:1152,height:648},deviceScaleFactor:1});
try{
  await page.goto(new URL('?capture=1',process.env.CAPTURE_URL||'http://127.0.0.1:18174/').href,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.__ready,null,{timeout:90000});
  await page.locator('#loading').waitFor({state:'hidden'});
  await page.evaluate(()=>{__changlu.start();__changlu.automaticLetters(false);});
  await page.addScriptTag({content:code.outputFiles[0].text});
  await page.evaluate(()=>__changlu.freeze());
  const maxClothEdge=await page.evaluate(()=>{
    const a=__changlu;
    const cloth=a.zones.town.group.children.find(o=>o.material?.name==='RedCloth') || a.zones.town.group.getObjectByName('Town_RedCloth');
    if(!cloth) throw Error('Missing cloth mesh');
    const {position}=cloth.geometry.attributes,idx=cloth.geometry.index,vertices=[new Probe.Vector3(),new Probe.Vector3(),new Probe.Vector3()];
    let longest=0;
    for(let i=0;i<idx.count;i+=3){
      for(let j=0;j<3;j++) vertices[j].fromBufferAttribute(position,idx.getX(i+j)).applyMatrix4(cloth.matrixWorld);
      for(let j=0;j<3;j++) longest=Math.max(longest,vertices[j].distanceTo(vertices[(j+1)%3]));
    }
    return longest;
  });
  assert(maxClothEdge<12,'Cloth at the cinema must not span multiple buildings: '+maxClothEdge);
  const samples=[];
  for(const [w,h] of [[1440,900],[390,844],[360,740],[844,390]]){
    await page.setViewportSize({width:w,height:h});
    for(const p of [.545,.554,.569,.593,.629]){
      const row=await page.evaluate(p=>{
        const a=__changlu;a.setProgress(p);a.advance(.016);a.settle(45);
        for(let n=0;n<90;n++)a.step(1/30);a.paper.render();
        const city=a.zones.city;
        let name;
        city.group.traverse(o=>{if(o.name.replace(/_/g,' ')==='Changluli name') name=o;});
        if(!name) throw Error('Missing dimensional station name');
        const bounds=new Probe.Box3().setFromObject(name),z=bounds.max.z+.025;
        const pts=[], blockers=new Set();
        const solid=[];
        city.group.traverseVisible(o=>{if(o.isMesh && !o.isInstancedMesh && !o.material.transparent) solid.push(o);});
        city.train.traverseVisible(o=>{if(o.isInstancedMesh && o.count>0){o.computeBoundingSphere();solid.push(o);}});
        const ray=new Probe.Raycaster(),eye=a.camera.position;
        for(const u of [0,.25,.5,.75,1])for(const v of [0,.5,1]){
          const point=new Probe.Vector3(bounds.min.x+u*(bounds.max.x-bounds.min.x),bounds.min.y+v*(bounds.max.y-bounds.min.y),z);
          ray.set(eye,point.clone().sub(eye).normalize());ray.far=eye.distanceTo(point)-.025;
          ray.intersectObjects(solid,false).forEach(hit=>blockers.add(hit.object.name));
          const q=point.project(a.camera);pts.push([q.x,q.y]);
        }
        const clip=pts.some(([x,y])=>Math.max(Math.abs(x),Math.abs(y))>.997);
        const projectedWidth=(Math.max(...pts.map(p=>p[0]))-Math.min(...pts.map(p=>p[0])))*innerWidth/2;
        return {p,width:innerWidth,height:innerHeight,clip,blockers:[...blockers],nameWidth:Math.round(projectedWidth)};
      },p);
      samples.push(row);
      assert(!row.clip && !row.blockers.length,JSON.stringify(row));
    }
  }
  const flights=[];
  for(const [width,height] of [[1152,648],[390,844]]){
    await page.setViewportSize({width,height});
    await page.waitForFunction(()=>Math.abs(__changlu.camera.aspect-innerWidth/innerHeight)<.002);
    const rows=await page.evaluate(({intervals,measureSolids})=>{
      const a=__changlu,camera=a.camera, names=['rural','town','city','rail','future'];
      const eyeAt=p=>{a.setProgress(p);a.step(1/60);return camera.position.clone();};
      return intervals.map(([start,end],i)=>{
        const Z=-420*i,from=names[i],to=names[i+1];
        const meshes=[];
        if(measureSolids) for(const name of [from,to]){
          a.zones[name].group.traverse(o=>{
            if(!o.isMesh || o.isInstancedMesh || o.userData.noNormal || !o.geometry.attributes.position || o.material.transparent) return;
            if(!o.geometry.boundingBox) o.geometry.computeBoundingBox();
            meshes.push(o);
          });
        }
        const points=[],hits=new Set(),ray=new Probe.Raycaster(),direction=new Probe.Vector3();
        let maxStep=0,maxTurn=0,bothBanks=0,dualViews=0,maxY=0,angle=null,minZ=Infinity,maxZ=-Infinity;
        for(let k=0;k<=96;k++){
          const p=start+(end-start)*k/96,eye=eyeAt(p);
          if(k>0){
            const last=points[k-1],distance=eye.distanceTo(last);
            maxStep=Math.max(maxStep,distance);maxTurn=Math.max(maxTurn,angle.angleTo(camera.quaternion)*180/Math.PI);
            if(measureSolids && distance>0){
              ray.set(last,direction.copy(eye).sub(last).normalize());ray.far=distance+.09;
              for(const hit of ray.intersectObjects(meshes,false)) hits.add(hit.object.name);
            }
          }
          maxY=Math.max(maxY,eye.y);minZ=Math.min(minZ,eye.z);maxZ=Math.max(maxZ,eye.z);
          const live=a.zones[from].group.visible && a.zones[to].group.visible;
          if(a.scene.getObjectByName('Island binding '+(i+1))) throw Error('Unexpected world thread');
          if(live && a.state.crossing){
            dualViews++;
            const visibleEdge=z=>[-125,-75,-30,0,30,75,125].some(x=>{
              const q=new Probe.Vector3(x,1,z).project(camera);
              return q.z>-1 && q.z<1 && Math.abs(q.x)<.98 && Math.abs(q.y)<.98;
            });
            if(visibleEdge(Z-148) && visibleEdge(Z-272)) bothBanks++;
          }
          angle=camera.quaternion.clone();points.push(eye);
        }
        let reverseError=0;
        for(let k=96;k>=0;k--){
          const eye=eyeAt(start+(end-start)*k/96);
          reverseError=Math.max(reverseError,eye.distanceTo(points[k]));
        }
        return {from,to,width:innerWidth,start,end,dualViews,bothBanks,maxY,maxStep,maxTurn,reverseError,
          crossesGap:maxZ>Z-148&&minZ<Z-272,hits:[...hits]};
      });
    },{intervals:crossings,measureSolids:width===1152});
    flights.push(...rows);
  }
  for(const row of flights){
    assert(row.crossesGap && row.maxY>75 && row.dualViews>=95 && row.bothBanks>=3 && row.reverseError<.001,JSON.stringify(row));
    assert(row.maxStep<12 && row.maxTurn<11 && row.hits.length===0,JSON.stringify(row));
  }
  const input={};
  const startingPoint=.227;
  const place=(p)=>{const a=__changlu;a.setProgress(p);a.advance(1/60);};
  const runFrames=n=>{for(let i=0;i<n;i++) __changlu.step(1/60);return __changlu.state.progress;};
  await page.setViewportSize({width:1152,height:648});
  await page.evaluate(place,startingPoint);
  await page.mouse.move(570,215);await page.mouse.wheel(0,110);
  await page.waitForFunction(p=>__changlu.state.target>p,startingPoint);
  input.wheel=await page.evaluate(runFrames,24);
  await page.keyboard.press('ArrowUp');
  input.reverse=await page.evaluate(runFrames,20);
  assert(input.wheel>startingPoint && input.reverse<input.wheel);
  await page.evaluate(place,startingPoint);
  await page.locator('#autoBtn').click();
  input.auto=await page.evaluate(runFrames,90);
  assert(input.auto>startingPoint && input.auto<.270);
  await page.locator('#autoBtn').click();
  await page.evaluate(place,.1);
  await page.locator('#timeline [data-ch="1"]').click();
  input.chapter=await page.evaluate(()=>{
    const a=__changlu;let frames=0,flightFrames=0,covered=false;
    while(a.state.jumping && frames++<1200){
      a.step(1/60);
      if(a.state.crossing){flightFrames++;covered ||= document.querySelector('#ink').classList.contains('on');}
    }
    return {flightSeconds:flightFrames/60,covered,at:a.state.progress};
  });
  assert(input.chapter.flightSeconds>1.7 && !input.chapter.covered && Math.abs(input.chapter.at-.315)<.00001);
  const touch=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,hasTouch:true,isMobile:true});
  try{
    await touch.goto(page.url(),{waitUntil:'networkidle'});
    await touch.waitForFunction(()=>window.__ready||window.__error,null,{timeout:120000});assert.equal(await touch.evaluate(()=>window.__error),undefined);await touch.locator('#loading').waitFor({state:'hidden'});
    await touch.evaluate(()=>{__changlu.start();__changlu.automaticLetters(false);});
    await touch.evaluate(()=>__changlu.freeze());
    await touch.evaluate(place,startingPoint);
    const driver=await touch.context().newCDPSession(touch);
    await driver.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:192,y:382}]});
    for(const y of [373,365,353,342]) await driver.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:192,y}]});
    await driver.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    input.swipe=await touch.evaluate(runFrames,24);
    assert(input.swipe>startingPoint && input.swipe<.270,'Real swipe from '+startingPoint+' reached '+input.swipe);
  }finally{await touch.close();}
  const labels=[];
  for(const [width,height] of [[1440,900],[1152,648],[390,844],[844,390],[360,740]]){
    await page.setViewportSize({width,height});
    const result=await page.evaluate(()=>{
      const a=__changlu;a.overview();a.settle(100);
      const boxes=[...document.querySelectorAll('.ov-label b')].map(el=>el.getBoundingClientRect());
      const pairs=[];
      boxes.forEach((r,i)=>boxes.slice(i+1).forEach((other,j)=>{
        if(r.left<other.right && r.right>other.left && r.top<other.bottom && r.bottom>other.top) pairs.push([i,i+j+1]);
      }));
      return {width:innerWidth,height:innerHeight,pairs,outside:boxes.some(r=>r.left<0||r.right>innerWidth||r.top<0||r.bottom>innerHeight)};
    });
    assert(!result.outside && !result.pairs.length,JSON.stringify(result));labels.push(result);
  }
  const local=await browser.newPage({viewport:{width:1000,height:650}});
  let offlineFlights;
  try{
    await local.route(/^https?:\/\//,r=>r.abort());
    await local.goto(pathToFileURL(path.resolve('dist','山河织路-离线单文件.html')).href);
    await local.waitForFunction(()=>window.__ready,null,{timeout:90000});await local.evaluate(()=>{__changlu.start();__changlu.automaticLetters(false);});
    offlineFlights=await local.evaluate(intervals=>{
      const a=__changlu,gl=a.renderer.getContext(),pixel=new Uint8Array(4);
      a.freeze();
      return intervals.map(([start,end])=>{
        a.setProgress((start+end)/2);a.advance(1/60);a.settle(16);
        const brightness=[];
        for(const x of [.2,.49,.78]) for(const y of [.17,.48,.75]){
          gl.readPixels(Math.floor(x*gl.drawingBufferWidth),Math.floor(y*gl.drawingBufferHeight),1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);
          brightness.push(pixel[0]*.3+pixel[1]*.6+pixel[2]*.1);
        }
        return {islands:Object.keys(a.zones).filter(k=>a.zones[k].group.visible),
          pixelRange:Math.round(Math.max(...brightness)-Math.min(...brightness))};
      });
    },crossings);
    assert(offlineFlights.every(row=>row.islands.length===2 && row.pixelRange>=12),JSON.stringify(offlineFlights));
  }finally{await local.close();}
  fs.writeFileSync('qa/refinement/visibility.json',JSON.stringify({maxClothEdge,samples,flights,input,labels,offlineFlights},null,2)+'\n');
  console.log('Four continuous flights checked in both directions and aspect ratios. Station name clear in '+samples.length+' views.');
}finally{await browser.close();}
