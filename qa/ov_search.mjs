import { chromium } from 'playwright';
const b=await chromium.launch({headless:true,executablePath:'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
const c=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
const p=await c.newPage();
await p.goto('http://127.0.0.1:8124/?ovs=1&v='+Date.now(),{waitUntil:'networkidle'});
await p.waitForFunction(()=>window.__ready,null,{timeout:120000});
const res=await p.evaluate(()=>{
  const C=window.__changlu.camera;
  const V=C.position.constructor;
  C.aspect=390/844; C.updateProjectionMatrix();
  const zones=window.__changlu.zones;
  const boxes={};
  for(const [id,z] of Object.entries(zones)){
    z.group.updateMatrixWorld(true);
    let mn=[1e9,1e9,1e9],mx=[-1e9,-1e9,-1e9];
    z.group.traverse(o=>{if(o.isMesh){o.geometry.computeBoundingBox();const bb=o.geometry.boundingBox.clone();bb.applyMatrix4(o.matrixWorld);mn=[Math.min(mn[0],bb.min.x),Math.min(mn[1],bb.min.y),Math.min(mn[2],bb.min.z)];mx=[Math.max(mx[0],bb.max.x),Math.max(mx[1],bb.max.y),Math.max(mx[2],bb.max.z)];}});
    boxes[id]=[mn,mx];
  }
  const target=[0,20,-800];
  const out=[];
  for(const az of [-30,-15,0,15,30,45,60,75,90,105,120]){
   for(const el of [15,25,35,45,55,65]){
    for(const dist of [1800,2400,3000,3600,4200]){
     for(const fov of [38,44,50]){
      const a=az*Math.PI/180, e=el*Math.PI/180;
      const pos=[target[0]+Math.sin(a)*Math.cos(e)*dist, target[1]+Math.sin(e)*dist, target[2]+Math.cos(a)*Math.cos(e)*dist];
      C.position.set(...pos); C.fov=fov; C.lookAt(new V(...target)); C.updateProjectionMatrix(); C.updateMatrixWorld(true);
      let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9, ok=true, minw=1e9;
      const centers=[];
      for(const [id,[mn,mx]] of Object.entries(boxes)){
        let bx0=1e9,bx1=-1e9,by0=1e9,by1=-1e9;
        for(let i=0;i<8;i++){
          const v=new V(i&1?mx[0]:mn[0], i&2?mx[1]:mn[1], i&4?mx[2]:mn[2]).project(C);
          const sx=(v.x*.5+.5)*390, sy=(-v.y*.5+.5)*844;
          bx0=Math.min(bx0,sx);bx1=Math.max(bx1,sx);by0=Math.min(by0,sy);by1=Math.max(by1,sy);
        }
        x0=Math.min(x0,bx0);x1=Math.max(x1,bx1);y0=Math.min(y0,by0);y1=Math.max(y1,by1);
        centers.push({id,x:+(bx0+bx1)/2,y:+(by0+by1)/2,w:+(bx1-bx0)});
        if(bx0<6||bx1>384||by0<118||by1>716) ok=false;
      }
      if(ok){ out.push({az,el,dist,fov,pos:pos.map(v=>+v.toFixed(0)),x0:+x0.toFixed(0),x1:+x1.toFixed(0),y0:+y0.toFixed(0),y1:+y1.toFixed(0),centers}); }
     }
    }
   }
  }
  out.sort((a,b)=>{const aw=Math.min(...a.centers.map(c=>c.w)),bw=Math.min(...b.centers.map(c=>c.w));return bw-aw;});
  return {n:out.length,best:out.slice(0,6)};
});
console.log(JSON.stringify(res,null,1));
await b.close();
