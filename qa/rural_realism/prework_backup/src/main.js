// 《山河织路》 — interactive 3D scroll. All geometry/audio original to this project.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { Soundscape } from './audio.js';
import { ASSET } from './assets.js';
import { makePaperPipeline } from './paper.js';
import { applyWater } from './water.js';

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const damp = (a, b, k, dt) => a + (b - a) * (1 - Math.exp(-k * dt));
const isTouch = matchMedia('(pointer: coarse)').matches;
const isMobile = innerWidth < 820 || isTouch;
const q = new URLSearchParams(location.search);
const captureMode = q.get('capture') === '1';
const lowQuality = isMobile && !q.get('high');
const motionQuery = matchMedia('(prefers-reduced-motion: reduce)');
let reducedMotion = motionQuery.matches;
motionQuery.addEventListener('change', e => { reducedMotion = e.matches; });
const ENTRY = [.1, .315, .545, .79, .95];
let preferences = {};
try { preferences = JSON.parse(localStorage.getItem('shanhe.preferences') || '{}') || {}; } catch {}
if (typeof preferences !== 'object') preferences = {};
function savePreferences() {
  try { localStorage.setItem('shanhe.preferences', JSON.stringify({ sound: state.sound, memories: [...state.collected] })); } catch {}
}

const SPACING = 420;
const ZONES = [
  { id: 'rural', label: '田埂晨', num: '壹', year: '1980s', line: '路是走出来的。', center: 0, file: 'rural.glb', start: 0.045, end: 0.215 },
  { id: 'town', label: '街市暮', num: '贰', year: '1990s', line: '路通向更大的世界。', center: -420, file: 'town.glb', start: 0.25, end: 0.43 },
  { id: 'city', label: '城夜雨', num: '叁', year: '2010s', line: '路把远方变成日常。', center: -840, file: 'city.glb', start: 0.47, end: 0.65 },
  { id: 'rail', label: '山河速', num: '肆', year: '2020s', line: '路让山河彼此相拥。', center: -1260, file: 'rail.glb', start: 0.69, end: 0.86 },
  { id: 'future', label: '星河远', num: '伍', year: '未来', line: '路从脚下，通向星辰。', center: -1680, file: 'future.glb', start: 0.90, end: 1.0 },
];

const PALETTES = [
  { name: 'rural', top: '#84a6ab', bot: '#f6e2c2', sun: '#ffd39a', fog: '#dfcfb2', fogNear: 135, fogFar: 760,
    sunDir: [-0.55, 0.16, -0.6], sunInt: 3.0, hemi: 1.05, fill: .55, fillColor: '#cfe0e8', exp: 1.15,
    ink: .58, bloom: .22, stars: 0, clouds: .6, waterDeep: '#3f5f45', waterShallow: '#8ba06a' },
  { name: 'town', top: '#536782', bot: '#f0b27a', sun: '#ffb066', fog: '#d9ad8a', fogNear: 80, fogFar: 520,
    sunDir: [-0.6, 0.12, -0.55], sunInt: 2.4, hemi: 1.0, fill: .4, fillColor: '#ffd2b0', exp: 1.12,
    ink: .54, bloom: .3, stars: .0, clouds: .4, waterDeep: '#345a58', waterShallow: '#82a08c' },
  { name: 'city', top: '#030712', bot: '#14243c', sun: '#a9c6ff', fog: '#0a1422', fogNear: 60, fogFar: 430,
    sunDir: [-0.35, 0.55, -0.3], sunInt: .7, hemi: .55, fill: .24, fillColor: '#ff7a9a', exp: 1.02,
    ink: .34, bloom: .62, stars: .55, clouds: .12, waterDeep: '#102a36', waterShallow: '#2b6470' },
  { name: 'rail', top: '#7595bd', bot: '#ffd2a1', sun: '#ffc98a', fog: '#dcd2c2', fogNear: 180, fogFar: 900,
    sunDir: [-0.62, 0.12, -0.5], sunInt: 2.7, hemi: 1.2, fill: .45, fillColor: '#d7e6ef', exp: 1.2,
    ink: .52, bloom: .28, stars: 0, clouds: .55, waterDeep: '#3c6a70', waterShallow: '#8fb6b1' },
  { name: 'future', top: '#02050d', bot: '#0b2a38', sun: '#b8d7ff', fog: '#0b1a24', fogNear: 140, fogFar: 760,
    sunDir: [-0.3, 0.5, -0.3], sunInt: 1.0, hemi: .82, fill: .46, fillColor: '#39e0c8', exp: 1.14,
    ink: .4, bloom: .52, stars: .9, clouds: .08, waterDeep: '#0b3038', waterShallow: '#2a7a70' },
];
const VOID_PAL = { name: 'void', top: '#f3ecdf', bot: '#e7dcc6', sun: '#ffd9a0', fog: '#efe6d5', fogNear: 500, fogFar: 2600,
  sunDir: [-0.45, .45, -0.42], sunInt: 2.15, hemi: 1.25, fill: .6, fillColor: '#fff6e5', exp: 1.14,
  ink: .4, bloom: .16, stars: 0, clouds: 0, waterDeep: '#4e6a5a', waterShallow: '#9ab09c' };
const OVERVIEW_PAL = { name: 'overview', top: '#f3ecdf', bot: '#e7dcc6', sun: '#ffd9a0', fog: '#ece2cf', fogNear: 760, fogFar: 4200,
  sunDir: [-0.45, .5, -0.42], sunInt: 2.45, hemi: 1.55, fill: .7, fillColor: '#fff6e5', exp: 1.2,
  ink: .72, bloom: .2, stars: 0, clouds: 0, waterDeep: '#4e6a5a', waterShallow: '#9ab09c' };

const CHAPTER_TITLES = ZONES.map(z => ({ num: z.num, year: z.year, title: z.label, line: z.line }));

// Camera keys: p (progress), pos [x,y,z], look [x,y,z], fov
const KEYS = [
  { p: 0.000, pos: [78, 44, 208], look: [-54, 5, 42], fov: 40 },
  { p: 0.018, pos: [58, 38, 180], look: [-34, 5, 50], fov: 42 },
  { p: 0.040, pos: [35, 44, 185], look: [-4, 5, 40], fov: 44 },
  { p: 0.065, pos: [18, 24, 135], look: [-5, 5, 20], fov: 46 },
  { p: 0.085, pos: [10, 13, 110], look: [-1, 4, 58], fov: 46 },
  { p: 0.100, pos: [6.2, 2.9, 64.5], look: [2.0, 1.15, 52.5], fov: 46 },
  { p: 0.118, pos: [1.2, 3.4, 38], look: [-5, 3, 2], fov: 48 },
  { p: 0.140, pos: [0, 3.8, 22], look: [-6, 4, -20], fov: 48 },
  { p: 0.165, pos: [0, 4.2, 0], look: [-6, 5, -58], fov: 48 },
  { p: 0.190, pos: [0, 7, -52], look: [-7, 5, -115], fov: 46 },
  { p: 0.208, pos: [0, 22, -100], look: [0, 3, -175], fov: 44 },
  { p: 0.230, pos: [0, 95, -175], look: [0, 0, -260], fov: 42 },
  { p: 0.245, pos: [0, 78, -244], look: [0, 3, -330], fov: 42 },
  { p: 0.265, pos: [3, 44, -282], look: [1, 4, -360], fov: 43 },
  { p: 0.285, pos: [4, 20, -322], look: [2, 4, -395], fov: 45 },
  { p: 0.300, pos: [5, 8.5, -360], look: [3, 4, -425], fov: 47 },
  { p: 0.315, pos: [1.6, 4.2, -436], look: [5.0, 1.55, -456.4], fov: 50 },
  { p: 0.335, pos: [0.0, 5.2, -445], look: [-1, 4, -505], fov: 48 },
  { p: 0.355, pos: [-1.0, 5.0, -478], look: [-3.6, 4.0, -540], fov: 47 },
  { p: 0.380, pos: [-3.4, 6.0, -508], look: [-3.5, 4.0, -568], fov: 46 },
  { p: 0.405, pos: [-1.0, 18, -548], look: [-3.5, 4, -605], fov: 44 },
  { p: 0.425, pos: [0, 52, -585], look: [0, 2, -655], fov: 42 },
  { p: 0.450, pos: [0, 100, -640], look: [0, 0, -720], fov: 42 },
  { p: 0.470, pos: [0, 70, -690], look: [0, 6, -780], fov: 43 },
  { p: 0.495, pos: [34, 58, -720], look: [0, 18, -810], fov: 44 },
  { p: 0.520, pos: [0, 26, -750], look: [0, 16, -830], fov: 45 },
  { p: 0.545, pos: [0, 18, -812], look: [0, 15, -848], fov: 52 },
  { p: 0.560, pos: [0, 8.5, -790], look: [0, 11, -852], fov: 47 },
  { p: 0.575, pos: [0, 6.5, -810], look: [0, 10, -870], fov: 47 },
  { p: 0.595, pos: [0, 6.2, -838], look: [0, 13, -890], fov: 48 },
  { p: 0.615, pos: [0, 14, -878], look: [0, 8, -940], fov: 46 },
  { p: 0.640, pos: [0, 46, -940], look: [0, 5, -1010], fov: 43 },
  { p: 0.660, pos: [0, 88, -980], look: [0, 0, -1060], fov: 42 },
  { p: 0.680, pos: [0, 100, -1040], look: [0, 4, -1120], fov: 42 },
  { p: 0.700, pos: [0, 112, -1080], look: [0, 20, -1160], fov: 42 },
  { p: 0.725, pos: [8, 96, -1110], look: [0, 34, -1230], fov: 43 },
  { p: 0.750, pos: [16, 72, -1150], look: [0, 36, -1270], fov: 44 },
  { p: 0.775, pos: [-55, 64, -1160], look: [2, 36, -1280], fov: 43 },
  { p: 0.790, pos: [-62, 58, -1202], look: [4, 34, -1310], fov: 42 },
  { p: 0.810, pos: [-50, 54, -1250], look: [4, 34, -1345], fov: 43 },
  { p: 0.830, pos: [-30, 66, -1305], look: [0, 30, -1390], fov: 44 },
  { p: 0.850, pos: [0, 92, -1370], look: [0, 14, -1450], fov: 43 },
  { p: 0.865, pos: [0, 104, -1420], look: [0, 4, -1510], fov: 42 },
  { p: 0.882, pos: [0, 110, -1470], look: [0, 10, -1550], fov: 42 },
  { p: 0.900, pos: [0, 116, -1505], look: [20, 20, -1620], fov: 43 },
  { p: 0.925, pos: [175, 78, -1520], look: [50, 30, -1735], fov: 46 },
  { p: 0.950, pos: [195, 62, -1580], look: [55, 30, -1735], fov: 47 },
  { p: 0.975, pos: [120, 32, -1670], look: [100, 38, -1756], fov: 47 },
  { p: 1.000, pos: [104, 30, -1700], look: [102, 36, -1760], fov: 46 },
];

