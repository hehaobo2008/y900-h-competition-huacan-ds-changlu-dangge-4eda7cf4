import { chromium } from 'playwright';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const root = process.cwd();
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME || chromium.executablePath() });
for (const [src, out, landscape] of [
  ['docs/flow.html', 'docs/交互流程图.pdf', true],
  ['docs/design.html', 'docs/设计说明.pdf', false],
]) {
  const page = await browser.newPage({ viewport: { width: landscape ? 1600 : 900, height: landscape ? 1130 : 1273 } });
  await page.goto(pathToFileURL(path.join(root, src)).href, { waitUntil: 'load' });
  await page.waitForTimeout(800);
  await page.pdf({ path: path.join(root, out), format: 'A4', landscape, printBackground: true, preferCSSPageSize: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  console.log('PDF', out);
  await page.close();
}
await browser.close();
