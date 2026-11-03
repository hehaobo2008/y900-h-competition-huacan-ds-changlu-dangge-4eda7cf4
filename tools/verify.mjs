import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'dist');
const shots = path.join(root, 'qa', 'optimized');
fs.mkdirSync(shots, { recursive: true });
assert(fs.existsSync(path.join(dist, 'app.js')), 'Run npm run build first');
const types = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.css':'text/css', '.png':'image/png', '.glb':'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).replace(/^\/nested\//, '/');
  const file = path.resolve(dist, '.' + (pathname.endsWith('/') ? pathname + 'index.html' : pathname));
  if (!file.startsWith(dist + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const candidates = [process.env.CHROME, chromium.executablePath(), 'C:/Users/HC/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'];
const executablePath = candidates.find(file => file && fs.existsSync(file));
const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}), args: ['--enable-webgl','--ignore-gpu-blocklist'] });
const errors = [];
let assertions = 0;
function check(value, message) { assert(value, message); assertions++; }
async function open(context, url = origin + '/') {
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__ready || window.__error, null, { timeout: 45000 });
  check(await page.evaluate(() => window.__ready && !window.__error), 'World loaded');
  await page.waitForFunction(() => getComputedStyle(document.querySelector('#loading')).visibility === 'hidden');
  return page;
}
async function mode(page, expected) { await page.waitForFunction(m => window.__changlu.state.mode === m, expected); }
async function chapter(page, index) {
  await page.locator(`#timeline [data-ch="${index}"]`).click();
  await page.waitForFunction(i => window.__changlu.state.chapter === i && !window.__changlu.state.jumping, index);
  check(await page.locator(`#timeline [data-ch="${index}"]`).getAttribute('aria-current') === 'step', 'Current chapter announced');
}
async function capture(page, name) {
  await page.waitForFunction(() => !document.querySelector('#ink').classList.contains('on') && [...document.querySelectorAll('.card.show,.info.show,.finale.show,.endcard.show')].every(node => Number(getComputedStyle(node).opacity) > .99));
  // Settle lighting independently of the travel timeline for reproducible QA.
  await page.evaluate(() => window.__changlu.settle(24));
  await page.waitForTimeout(100);
  await page.screenshot({ path: path.join(shots, name + '.png') });
}
async function layout(page) {
  return page.evaluate(() => {
    const rect = selector => { const r = document.querySelector(selector).getBoundingClientRect(); return { x:r.x, y:r.y, width:r.width, height:r.height }; };
    return { width:innerWidth, height:innerHeight, scrollWidth:document.documentElement.scrollWidth, world:rect('#world'), canvas:rect('#gl'), start:rect('#startBtn'), gallery:rect('.chapter-gallery'), title:rect('.title') };
  });
}

