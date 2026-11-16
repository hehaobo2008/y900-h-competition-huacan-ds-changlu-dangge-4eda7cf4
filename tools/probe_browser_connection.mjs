import {chromium} from 'playwright';
const url=process.argv[2]||'https://harmonyconnectwindows.com/404.html';
await Promise.all([
 ['default-tcp',['--no-proxy-server']],
 ['without-quic',['--no-proxy-server','--disable-quic']],
 ['http1-diagnostic',['--no-proxy-server','--disable-quic','--disable-http2']],
].map(async([name,args])=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args});
 const page=await browser.newPage(),cdp=await page.context().newCDPSession(page);await cdp.send('Network.enable');
 let protocol;cdp.on('Network.responseReceived',e=>{if(e.type==='Document')protocol=e.response.protocol});
 const start=Date.now();
 try{const r=await page.goto(url,{waitUntil:'commit',timeout:25000});console.log(JSON.stringify({name,status:r.status(),protocol,seconds:(Date.now()-start)/1000}))}
 catch(e){console.log(JSON.stringify({name,error:e.message,seconds:(Date.now()-start)/1000}))}
 finally{await browser.close()}
}));