const OVERVIEW_POSE = { pos: [900, 700, 600], look: [0, 0, -820], fov: 42 };
const OVERVIEW_POSE_PORTRAIT = { pos: [-341, 3192, -57], look: [0, 20, -900], fov: 48 };
function overviewPose() { return innerWidth / innerHeight < .85 ? OVERVIEW_POSE_PORTRAIT : OVERVIEW_POSE; }

// ---------------------------------------------------------------- UI helpers
const el = {
  loading: $('#loading'), loadFill: $('#loadFill'), loadPct: $('#loadPct'),
  landing: $('#landing'), startBtn: $('#startBtn'), hud: $('#hud'),
  chapter: $('#chapter'), chNum: $('#chNum'), chYear: $('#chYear'), chTitle: $('#chTitle'), chLine: $('#chLine'),
  hotspot: $('#hotspot'), card: $('#card'), cardClose: $('#cardClose'), cardEyebrow: $('#cardEyebrow'),
  cardTitle: $('#cardTitle'), cardBody: $('#cardBody'), cardIndex: $('#cardIndex'),
  tlFill: $('#tlFill'), timeline: $('#timeline'), scrollHint: $('#scrollHint'),
  overviewBtn: $('#overviewBtn'), soundBtn: $('#soundBtn'), soundTxt: $('#soundTxt'), infoBtn: $('#infoBtn'),
  info: $('#info'), infoClose: $('#infoClose'), overview: $('#overview'), ovLabels: $('#ovLabels'), ovBack: $('#ovBack'),
  ink: $('#ink'), finale: $('#finale'), wishInput: $('#wishInput'), launchBtn: $('#launchBtn'), skipFinale: $('#skipFinale'),
  endCard: $('#endCard'), endWish: $('#endWish'), againBtn: $('#againBtn'), endOverviewBtn: $('#endOverviewBtn'),
  toast: $('#toast'),
  world: $('#world'), autoBtn: $('#autoBtn'), autoTxt: $('#autoTxt'), homeBtn: $('#homeBtn'),
  travelMeta: $('#travelMeta'), journeyPct: $('#journeyPct'), collectedTxt: $('#collectedTxt'), memoryBtn: $('#memoryBtn'),
  landingSoundBtn: $('#landingSoundBtn'), endCollection: $('#endCollection'),
};

const state = {
  mode: 'loading', // loading landing travel overview finalePrompt finale ended
  progress: 0, target: 0, chapter: -1, chapterShown: false,
  jumping: null, started: false, finaleShown: false, ended: false,
  voidMix: 1, time: 0, mouse: new THREE.Vector2(), look: new THREE.Vector2(),
  wish: '愿山河无恙，路远必达', sound: preferences.sound === true, ready: false, frozen: false,
  auto: false, modal: null,
  collected: new Set((Array.isArray(preferences.memories) ? preferences.memories : []).filter(i => Number.isInteger(i) && i >= 0 && i < 5)),
};

let previousMode = null;
function hidden(node, value) {
  if (node.classList.contains('hidden') !== value) node.classList.toggle('hidden', value);
  node.inert = value || !!state.modal;
}
function syncUIState(force = false) {
  if (!force && previousMode === state.mode) return;
  const wasLanding = previousMode === 'landing';
  previousMode = state.mode;
  document.body.dataset.mode = state.mode;
  hidden(el.landing, state.mode !== 'landing');
  hidden(el.hud, !['travel', 'finalePrompt'].includes(state.mode));
  hidden(el.timeline, state.mode !== 'travel');
  hidden(el.travelMeta, state.mode !== 'travel');
  hidden(el.overview, state.mode !== 'overview');
  el.endCard.classList.toggle('show', state.mode === 'ended');
  el.endCard.inert = state.mode !== 'ended' || !!state.modal;
  el.hotspot.inert = !el.hotspot.classList.contains('show') || !!state.modal;
  if (wasLanding !== (state.mode === 'landing')) resizeViewport();
}
let panelReturnFocus = null;
function closePanels(restoreFocus = true) {
  const wasOpen = state.modal;
  for (const panel of [el.card, el.info, el.finale]) { panel.classList.remove('show'); panel.inert = true; }
  state.modal = null;
  el.infoBtn.setAttribute('aria-expanded', 'false');
  syncUIState(true);
  if (restoreFocus && wasOpen && panelReturnFocus?.isConnected && !panelReturnFocus.closest('[inert]')) panelReturnFocus.focus({ preventScroll: true });
}
function openPanel(panel, focusTarget) {
  const returnFocus = document.activeElement;
  closePanels(false); setAuto(false);
  clearTimeout(showToast._t); el.toast.classList.remove('show');
  state.modal = panel;
  panelReturnFocus = returnFocus;
  panel.classList.add('show'); panel.inert = false;
  el.infoBtn.setAttribute('aria-expanded', String(panel === el.info));
  syncUIState(true);
  (focusTarget || panel.querySelector('button,input'))?.focus({ preventScroll: true });
}
function setAuto(on) {
  state.auto = !!on;
  el.autoBtn.setAttribute('aria-pressed', String(state.auto));
  el.autoBtn.setAttribute('aria-label', state.auto ? '暂停自动漫游' : '开始自动漫游');
  el.autoTxt.textContent = state.auto ? '暂停漫游' : '自动漫游';
  el.autoBtn.querySelector('use').setAttribute('href', state.auto ? '#i-pause' : '#i-play');
}
function resizeViewport() {
  const width = Math.max(1, el.world.clientWidth), height = Math.max(1, el.world.clientHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, lowQuality ? 1.5 : 1.75));
  renderer.setSize(width, height, false);
  camera.aspect = width / height; camera.updateProjectionMatrix();
  paper.setSize(width, height);
}

