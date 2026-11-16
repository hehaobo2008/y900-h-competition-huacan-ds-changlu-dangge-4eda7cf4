import * as THREE from 'three';
import {makePaperPipeline} from '../../src/paper.js';
import {ASSET} from '../../src/assets.js';
import {RADIUS} from './choreography.js';
const noise=`
float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
float noise3(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
 mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);}
float fbm(vec3 p){float s=0.,w=.5;for(int i=0;i<4;i++){s+=w*noise3(p);p=p*2.03+vec3(13.1,7.2,5.4);w*=.5;}return s;}
`;
const vertex=`varying vec2 vUv;varying vec3 worldN;varying vec3 worldP;varying vec3 localP;
void main(){vUv=uv;localP=normalize(position);worldN=normalize(mat3(modelMatrix)*normal);vec4 p=modelMatrix*vec4(position,1.);worldP=p.xyz;gl_Position=projectionMatrix*viewMatrix*p;}`;
export function softenSky(material){
 material.uniforms.vacuumFade={value:0};material.uniforms.upperAtmosphere={value:0};
 material.fragmentShader='uniform float vacuumFade,upperAtmosphere;\n'+material.fragmentShader.replace('gl_FragColor=vec4(paint,1.);',`float horizon=pow(1.-abs(normalize(direction).y),2.7);
 vec3 highAir=mix(vec3(.003,.010,.026),vec3(.043,.105,.165),horizon);
 paint=mix(paint,highAir,upperAtmosphere);
 gl_FragColor=vec4(mix(paint,vec3(.0008,.0018,.0042),vacuumFade),1.);`);
 material.needsUpdate=true;
}
export function makeStars(){
 const positions=new Float32Array(750*3);let seed=734;
 const random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
 for(let i=0;i<750;i++){const z=random()*2-1,q=random()*Math.PI*2,r=Math.sqrt(1-z*z);positions.set([r*Math.cos(q)*70000,z*70000,r*Math.sin(q)*70000],i*3);}
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));
 const stars=new THREE.Points(geometry,new THREE.PointsMaterial({color:'#abc4d7',size:1.2,sizeAttenuation:false,transparent:true,opacity:0,depthWrite:false,fog:false}));
 stars.name='Distant stars';stars.renderOrder=-15;stars.userData.noNormal=true;return stars;
}
export async function makeEarthWorld(renderer,launchSky){
 const scene=new THREE.Scene();scene.background=new THREE.Color('#02050b');
 const camera=new THREE.PerspectiveCamera(52,innerWidth/innerHeight,1,160000);
 const loader=new THREE.TextureLoader();
 const [texture,cloudMap]=await Promise.all([loader.loadAsync(ASSET('/prototype/earth.jpg')),loader.loadAsync(ASSET('/prototype/clouds.jpg'))]);
 texture.colorSpace=THREE.SRGBColorSpace;cloudMap.colorSpace=THREE.NoColorSpace;
 for(const map of [texture,cloudMap]){map.anisotropy=Math.min(16,renderer.capabilities.getMaxAnisotropy());map.wrapS=THREE.RepeatWrapping;}
 const sunLocal={value:new THREE.Vector3()},cloudShift={value:.04};
 const sun=new THREE.Vector3(-.65,.68,.34).normalize(),haze={value:.1};
 const sphere=new THREE.SphereGeometry(1,512,256);
 const material=new THREE.ShaderMaterial({
  uniforms:{surface:{value:texture},cloudMap:{value:cloudMap},sun:{value:sun},sunLocal,haze,cloudShift},vertexShader:vertex,fragmentShader:noise+`
   uniform sampler2D surface,cloudMap;uniform vec3 sun,sunLocal;uniform float haze,cloudShift;
   varying vec2 vUv;varying vec3 worldN;varying vec3 worldP;varying vec3 localP;
   void main(){
    vec3 n=normalize(worldN),view=normalize(cameraPosition-worldP);
    vec3 base=texture2D(surface,vUv).rgb;
    float luminance=dot(base,vec3(.2126,.7152,.0722));
    base=mix(vec3(luminance),base,.82);
    float water=smoothstep(.015,.065,base.b-base.r)* (1.-smoothstep(.15,.34,luminance));
    base=mix(base,base*.72+vec3(.009,.022,.026),water*.32);
    base*=.98+.05*fbm(localP*1400.);
    float light=.07+.93*pow(max(0.,dot(n,sun)),.78);
    vec3 cloudRay=normalize(localP+sunLocal*.0013/max(.25,dot(localP,sunLocal)));
    vec2 shadowUV=vec2(fract(atan(cloudRay.z,-cloudRay.x)/6.2831853),asin(clamp(cloudRay.y,-1.,1.))/3.14159265+.5);
    shadowUV.x+=cloudShift;
    float cloudShadow=texture2D(cloudMap,shadowUV,1.0).r;
    vec3 color=base*light*(1.-.23*smoothstep(.14,.8,cloudShadow));
    float limb=pow(1.-max(0.,dot(n,view)),3.);
    color=mix(color,vec3(.075,.19,.28),clamp(limb*.68+haze,0.,.72));
    gl_FragColor=vec4(color,1.);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
   }`});
 const earth=new THREE.Mesh(sphere,material);earth.scale.setScalar(RADIUS);earth.name='Continuous Earth';earth.userData.noNormal=true;scene.add(earth);
 // Orient the launch latitude at the top of the sphere, with north in the
 // camera's forward direction. This removes the previous mid-shot roll.
 const lat=30*Math.PI/180,lon=116*Math.PI/180;
 const normal=new THREE.Vector3(Math.cos(lat)*Math.cos(lon),Math.sin(lat),-Math.cos(lat)*Math.sin(lon));
 const east=new THREE.Vector3(-Math.sin(lon),0,-Math.cos(lon));
 const north=new THREE.Vector3(-Math.sin(lat)*Math.cos(lon),Math.cos(lat),Math.sin(lat)*Math.sin(lon));
 const from=new THREE.Matrix4().makeBasis(east,normal,north.clone().negate()).transpose();
 const to=new THREE.Matrix4().makeBasis(new THREE.Vector3(.8,0,-.6),new THREE.Vector3(0,1,0),new THREE.Vector3(.6,0,.8));
 earth.quaternion.setFromRotationMatrix(to.multiply(from));
 sunLocal.value.copy(sun).applyQuaternion(earth.quaternion.clone().invert());
 // An 8K cloud-density atlas keeps weather fronts and fine wisps intact.
 // Density drives both optical thickness and the offset shadow on the surface.
 const cloudUniforms={cloudMap:{value:cloudMap},sun:{value:sun},haze,cloudShift};
 function cloudLayer(height,opacity,soften,lower){
  const mesh=new THREE.Mesh(sphere,new THREE.ShaderMaterial({
   uniforms:{...cloudUniforms,layerOpacity:{value:opacity},mipSoftness:{value:soften},lower:{value:lower}},
   vertexShader:vertex,transparent:true,depthWrite:false,fragmentShader:`
    uniform sampler2D cloudMap;uniform vec3 sun;uniform float haze,layerOpacity,mipSoftness,lower,cloudShift;
    varying vec2 vUv;varying vec3 worldN;varying vec3 worldP;
    void main(){
     vec4 sampleCloud=texture2D(cloudMap,vUv+vec2(cloudShift,0.),mipSoftness);
     float density=clamp((sampleCloud.r-.018)/.982,0.,1.);
     float alpha=(1.-exp(-density*1.65))*layerOpacity;
     vec3 normal=normalize(worldN),view=normalize(cameraPosition-worldP);
     float light=.34+.76*max(0.,dot(normal,sun));
     vec3 col=mix(vec3(.72,.79,.83),vec3(.99,.99,.97),smoothstep(.06,.65,density))*light*(1.15-lower*.13);
     float thin=1.-smoothstep(.1,.7,density);
     col=mix(col,vec3(.22,.31,.39),thin*.15+lower*.12);
     float limb=pow(1.-max(0.,dot(normal,view)),4.);
     col=mix(col,vec3(.12,.27,.37),limb*.32+haze*.25);
     gl_FragColor=vec4(col,alpha);
     #include <tonemapping_fragment>
     #include <colorspace_fragment>
    }`
  }));
  mesh.scale.setScalar(RADIUS+height);mesh.quaternion.copy(earth.quaternion);mesh.userData.noNormal=true;scene.add(mesh);return mesh;
 }
 const cloudBase=cloudLayer(5.2,.34,1.0,1);cloudBase.name='Cloud underside';
 const clouds=cloudLayer(9.0,1.10,0,0);clouds.name='Satellite cloud canopy';
 const atmosphere=new THREE.Mesh(sphere,new THREE.ShaderMaterial({
  side:THREE.BackSide,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
  uniforms:{sun:{value:sun}},vertexShader:vertex,fragmentShader:`
   uniform vec3 sun;varying vec3 worldN;varying vec3 worldP;
   void main(){
    vec3 ray=normalize(worldP-cameraPosition);float b=dot(cameraPosition,ray);
    float span=sqrt(max(0.,b*b-dot(cameraPosition,cameraPosition)+6436.*6436.));
    float begin=max(0.,-b-span),end=-b+span,stepSize=max(0.,end-begin)/12.;
    float optical=0.,day=0.;
    for(int i=0;i<12;i++){
     vec3 p=cameraPosition+ray*(begin+(float(i)+.5)*stepSize);
     float density=exp(-max(0.,length(p)-6371.)/9.0)*stepSize;
     optical+=density;day+=density*(.22+.78*max(0.,dot(normalize(p),sun)));
    }
    float glow=(1.-exp(-optical*.018))*day/max(.001,optical);
    gl_FragColor=vec4(.12,.32,.53,glow*.8);
   }`}));
 atmosphere.name='Thin atmosphere';atmosphere.scale.setScalar(RADIUS+65);atmosphere.userData.noNormal=true;scene.add(atmosphere);
 const sky=launchSky.group.clone(true);
 sky.traverse(o=>{if(o.isMesh)o.material=launchSky.mat.clone()});
 sky.userData.noNormal=true;scene.add(sky);
 const stars=makeStars();stars.material.opacity=.55;scene.add(stars);
 const paper=makePaperPipeline(renderer,scene,camera,{ink:0,grain:.014,bloomStrength:.075,paper:'#eaf1f3'});
 function render(altitude,skyFade=1){
  haze.value=.17*Math.exp(-altitude/600);
  sky.position.copy(camera.position);sky.traverse(o=>{if(o.isMesh){o.material.uniforms.vacuumFade.value=skyFade;o.material.uniforms.upperAtmosphere.value=1;}});
  stars.position.copy(camera.position);stars.material.opacity=skyFade*.55;camera.updateMatrixWorld();paper.render();
 }
 return {scene,camera,earth,clouds,atmosphere,paper,render,
  resize(w,h){camera.aspect=w/h;camera.updateProjectionMatrix();paper.setSize(w,h)}
 };
}
