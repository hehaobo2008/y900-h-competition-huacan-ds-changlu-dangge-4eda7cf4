import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';

const stage=process.argv[2]||JSON.parse(fs.readFileSync(new URL('../deployment/hcw.json',import.meta.url),'utf8')).releaseDirectory;
const read=name=>JSON.parse(fs.readFileSync(path.join(stage,name),'utf8').replace(/^\uFEFF/,''));
const files=read('published-files.json'),before=read('production-files.json');
const expected=read('site-files.json').filter(f=>f.path!=='_headers');
const hash=createRequire('C:/Users/HC/AppData/Local/npm-cache/_npx/f53f07989cdda700/node_modules/wrangler/package.json')('blake3-wasm').hash;
assert.deepEqual(Object.keys(files).sort(),expected.map(f=>'/'+f.path).sort());
for(const [name,digest] of Object.entries(files)){
  const file=path.join(stage,'website',name.slice(1));
  assert.equal(hash(fs.readFileSync(file).toString('base64')+path.extname(file).slice(1)).toString('hex').slice(0,32),digest,name);
}
const changed=Object.keys(files).filter(name=>before[name]!==files[name]);
const removed=Object.keys(before).filter(name=>!(name in files));
assert.equal(removed.length,0);
assert(changed.every(name=>name.startsWith('/assets/experiences/aa384c92ca76/')));
assert.deepEqual(changed.sort(),read('release-status.json').changed.map(name=>'/'+name).sort());
const result={verified:expected.length,exactCandidateAssets:true,changed,removed,otherFilesUnchanged:true,openSourceUnchanged:Object.keys(before).filter(name=>name.startsWith('/open-source/')).every(name=>before[name]===files[name])};
assert(result.openSourceUnchanged);
fs.writeFileSync(path.join(stage,'published-asset-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({verified:result.verified,changed:changed.length,removed:0,otherFilesUnchanged:true,openSourceUnchanged:true}));
