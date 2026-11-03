import {chromium} from 'playwright';
import fs from 'node:fs';
const out='qa/rural_realism/tree_candidate';
fs.mkdirSync(out,{recursive:true});
const b=await chromium.launch({headless:true,executablePath:process.env.CHROME || 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
try {
  const p=await b.newPage({acceptDownloads:true});
  await p.goto('https://polyyai.itch.io/3d-deciduous-trees-pack',{waitUntil:'domcontentloaded',timeout:45000});
  await p.locator('a.buy_btn:visible').first().click();
  await p.getByText('No thanks, just take me to the downloads').click();
  await p.getByRole('link',{name:'Download',exact:true}).waitFor({timeout:30000});
  const pending=p.waitForEvent('download',{timeout:60000});
  await p.getByRole('link',{name:'Download',exact:true}).click();
  const download=await pending;
  await download.saveAs(out+'/pack.zip');
  console.log('Saved candidate pack:',download.suggestedFilename(),fs.statSync(out+'/pack.zip').size,'bytes');
} finally { await b.close(); }
