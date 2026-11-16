import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';
import {chromium} from 'playwright';import {pathToFileURL} from 'node:url';
const checks=[],metrics={};const check=(ok,name)=>{assert(ok,name);checks.push(name)};
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const p=await browser.newPage({viewport:{width:1600,height:900}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.route(/^https?:/,r=>r.abort());
try{
 await p.goto(pathToFileURL(path.resolve('dist/山河织路-离线单文件.html')).href);
 await p.waitForFunction(()=>window.__ready||window.__error,null,{timeout:120000});
 check(await p.evaluate(()=>!!window.__ready&&!window.__error),'Offline production loads');
 await p.waitForFunction(()=>getComputedStyle(document.querySelector('#loading')).visibility==='hidden');
 await p.evaluate(()=>{__changlu.freeze();__changlu.start();__changlu.automaticLetters(false)});
 const geometry=await p.evaluate(()=>{
  const a=__changlu,rail=a.zones.rail.group;rail.updateWorldMatrix(true,true);
  const bounds=name=>{let low=Infinity,high=-Infinity,n=0;rail.traverse(o=>{if(o.isMesh&&o.material?.name===name){const v=o.geometry.attributes.position;for(let i=0;i<v.count;i++){const p=o.position.clone().fromBufferAttribute(v,i);o.localToWorld(p);low=Math.min(low,p.z);high=Math.max(high,p.z);n++;}}});return {low,high,centre:(low+high)/2,n}};
  return {plaque:bounds('Valley bridge enamel'),letters:bounds('Bridge ivory letters'),root:rail.position.toArray()};
 });
 metrics.bridge=geometry;
 check(geometry.plaque.n>0&&Math.abs(geometry.plaque.centre-geometry.root[2])<.002,'Bridge plaque is centred on the middle of the span');
 check(geometry.letters.n>0&&Math.abs(geometry.letters.centre-geometry.root[2])<.15,'Plaque lettering is visually centred');
 const movement=await p.evaluate(()=>{
  const a=__changlu;a.setProgress(.84);a.step(0);const root=a.zones.future.metro;
  const cars=root.children.filter(o=>o.name.startsWith('Metro'));
  const sample=()=>cars.map(c=>({p:c.position.toArray(),yaw:c.rotation.y}));
  const dormant=sample();a.setProgress(.86);for(let i=0;i<60;i++)a.step(1/60);const beforeEntry=sample();
  a.setProgress(.945);a.settle(24);const first=sample();let residual=0,minGap=Infinity,maxGap=0;
  // Drive several laps with a stationary camera and inspect the full guideway.
  for(let f=0;f<720;f++){a.step(1/6);const s=sample();
   for(let i=0;i<5;i++){const [x,y,z]=s[i].p;residual=Math.max(residual,Math.abs(((x+18)/70)**2+((z+12)/48)**2-1),Math.abs(y-13.82));
    if(i){const d=Math.hypot(...s[i].p.map((v,k)=>v-s[i-1].p[k]));minGap=Math.min(minGap,d);maxGap=Math.max(maxGap,d);}}
  }
  return {names:cars.map(c=>c.name),dormant,beforeEntry,first,last:sample(),residual,minGap,maxGap,p:a.state.progress};
 });
 metrics.metro=movement;
 check(movement.names.length===5,'Future metro has five independently positioned coaches');
 check(movement.dormant.every((v,i)=>Math.hypot(...v.p.map((x,k)=>x-movement.beforeEntry[i].p[k]))>5),'Future metro starts before island entry');
 check(movement.p===.945&&movement.first.every((v,i)=>Math.hypot(...v.p.map((x,k)=>x-movement.last[i].p[k]))>5),'Future metro keeps moving with stationary camera');
 check(movement.residual<1e-8,'All five cars stay on the guideway centreline around the entire loop');
 check(movement.minGap>9.40&&movement.maxGap<9.46,'Articulated car spacing remains stable around bends');
 check(new Set(movement.last.map(c=>c.yaw.toFixed(2))).size===5,'Each coach follows its own track tangent');
 check(!await p.evaluate(()=>!!document.querySelector('#previewUI')||!!window.__earthPreview),'Prototype has no entry point in production');
 check(errors.length===0,'No browser errors');
 fs.mkdirSync('qa/transit',{recursive:true});fs.writeFileSync('qa/transit/results.json',JSON.stringify({checks:checks.length,passed:checks,metrics,errors},null,2));console.log('PASS',checks.length,'transit checks');
}finally{await browser.close()}
