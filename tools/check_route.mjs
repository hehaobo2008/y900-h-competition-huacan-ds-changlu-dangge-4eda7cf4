import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';
import { chromium } from 'playwright';

const directory=path.resolve(process.argv[2]||'qa/refinement/route');
fs.mkdirSync(directory,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME||chromium.executablePath(),args:['--enable-webgl','--ignore-gpu-blocklist']});
const page=await browser.newPage({viewport:{width:1152,height:648},deviceScaleFactor:1});
const rows=[
  [.10,.123,.15,.177,.201,.217,.230,.244],
  [.259,.28,.315,.347,.379,.40,.429,.45],
  [.48,.505,.53,.545,.565,.588,.614,.646],
  [.666,.701,.735,.76,.79,.813,.847,.875],
  [.90,.922,.94,.95,.964,.977,.989,1]
];
try{
  await page.goto(new URL('?capture=1',process.env.CAPTURE_URL||'http://127.0.0.1:18174/').href,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.__ready,null,{timeout:90000});
  await page.evaluate(()=>{__changlu.start();__changlu.automaticLetters(false);__changlu.freeze();});
  const style=await page.addStyleTag({content:'#app > :not(#world),#world > :not(canvas){display:none!important}'});
  for(const [i,row] of rows.entries()){
    const thumbs=[];
    for(const [j,p] of row.entries()){
      await page.evaluate(p=>{const a=__changlu;a.state.time=10;a.setProgress(p);a.settle(15);if(p>=.504&&p<.847)for(let k=0;k<30;k++)a.step(1/24);a.settle(45);},p);
      const file=path.join(directory,Math.round(p*1000)+'.jpg');
      const data=await page.screenshot({path:file,type:'jpeg',quality:91});
      thumbs.push({input:await sharp(data).resize(256,144).png().toBuffer(),left:j%4*256,top:Math.floor(j/4)*165},
        {input:Buffer.from('<svg width="256" height="20"><text x="8" y="15" fill="#dfd6c7" font-size="14">'+p+'</text></svg>'),left:j%4*256,top:Math.floor(j/4)*165+144});
    }
    await sharp({create:{width:1024,height:330,channels:3,background:'#29303a'}}).composite(thumbs).jpeg({quality:88}).toFile(path.join(directory,'act-'+(i+1)+'.jpg'));
  }
  await style.evaluate(s=>s.remove());
  for(const [label,width,height] of [['wide',1440,900],['phone',390,844]]){
    await page.setViewportSize({width,height});
    await page.evaluate(()=>{const a=__changlu;a.setProgress(.545);a.advance(.016);a.settle(75);});
    await page.waitForTimeout(340);await page.screenshot({path:path.join(directory,'hud-'+label+'.jpg'),quality:90});
  }
} finally{await browser.close();}
