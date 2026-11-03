import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { makePaperPipeline } from './paper.js';
import { applyWater } from './water.js';
const q = new URLSearchParams(location.search);
const night = q.get('night') === '1';
const usePost = q.get('post') !== '0';
const glb = q.get('glb') || '/assets/zones/rural.glb';
const canvas = document.querySelector('#c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = night ? 1.0 : 1.28;
renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
scene.background = new THREE.Color(night ? '#070d18' : '#e8e1d2');
scene.fog = new THREE.Fog(night ? '#0a1420' : (q.get('fog') || '#e8ddc8'), 170, 430);
const sky = new THREE.Mesh(new THREE.SphereGeometry(700, 32, 20), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false,
  uniforms: { top: { value: new THREE.Color(night ? '#040814' : (q.get('sky') || '#9db9bd')) }, bot: { value: new THREE.Color(night ? '#1a2b40' : (q.get('hz') || '#f7e6c9')) }, sunDir: { value: new THREE.Vector3(-0.6, 0.2, -0.55).normalize() }, sunCol: { value: new THREE.Color(night ? '#9fc4ff' : '#ffd9a0') } },
  vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: 'varying vec3 vP; uniform vec3 top; uniform vec3 bot; uniform vec3 sunDir; uniform vec3 sunCol; void main(){ float h = smoothstep(-0.08, 0.55, vP.y); vec3 c = mix(bot, top, h); float d = max(dot(vP, sunDir), 0.0); c += sunCol * pow(d, 80.0) * 0.55; gl_FragColor = vec4(c,1.0); }'
}));
sky.userData.noNormal = true;
scene.add(sky);
const texLoader = new THREE.TextureLoader();
const cloudTex = texLoader.load('/assets/textures/cloud.png');
const cloudMat = new THREE.SpriteMaterial({ map: cloudTex, transparent: true, opacity: .42, depthWrite: false, color: '#f6dfc4', fog: false });
const clouds = [[-360, 115, -560, 280, 95, .58], [40, 145, -610, 360, 110, .45], [380, 105, -560, 300, 90, .5], [-560, 80, -420, 240, 80, .35], [560, 135, -500, 320, 100, .32], [-80, 190, -650, 400, 120, .3]];
for (const [x, y, z, sx, sy, op] of clouds) { const sp = new THREE.Sprite(cloudMat.clone()); sp.material.opacity = op * .7; sp.position.set(x, y, z); sp.scale.set(sx, sy, 1); sp.userData.noNormal = true; scene.add(sp); }
const glowTex = texLoader.load('/assets/textures/glow.png');
const sunGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, opacity: night ? .18 : .55, depthWrite: false, color: night ? '#cfe0ff' : '#ffc98c', blending: THREE.AdditiveBlending, fog: false }));
sunGlow.position.set(-420, 85, -660); sunGlow.scale.set(180, 180, 1); sunGlow.userData.noNormal = true; scene.add(sunGlow);
const camera = new THREE.PerspectiveCamera(Number(q.get('fov') || 38), innerWidth / innerHeight, 0.1, 800);
const cam = (q.get('cam') || '80,48,105').split(',').map(Number);
const tgt = (q.get('target') || '-5,5,0').split(',').map(Number);
camera.position.set(...cam);
const controls = new OrbitControls(camera, canvas);
controls.target.set(...tgt);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.495;
scene.add(new THREE.HemisphereLight(night ? '#5b7ca8' : '#f4efe2', night ? '#121820' : '#6b5b45', night ? .55 : 1.55));
const sun = new THREE.DirectionalLight(night ? '#9db8ff' : (q.get('sun') || '#ffd9a8'), night ? .75 : 2.5);
sun.position.set(-80, 70, 85);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
const S = 150;
sun.shadow.camera.left = -S; sun.shadow.camera.right = S;
sun.shadow.camera.top = S; sun.shadow.camera.bottom = -S;
sun.shadow.camera.near = 1; sun.shadow.camera.far = 320;
sun.shadow.bias = -0.0002;
 sun.shadow.normalBias = 0.6;
scene.add(sun);
const fill = new THREE.DirectionalLight(night ? '#ff7a9a' : '#cfe0e8', night ? .18 : .55);
fill.position.set(60, 25, 80);
scene.add(fill);
const paper = makePaperPipeline(renderer, scene, camera, { ink: Number(q.get('ink')||0.9), grain: 0.06, debug: Number(q.get('debug')||0) });
window.__scene = scene; window.__camera = camera;
const loader = new GLTFLoader();
const vglb = q.get('vehicle');
const vpos = (q.get('vpos') || '0,0,0').split(',').map(Number);
const vrot = Number(q.get('vrot') || 0);
const vscale = Number(q.get('vscale') || 1);
if (vglb) new GLTFLoader().load(vglb, v => {
  const g = v.scene; g.position.set(...vpos); g.rotation.y = vrot; g.scale.setScalar(vscale);
  scene.add(g);
  g.traverse(o => { if (o.isMesh) { o.castShadow = o.receiveShadow = true; } });
  window.__vehicleReady = true;
}, undefined, e => console.error('vehicle', e));
loader.load(glb, g => {
  scene.add(g.scene);
  let meshes = 0, verts = 0, tris = 0; const mats = new Set(); const names = [];
  g.scene.traverse(o => {
    if (o.isMesh) {
      meshes++; const gg = o.geometry;
      verts += gg.attributes.position?.count || 0;
      tris += (gg.index ? gg.index.count : gg.attributes.position.count) / 3;
      mats.add(o.material.name); o.castShadow = o.receiveShadow = true;
      if (names.length < 30) names.push(o.name + ':' + o.material.name + ':' + (gg.attributes.color ? 'C' : '-'));
    }
    if (o.name.startsWith('FX_')) names.push('FX ' + o.name + ' ' + o.position.toArray().map(v=>v.toFixed(1)));
  });
  window.__info = { meshes, verts, tris: Math.round(tris), mats: [...mats], names };
  window.__waterSet = applyWater(scene);
  window.__water = window.__waterSet.pondMat.uniforms;
  window.__ready = true; console.log('READY', JSON.stringify(window.__info));
}, undefined, e => { window.__error = String(e); console.error(e); });
let t = 0;
function loop(){ requestAnimationFrame(loop); t += .016; if (window.__waterSet) { window.__waterSet.pondMat.uniforms.uTime.value = t; window.__waterSet.paddyMat.uniforms.uTime.value = t; } controls.update(); if (usePost) paper.render(); else { renderer.render(scene, camera); } }
loop();
addEventListener('resize', () => { camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
window.__setCam = (p, t) => { camera.position.set(...p); controls.target.set(...t); controls.update(); };