// ---------------------------------------------------------------- renderer
const canvas = $('#gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, lowQuality ? 1.5 : 2));
renderer.setSize(innerWidth, innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#efe6d5');
const camera = new THREE.PerspectiveCamera(44, innerWidth / innerHeight, 0.1, 4000);
camera.position.set(70, 82, 310);

const paper = makePaperPipeline(renderer, scene, camera, {
  ink: .9, grain: .055, bloomStrength: .35, paper: '#f3ecdf',
});
if (lowQuality) paper.bloom.enabled = false;

// ---------------------------------------------------------------- sky
const texLoader = new THREE.TextureLoader();
const grainTex = null; // paper pipeline owns its own
const cloudTex = texLoader.load(ASSET('/assets/textures/cloud.png'));
const glowTex = texLoader.load(ASSET('/assets/textures/glow.png'));
const starTex = texLoader.load(ASSET('/assets/textures/star.png'));
const smokeTex = texLoader.load(ASSET('/assets/textures/smoke.png'));
const shadowTex = texLoader.load(ASSET('/assets/textures/shadow.png'));

class Sky {
  constructor() {
    this.group = new THREE.Group();
    this.group.userData.noNormal = true;
    scene.add(this.group);
    const geo = new THREE.SphereGeometry(1200, 32, 20);
    this.mat = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: {
        top: { value: new THREE.Color('#93b3b5') }, bot: { value: new THREE.Color('#f7e7cb') },
        sunDir: { value: new THREE.Vector3(-.55, .26, -.55).normalize() },
        sunCol: { value: new THREE.Color('#ffd7a0') }, glow: { value: .55 },
      },
      vertexShader: 'varying vec3 vP; void main(){ vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
      fragmentShader: `varying vec3 vP; uniform vec3 top,bot,sunCol,sunDir; uniform float glow;
        void main(){ vec3 d=normalize(vP); float h=smoothstep(-.08,.55,d.y); vec3 c=mix(bot,top,h);
        float s=max(dot(d,normalize(sunDir)),0.0); c+=sunCol*pow(s,180.0)*glow*.9;
        c+=sunCol*pow(s,12.0)*glow*.10; gl_FragColor=vec4(c,1.0); }`
    });
    this.dome = new THREE.Mesh(geo, this.mat);
    this.dome.userData.noNormal = true;
    this.group.add(this.dome);
    // stars
    const n = 1600, pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2, b = Math.random() * Math.PI * .48 + .03;
      const r = 900;
      pos[i * 3] = Math.cos(a) * Math.cos(b) * r;
      pos[i * 3 + 1] = Math.sin(b) * r;
      pos[i * 3 + 2] = Math.sin(a) * Math.cos(b) * r;
    }
    const sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    this.starMat = new THREE.PointsMaterial({ size: 2.0, map: starTex, transparent: true, opacity: 0,
      depthWrite: false, blending: THREE.AdditiveBlending, color: '#dbe7ff', sizeAttenuation: true, fog: false });
    this.stars = new THREE.Points(sg, this.starMat);
    this.stars.userData.noNormal = true;
    this.group.add(this.stars);
    // clouds
    this.clouds = [];
    const specs = [[-420, 85, -760, 520, 160, .55], [60, 128, -900, 640, 190, .42], [460, 78, -760, 480, 150, .48],
      [-620, 62, -520, 420, 130, .32], [620, 105, -540, 520, 160, .32], [0, 168, -980, 760, 200, .22]];
    for (const [x, y, z, sx, sy, op] of specs) {
      const m = new THREE.SpriteMaterial({ map: cloudTex, transparent: true, opacity: op, depthWrite: false,
        color: '#f6dfc4', fog: false });
      const sp = new THREE.Sprite(m);
      sp.position.set(x, y, z); sp.scale.set(sx, sy, 1); sp.userData.noNormal = true;
      this.group.add(sp); this.clouds.push(sp);
    }
    // sun / moon glow
    this.sunHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, opacity: .55,
      depthWrite: false, color: '#ffc98c', blending: THREE.AdditiveBlending, fog: false }));
    this.sunHalo.scale.set(92, 92, 1); this.sunHalo.userData.noNormal = true; this.group.add(this.sunHalo);
    this.sunCore = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, opacity: .9,
      depthWrite: false, color: '#ffe3af', blending: THREE.AdditiveBlending, fog: false }));
    this.sunCore.scale.set(28, 28, 1); this.sunCore.userData.noNormal = true; this.group.add(this.sunCore);
    this.target = { ...PALETTES[0] };
    this.cur = {
      top: new THREE.Color(PALETTES[0].top), bot: new THREE.Color(PALETTES[0].bot),
      sun: new THREE.Color(PALETTES[0].sun), dir: new THREE.Vector3(...PALETTES[0].sunDir).normalize(),
      glow: .55, stars: 0, clouds: .55, visible: true,
    };
    this.setPalette(PALETTES[0]);
  }
  setPalette(p) {
    this.target = p;
  }
  update(dt, camera, voidMix) {
    const t = this.target;
    this.cur.top.lerp(new THREE.Color(t.top), 1 - Math.exp(-dt * 1.6));
    this.cur.bot.lerp(new THREE.Color(t.bot), 1 - Math.exp(-dt * 1.6));
    this.cur.sun.lerp(new THREE.Color(t.sun), 1 - Math.exp(-dt * 1.6));
    this.cur.dir.lerp(new THREE.Vector3(...t.sunDir).normalize(), 1 - Math.exp(-dt * 1.2)).normalize();
    this.cur.glow = damp(this.cur.glow, t.name === 'city' || t.name === 'future' ? .28 : .6, 2, dt);
    this.cur.stars = damp(this.cur.stars, t.stars ?? 0, 2, dt);
    this.cur.clouds = damp(this.cur.clouds, t.clouds ?? 0, 2, dt);
    this.mat.uniforms.top.value.copy(this.cur.top);
    this.mat.uniforms.bot.value.copy(this.cur.bot);
    this.mat.uniforms.sunCol.value.copy(this.cur.sun);
    this.mat.uniforms.sunDir.value.copy(this.cur.dir);
    this.mat.uniforms.glow.value = this.cur.glow;
    this.group.position.set(camera.position.x, 0, camera.position.z);
    this.stars.material.opacity = this.cur.stars * .8;
    this.stars.visible = this.cur.stars > .01;
    for (const c of this.clouds) c.material.opacity = (c.userData.baseOp ??= c.material.opacity) * this.cur.clouds;
    const d = this.cur.dir;
    this.sunHalo.position.set(d.x * 900, d.y * 900, d.z * 900);
    this.sunCore.position.copy(this.sunHalo.position);
    this.sunHalo.material.color.copy(this.cur.sun).lerp(new THREE.Color('#fff2d0'), .3);
    this.sunCore.material.color.copy(this.cur.sun).lerp(new THREE.Color('#ffffff'), .45);
    this.sunHalo.material.opacity = (t.name === 'city' || t.name === 'future') ? .10 : .34;
    this.sunCore.material.opacity = (t.name === 'city' || t.name === 'future') ? .25 : .8;
    this.group.visible = voidMix < .9;
    this.group.userData.void = voidMix;
  }
}
const sky = new Sky();

// ---------------------------------------------------------------- lights
const hemi = new THREE.HemisphereLight('#f4efe2', '#6b5b45', 1.4);
scene.add(hemi);
const sun = new THREE.DirectionalLight('#ffd9a8', 2.4);
sun.castShadow = true;
sun.shadow.mapSize.set(lowQuality ? 1024 : 2048, lowQuality ? 1024 : 2048);
sun.shadow.camera.left = -80; sun.shadow.camera.right = 80;
sun.shadow.camera.top = 80; sun.shadow.camera.bottom = -80;
sun.shadow.camera.near = 1; sun.shadow.camera.far = 420;
sun.shadow.bias = -0.00015; sun.shadow.normalBias = .6;
scene.add(sun); scene.add(sun.target);
const fill = new THREE.DirectionalLight('#cfe0e8', .55);
scene.add(fill);

// ---------------------------------------------------------------- thread + island shadows
const threadCurve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(0, 2.4, 150), new THREE.Vector3(0, 2.0, 60), new THREE.Vector3(0, 2.0, -40),
  new THREE.Vector3(0, 2.4, -150), new THREE.Vector3(0, 3.2, -210), new THREE.Vector3(0, 2.0, -280),
  new THREE.Vector3(0, 2.0, -360), new THREE.Vector3(0, 2.4, -570), new THREE.Vector3(0, 3.2, -630),
  new THREE.Vector3(0, 2.0, -700), new THREE.Vector3(0, 2.0, -780), new THREE.Vector3(0, 2.4, -990),
  new THREE.Vector3(0, 3.2, -1050), new THREE.Vector3(0, 2.0, -1120), new THREE.Vector3(0, 2.0, -1200),
  new THREE.Vector3(0, 2.4, -1410), new THREE.Vector3(0, 3.2, -1470), new THREE.Vector3(0, 2.0, -1540),
  new THREE.Vector3(0, 2.0, -1620), new THREE.Vector3(0, 2.4, -1830),
], false, 'catmullrom', .12);
const threadMat = new THREE.MeshStandardMaterial({ color: '#7c2019', emissive: '#c0392b', emissiveIntensity: 1.7, roughness: .5, metalness: .1 });
const thread = new THREE.Mesh(new THREE.TubeGeometry(threadCurve, 520, .22, 6, false), threadMat);
thread.visible = false;
scene.add(thread);
const threadGlowMat = new THREE.MeshBasicMaterial({ color: '#ff6a45', transparent: true, opacity: .18, blending: THREE.AdditiveBlending, depthWrite: false });
const threadGlow = new THREE.Mesh(new THREE.TubeGeometry(threadCurve, 520, .62, 6, false), threadGlowMat);
threadGlow.visible = false; scene.add(threadGlow);
// symbolic red thread for the scroll overview: drawn on top, like ink on paper
const ovThreadMat = new THREE.MeshBasicMaterial({ color: '#b23a2a', transparent: true, opacity: .86, depthTest: false, depthWrite: false });
const ovThread = new THREE.Mesh(new THREE.TubeGeometry(threadCurve, 520, 1.5, 5, false), ovThreadMat);
ovThread.renderOrder = 900; ovThread.visible = false; scene.add(ovThread);
const ovThreadGlowMat = new THREE.MeshBasicMaterial({ color: '#ff7a55', transparent: true, opacity: .14, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending });
const ovThreadGlow = new THREE.Mesh(new THREE.TubeGeometry(threadCurve, 520, 4.2, 5, false), ovThreadGlowMat);
ovThreadGlow.renderOrder = 899; ovThreadGlow.visible = false; scene.add(ovThreadGlow);

const islandShadows = new THREE.Group();
scene.add(islandShadows);
const islandShadowByZone = {};
for (const z of ZONES) {
  const m = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, opacity: .28, depthWrite: false, color: '#3b2a18' });
  const p = new THREE.Mesh(new THREE.PlaneGeometry(430, 430), m);
  p.rotation.x = -Math.PI / 2; p.position.set(0, -12, z.center); p.userData.noNormal = true;
  islandShadows.add(p);
  islandShadowByZone[z.id] = p;
}
islandShadows.visible = false;

// ---------------------------------------------------------------- water + zones
const water = applyWater(scene, 'all'); // created once; no water meshes yet, but materials ready
// applyWater already traversed empty scene; we will re-apply after zones load via helper below.
const waterSet = water;
let waterApplied = false;
function applyWaterToZones() {
  if (waterApplied) return;
  scene.traverse(o => {
    if (o.isMesh && o.material && o.material.name === 'Water') {
      const isPaddy = o.name.includes('Paddy') || o.name.includes('Terrace');
      o.material = isPaddy ? waterSet.paddyMat : waterSet.pondMat;
      o.receiveShadow = false;
    }
  });
  waterApplied = true;
}

