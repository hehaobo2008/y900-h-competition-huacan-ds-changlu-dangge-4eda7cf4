import * as THREE from 'three';
import { ASSET } from './assets.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

export function makePaperPipeline(renderer, scene, camera, opts = {}) {
  const css = renderer.getSize(new THREE.Vector2());
  const dpr = renderer.getPixelRatio();
  const size = new THREE.Vector2(css.x * dpr, css.y * dpr);
  const normalRT = new THREE.WebGLRenderTarget(size.x, size.y, {
    minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
    type: THREE.UnsignedByteType
  });
  normalRT.depthTexture = new THREE.DepthTexture(size.x, size.y);
  const normalMat = new THREE.MeshNormalMaterial({ flatShading: false });
  const composer = new EffectComposer(renderer);
  composer.setSize(css.x, css.y);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), opts.bloomStrength ?? 0.4, 0.55, 0.82);
  composer.addPass(bloom);
  const grain = new THREE.TextureLoader().load(ASSET('/assets/textures/grain.png'));
  grain.wrapS = grain.wrapT = THREE.RepeatWrapping;
  const shader = {
    uniforms: {
      tDiffuse: { value: null }, tNormal: { value: null },
      tDepth: { value: null }, tGrain: { value: null },
      resolution: { value: new THREE.Vector2(size.x, size.y) },
      cameraNear: { value: camera.near }, cameraFar: { value: camera.far },
      ink: { value: opts.ink ?? 0.85 }, grainAmount: { value: opts.grain ?? 0.06 },
      paperTint: { value: new THREE.Color(opts.paper || '#f4ecdc') },
      edgeWidth: { value: 1.25 }, time: { value: 0 }
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `
      #include <packing>
      varying vec2 vUv;
      uniform sampler2D tDiffuse, tNormal, tDepth, tGrain;
      uniform vec2 resolution;
      uniform float cameraNear, cameraFar, ink, grainAmount, edgeWidth, time;
      uniform vec3 paperTint;
      float viewZ(vec2 uv){ float d = texture2D(tDepth, uv).x; return -perspectiveDepthToViewZ(d, cameraNear, cameraFar); }
      void main(){
        vec3 col = texture2D(tDiffuse, vUv).rgb;
        vec2 px = edgeWidth / resolution;
        vec2 uvL = vUv + vec2(-px.x, 0.0), uvR = vUv + vec2(px.x, 0.0);
        vec2 uvD = vUv + vec2(0.0, -px.y), uvU = vUv + vec2(0.0, px.y);
        vec3 n0 = texture2D(tNormal, vUv).rgb * 2.0 - 1.0;
        vec3 nL = texture2D(tNormal, uvL).rgb * 2.0 - 1.0;
        vec3 nR = texture2D(tNormal, uvR).rgb * 2.0 - 1.0;
        vec3 nD = texture2D(tNormal, uvD).rgb * 2.0 - 1.0;
        vec3 nU = texture2D(tNormal, uvU).rgb * 2.0 - 1.0;
        float z0 = viewZ(vUv), zL = viewZ(uvL), zR = viewZ(uvR), zD = viewZ(uvD), zU = viewZ(uvU);
        float nEdge = max(max(1.0 - dot(n0, nL), 1.0 - dot(n0, nR)), max(1.0 - dot(n0, nD), 1.0 - dot(n0, nU)));
        // Preserve silhouettes without covering sloping terrain in solid ink.
        float zScale = 0.08 + z0 * 0.018;
        float zEdge = max(max(abs(zL - z0), abs(zR - z0)), max(abs(zD - z0), abs(zU - z0))) / zScale;
        float edge = smoothstep(0.10, 0.42, nEdge) * 0.9 + smoothstep(0.6, 1.7, zEdge) * 0.8;
        edge = clamp(edge, 0.0, 1.0);
        float grain = texture2D(tGrain, vUv * vec2(resolution.x / resolution.y, 1.0) * 2.1 + vec2(time * 0.0007, 0.0)).r;
        float fiber = texture2D(tGrain, vUv * vec2(7.0, 5.0) + 0.3).r;
        // warm paper grade, slight pigment saturation
        col = pow(col, vec3(0.96, 1.0, 1.02));
        float lum = dot(col, vec3(0.299, 0.587, 0.114));
        col = mix(vec3(lum), col, 1.14);
        col = mix(col, paperTint, 0.025);
        col *= 1.0 + (grain - 0.5) * grainAmount;
        col += (fiber - 0.5) * 0.012;
        // ink line, slightly broken like dry brush
        float broken = smoothstep(0.18, 0.72, grain * 0.7 + 0.3);
        col = mix(col, vec3(0.105, 0.085, 0.065), edge * ink * (0.72 + 0.28 * broken));
        // vignette
        vec2 q = vUv - 0.5;
        float vig = 1.0 - smoothstep(0.28, 0.85, length(q * vec2(1.0, 1.15)));
        col *= 0.94 + 0.06 * vig;
        gl_FragColor = vec4(col, 1.0);
        #include <colorspace_fragment>
      }`
  };
  const paperPass = new ShaderPass(shader);
  // ShaderPass clones uniforms; render-target textures must be re-bound after cloning.
  paperPass.uniforms.tNormal.value = normalRT.texture;
  paperPass.uniforms.tDepth.value = normalRT.depthTexture;
  paperPass.uniforms.tGrain.value = grain;
  composer.addPass(paperPass);
  return {
    composer, normalRT, normalMat, paperPass, bloom,
    render() {
      renderer.setRenderTarget(normalRT);
      const hidden = [];
      scene.traverse(o => { if (o.userData && o.userData.noNormal && o.visible) { o.visible = false; hidden.push(o); } });
      scene.overrideMaterial = normalMat;
      const fog = scene.fog; scene.fog = null;
      const bg = scene.background; scene.background = new THREE.Color(0x000000);
      renderer.render(scene, camera);
      scene.overrideMaterial = null;
      for (const o of hidden) o.visible = true;
      scene.fog = fog; scene.background = bg;
      renderer.setRenderTarget(null);
      paperPass.uniforms.time.value += 0.016;
      composer.render();
    },
    setSize(w, h) {
      const d = renderer.getPixelRatio();
      composer.setPixelRatio(d);
      composer.setSize(w, h);
      normalRT.setSize(w * d, h * d);
      paperPass.uniforms.resolution.value.set(w * d, h * d);
      bloom.resolution.set(w, h);
    }
  };
}
