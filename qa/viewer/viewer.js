import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const canvas = document.querySelector('#c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#e9e4d6');
scene.fog = new THREE.Fog('#e9e4d6', 40, 130);

const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.1, 500);
camera.position.set(18, 14, 28);

const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 4, 0);
controls.enableDamping = true;

scene.add(new THREE.HemisphereLight('#e8f0ef', '#6a5b46', 1.1));
const sun = new THREE.DirectionalLight('#ffe0b0', 2.4);
sun.position.set(-25, 38, 20);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -40; sun.shadow.camera.right = 40;
sun.shadow.camera.top = 40; sun.shadow.camera.bottom = -40;
sun.shadow.camera.near = 1; sun.shadow.camera.far = 120;
sun.shadow.bias = -0.0004;
scene.add(sun);

const loader = new GLTFLoader();
const info = {};
loader.load('/assets/test_zone.glb', (gltf) => {
  const root = gltf.scene;
  scene.add(root);
  let meshes = 0, verts = 0, tris = 0;
  const mats = new Set();
  const names = [];
  root.traverse(o => {
    if (o.isMesh) {
      meshes++;
      const g = o.geometry;
      verts += g.attributes.position?.count || 0;
      tris += (g.index ? g.index.count : g.attributes.position.count) / 3;
      mats.add(o.material.name);
      o.castShadow = o.receiveShadow = true;
      if (names.length < 10) names.push(`${o.name}:${o.material.name}:${!!g.attributes.color}`);
    }
  });
  info.meshes = meshes; info.verts = verts; info.tris = Math.round(tris);
  info.mats = [...mats]; info.names = names;
  info.hotspots = root.children.filter(o => o.name.startsWith('FX_')).map(o => ({ name: o.name, pos: o.position.toArray() }));
  window.__info = info;
  window.__ready = true;
  console.log('READY', JSON.stringify(info));
}, undefined, (e) => { console.error(e); window.__error = String(e); });

function loop() {
  requestAnimationFrame(loop);
  controls.update();
  renderer.render(scene, camera);
}
loop();
window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
window.__snap = () => { renderer.render(scene, camera); return true; };
