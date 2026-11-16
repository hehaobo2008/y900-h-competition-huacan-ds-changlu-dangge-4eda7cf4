import * as THREE from 'three';
import {AssetTextureLoader} from './asset_loaders.js';

const names = ['day','night','market-horizon','avenue-horizon','port-horizon','river-horizon',
  'camphor','willow','pine','reeds','granary','market','noodles','orangery',
  'harvester','family','umbrella','scientist','lime','tiles','earth','puddles',
  'copse','foreshore','conifers','rice','balcony','tenement','laboratory','cottage'];
export async function loadPaintings() {
  const loader = new AssetTextureLoader();
  const pairs = await Promise.all(names.map(async name => {
    const texture = await loader.loadAsync('/assets/painted/' + name + '.webp');
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 4;
    texture.name = name;
    return [name,texture];
  }));
  return Object.fromEntries(pairs);
}

const skies = { rural:['day',.19],town:['market-horizon',.58],city:['avenue-horizon',.54],
  rail:['river-horizon',.35],future:['port-horizon',.51] };

export class PaintedSky {
  constructor(scene) {
    this.group = new THREE.Group();
    this.tint = new THREE.Color();
    this.group.userData.noNormal = true;
    this.mat = new THREE.ShaderMaterial({
      side:THREE.BackSide,depthWrite:false,fog:false,
      uniforms:{painting:{value:null},nextPainting:{value:null},zenith:{value:null},cloudPaper:{value:null},
        skyFrame:{value:new THREE.Vector4()},nextFrame:{value:new THREE.Vector4()},skyBlend:{value:0},
        mist:{value:0},land:{value:new THREE.Color('#8ca882')},mistLight:{value:new THREE.Color()}},
      vertexShader:'varying vec3 direction; void main(){direction=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
      fragmentShader:`varying vec3 direction;
        uniform sampler2D painting,nextPainting,zenith,cloudPaper;
        uniform vec4 skyFrame,nextFrame; uniform float skyBlend,mist; uniform vec3 land,mistLight;
        vec3 sampleSky(sampler2D plate,vec4 frame,float lon,float elev,vec3 dir){
          float u=1.-abs(mod(frame.x+lon*2.,2.)-1.);
          vec3 paint=texture2D(plate,vec2(u,clamp(frame.y+elev*frame.z,.008,.993))).rgb;
          if(frame.w>0. && elev>.50){
            // Project the overhead painting onto a tangent plane. Longitude
            // collapses at the pole and would pinch the brushwork into a seam.
            vec2 uv=vec2(.51,.68)+dir.xz*vec2(.47,.29);
            paint=mix(paint,texture2D(zenith,uv).rgb,smoothstep(.50,1.02,elev));
          }
          if(frame.w>0.){
            float luminance=dot(paint,vec3(.2126,.7152,.0722));
            paint=mix(vec3(luminance),paint,.71)*vec3(.94,1.015,1.01);
          }
          return paint;
        }
        void main(){
          vec3 d=normalize(direction);
          float lon=atan(d.x,-d.z)/6.2831853;
          float elev=asin(clamp(d.y,-1.,1.));
          vec3 paint=sampleSky(painting,skyFrame,lon,elev,d);
          if(skyBlend>0.) paint=mix(paint,sampleSky(nextPainting,nextFrame,lon,elev,d),skyBlend);
          paint=mix(land,paint,smoothstep(-.16,-.065,elev));
          if(mist>0. && d.y<0.){
            // Project a low bank of painted cloud below the book edges. Its brushwork
            // stays in world space as the viewer flies past it in either direction.
            vec2 ground=cameraPosition.xz+d.xz*(-22.-cameraPosition.y)/min(d.y,-.013);
            vec2 sheet=1.-abs(mod(ground*vec2(.0032,.0045)+vec2(.52,.91),2.)-1.);
            vec3 cloud=texture2D(cloudPaper,vec2(sheet.x,.39+sheet.y*.58)).rgb;
            float light=smoothstep(.24,.82,dot(cloud,vec3(.28,.57,.15)));
            vec3 bank=mix(land*.86,mistLight,.20+.67*light);
            paint=mix(paint,bank,mist*(1.-smoothstep(-.19,-.025,elev)));
          }
          gl_FragColor=vec4(paint,1.);
        }`
    });
    const dome=new THREE.Mesh(new THREE.SphereGeometry(1400,50,26),this.mat);
    dome.renderOrder=-20;
    this.group.add(dome); scene.add(this.group);
    const {cloudPaper,mist,mistLight,land}=this.mat.uniforms;
    const bankMaterial=new THREE.ShaderMaterial({
      transparent:true,depthWrite:false,side:THREE.DoubleSide,
      uniforms:{cloudPaper,mist,mistLight,land},
      vertexShader:`varying vec2 field; varying vec2 brushUV;
        void main(){
          field=position.xy;
          vec3 local=position;
          local.z+=2.1*sin(field.x*.033+field.y*.021)+1.4*cos(field.y*.093-field.x*.013);
          brushUV=(modelMatrix*vec4(local,1.)).xz;
          gl_Position=projectionMatrix*modelViewMatrix*vec4(local,1.);
        }`,
      fragmentShader:`varying vec2 field; varying vec2 brushUV;
        uniform sampler2D cloudPaper; uniform float mist; uniform vec3 mistLight,land;
        void main(){
          vec2 sheet=1.-abs(mod(brushUV*vec2(.006,.013)+vec2(.32,.71),2.)-1.);
          vec3 paint=texture2D(cloudPaper,vec2(sheet.x,.42+.52*sheet.y)).rgb;
          float brush=smoothstep(.21,.85,dot(paint,vec3(.28,.57,.15)));
          float shore=abs(abs(field.y)-59.);
          float coverage=(1.-smoothstep(3.,64.,shore+17.*(brush-.45)))*(1.-smoothstep(143.,271.,abs(field.x)));
          float alpha=mist*coverage*(.13+.47*brush);
          gl_FragColor=vec4(mix(land,mistLight,.52+.31*brush),alpha);
        }`
    });
    this.banks=new THREE.Mesh(new THREE.PlaneGeometry(600,290,25,14),bankMaterial);
    this.banks.name='Mist along the island edges';
    this.banks.rotation.x=-Math.PI/2;this.banks.position.y=7;
    this.banks.visible=false;this.banks.userData.noNormal=true;scene.add(this.banks);
  }
  setPalette(p,next=p,blend=0) {
    if(!this.plates || !skies[p.name]) return;
    const u=this.mat.uniforms;
    u.painting.value=this.plates[skies[p.name][0]];
    u.nextPainting.value=this.plates[skies[next.name][0]];
    u.zenith.value=this.plates.night;
    u.cloudPaper.value=this.plates.day;
    for(const [key,frame] of [[p.name,u.skyFrame.value],[next.name,u.nextFrame.value]]){
      frame.set(skies[key][1],key==='rail'?.235:.135,key==='rail'?1.82:1.08,key==='future'?1:0);
    }
    u.skyBlend.value=blend;
    u.land.value.set(p.fog).lerp(this.tint.set(next.fog),blend);
    u.mistLight.value.set(p.bot).lerp(this.tint.set(next.bot),blend);
  }
  update(camera,mist,overview,gapZ) {
    this.group.position.copy(camera.position);
    this.group.visible=!!this.plates && !overview;
    this.mat.uniforms.mist.value=mist;
    this.banks.visible=gapZ!==undefined && mist>.001;
    if(this.banks.visible) this.banks.position.z=gapZ;
  }
}

