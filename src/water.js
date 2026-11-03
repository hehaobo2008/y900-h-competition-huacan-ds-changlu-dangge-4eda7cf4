import * as THREE from 'three';
export function applyWater(scene, kind = 'all') {
  const zoneKind = kind;
  const uniforms = {
    uTime: { value: 0 },
    uSunDir: { value: new THREE.Vector3(-0.5, 0.2, -0.55).normalize() },
    uDeep: { value: new THREE.Color('#2f5a52') },
    uShallow: { value: new THREE.Color('#7fa58f') },
    uSky: { value: new THREE.Color('#cfd9ce') },
    uSun: { value: new THREE.Color('#ffd9a0') },
    fogColor: { value: new THREE.Color('#e8ddc8') },
    fogNear: { value: 170 }, fogFar: { value: 430 }
  };
  const makeMat = (over) => {
    const u = THREE.UniformsUtils.clone(uniforms);
    for (const k in over) u[k].value = over[k];
    return new THREE.ShaderMaterial({
    uniforms: u, fog: true, side: THREE.FrontSide,
    vertexShader: `
      varying vec3 vWorld;
      #include <common>
      #include <fog_pars_vertex>
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorld = wp.xyz;
        vec4 mvPosition = viewMatrix * wp;
        gl_Position = projectionMatrix * mvPosition;
        #include <fog_vertex>
      }`,
    fragmentShader: `
      uniform float uTime;
      uniform vec3 uSunDir, uDeep, uShallow, uSky, uSun;
      varying vec3 vWorld;
      #include <common>
      #include <fog_pars_fragment>
      void main() {
        vec2 p = vWorld.xz;
        float w1 = sin(p.x * .55 + uTime * .9) * .04;
        float w2 = sin(p.y * .72 - uTime * .7) * .035;
        float w3 = sin((p.x + p.y) * 1.35 + uTime * 1.7) * .02;
        vec3 n = normalize(vec3(w1 + w3, 1.0, w2 - w3));
        vec3 view = normalize(cameraPosition - vWorld);
        float fres = pow(1.0 - max(dot(n, view), 0.0), 3.0);
        float band = smoothstep(.55, .95, sin((p.x - p.y) * .28 + uTime * .25) * .5 + .5);
        vec3 col = mix(uDeep, uShallow, .35 + .3 * (w1 + w2) * 8.0 + band * .18);
        col = mix(col, uSky, fres * .55);
        vec3 h = normalize(view + normalize(uSunDir));
        float spec = pow(max(dot(n, h), 0.0), 160.0) * 1.4;
        spec += pow(max(dot(n, h), 0.0), 18.0) * .10;
        col += uSun * spec;
        float ripple = (1.0 - smoothstep(.0, .02, abs(sin(p.x * 2.3 + p.y * 1.2 + uTime * 1.8)))) * .035;
        col += ripple * uSky;
        gl_FragColor = vec4(col, 1.0);
        #include <fog_fragment>
      }`
  }); };
  const pondMat = makeMat({ uDeep: new THREE.Color('#2f5a52'), uShallow: new THREE.Color('#8fb7a3'), uSky: new THREE.Color('#cfd9ce') });
  const paddyMat = makeMat({ uDeep: new THREE.Color('#435f43'), uShallow: new THREE.Color('#8ba06a'), uSky: new THREE.Color('#b7c9ae') });
  scene.traverse(o => {
    if (o.isMesh && o.material && o.material.name === 'Water') {
      const isPaddy = o.name.includes('Paddy') || o.name.includes('Terrace');
      o.material = isPaddy ? paddyMat : pondMat;
      o.receiveShadow = false;
    }
  });
  return { pondMat, paddyMat };
}
