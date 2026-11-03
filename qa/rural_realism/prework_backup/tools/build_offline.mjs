import { build } from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dir, '..');
const dist = path.join(root, 'dist');
const appJs = path.join(dist, 'app.js');
if (!fs.existsSync(appJs)) throw new Error('run tools/build_h5.mjs first');
const js = fs.readFileSync(appJs, 'utf8');
const css0 = fs.readFileSync(path.join(root, 'src/style.css'), 'utf8');
const html0 = fs.readFileSync(path.join(root, 'src/index.html'), 'utf8');

const files = [
  ...['rural','town','city','rail','future'].map(f => `assets/zones/${f}.glb`),
  ...['rickshaw','car','green_train','hsr','rocket'].map(f => `assets/vehicles/${f}.glb`),
  ...['cloud.png','glow.png','star.png','smoke.png','shadow.png','grain.png','ink.png','seal.png'].map(f => `assets/textures/${f}`),
];
const mime = (p) => p.endsWith('.glb') ? 'model/gltf-binary' : p.endsWith('.png') ? 'image/png' : p.endsWith('.jpg') ? 'image/jpeg' : 'application/octet-stream';
const map = {};
for (const rel of files) {
  const buf = fs.readFileSync(path.join(root, rel));
  map['/' + rel] = `data:${mime(rel)};base64,${buf.toString('base64')}`;
}
const dataCSS = (p) => {
  const rel = p.replace(/^(?:\.\/|\/)/, '');
  return `data:${mime(rel)};base64,${fs.readFileSync(path.join(root, rel)).toString('base64')}`;
};
let css = css0.replace(/url\(['"]?((?:\.\/|\/)assets\/[^)'"]+)['"]?\)/g, (_, p) => `url('${dataCSS(p)}')`);
let html = html0
  .replace(/<link rel="icon" href="[^"]+">/, `<link rel="icon" href="${map['/assets/textures/seal.png']}">`)
  .replace(/<link rel="stylesheet" href="\.\/style\.css">/, `<style>\n${css}\n</style>`)
  .replace(/src="\/assets\/textures\/seal\.png"/g, `src="${map['/assets/textures/seal.png']}"`);
const payload = `window.__ASSET_MAP = ${JSON.stringify(map)};\n${js}`.replace(/<\/script/gi, '<\/script');
html = html.replace('<script src="./app.js"></script>', () => `<script>\n${payload}\n</script>`);
const out = path.join(dist, '山河织路-离线单文件.html');
fs.writeFileSync(out, html);
console.log('OFFLINE', (fs.statSync(out).size / 1048576).toFixed(1) + 'MB', out);
