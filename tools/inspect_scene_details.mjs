import fs from 'node:fs';
import path from 'node:path';
import {chromium} from 'playwright';
import sharp from 'sharp';

// Identical frozen lighting and camera displacement in both versions expose
// surfaces that exchange depth without confusing them with rain or moving trains.
const dir=path.resolve(process.argv[2] || 'qa/scenery/current');
fs.mkdirSync(dir,{recursive:true});
const views=[
  ['roof',.57,[24,173,-716],[-39,117,-785],34],
  ['paving',.57,[-19,32,-716],[-23,.2,-737],43],
  ['ground',.57,[-143,26,-854],[-142,0,-861],29],
  ['avenue',.55,[-3,4,-810],[.5,2.7,-865],49],
  ['bank',.79,[-34,76,-1204],[0,39,-1144],54],
  ['south',.79,[4,38.2,-1176],[0,37.3,-1152],52],
  ['back',.79,[31,65,-1087],[0,32,-1123],48],
  ['north',.79,[-4,39,-1342],[0,37.5,-1368],50],
  ['forest',.79,[-86,127,-1219],[-55,14,-1200],56],
  ['port',.945,[134,40,-1635],[6,29,-1686],51],
  ['garden',.972,[141,13,-1712],[127,12,-1728],50],
  ['nursery',.972,[135.6,10.1,-1716.6],[126.8,9.2,-1729],52],
  ['gallery',.945,[53,34,-1654],[30,30,-1669],46],
  ['lane',.315,[4.5,3.1,-376.8],[-1.73,3.1,-384.1],55],
  ['boulevard',.55,[-6.4,3.6,-807],[-15.8,3.55,-817],48],
  ['quay',.955,[68,6.7,-1617],[58,6.0,-1632],50],
  ['river-pines',.79,[-18,36,-1333],[-36,30.3,-1344],49],
  ['crowns-above',.79,[-67,72,-1337],[-42,21,-1329],47],
  ['port-trees',.955,[82,5.5,-1624],[88,5.4,-1639],53],
  ['city-trees',.55,[-7.8,4.1,-819],[-15.8,3.8,-830],49]
];
const requested=process.argv.slice(3);
const shots=requested.length?views.filter(([name])=>requested.includes(name)):views;
const browser=await chromium.launch({executablePath:process.env.CHROME || chromium.executablePath(),args:['--enable-webgl','--ignore-gpu-blocklist']});
try{
  const page=await browser.newPage({viewport:{width:1060,height:620},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
  await page.goto(new URL('?capture=1',process.env.CAPTURE_URL || 'http://127.0.0.1:18174/').href);
  await page.waitForFunction(()=>window.__ready,null,{timeout:100000});
  await page.evaluate(()=>{__changlu.start();__changlu.automaticLetters(false);__changlu.freeze();});
  await page.addStyleTag({content:'#app > :not(#world), #world > :not(canvas){display:none!important}'});
  const measure={};
  for(const [name,p,pos,look,fov] of shots){
    await page.evaluate(p=>{const a=__changlu;a.setProgress(p);a.settle(38);},p);
    const samples=['roof','ground','paving','avenue'].includes(name)?[0,.012,-.012,.006]:[0];
    let first;
    for(const offset of samples){
      await page.evaluate(({pos,look,fov,offset})=>{
        const a=__changlu,c=a.camera;c.position.set(pos[0]+offset,pos[1],pos[2]);
        c.lookAt(look[0]+offset,look[1],look[2]);c.fov=fov;c.updateProjectionMatrix();c.updateMatrixWorld();a.paper.render();
      },{pos,look,fov,offset});
      const png=await page.screenshot();
      if(offset===0){await sharp(png).jpeg({quality:92}).toFile(path.join(dir,name+'.jpg'));}
      if(samples.length===1)continue;
      const pixels=await sharp(png).extract({left:200,top:115,width:660,height:405}).greyscale().raw().toBuffer();
      if(!first){first=pixels;measure[name]=[];continue;}
      let changes=0;for(let i=0;i<pixels.length;i++)if(Math.abs(pixels[i]-first[i])>12)changes++;
      measure[name].push(+(changes*100/pixels.length).toFixed(3));
    }
  }
  if(errors.length)throw Error(errors.join('\n'));
  if(Object.keys(measure).length)fs.writeFileSync(path.join(dir,'flicker.json'),JSON.stringify(measure,null,2));
  const tiles=await Promise.all(shots.map(async([name],i)=>({input:await sharp(path.join(dir,name+'.jpg')).resize(310,180).png().toBuffer(),left:(i%3)*310,top:Math.floor(i/3)*180})));
  await sharp({create:{width:930,height:Math.ceil(shots.length/3)*180,channels:3,background:'#e8dfcc'}}).composite(tiles).jpeg({quality:93}).toFile(path.join(dir,'review.jpg'));
  console.log(measure);
}finally{await browser.close();}