const zones = {};
const fx = [];
const gltfLoader = new GLTFLoader();
gltfLoader.setMeshoptDecoder(MeshoptDecoder);
let loadedCount = 0;
let totalAssets = ZONES.length + 5;
function bumpLoad() {
  loadedCount++;
  const pct = Math.min(100, Math.round(loadedCount / totalAssets * 100));
  if (el.loadFill) el.loadFill.style.width = pct + '%';
  if (el.loadPct) el.loadPct.textContent = pct + '%';
  $('.load-line').setAttribute('aria-valuenow', String(pct));
  $('#loadStatus').textContent = `铺开时代之岛 · ${loadedCount} / ${totalAssets}`;
}
function loadAsset(url) {
  return new Promise((resolve, reject) => {
    gltfLoader.load(ASSET(url), (g) => { bumpLoad(); resolve(g); },
      undefined, (e) => { reject(new Error('Required scene could not load: ' + url, { cause: e })); });
  });
}

async function loadWorld() {
  const tasks = ZONES.map(z => loadAsset('/assets/zones/' + z.file).then(g => ({ z, g })));
  const [zoneResults, rick, train, carG, hsr, rocket] = await Promise.all([
    Promise.all(tasks),
    loadAsset('/assets/vehicles/rickshaw.glb'),
    loadAsset('/assets/vehicles/green_train.glb'),
    loadAsset('/assets/vehicles/car.glb'),
    loadAsset('/assets/vehicles/hsr.glb'),
    loadAsset('/assets/vehicles/rocket.glb'),
  ]);
  for (const { z, g } of zoneResults) {
    if (!g) { zones[z.id] = { spec: z, group: null, hotspot: null, lights: [], smoke: [] }; continue; }
    const group = g.scene;
    group.position.z = z.center;
    scene.add(group);
    const data = { spec: z, group, hotspot: null, lights: [], smoke: [] };
    group.updateMatrixWorld(true);
    group.traverse(o => {
      if (o.isMesh) {
        o.castShadow = true; o.receiveShadow = true;
        if (o.material) o.material.envMapIntensity = .6;
      }
      if (o.name && o.name.startsWith('FX_')) {
        const wp = new THREE.Vector3();
        o.getWorldPosition(wp);
        if (o.name.startsWith('FX_Hotspot')) data.hotspot = wp;
        else if (o.name.startsWith('FX_Light')) data.lights.push(wp);
        else if (o.name.startsWith('FX_Smoke')) data.smoke.push(wp);
        else if (o.name.startsWith('FX_Fireflies')) data.fireflies = wp;
      }
    });
    // glows at lamp anchors
    for (const p of data.lights) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, opacity: .5,
        depthWrite: false, color: '#ffd9a0', blending: THREE.AdditiveBlending, fog: false }));
      s.position.copy(p); s.scale.set(7, 7, 1); s.userData.noNormal = true;
      scene.add(s); data.glowSprites = data.glowSprites || []; data.glowSprites.push(s);
    }
    // smoke
    for (const p of data.smoke) {
      for (let i = 0; i < 5; i++) {
        const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: smokeTex, transparent: true, opacity: .24,
          depthWrite: false, color: '#cfc6b6', fog: true }));
        s.position.copy(p).add(new THREE.Vector3((Math.random() - .5) * 2, Math.random() * 2, (Math.random() - .5) * 2));
        s.scale.set(5, 5, 1); s.userData.noNormal = true;
        s.userData.smoke = { base: p.clone(), phase: Math.random() * 8, speed: .7 + Math.random() * .5, sway: Math.random() * 6 };
        scene.add(s); data.smokeSprites = data.smokeSprites || []; data.smokeSprites.push(s);
      }
    }
    // fireflies
    if (data.fireflies) {
      const n = 60, pos = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) {
        pos[i*3] = data.fireflies.x + (Math.random() - .5) * 42;
        pos[i*3+1] = data.fireflies.y + Math.random() * 5;
        pos[i*3+2] = data.fireflies.z + (Math.random() - .5) * 42;
      }
      const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      const fm = new THREE.PointsMaterial({ size: .5, map: starTex, transparent: true, opacity: .7, depthWrite: false,
        color: '#ffd98a', blending: THREE.AdditiveBlending, sizeAttenuation: true });
      const points = new THREE.Points(fg, fm); points.userData.noNormal = true; scene.add(points);
      data.fireflyPoints = points;
    }
    zones[z.id] = data;
    fx.push(...data.lights.map(p => ({ p, zone: z.id })));
  }
  applyWaterToZones();

  // rickshaw in the rural
  if (rick) {
    const r = rick.scene;
    r.position.set(2.2, .06, 52); r.rotation.y = Math.PI / 2;
    r.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(r); zones.rural.vehicle = r;
  }
  // green train on the city viaduct
  if (train) {
    const tg = new THREE.Group(); tg.add(train.scene);
    tg.position.set(-160, 13.72, -845); tg.rotation.y = -Math.PI / 2;
    tg.traverse(o => {
      if (!o.isMesh) return;
      o.castShadow = true; o.receiveShadow = true;
      if (/^TrainGreen/.test(o.material?.name || '')) {
        o.material.emissive = new THREE.Color('#3f7d4a');
        o.material.emissiveIntensity = .24;
      }
    });
    scene.add(tg); zones.city.train = tg;
  }
  // 1990s car in the town
  if (carG) {
    const cg = new THREE.Group(); cg.add(carG.scene);
    cg.position.set(4.6, .05, -456.4); cg.rotation.y = 0.1238 + Math.PI;
    cg.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(cg); zones.town.car = cg;
  }
  // high-speed train on the rail bridge
  if (hsr) {
    const hg = new THREE.Group(); hg.add(hsr.scene);
    hg.position.set(2.4, 32.95, -1260);
    hg.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(hg); zones.rail.hsr = hg;
  }
  // heavy-lift rocket at the future pad (PAD=(102,80) local, base z=7)
  if (rocket) {
    const rg = new THREE.Group(); rg.add(rocket.scene);
    rg.position.set(102, 7, -1760); rg.scale.setScalar(1);
    rg.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(rg); zones.future.rocket = rg;
  }
  // use hotspot anchors; fallback positions
  if (zones.rural && zones.rural.vehicle) zones.rural.hotspot = new THREE.Vector3(2.2, 2.2, 52);
  if (zones.town && zones.town.car) zones.town.hotspot = new THREE.Vector3(4.6, 1.55, -456.4);
  const fallback = { rural: [2, 2, 52], town: [0, 3, -380], city: [0, 14, -845], rail: [0, 32, -1260], future: [0, 8, -1710] };
  for (const z of ZONES) {
    if (!zones[z.id].hotspot) zones[z.id].hotspot = new THREE.Vector3(...fallback[z.id]);
  }
}

// ---------------------------------------------------------------- camera sampling
function hermite(field, t) {
  const n = KEYS.length;
  if (t <= KEYS[0].p) return KEYS[0][field].slice();
  if (t >= KEYS[n-1].p) return KEYS[n-1][field].slice();
  let i = 0;
  while (i < n-1 && KEYS[i+1].p < t) i++;
  const k0 = KEYS[Math.max(0, i-1)], k1 = KEYS[i], k2 = KEYS[i+1], k3 = KEYS[Math.min(n-1, i+2)];
  const dt = k2.p - k1.p;
  const u = (t - k1.p) / dt;
  const t0 = k0.p, t1 = k1.p, t2 = k2.p, t3 = k3.p;
  const out = [];
  for (let j = 0; j < k1[field].length; j++) {
    const p0 = k0[field][j], p1 = k1[field][j], p2 = k2[field][j], p3 = k3[field][j];
    const m1 = (p2 - p0) / Math.max(1e-6, t2 - t0) * dt;
    const m2 = (p3 - p1) / Math.max(1e-6, t3 - t1) * dt;
    const u2 = u*u, u3 = u2*u;
    const h00 = 2*u3 - 3*u2 + 1, h10 = u3 - 2*u2 + u, h01 = -2*u3 + 3*u2, h11 = u3 - u2;
    out.push(h00*p1 + h10*m1 + h01*p2 + h11*m2);
  }
  return out;
}
function sampleFov(t) {
  // smooth fov between keys
  let i = 0; while (i < KEYS.length-1 && KEYS[i+1].p < t) i++;
  const a = KEYS[i], b = KEYS[Math.min(KEYS.length-1, i+1)];
  const u = b.p === a.p ? 0 : clamp((t - a.p)/(b.p - a.p), 0, 1);
  return a.fov + (b.fov - a.fov) * smooth(u);
}