const paintKeys={
  rural:[.73,.58,.34,0], town:[-.64,.50,.60,0], city:[-.55,.67,.48,1],
  rail:[-.70,.48,.45,0], future:[.50,.60,.64,1]
};
const canopyPaint={
  town:['#395d43','#a0b45d'],city:['#264c50','#698b73'],river:['#315f4c','#91aa69'],
  pine:['#265449','#6c986e'],silver:['#3a5d59','#99b3a2'],copper:['#72475c','#c28e76']
};

// Preserve mesh UVs, liveries and cast shadows. Compress the lighting response into
// three masses, then add separate reflected colour and a short highlight on metal.
export function illustrate(mat, chapter) {
  if(!mat?.isMeshStandardMaterial || mat.userData.paintChapter===chapter) return;
  mat.userData.paintChapter=chapter;
  const key=paintKeys[chapter];
  const isNight=key[3]===1;
  const foliage=canopyPaint[mat.name.replace(/^Q leaves /,'')];
  const previous=mat.onBeforeCompile.bind(mat);
  const cache=mat.customProgramCacheKey();
  mat.customProgramCacheKey=()=>cache+'-paint-'+chapter+(foliage?'-foliage':'');
  mat.envMapIntensity=.20;
  if(mat.normalMap) mat.normalScale.multiplyScalar(.27);
  mat.onBeforeCompile=(shader,renderer)=>{
    previous(shader,renderer);
    if(chapter==='rail'){
      shader.vertexShader='varying vec3 boreWorld;\n'+shader.vertexShader.replace('#include <project_vertex>',`
        vec4 bp=vec4(transformed,1.);
        #ifdef USE_INSTANCING
        bp=instanceMatrix*bp;
        #endif
        boreWorld=(modelMatrix*bp).xyz;
        #include <project_vertex>`);
      shader.fragmentShader='varying vec3 boreWorld;\n'+shader.fragmentShader;
    }
    shader.uniforms.paintKey={value:new THREE.Vector3(...key.slice(0,3)).normalize()};
    if(foliage){
      shader.uniforms.leafShade={value:new THREE.Color(foliage[0])};
      shader.uniforms.leafLight={value:new THREE.Color(foliage[1])};
      shader.fragmentShader='uniform vec3 leafShade, leafLight;\n'+shader.fragmentShader;
    }
    shader.fragmentShader='uniform vec3 paintKey;\n'+shader.fragmentShader.replace('#include <opaque_fragment>',`
      vec3 pigment=max(diffuseColor.rgb,vec3(0.));
      vec3 wn=inverseTransformDirection(normal,viewMatrix);
      ${foliage?'wn*=gl_FrontFacing?1.:-1.;':''}
      float nd=dot(wn,paintKey);
      float lum=dot(pigment,vec3(.25,.60,.15));
      float direct=dot(reflectedLight.directDiffuse,vec3(.25,.60,.15))/max(.04,lum);
      float face=nd+.16*clamp(direct,0.,1.);
      float aa=clamp(fwidth(face)*1.2,.035,.12);
      float mid=smoothstep(-.28-aa,-.28+aa,face);
      float light=smoothstep(.47-aa,.47+aa,face)*(.66+.34*smoothstep(.015,.36,direct));
      vec3 base=pow(pigment,vec3(.90));
      vec3 shade=base*${isNight?'vec3(.28,.37,.66)':'vec3(.45,.59,.63)'}+${isNight?'vec3(.015,.022,.061)':'vec3(.012,.018,.027)'};
      vec3 halfTone=base*${isNight?'vec3(.50,.66,.88)':'vec3(.89,.91,.78)'};
      vec3 lit=base*${isNight?'vec3(.85,.97,1.17)':'vec3(1.38,1.20,.95)'};
      vec3 painted=mix(mix(shade,halfTone,mid*.91),lit,light);
      float glint=smoothstep(.13,.38,dot(totalSpecular,vec3(.26,.56,.18)));
      painted+=totalSpecular*.14+glint*(.06+.12*metalnessFactor);
      outgoingLight=mix(painted,outgoingLight-totalEmissiveRadiance,.15)+totalEmissiveRadiance;
      ${foliage?`// Both sides of each leaf spray share its authored crown normal.
      // Join the individually cut leaves into two readable masses of foliage.
      float leafValue=clamp(.32+.40*nd+.87*lum,0.,1.);
      float wash=.66*smoothstep(.27,.86,leafValue)+.34*leafValue;
      outgoingLight=mix(outgoingLight,mix(leafShade,leafLight,wash)*(.79+.20*clamp(direct,0.,1.)),.65);`:''}
      ${chapter==='rail'?`float along=abs(boreWorld.z+1260.);
        float bore=smoothstep(107.8,119.,along)*(1.-smoothstep(142.,146.,along))
         *smoothstep(30.75,31.6,boreWorld.y)
         *(1.-smoothstep(6.9,7.3,abs(boreWorld.x)))*(1.-smoothstep(42.5,43.2,boreWorld.y));
       outgoingLight=mix(outgoingLight,outgoingLight*vec3(.075,.104,.135)+totalEmissiveRadiance,bore);`:''}
      #include <opaque_fragment>`);
  };
  mat.needsUpdate=true;
}