try {
  if (!process.argv.includes('--recovery-only')) {
  const desktop = await browser.newContext({ viewport: { width:1440, height:960 }, deviceScaleFactor:1 });
  const page = await open(desktop);
  let box = await layout(page);
  check(Math.abs(box.world.width - box.canvas.width) <= 2 && Math.abs(box.world.height - box.canvas.height) <= 2, 'Canvas fits exhibition frame, allowing its border');
  await capture(page, 'desktop-cover');
  await page.locator('#landingInfoBtn').click();
  check(await page.locator('#infoClose').evaluate(node => node === document.activeElement), 'Dialog receives focus');
  check(await page.locator('#landing').evaluate(node => node.inert), 'Background is inert while reading');
  await page.keyboard.press('Escape');
  check(await page.locator('#landingInfoBtn').evaluate(node => node === document.activeElement), 'Dialog restores focus');
  await page.locator('#landingOverviewBtn').click(); await mode(page, 'overview');
  await page.waitForTimeout(1800); await capture(page, 'desktop-overview');
  await page.locator('#ovBack').click(); await mode(page, 'landing');
  await page.locator('[data-entry="2"]').click();
  await page.waitForFunction(() => window.__changlu.state.chapter === 2 && !window.__changlu.state.jumping);
  check(await page.evaluate(() => document.body.classList.contains('dark-scene')), 'Night scene has legible light UI');
  await capture(page, 'desktop-city');
  await page.locator('#memoryBtn').click();
  check(await page.locator('#cardTitle').textContent() === '夜班车', 'Memory matches current era');
  const paused = await page.evaluate(() => window.__changlu.state.progress);
  await page.mouse.wheel(0, 250);
  await page.waitForTimeout(300);
  check(await page.evaluate(() => window.__changlu.state.progress) === paused, 'Reading pauses movement and wheel input');
  await page.keyboard.press('Tab');
  check(await page.locator('#cardClose').evaluate(node => node === document.activeElement), 'Focus stays inside memory card');
  await capture(page, 'desktop-memory'); await page.keyboard.press('Escape');
  await page.locator('#autoBtn').click();
  await page.waitForFunction(p => window.__changlu.state.progress > p + .001, paused);
  await page.mouse.wheel(0, 60);
  check(await page.evaluate(() => !window.__changlu.state.auto), 'Manual movement stops autoplay');
  for (let i = 0; i < 5; i++) {
    await chapter(page, i);
    if (i === 3) { check(!await page.evaluate(() => document.body.classList.contains('dark-scene')), 'Dawn uses dark, readable UI'); await capture(page, 'desktop-rail'); }
    await page.locator('#memoryBtn').click(); await page.keyboard.press('Escape');
  }
  check(await page.locator('#collectedTxt').textContent() === '拾光 5 / 5', 'All memories collected exactly once');
  await page.reload({waitUntil:'networkidle'}); await page.waitForFunction(() => window.__ready); await page.waitForTimeout(1500);
  check(await page.evaluate(() => window.__changlu.state.collected.size) === 5, 'Collection survives reload');
  await page.locator('#startBtn').click(); await mode(page,'travel');
  await page.locator('#soundBtn').click();
  check(await page.evaluate(() => window.__changlu.soundInfo().on), 'Sound turns on after user gesture');
  await page.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable:true, get:() => true }); document.dispatchEvent(new Event('visibilitychange')); });
  await page.waitForFunction(() => window.__changlu.soundInfo().state === 'suspended');
  check(await page.evaluate(() => window.__changlu.soundInfo().bed === null), 'Background sound schedulers stop');
  await page.evaluate(() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); });
  await page.waitForFunction(() => window.__changlu.soundInfo().state === 'running' && window.__changlu.soundInfo().bed !== null);
  check(await page.evaluate(() => window.__changlu.soundInfo().on), 'Foreground restores the current soundscape');
  await page.locator('#soundBtn').click();
  check(!await page.evaluate(() => window.__changlu.soundInfo().on), 'Sound turns off');
  await page.evaluate(() => { window.__changlu.setProgress(1); }); await mode(page, 'finalePrompt');
  await page.locator('#wishInput').fill('Home m End · 愿每一条路都有归途');
  await page.locator('#wishInput').press('Home'); await page.locator('#wishInput').press('ArrowUp');
  check(await page.evaluate(() => window.__changlu.state.mode === 'finalePrompt' && !window.__changlu.state.sound), 'Typing does not trigger travel or sound shortcuts');
  await page.locator('[data-wish="愿心之所向，皆有路可往"]').click();
  check(await page.locator('#wishInput').inputValue() === '愿心之所向，皆有路可往', 'Wish preset fills input');
  await capture(page, 'desktop-wish');
  const originalChildren = await page.evaluate(() => window.__changlu.scene.children.length);
  await page.locator('#launchBtn').click(); await mode(page,'finale');
  await page.evaluate(() => window.__changlu.step(2)); await capture(page,'desktop-launch');
  await page.evaluate(() => window.__changlu.step(8)); await mode(page, 'ended');
  check(await page.locator('#endWish').textContent() === '愿心之所向，皆有路可往', 'Ending contains chosen wish');
  await capture(page, 'desktop-ending');
  await page.locator('#endOverviewBtn').click(); await mode(page,'overview'); await page.locator('#ovBack').click(); await mode(page,'ended');
  check(await page.locator('#endCard').evaluate(node => !node.inert), 'Overview returns to usable ending');
  await page.locator('#againBtn').click(); await mode(page,'travel');
  check(await page.evaluate(() => window.__changlu.scene.children.length) === originalChildren, 'Replay disposes launch effects');
  await page.locator('#homeBtn').click(); await mode(page,'landing');
  check(await page.evaluate(() => !window.__changlu.state.started && !window.__changlu.state.modal), 'Return to cover resets navigation');
  await desktop.close();
  console.log('PASS desktop: chapter navigation, memories, autoplay, dialogs, audio, launch, replay');

  for (const [name, width, height] of [['phone',390,844],['landscape',844,390],['small-phone',360,640]]) {
    const context = await browser.newContext({viewport:{width,height},deviceScaleFactor:1,isMobile:true,hasTouch:true});
    const mobile = await open(context);
    box = await layout(mobile);
    check(box.scrollWidth === width, name + ' has no horizontal overflow');
    check(box.start.y >= 0 && box.start.y + box.start.height <= box.gallery.y && box.start.y + box.start.height <= height, name + ' has a reachable start button above the gallery');
    check(box.world.height > 90 && box.world.y + box.world.height <= box.gallery.y, name + ' scene does not overlap chapter gallery');
    await capture(mobile, name + '-cover');
    await mobile.locator('#startBtn').tap(); await mode(mobile,'travel');
    await chapter(mobile,3); await capture(mobile,name+'-travel');
    await mobile.locator('#memoryBtn').tap(); await capture(mobile,name+'-memory'); await mobile.locator('#cardClose').tap();
    await mobile.locator('#overviewBtn').tap(); await mode(mobile,'overview');
    await mobile.waitForTimeout(2200); await capture(mobile,name+'-overview');
    const label = mobile.locator('.ov-label[data-zone="town"]');
    const lb = await label.boundingBox();
    check(lb && lb.x >= 0 && lb.y >= 0 && lb.x+lb.width <= width && lb.y+lb.height <= height, name+' overview has an accessible town label');
    await label.tap(); await mode(mobile,'travel');
    await mobile.evaluate(() => window.__changlu.setProgress(1)); await mode(mobile,'finalePrompt');
    await capture(mobile,name+'-wish');
    const finaleBox = await mobile.locator('#finale').boundingBox();
    check(finaleBox.y >= 0 && finaleBox.y+finaleBox.height <= height, name+' wish panel fits viewport');
    await mobile.locator('#skipFinale').tap(); await mode(mobile,'ended');
    await context.close();
    console.log('PASS ' + name + ': layout, touch navigation, memory, overview, finale');
  }

  const nestedContext = await browser.newContext({viewport:{width:1280,height:800},reducedMotion:'reduce'});
  const nested = await open(nestedContext, origin+'/nested/');
  check(await nested.evaluate(() => window.__changlu.renderer.domElement.width > 0), 'Subdirectory deployment resolves assets');
  await nested.locator('#startBtn').click(); await nested.evaluate(() => window.__changlu.setProgress(1)); await mode(nested,'finalePrompt');
  await nested.locator('#launchBtn').click(); await mode(nested,'ended');
  check(await nested.evaluate(() => window.__changlu.zones.future.rocket.position.y) === 7, 'Reduced motion skips launch movement');
  await nestedContext.close();
  console.log('PASS nested deployment and reduced motion');

  const offlineContext = await browser.newContext({viewport:{width:1280,height:800}});
  const offline = await open(offlineContext, pathToFileURL(path.join(dist,'山河织路-离线单文件.html')).href);
  await offline.locator('[data-entry="1"]').click(); await offline.waitForFunction(() => window.__changlu.state.chapter === 1 && !window.__changlu.state.jumping);
  await offline.locator('#memoryBtn').click();
  check(await offline.locator('#cardTitle').textContent() === '第一辆自己的车', 'Offline scenes and memories work without a server');
  await capture(offline,'offline-memory'); await offlineContext.close();
  console.log('PASS offline single file');
  }

  const failureContext = await browser.newContext();
  await failureContext.route('**/assets/zones/rural.glb', route => route.fulfill({status:404,body:'Missing'}));
  const failure = await failureContext.newPage();
  await failure.goto(origin+'/'); await failure.waitForFunction(() => !!window.__error);
  check(await failure.locator('#retryBtn').evaluate(node => node === document.activeElement && !node.closest('[inert]')), 'Missing model shows accessible recovery');
  await failureContext.close();
  const noGLContext = await browser.newContext();
  await noGLContext.addInitScript(() => { const get = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function(type,...args) { return type.startsWith('webgl') ? null : get.call(this,type,...args); }; });
  const noGL = await noGLContext.newPage(); await noGL.goto(origin+'/'); await noGL.waitForFunction(() => !!window.__error);
  check(await noGL.locator('#errorScreen').isVisible(), 'WebGL initialization failure has a useful fallback');
  await noGLContext.close();
  check(errors.length === 0, 'No runtime or console errors: ' + errors.join('\n'));
  if (!process.argv.includes('--recovery-only')) fs.writeFileSync(path.join(shots, 'results.json'), JSON.stringify({ checks: assertions, runtimeErrors: errors, screenshots: fs.readdirSync(shots).filter(name => name.endsWith('.png')) }, null, 2));
  console.log(`PASS ${assertions} checks; screenshots: ${shots}`);
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