// ---------------------------------------------------------------- palette/light updates
let paletteCur = {
  fog: new THREE.Color(PALETTES[0].fog), fogNear: PALETTES[0].fogNear, fogFar: PALETTES[0].fogFar,
  exp: PALETTES[0].exp, ink: PALETTES[0].ink, bloom: PALETTES[0].bloom,
  sunInt: PALETTES[0].sunInt, hemi: PALETTES[0].hemi, fill: PALETTES[0].fill,
};
let paletteTarget = PALETTES[0];
function setPaletteTarget(p) { paletteTarget = p; }
function updatePalette(dt) {
  const k = 1 - Math.exp(-dt * 1.8);
  paletteCur.fog.lerp(new THREE.Color(paletteTarget.fog), k);
  paletteCur.fogNear = damp(paletteCur.fogNear, paletteTarget.fogNear, 1.8, dt);
  paletteCur.fogFar = damp(paletteCur.fogFar, paletteTarget.fogFar, 1.8, dt);
  paletteCur.exp = damp(paletteCur.exp, paletteTarget.exp, 1.8, dt);
  paletteCur.ink = damp(paletteCur.ink, paletteTarget.ink, 1.8, dt);
  paletteCur.bloom = damp(paletteCur.bloom, paletteTarget.bloom, 1.8, dt);
  paletteCur.sunInt = damp(paletteCur.sunInt, paletteTarget.sunInt, 1.8, dt);
  paletteCur.hemi = damp(paletteCur.hemi, paletteTarget.hemi, 1.8, dt);
  paletteCur.fill = damp(paletteCur.fill, paletteTarget.fill, 1.8, dt);
  if (!scene.fog) scene.fog = new THREE.Fog(paletteCur.fog, paletteCur.fogNear, paletteCur.fogFar);
  scene.fog.color.copy(paletteCur.fog);
  scene.fog.near = paletteCur.fogNear; scene.fog.far = paletteCur.fogFar;
  scene.background.copy(paletteCur.fog);
  renderer.toneMappingExposure = paletteCur.exp;
  paper.paperPass.uniforms.ink.value = paletteCur.ink;
  paper.bloom.strength = paletteCur.bloom;
  hemi.intensity = paletteCur.hemi;
  sun.intensity = paletteCur.sunInt;
  fill.intensity = paletteCur.fill;
  sun.color.lerp(new THREE.Color(paletteTarget.sun), k);
  fill.color.lerp(new THREE.Color(paletteTarget.fillColor || '#cfe0e8'), k);
  hemi.color.lerp(new THREE.Color(paletteTarget.top), k * .5).lerp(new THREE.Color('#f4efe2'), .3);
  // water sun
  const sd = new THREE.Vector3(...paletteTarget.sunDir).normalize();
  waterSet.pondMat.uniforms.uSunDir.value.copy(sd);
  waterSet.paddyMat.uniforms.uSunDir.value.copy(sd);
  waterSet.pondMat.uniforms.uSun.value.copy(new THREE.Color(paletteTarget.sun));
  waterSet.paddyMat.uniforms.uSun.value.copy(new THREE.Color(paletteTarget.sun));
}

// ---------------------------------------------------------------- progress / camera
function chapterAt(t) {
  if (t >= 1) return ZONES.length - 1;
  if (t < 0.045) return -1;
  for (let i = 0; i < ZONES.length; i++) {
    if (t >= ZONES[i].start && t < ZONES[i].end) return i;
  }
  return -1;
}
function voidAmount(t) {
  let v = 0;
  if (t < .055) v = Math.max(v, 1 - smooth((t - .018) / .045));
  const gaps = [.23, .45, .67, .88];
  for (const c of gaps) {
    const d = Math.abs(t - c);
    v = Math.max(v, 1 - smooth((d - .008) / .028));
  }
  return clamp(v, 0, 1);
}
function currentPalette() {
  if (state.mode === 'overview') return OVERVIEW_PAL;
  if (state.voidMix > .55) return VOID_PAL;
  if (state.chapter >= 0) return PALETTES[state.chapter];
  return state.progress < .045 ? VOID_PAL : PALETTES[clamp(state.chapter, 0, 4)];
}

function updateCamera(dt) {
  if (state.mode === 'landing') {
    const distance = camera.aspect < 1.2 ? 1.2 : 1;
    const drift = reducedMotion ? 0 : Math.sin(state.time * .08) * 3;
    camera.position.set((265 + drift) * distance, 225 * distance, 300 * distance);
    camera.fov = 41; camera.updateProjectionMatrix();
    camera.lookAt(0, 0, 0); state.camLook = new THREE.Vector3(0, 0, 0);
    return;
  }
  if (state.mode === 'overview') {
    const k = 1 - Math.exp(-dt * 1.8);
    const pose = overviewPose();
    camera.position.lerp(new THREE.Vector3(...pose.pos), k);
    const l = new THREE.Vector3(...pose.look);
    camera.fov = damp(camera.fov, pose.fov, 2, dt); camera.updateProjectionMatrix();
    camera.lookAt(l);
    return;
  }
  if (state.mode === 'finale') return; // handled in finale update
  const t = state.progress;
  const p = hermite('pos', t);
  const l = hermite('look', t);
  const fov = sampleFov(t);
  // mouse parallax
  const par = reducedMotion ? 0 : 1;
  const mx = state.look.x * par, my = state.look.y * par;
  const target = new THREE.Vector3(l[0] + mx * 4.2, l[1] + my * 2.6, l[2]);
  // gentle landing drift
  if (state.mode === 'landing') {
    p[0] += Math.sin(state.time * .08) * 2.2;
    p[1] += Math.sin(state.time * .11) * .8;
  }
  camera.position.set(p[0], p[1], p[2]);
  camera.fov = damp(camera.fov, fov, 6, dt); camera.updateProjectionMatrix();
  camera.lookAt(target);
  state.camLook = target;
}

function updateZoneVisibility() {
  const show = new Set();
  if (state.mode === 'overview') { ZONES.forEach(z => show.add(z.id)); }
  else if (state.mode === 'landing') { show.add('rural'); }
  else if (state.mode === 'travel' || state.mode === 'finalePrompt') {
    if (state.voidMix > .08) {
      const gaps = [.23, .45, .67, .88];
      let gi = 0, gd = 1e9;
      gaps.forEach((g, i) => { const d = Math.abs(state.progress - g); if (d < gd) { gd = d; gi = i; } });
      show.add(ZONES[gi].id);
      if (ZONES[gi + 1]) show.add(ZONES[gi + 1].id);
    } else if (state.chapter >= 0) {
      show.add(ZONES[state.chapter].id);
    }
  } else if (state.mode === 'finale' || state.mode === 'ended') { show.add('future'); }
  for (const z of ZONES) {
    const d = zones[z.id];
    if (d && d.group) d.group.visible = show.has(z.id);
    if (islandShadowByZone[z.id]) islandShadowByZone[z.id].visible = show.has(z.id) && (state.voidMix > .15 || state.mode === 'overview' || state.mode === 'landing');
  }
  const all = state.mode === 'overview';
  if (zones.rural?.vehicle) zones.rural.vehicle.visible = all || show.has('rural');
  if (zones.city?.train) zones.city.train.visible = all || show.has('city');
  if (zones.town?.car) zones.town.car.visible = all || show.has('town');
  if (zones.rail?.hsr) zones.rail.hsr.visible = all || show.has('rail');
  if (zones.future?.rocket) zones.future.rocket.visible = all || show.has('future') || state.mode === 'finale' || state.mode === 'ended';
}

function updateSkyLights(dt) {
  state.voidMix = state.mode === 'overview' ? 1 : voidAmount(state.progress);
  const p = currentPalette();
  setPaletteTarget(p);
  updatePalette(dt);
  sky.setPalette(p);
  sky.update(dt, camera, state.voidMix);
  // lights follow the camera look point
  const look = state.camLook || new THREE.Vector3(0, 5, state.progress < .5 ? 0 : -1000);
  const sd = new THREE.Vector3(...p.sunDir).normalize();
  sun.target.position.set(look.x, look.y, look.z);
  sun.position.set(look.x + sd.x * 190, look.y + sd.y * 190 + 25, look.z + sd.z * 190);
  sun.target.updateMatrixWorld();
  fill.position.set(look.x - sd.x * 80 + 30, look.y + 60, look.z - sd.z * 80 + 40);
  if (state.voidMix > .5) {
    scene.background.copy(new THREE.Color('#f3ecdf'));
    if (scene.fog) {
      scene.fog.color.set('#efe6d5');
      const portraitOv = state.mode === 'overview' && innerWidth / innerHeight < .85;
      scene.fog.near = ovDistanceNear();
      scene.fog.far = portraitOv ? 10000 : state.mode === 'overview' ? 7000 : 2800;
    }
    hemi.intensity = Math.max(hemi.intensity, 1.7);
    sun.intensity = Math.max(sun.intensity, 1.0);
  }
  const ov = state.mode === 'overview';
  thread.visible = !ov && state.voidMix > .25;
  threadGlow.visible = thread.visible;
  ovThread.visible = ov; ovThreadGlow.visible = ov;
  threadMat.emissiveIntensity = 1.2 + state.voidMix * 1.2;
  threadGlowMat.opacity = .12 + state.voidMix * .2;
  islandShadows.visible = true;
  islandShadows.children.forEach((m) => m.material.opacity = .1 + state.voidMix * .22);
}

function ovDistanceNear() {
  if (state.mode !== 'overview') return 500;
  return innerWidth / innerHeight < .85 ? 2600 : 1900;
}

