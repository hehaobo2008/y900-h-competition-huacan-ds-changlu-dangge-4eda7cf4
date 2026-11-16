import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';import {spawn} from 'node:child_process';import {once} from 'node:events';
import ffmpeg from 'ffmpeg-static';import {chromium} from 'playwright';
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const p=await browser.newPage({viewport:{width:1280,height:720}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
const target=path.resolve('dist/回望地球-小样预览.mp4');let encoder;
try{
 await p.goto(pathToFileURL(path.resolve('dist/回望地球-独立小样.html')).href);
 await p.waitForFunction(()=>window.__earthPreview?.ready||window.__prototypeError,null,{timeout:120000});
 if(await p.evaluate(()=>window.__prototypeError))throw new Error(await p.evaluate(()=>window.__prototypeError));
 await p.addStyleTag({content:'.preview-controls,.preview-credits,#phaseLabel{display:none!important}'});
 encoder=spawn(ffmpeg,['-y','-f','image2pipe','-vcodec','mjpeg','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',target],{stdio:['pipe','ignore','pipe'],windowsHide:true});
 let messages='';encoder.stderr.on('data',d=>{messages=(messages+d).slice(-2000)});const done=new Promise((resolve,reject)=>{encoder.on('error',reject);encoder.on('exit',code=>code===0?resolve():reject(new Error(messages)))});
 for(let frame=0;frame<26*24;frame++){
  await p.evaluate(t=>__earthPreview.seek(t),frame/24);const buffer=await p.screenshot({type:'jpeg',quality:93});
  if(!encoder.stdin.write(buffer))await once(encoder.stdin,'drain');
  if(frame%120===0)console.log('Rendered',frame/24,'seconds');
 }
 encoder.stdin.end();await done;if(errors.length)throw new Error(errors.join('\n'));console.log('VIDEO',target,fs.statSync(target).size,'bytes');
}finally{encoder?.stdin?.end();await browser.close()}
