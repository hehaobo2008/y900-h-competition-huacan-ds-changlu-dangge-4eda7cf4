import { build } from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dir, '..');
const dist = path.join(root, 'dist');
fs.mkdirSync(dist, { recursive: true });
await build({
  entryPoints: [path.join(root, 'src/bootstrap.js')],
  bundle: true, format: 'iife', target: 'es2020', outfile: path.join(dist, 'app.js'),
  logLevel: 'warning', sourcemap: false, minify: true,
});
const copy = (rel) => {
  const src = path.join(root, rel), dst = path.join(dist, rel);
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
};
fs.copyFileSync(path.join(root,'src/index.html'), path.join(dist,'index.html'));
fs.copyFileSync(path.join(root,'src/style.css'), path.join(dist,'style.css'));
const zones = ['rural','town','city','rail','future'];
const vehicles = ['rickshaw','car','green_train','hsr','rocket'];
const textures = ['cloud.png','glow.png','star.png','smoke.png','shadow.png','grain.png','ink.png','seal.png'];
for (const f of zones) copy(`assets/zones/${f}.glb`);
for (const f of vehicles) copy(`assets/vehicles/${f}.glb`);
for (const f of textures) copy(`assets/textures/${f}`);
const total = fs.readdirSync(path.join(dist,'assets','zones')).reduce((a,f)=>a+fs.statSync(path.join(dist,'assets','zones',f)).size,0);
console.log('H5 built to dist · zones', (total/1048576).toFixed(1)+'MB');