// ---------------------------------------------------------------- ambient animation
function updateAmbient(dt) {
  waterSet.pondMat.uniforms.uTime.value = state.time;
  waterSet.paddyMat.uniforms.uTime.value = state.time;
  // train
  const city = zones.city;
  if (city && city.train) {
    const u = smooth((state.progress - .44) / .22);
    city.train.position.x = -190 + u * 420;
    city.train.visible = state.progress > .42 && state.progress < .69;
  }
  const rail = zones.rail;
  if (rail && rail.hsr) {
    const u = smooth((state.progress - .68) / .18);
    rail.hsr.position.z = -1260 + (0.5 - u) * 180;
  }
  // smoke
  for (const z of Object.values(zones)) {
    if (!z.smokeSprites) continue;
    for (const s of z.smokeSprites) {
      const sm = s.userData.smoke;
      const t = state.time * sm.speed + sm.phase;
      s.position.set(sm.base.x + Math.sin(t * .7) * 1.6, sm.base.y + (t * 2.2) % 26, sm.base.z + Math.cos(t * .5) * 1.2);
      s.material.opacity = .22 * (1 - ((t * 2.2) % 26) / 26);
      s.scale.setScalar(4 + ((t * 2.2) % 26) * .45);
    }
  }
  // fireflies
  for (const z of Object.values(zones)) {
    if (z.fireflyPoints) z.fireflyPoints.rotation.y = state.time * .04;
  }
  // lamp glows
  for (const z of Object.values(zones)) {
    if (z.glowSprites) for (const s of z.glowSprites) s.material.opacity = .38 + Math.sin(state.time * 1.3 + s.position.x) * .08;
  }
}

// ---------------------------------------------------------------- UI functions
function setChapterUI(idx, visible) {
  if (idx < 0) { el.chapter.classList.remove('show'); return; }
  const c = CHAPTER_TITLES[idx];
  if (state.uiChapter !== idx) {
    state.uiChapter = idx;
    el.chNum.textContent = c.num; el.chYear.textContent = c.year; el.chTitle.textContent = c.title; el.chLine.textContent = c.line;
    $$('#timeline .tl-marks button').forEach((b, i) => {
      b.classList.toggle('active', i === idx);
      if (i === idx) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
    });
  }
  el.chapter.classList.toggle('show', !!visible);
}
function showToast(msg) {
  el.toast.textContent = msg; el.toast.classList.add('show');
  clearTimeout(showToast._t); showToast._t = setTimeout(() => el.toast.classList.remove('show'), 2200);
}
function updateLoading() { }
function startExperience() {
  if (state.started) return;
  state.started = true; state.mode = 'travel';
  el.landing.classList.add('hidden');
  setTimeout(() => el.landing.classList.add('hidden'), 0);
  el.hud.classList.remove('hidden');
  el.timeline.classList.remove('hidden');
  el.scrollHint.classList.add('show');
  state.target = .058;
  el.timeline.classList.remove('hidden');
  syncUIState(true);
  if (state.sound) audio.init();
  setTimeout(() => { if (state.mode === 'travel' && !state.modal) showToast(isTouch ? '上滑向前 · 左右拖动回望' : '滚动向前 · 拖动回望'); }, 900);
}
function jumpTo(t) {
  closePanels(false); setAuto(false);
  disposeFinale();
  state.finaleShown = false;
  state.mode = 'travel';
  state.look.set(0, 0);
  state.jumping = { from: state.progress, to: clamp(t, 0, 1), t: 0, dur: reducedMotion ? .01 : 1.25 };
  if (!reducedMotion) {
    el.ink.classList.add('on');
    setTimeout(() => el.ink.classList.remove('on'), 650);
  }
  syncUIState(true);
}
function enterOverview() {
  if (state.mode === 'overview') return;
  closePanels(false); setAuto(false);
  state.overviewOrigin = state.mode;
  state.returnProgress = state.progress;
  state.mode = 'overview';
  el.overview.classList.remove('hidden');
  el.hud.classList.add('hidden'); el.timeline.classList.add('hidden'); el.chapter.classList.remove('show');
  el.hotspot.classList.remove('show'); el.scrollHint.classList.remove('show');
  buildOverviewLabels();
  syncUIState(true);
  el.ovBack.textContent = state.overviewOrigin === 'landing' ? '返回封面 →' : state.overviewOrigin === 'ended' ? '返回尾声 →' : '回到路上 →';
  el.ovBack.focus({ preventScroll: true });
}
function exitOverview(toTravel = false) {
  state.mode = toTravel ? 'travel' : state.overviewOrigin || 'travel';
  el.overview.classList.add('hidden');
  el.hud.classList.remove('hidden'); el.timeline.classList.remove('hidden');
  el.scrollHint.classList.add('show');
  syncUIState(true);
  if (state.mode === 'landing') el.startBtn.focus({ preventScroll: true });
  else if (state.mode === 'travel') el.overviewBtn.focus({ preventScroll: true });
}
function buildOverviewLabels() {
  el.ovLabels.innerHTML = '';
  for (const z of ZONES) {
    const b = document.createElement('button');
    b.className = 'ov-label'; b.type = 'button';
    b.innerHTML = `<i></i><b>${z.num} · ${z.label}</b><em>${z.year}</em>`;
    b.addEventListener('click', () => {
      if (!state.started) startExperience();
      exitOverview(true); jumpTo(ENTRY[ZONES.indexOf(z)]);
    });
    b.dataset.zone = z.id;
    el.ovLabels.appendChild(b);
  }
  state.ovLabels = [...el.ovLabels.querySelectorAll('.ov-label')];
}
function updateOverviewLabels() {
  if (state.mode !== 'overview') return;
  for (const b of state.ovLabels || []) {
    const z = ZONES.find(q => q.id === b.dataset.zone);
    const v = new THREE.Vector3(0, 50, z.center);
    v.project(camera);
    const x = (v.x * .5 + .5) * innerWidth, y = (-v.y * .5 + .5) * innerHeight;
    b.style.left = x + 'px'; b.style.top = y + 'px';
    b.style.opacity = (v.z < 1 ? 1 : 0);
    b.inert = v.z >= 1;
  }
}
function openCard() {
  if (state.mode !== 'travel' || state.chapter < 0) return;
  const idx = state.chapter;
  const data = CARDS[idx];
  if (!data) return;
  el.cardEyebrow.textContent = data.eyebrow;
  el.cardTitle.textContent = data.title;
  el.cardBody.textContent = data.body;
  el.cardIndex.textContent = `0${idx+1} / 05`;
  state.collected.add(idx); savePreferences(); updateCollection();
  openPanel(el.card, el.cardClose);
}
function updateCollection() {
  el.collectedTxt.textContent = `拾光 ${state.collected.size} / 5`;
  $$('#timeline button[data-ch]').forEach((button, i) => button.classList.toggle('collected', state.collected.has(i)));
}
const CARDS = [
  { eyebrow: '1980s · 村口', title: '车把上的马灯', body: '天没亮，路先醒了。板车把一年的收成和一家人的盼望，一起推到镇上去。' },
  { eyebrow: '1990s · 街心', title: '第一辆自己的车', body: '喇叭响了三声，整条街都回头。车窗摇下来，风里是录像厅和冰棍的味道。' },
  { eyebrow: '2010s · 车窗', title: '夜班车', body: '绿皮车穿过雨夜，车窗里一格一格的灯。每一格，都是一个正在回家的人。' },
  { eyebrow: '2020s · 桥上', title: '一杯茶的时间', body: '桥从山河上跨过去。从前要走一天的路，如今只够喝完一杯热茶。' },
  { eyebrow: '未来 · 星海', title: '回望', body: '从地球出发的人，仍记得村口那条路。所有的远方，都从脚下开始。' },
];

// ---------------------------------------------------------------- audio (original procedural soundscape)
const audio = new Soundscape((on) => {
  state.sound = on;
  el.soundBtn.classList.toggle('muted', !on);
  el.soundTxt.textContent = on ? '声音开' : '声音关';
  el.soundBtn.setAttribute('aria-label', on ? '关闭声音' : '开启声音');
  el.soundBtn.setAttribute('aria-pressed', String(on));
  el.landingSoundBtn.setAttribute('aria-pressed', String(on));
  el.landingSoundBtn.querySelector('span').textContent = on ? '声音已开启' : '开启声音';
  savePreferences();
}, state.sound);
function toggleSound() { audio.init(); audio.toggle(); }
// Apply saved preference without creating an AudioContext before a gesture.
audio.onChange(state.sound);

// ---------------------------------------------------------------- events
addEventListener('wheel', (e) => {
  if (state.modal || e.ctrlKey) return;
  if (state.mode === 'landing') { if (e.deltaY > 20) startExperience(); return; }
  if (state.mode !== 'travel') return;
  e.preventDefault();
  setAuto(false); state.jumping = null;
  const pixels = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? innerHeight : 1);
  state.target = clamp(state.target + clamp(pixels, -160, 160) * .000085, 0, 1);
  if (state.target > .996) state.target = 1;
}, { passive: false });

let touch = null;
canvas.addEventListener('pointerdown', (e) => {
  if (state.modal) return;
  if (e.pointerType === 'mouse' && e.button !== 0) return;
  setAuto(false); state.jumping = null;
  canvas.setPointerCapture(e.pointerId);
  touch = { x: e.clientX, y: e.clientY, lastY: e.clientY, lookX: state.look.x, lookY: state.look.y, moved: 0, scrolling: state.mode === 'travel' };
  if (state.mode === 'landing') { /* let button handle */ }
});
addEventListener('pointermove', (e) => {
  state.mouse.set((e.clientX / innerWidth - .5) * 2, (e.clientY / innerHeight - .5) * 2);
  if (!touch) return;
  const dx = e.clientX - touch.x, dy = e.clientY - touch.y;
  touch.moved = Math.max(touch.moved, Math.abs(dx) + Math.abs(dy));
  if (state.mode === 'travel') {
    state.look.x = clamp(touch.lookX - dx / innerWidth * 2, -1, 1);
    if (e.pointerType === 'mouse') state.look.y = clamp(touch.lookY - dy / innerHeight * 1.2, -.8, .8);
    if (e.pointerType !== 'mouse') {
      state.target = clamp(state.target - (e.clientY - touch.lastY) * .00055, 0, 1);
      touch.lastY = e.clientY;
    }
  }
}, { passive: true });
addEventListener('pointerup', () => { touch = null; });
addEventListener('pointercancel', () => { touch = null; });

addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (state.modal === el.finale) { closePanels(); state.mode = 'travel'; state.target = .975; state.finaleShown = false; syncUIState(true); }
    else if (state.modal) closePanels();
    else if (state.mode === 'overview') exitOverview();
    return;
  }
  if (state.modal) {
    if (e.key === 'Tab') {
      const stops = [...state.modal.querySelectorAll('button,input,select,textarea,a[href],[tabindex]:not([tabindex="-1"])')].filter(node => !node.disabled && node.getClientRects().length);
      const first = stops[0], last = stops.at(-1);
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
    }
    return;
  }
  if (e.target.closest('input,textarea,select,[contenteditable="true"]') || e.ctrlKey || e.altKey || e.metaKey) return;
  if ((e.key === 'Enter' || e.key === ' ') && e.target.closest('button,a')) return;
  if (state.mode === 'landing' && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); startExperience(); return; }
  if (state.mode === 'travel') {
    if (['ArrowDown','PageDown',' ','ArrowUp','PageUp','Home','End'].includes(e.key)) { setAuto(false); state.jumping = null; }
    if (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ') { state.target = clamp(state.target + .035, 0, 1); e.preventDefault(); }
    if (e.key === 'ArrowUp' || e.key === 'PageUp') { state.target = clamp(state.target - .035, 0, 1); e.preventDefault(); }
    if (e.key === 'Home') { jumpTo(0); }
    if (e.key === 'End') { jumpTo(1); }
  }
  if (e.key === 'm' || e.key === 'M') toggleSound();
});

el.startBtn.addEventListener('click', startExperience);
el.overviewBtn.addEventListener('click', () => { audio.sfx('click'); state.mode === 'overview' ? exitOverview() : enterOverview(); });
el.ovBack.addEventListener('click', () => { audio.sfx('click'); exitOverview(); });
el.soundBtn.addEventListener('click', toggleSound);
el.landingSoundBtn.addEventListener('click', toggleSound);
el.infoBtn.addEventListener('click', () => { audio.sfx('click'); openPanel(el.info, el.infoClose); });
$('#landingInfoBtn').addEventListener('click', () => openPanel(el.info, el.infoClose));
$('#landingOverviewBtn').addEventListener('click', enterOverview);
el.infoClose.addEventListener('click', () => closePanels());
el.cardClose.addEventListener('click', () => closePanels());
el.memoryBtn.addEventListener('click', openCard);
el.autoBtn.addEventListener('click', () => { if (state.mode === 'travel' && !state.modal) { setAuto(!state.auto); if (state.auto) showToast('沿着红线慢慢走 · 手动操作可暂停'); } });
el.homeBtn.addEventListener('click', () => {
  closePanels(false); setAuto(false); disposeFinale();
  state.started = false; state.mode = 'landing'; state.progress = 0; state.target = 0;
  state.jumping = null; state.finaleShown = false; state.chapter = -1;
  el.endCard.classList.remove('show'); el.endCard.inert = true;
  el.chapter.classList.remove('show'); el.hotspot.classList.remove('show');
  syncUIState(true); el.startBtn.focus({ preventScroll: true });
});
$$('[data-entry]').forEach(button => button.addEventListener('click', () => { startExperience(); jumpTo(ENTRY[Number(button.dataset.entry)]); }));
$$('[data-wish]').forEach(button => button.addEventListener('click', () => { el.wishInput.value = button.dataset.wish; el.wishInput.focus(); }));
$('#fullscreenBtn').addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
    else showToast('当前浏览器暂不支持全屏');
  } catch { showToast('请在浏览器中开启全屏浏览'); }
});
addEventListener('fullscreenchange', () => $('#fullscreenBtn').setAttribute('aria-label', document.fullscreenElement ? '退出全屏' : '进入全屏'));
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { setAuto(false); audio.suspend(); }
  else { last = performance.now(); audio.resume(); }
});
el.hotspot.addEventListener('click', () => { audio.sfx('click'); openCard(); });
el.timeline.addEventListener('click', (e) => {
  const b = e.target.closest('button[data-ch]');
  if (!b) return;
  audio.sfx('click');
  const i = Number(b.dataset.ch);
  const z = ZONES[i];
  jumpTo(ENTRY[i]);
});
el.launchBtn.addEventListener('click', () => launchFinale());
el.skipFinale.addEventListener('click', () => { if (state.mode === 'finalePrompt') { state.wish = el.wishInput.value.trim() || '愿山河无恙，路远必达'; closePanels(false); showEnd(); } });
el.againBtn.addEventListener('click', () => resetExperience());
el.endOverviewBtn.addEventListener('click', () => { el.endCard.classList.remove('show'); el.endCard.inert = true; enterOverview(); });
el.wishInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') launchFinale(); });

const viewportObserver = new ResizeObserver(resizeViewport);
viewportObserver.observe(el.world);

// ---------------------------------------------------------------- finale
let finale = { t: 0, active: false, plume: [], endTimer: 0 };
function disposeFinale() {
  for (const timer of finale.timers || []) clearTimeout(timer);
  for (const sprite of [...(finale.plume || []), finale.plumeGlow].filter(Boolean)) {
    scene.remove(sprite); sprite.material.dispose();
  }
  document.querySelectorAll('.lantern').forEach(node => node.remove());
  finale = { t: 0, active: false, plume: [], timers: [] };
  const rocket = zones.future?.rocket;
  if (rocket) { rocket.position.y = 7; rocket.rotation.z = 0; }
  audio.stopLaunch();
}
function launchFinale() {
  if (state.mode !== 'finalePrompt') return;
  state.wish = el.wishInput.value.trim().slice(0, 24) || '愿山河无恙，路远必达';
  closePanels(false); setAuto(false);
  if (reducedMotion) { showEnd(); return; }
  el.finale.classList.remove('show');
  el.chapter.classList.remove('show');
  state.mode = 'finale'; state.ended = false;
  disposeFinale();
  finale = { t: 0, active: true, plume: [], timers: [], startPos: camera.position.clone(), startLook: (state.camLook || new THREE.Vector3(0, 30, -1750)).clone() };
  audio.sfx('whoosh');
  audio.launch();
  // rocket plume glow
  const r = zones.future?.rocket;
  if (r) {
    const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, opacity: .8,
      depthWrite: false, color: '#ffb35a', blending: THREE.AdditiveBlending, fog: false }));
    glow.position.set(r.position.x, r.position.y + 2, r.position.z);
    glow.scale.set(22, 30, 1); glow.userData.noNormal = true; scene.add(glow); finale.plumeGlow = glow;
    for (let i = 0; i < 26; i++) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: smokeTex, transparent: true, opacity: .6,
        depthWrite: false, color: '#e8ddca', fog: true }));
      s.position.set(r.position.x + (Math.random()-.5)*14, r.position.y + Math.random()*6, r.position.z + (Math.random()-.5)*14);
      s.scale.setScalar(10 + Math.random()*18); s.userData.noNormal = true;
      s.userData.p = { vy: 6 + Math.random()*14, vx: (Math.random()-.5)*6, vz: (Math.random()-.5)*6, life: 0, max: 4 + Math.random()*4 };
      scene.add(s); finale.plume.push(s);
    }
  }
  if (!captureMode) {
    // lanterns
    for (let i = 0; i < 6; i++) finale.timers.push(setTimeout(() => {
      const l = document.createElement('div'); l.className = 'lantern'; l.textContent = state.wish;
      l.style.left = (18 + Math.random() * 64) + 'vw'; l.style.top = (58 + Math.random() * 18) + 'vh';
      document.getElementById('app').appendChild(l);
      finale.timers.push(setTimeout(() => l.remove(), 7600));
    }, i * 450));
  }
}
function updateFinale(dt) {
  if (!finale.active) return;
  finale.t += dt;
  const t = finale.t;
  const r = zones.future?.rocket;
  const ease = smooth(clamp(t / 7.5, 0, 1));
  if (r) {
    r.position.y = 7 + ease * 320;
    r.rotation.z = Math.sin(t * .7) * .006 * (1 - ease);
    if (finale.plumeGlow) { finale.plumeGlow.position.set(r.position.x, r.position.y + 3, r.position.z); finale.plumeGlow.scale.set(22 + ease*30, 30 + ease*50, 1); finale.plumeGlow.material.opacity = .8 * (1 - ease*.4); }
    for (const s of finale.plume) {
      const p = s.userData.p; p.life += dt;
      s.position.x += p.vx * dt; s.position.y += p.vy * dt; s.position.z += p.vz * dt;
      s.material.opacity = Math.max(0, .55 * (1 - p.life / p.max)) * (1 - ease*.3);
      s.scale.setScalar(10 + p.life * 5 + Math.random() * 2);
    }
    const camTarget = new THREE.Vector3(r.position.x, r.position.y + 2, r.position.z);
    const camPos = new THREE.Vector3(r.position.x - 78, r.position.y + 46, r.position.z + 168);
    const pull = smooth(clamp((t - 6.0) / 3.0, 0, 1));
    camera.position.lerp(camPos.lerp(new THREE.Vector3(220, 190, r.position.z + 300), pull), 1 - Math.exp(-dt * 1.8));
    const look = camTarget.clone().lerp(new THREE.Vector3(0, 60, r.position.z - 80), pull);
    camera.lookAt(look);
    camera.fov = 44 + pull * 8; camera.updateProjectionMatrix();
    state.camLook = look;
  } else {
    const pull = smooth(clamp(t / 6, 0, 1));
    camera.position.lerp(new THREE.Vector3(180, 150, -1550), 1 - Math.exp(-dt * 1.2));
    camera.lookAt(new THREE.Vector3(0, 20, -1700)); camera.fov = 40 + pull * 10; camera.updateProjectionMatrix();
  }
  if (!captureMode && t > 9.3) showEnd();
}
function showEnd() {
  if (state.mode === 'ended') return;
  state.mode = 'ended';
  el.endWish.textContent = state.wish;
  el.endCollection.textContent = state.collected.size === 5 ? '五枚拾光，已织成一段完整的记忆。' : `已拾起 ${state.collected.size} / 5 段记忆 · 来路，仍值得再走一次。`;
  el.endCard.classList.add('show');
  el.hud.classList.add('hidden'); el.timeline.classList.add('hidden');
  el.chapter.classList.remove('show'); el.hotspot.classList.remove('show');
  el.finale.classList.remove('show');
  closePanels(false); syncUIState(true);
  el.againBtn.focus({ preventScroll: true });
}
function resetExperience() {
  el.endCard.classList.add('show');
  el.endCard.classList.remove('show');
  disposeFinale(); closePanels(false); setAuto(false);
  state.mode = 'travel'; state.progress = 0; state.target = .045; state.chapter = -1; state.finaleShown = false; state.ended = false;
  el.hud.classList.remove('hidden'); el.timeline.classList.remove('hidden');
  el.endCard.classList.remove('show');
  el.ink.classList.add('on'); setTimeout(() => el.ink.classList.remove('on'), 500);
  state.jumping = null; state.look.set(0, 0); syncUIState(true);
}

