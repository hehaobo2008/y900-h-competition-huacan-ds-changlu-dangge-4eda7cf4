import * as THREE from 'three';
import {AssetTextureLoader} from './asset_loaders.js';
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
  const clearNormals = new THREE.Color(0x000000);
  // The canvas antialias setting alone cannot cover geometry drawn into the paper pass.
  const colorTarget=new THREE.WebGLRenderTarget(size.x,size.y,{type:THREE.HalfFloatType});
  const composer = new EffectComposer(renderer,colorTarget);
  const gl=renderer.getContext();
  const samples=gl.getInternalformatParameter(gl.RENDERBUFFER,gl.RGBA16F,gl.SAMPLES);
  composer.readBuffer.samples=Array.from(samples || []).find(n=>n>0 && n<=4) || 0;
  composer.readBuffer.resolveDepthBuffer=false;
  composer.setSize(css.x, css.y);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), opts.bloomStrength ?? 0.4, 0.55, 0.82);
  composer.addPass(bloom);
  const grain = new AssetTextureLoader().load('/assets/textures/grain.png');
  grain.wrapS = grain.wrapT = THREE.RepeatWrapping;
  const shader = {
    uniforms: {
      tDiffuse: { value: null }, tNormal: { value: null },
      tDepth: { value: null }, tGrain: { value: null },
      resolution: { value: new THREE.Vector2(size.x, size.y) },
      cameraNear: { value: camera.near }, cameraFar: { value: camera.far },
      ink: { value: opts.ink ?? 0.85 }, grainAmount: { value: opts.grain ?? 0.06 },
      paperTint: { value: new THREE.Color(opts.paper || '#f4ecdc') },
      edgeWidth: { value: .91 }, time: { value: 0 },
      projectionScale: { value: 1 }, invProjection: { value: camera.projectionMatrixInverse }
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `
      #include <packing>
      varying vec2 vUv;
      uniform sampler2D tDiffuse, tNormal, tDepth, tGrain;
      uniform vec2 resolution;
      uniform float cameraNear, cameraFar, ink, grainAmount, edgeWidth, time, projectionScale;
      uniform mat4 invProjection;
      uniform vec3 paperTint;
      float viewZ(vec2 uv){ float d = texture2D(tDepth, uv).x; return -perspectiveDepthToViewZ(d, cameraNear, cameraFar); }
      vec3 positionAt(vec2 uv){
        vec4 v=invProjection*vec4(uv*2.0-1.0,texture2D(tDepth,uv).x*2.0-1.0,1.0);
        return v.xyz/v.w;
      }
      float contact(vec3 p,vec3 normal,vec2 uv,float radius){
        vec3 delta=positionAt(uv)-p; float dist=length(delta);
        return max(0.0,dot(normal,delta/max(.001,dist))-.13)*(1.0-smoothstep(.06,radius,dist));
      }
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
        float zScale = 0.08 + z0 * 0.014;
        float zEdge = max(abs(zL+zR-2.0*z0),abs(zU+zD-2.0*z0)) / zScale;
        float edge = smoothstep(0.10, 0.42, nEdge) * 0.9 + smoothstep(0.6, 1.7, zEdge) * 0.8;
        edge = clamp(edge, 0.0, 1.0);
        float grain = texture2D(tGrain, vUv * vec2(resolution.x / resolution.y, 1.0) * 2.1 + vec2(time * 0.0007, 0.0)).r;
        float fiber = texture2D(tGrain, vUv * vec2(7.0, 5.0) + 0.3).r;
        if(z0 < 160.0 && dot(n0,n0)<1.25){
          vec3 p=positionAt(vUv); vec3 nn=normalize(n0);
          float radius=clamp(z0*.032,.20,1.30);
          vec2 r=clamp(radius*projectionScale/max(z0,.2),2.0,26.0)/resolution;
          float ao=contact(p,nn,vUv+r*vec2(.91,.41),radius)+contact(p,nn,vUv+r*vec2(-.41,.91),radius)
                  +contact(p,nn,vUv+r*vec2(-.91,-.41),radius)+contact(p,nn,vUv+r*vec2(.41,-.91),radius);
          col *= 1.0-min(ao*.12,.22)*(1.0-smoothstep(90.0,160.0,z0));
        }
        col *= mix(vec3(1.0),paperTint,.018);
        float line=edge*ink*(.90+.10*grain)*(1.-.77*smoothstep(22.,155.,z0));
        vec3 inkTone=mix(vec3(.026,.043,.066),vec3(.102,.069,.056),smoothstep(.08,.5,col.r-col.b+.16));
        col=mix(col,min(col*.76,inkTone),line);
        vec2 q = vUv - 0.5;
        float vig = 1.0 - smoothstep(0.28, 0.85, length(q * vec2(1.0, 1.15)));
        col *= (0.94 + 0.06 * vig)*(1.0+(grain-.5)*grainAmount+(fiber-.5)*.012);
        gl_FragColor = vec4(max(col,0.0), 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`
  };
  const paperPass = new ShaderPass(shader);
  // Only the colour buffer receiving actual scene geometry needs multisampling.
  // The final paper goes to screen (or the warm-up target) and has no consumer after it.
  paperPass.needsSwap=false;
  // ShaderPass clones uniforms; render-target textures must be re-bound after cloning.
  paperPass.uniforms.tNormal.value = normalRT.texture;
  paperPass.uniforms.tDepth.value = normalRT.depthTexture;
  paperPass.uniforms.tGrain.value = grain;
  composer.addPass(paperPass);
  return {
    composer, normalRT, normalMat, paperPass, bloom,
    render() {
      // Distant island views need more depth precision for architectural details.
      // Preserve the close clipping distance at pedestrian eye level.
      const near = Math.min(4, .1 + .016 * Math.max(0, camera.position.y - 4.5));
      if (opts.autoNear !== false && Math.abs(camera.near - near) > .0001) {
        camera.near = near;
        camera.updateProjectionMatrix();
      }
      paperPass.uniforms.cameraNear.value = camera.near;
      paperPass.uniforms.cameraFar.value = camera.far;
      this.prepareWoodland?.(camera);
      paperPass.uniforms.projectionScale.value = .5*paperPass.uniforms.resolution.value.y*camera.projectionMatrix.elements[5];
      renderer.setRenderTarget(normalRT);
      const hidden = [];
      scene.traverseVisible(o => { if (o.userData.noNormal) { o.visible = false; hidden.push(o); } });
      scene.overrideMaterial = normalMat;
      const fog = scene.fog; scene.fog = null;
      const bg = scene.background; scene.background = clearNormals;
      const shadowUpdate=renderer.shadowMap.autoUpdate;
      renderer.shadowMap.autoUpdate=false;
      renderer.render(scene, camera);
      renderer.shadowMap.autoUpdate=shadowUpdate;
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
