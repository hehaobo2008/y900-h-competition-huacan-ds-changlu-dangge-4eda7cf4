import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';
import sharp from 'sharp';
import { crossings } from '../src/journey.js';

const out=path.resolve('qa/crossings');
fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME||chromium.executablePath(),
  args:['--enable-webgl','--ignore-gpu-blocklist']});
const page=await browser.newPage({viewport:{width:1152,height:648},deviceScaleFactor:1});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error') errors.push(m.text());});
const times=[0,.12,.24,.36,.47,.58,.70,.82,.92,1];
const names=['田埂晨 → 街市暮','街市暮 → 城夜雨','城夜雨 → 山河速','山河速 → 星河远'];
const storyFrames=[0,3,6,9];
try{
  await page.goto(new URL('?capture=1',process.env.CAPTURE_URL||'http://127.0.0.1:18174/').href,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.__ready,null,{timeout:90000});
  await page.evaluate(()=>{__changlu.start();__changlu.automaticLetters(false);__changlu.freeze();});
  await page.addStyleTag({content:'#app > :not(#world),#world > :not(canvas){display:none!important}'});
  for(const [view,width,height] of [['wide',1152,648],['phone',390,844]]){
    await page.setViewportSize({width,height});
    await page.waitForFunction(()=>Math.abs(__changlu.camera.aspect-innerWidth/innerHeight)<.002);
    const rows=[];
    for(const [i,[start,end]] of crossings.entries()){
      const frames=[];
      for(const [j,fraction] of times.entries()){
        const p=start+(end-start)*fraction;
        await page.evaluate(p=>{const a=__changlu;a.setProgress(p);a.state.time=12;a.step(1/60);a.settle(20);},p);
        const buf=await page.screenshot({type:'jpeg',quality:90});
        if(view==='wide' && storyFrames.includes(j)) fs.writeFileSync(path.join(out,`cross-${i+1}-${j}.jpg`),buf);
        const w=view==='phone'?116:260,h=Math.round(w*height/width);
        frames.push({input:await sharp(buf).resize(w,h).toBuffer(),left:j%5*w,top:Math.floor(j/5)*h});
      }
      const w=view==='phone'?116:260,h=Math.round(w*height/width);
      const row=await sharp({create:{width:5*w,height:2*h,channels:3,background:'#e8e1cf'}})
        .composite(frames).jpeg({quality:91}).toBuffer();
      fs.writeFileSync(path.join(out,`${view}-${i+1}.jpg`),row);
      if(view==='wide'){
        const thumbs=await Promise.all(storyFrames.map(j=>sharp(path.join(out,`cross-${i+1}-${j}.jpg`)).resize(310,174).toBuffer()));
        const top=64+i*220;
        rows.push({input:Buffer.from(`<svg width="1236" height="33"><text x="0" y="24" font-family="Microsoft YaHei" font-size="20" fill="#48433b">${names[i]}</text></svg>`),left:20,top});
        thumbs.forEach((input,j)=>rows.push({input,left:20+j*317,top:top+36}));
      }
    }
    if(view==='wide'){
      rows.push({input:Buffer.from('<svg width="1070" height="50"><text x="0" y="35" font-family="Microsoft YaHei" font-size="27" fill="#813c31">山河织路　·　四次跨岛</text></svg>'),left:20,top:8});
      await sharp({create:{width:1300,height:948,channels:3,background:'#f3eddf'}}).composite(rows)
        .jpeg({quality:93}).toFile(path.join(out,'四段跨岛实景.jpg'));
    }
  }
  assert.deepEqual(errors,[]);
  console.log('Four crossings captured at ten stops each on desktop and portrait.');
}finally{await browser.close();}