// ---------------------------------------------------------------- main loop
function tick(dt) {
  state.time += reducedMotion ? 0 : dt;
  if (state.auto && state.mode === 'travel' && !state.modal) state.target = clamp(state.target + dt / 175, 0, 1);
  if (state.mode === 'travel' || state.mode === 'landing') {
    if (state.modal) {
      // Reading a memory or the guide pauses the journey at its current frame.
    } else if (state.jumping) {
      state.jumping.t += dt;
      const u = clamp(state.jumping.t / state.jumping.dur, 0, 1);
      const e = u < .5 ? 4*u*u*u : 1 - Math.pow(-2*u + 2, 3) / 2;
      state.progress = state.jumping.from + (state.jumping.to - state.jumping.from) * e;
      state.target = state.progress;
      if (u >= 1) state.jumping = null;
    } else {
      state.progress = damp(state.progress, state.target, 3.4, dt);
    }
    state.progress = clamp(state.progress, 0, 1);
    const ci = chapterAt(state.progress);
    if (ci !== state.chapter) {
      state.chapter = ci;
      setChapterUI(ci, ci >= 0);
      if (ci >= 0) audio.setChapter(ci);
    }
    setChapterUI(state.chapter, state.chapter >= 0 && state.voidMix < .55 && state.mode !== 'overview');
    updateCamera(dt);
    // hotspot
    updateHotspot();
    // finale trigger
    if (state.progress > .996 && state.mode === 'travel' && !state.finaleShown) {
      state.finaleShown = true; state.mode = 'finalePrompt';
      el.finale.classList.add('show'); el.hotspot.classList.remove('show');
      el.chapter.classList.remove('show');
      openPanel(el.finale, el.wishInput);
    }
  } else if (state.mode === 'overview') {
    updateCamera(dt);
  } else if (state.mode === 'finale') {
    updateFinale(dt);
  } else if (state.mode === 'finalePrompt') {
    // keep camera at end pose with a slow drift
    const p = hermite('pos', 1), l = hermite('look', 1);
    camera.position.set(p[0] + (reducedMotion ? 0 : Math.sin(state.time * .1) * 2), p[1], p[2]);
    camera.lookAt(new THREE.Vector3(l[0], l[1], l[2])); state.camLook = new THREE.Vector3(l[0], l[1], l[2]);
  }
  updateSkyLights(dt);
  updateZoneVisibility();
  updateAmbient(dt);
  updateOverviewLabels();
  const darkScene = state.voidMix < .5 && (state.chapter === 2 || state.chapter === 4 || state.mode === 'finale' || state.mode === 'finalePrompt') && state.mode !== 'landing' && state.mode !== 'overview';
  document.body.classList.toggle('dark-scene', darkScene);
  // HUD progress
  el.tlFill.style.width = (state.progress * 100).toFixed(2) + '%';
  el.journeyPct.textContent = String(Math.round(state.progress * 100)).padStart(2, '0') + '%';
  el.memoryBtn.disabled = state.chapter < 0;
  el.hotspot.inert = !el.hotspot.classList.contains('show') || !!state.modal;
  syncUIState();
  el.scrollHint.classList.toggle('show', state.mode === 'travel' && state.progress < .08);
  paper.render();
  if (!touch && !isTouch && !reducedMotion) {
    state.look.x = damp(state.look.x, state.mouse.x * .5, 1.5, dt);
    state.look.y = damp(state.look.y, state.mouse.y * .5, 1.5, dt);
  }
}

let last = performance.now();
function raf(now) {
  const dt = Math.min(.05, (now - last) / 1000); last = now;
  if (state.ready && !state.frozen && !document.hidden) tick(dt);
  requestAnimationFrame(raf);
}

// hotspot projection
function updateHotspot() {
  if (state.mode !== 'travel' || state.chapter < 0 || state.voidMix > .4) { el.hotspot.classList.remove('show'); return; }
  const z = ZONES[state.chapter]; const data = zones[z.id];
  if (!data || !data.hotspot) { el.hotspot.classList.remove('show'); return; }
  const v = data.hotspot.clone().project(camera);
  const on = v.z < 1 && v.z > -1 && Math.abs(v.x) < 1.15 && Math.abs(v.y) < 1.1;
  el.hotspot.classList.toggle('show', on);
  if (on) {
    el.hotspot.style.left = ((v.x * .5 + .5) * innerWidth) + 'px';
    el.hotspot.style.top = ((-v.y * .5 + .5) * innerHeight) + 'px';
  }
}

// ---------------------------------------------------------------- boot
async function boot() {
  await loadWorld();
  state.ready = true;
  state.mode = 'landing';
  window.__ready = true;
  setPaletteTarget(VOID_PAL);
  sky.setPalette(VOID_PAL);
  el.loadFill.style.width = '100%'; el.loadPct.textContent = '100%';
  syncUIState(true); resizeViewport(); updateCollection();
  setTimeout(() => {
    el.loading.style.opacity = '0';
    setTimeout(() => el.loading.classList.add('hidden'), 900);
    el.landing.classList.remove('hidden');
  }, 500);
  requestAnimationFrame(raf);
}
export const ready = boot();

// deterministic capture / inspection API
window.__changlu = {
  state, scene, camera, renderer, paper, sky, zones, waterSet,
  setProgress(t, instant = true) { state.progress = clamp(t, 0, 1); state.target = state.progress; if (instant) { state.jumping = null; } },
  freeze(v = true) { state.frozen = !!v; },
  advance(dt = 1 / 24) { tick(dt); paper.render(); },
  scrollTo(p) { state.target = clamp(p, 0, 1); },
  showCard() { openCard(); },
  hideCard() { closePanels(); },
  soundInfo() { return audio.info(); },
  info() { const cv = {}; for (const k of Object.keys(zones)) cv[k] = !!zones[k]?.group?.visible; return { progress: state.progress, mode: state.mode, chapter: state.chapter, voidMix: state.voidMix, cam: camera.position.toArray(), look: state.camLook?.toArray?.(), visible: cv }; },
  settle(steps = 60) {
    const ci = chapterAt(state.progress);
    if (ci !== state.chapter) {
      state.chapter = ci;
      setChapterUI(ci, ci >= 0);
      if (ci >= 0) audio.setChapter(ci);
    }
    for (let i = 0; i < steps; i++) { updateCamera(.1); updateSkyLights(.1); updateAmbient(.1); }
    updateZoneVisibility(); updateHotspot(); updateOverviewLabels();
    paper.render();
  },
  step(dt) { tick(dt); },
  start: startExperience,
  overview: enterOverview,
  exitOverview,
  launch: () => { state.mode = 'finalePrompt'; launchFinale(); },
  showEnd,
  photo(id) {
    const poses = {
      rural: { p: .09 }, town: { p: .31 }, city: { p: .56 }, rail: { p: .79 }, future: { p: .96 },
      overview: null,
    };
    document.body.classList.add('photo');
    if (id === 'overview') { enterOverview(); document.querySelectorAll('#hud,#timeline,#chapter,#hotspot,.ov-head,.ov-foot').forEach(e => e.style.display = 'none'); return; }
    state.mode = 'travel'; const t = poses[id]?.p ?? .09; this.setProgress(t); state.chapter = chapterAt(t); tick(0.001);
  },
  resumeUI() { document.body.classList.remove('photo'); location.reload(); },
};
