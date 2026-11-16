import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';

function surfaceGrain() {
  const size=256, data=new Uint8Array(size*size*4);
  const hash=(x,y)=>{
    let n=Math.imul(x+1,374761393)+Math.imul(y+17,668265263);
    n=Math.imul(n^(n>>>13),1274126177);
    return ((n^(n>>>16))>>>0)/4294967296;
  };
  function octave(x,y,n) {
    const u=x*n/size,v=y*n/size,i=Math.floor(u),j=Math.floor(v);
    let a=u-i,b=v-j; a=a*a*(3-2*a); b=b*b*(3-2*b);
    const mix=(a,b,t)=>a+(b-a)*t;
    return mix(mix(hash(i,j),hash((i+1)%n,j),a),mix(hash(i,(j+1)%n),hash((i+1)%n,(j+1)%n),a),b);
  }
  for(let y=0;y<size;y++) for(let x=0;x<size;x++){
    const i=(y*size+x)*4;
    data[i]=255*(octave(x,y,4)*.46+octave(x,y,12)*.34+octave(x,y,36)*.20);
    data[i+1]=255*(hash(x,y)*.54+octave(x,y,80)*.46);
    data[i+2]=255*octave(x,y,24); data[i+3]=255;
  }
  const texture=new THREE.DataTexture(data,size,size);
  texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
  texture.magFilter=THREE.LinearFilter; texture.minFilter=THREE.LinearMipmapLinearFilter;
  texture.generateMipmaps=true; texture.anisotropy=4; texture.needsUpdate=true;
  return texture;
}
const grain=surfaceGrain();

export function paintSurfaces(mat, chapter, plates) {
  const kind=mat.name;
  const surface={
    Rural_Limewash_PBR:'lime',Rural_Grey_Tile_PBR:'tile',Rural_Dirt_PBR:'earth',
    Rural_Compacted_Tracks:'tracks',Rural_Ground_PBR:'field','Valley earth and grass':'valley',F_Matte:'coast',
    F_Glass:'glass','Coastal low emissivity glass':'facadeGlass','City window colour':'facadeGlass',F_White:'ceramic',CityConcrete:'concrete','City facades':'nightMasonry',
  }[kind] || (chapter==='town' && kind==='Matte'?'plaster':null);
  if(!surface) return;
  const previous=mat.onBeforeCompile.bind(mat),cache=mat.customProgramCacheKey();
  mat.customProgramCacheKey=()=>cache+'-surface-'+surface;
  const plate={lime:'lime',tile:'tiles',earth:'earth',tracks:'earth',plaster:'lime',concrete:'lime',nightMasonry:'lime',field:'earth',facadeGlass:chapter==='future'?'port-horizon':'avenue-horizon'}[surface];
  if(plate && surface!=='facadeGlass') {plates[plate].wrapS=plates[plate].wrapT=THREE.RepeatWrapping;plates[plate].needsUpdate=true;}
  const coatings={
    lime:`vec3 c=texture2D(pigmentPlate,vec2(projected.x*.16,clamp(wp.y*.215,.015,.985))).rgb;
      diffuseColor.rgb=mix(diffuseColor.rgb,c,.87);`,
    tile:`vec3 c=texture2D(pigmentPlate,wp.xz*vec2(.49,.42)).rgb;
      diffuseColor.rgb=mix(diffuseColor.rgb,c*.96,.86);`,
    earth:`vec3 c=texture2D(pigmentPlate,wp.xz*.155).rgb;
      diffuseColor.rgb=mix(diffuseColor.rgb,c*.86,.83);`,
    tracks:`vec3 c=texture2D(pigmentPlate,wp.xz*.18).rgb;
      diffuseColor.rgb=mix(diffuseColor.rgb,c*.70,.77);`,
    field:`vec3 moss=mix(vec3(.14,.229,.072),vec3(.40,.43,.13),smoothstep(.24,.67,speck.r));
      float brush=dot(texture2D(pigmentPlate,wp.xz*.089).rgb,vec3(.31,.57,.12));
      diffuseColor.rgb=mix(diffuseColor.rgb,moss,.41)*(.72+.24*speck.b+.60*brush);`,
    valley:`{
      float stripe=fract(wp.y*.22+speck.r*.8);
      float forest=smoothstep(.27,.74,speck.r+worldN.y*.16);
      vec3 hills=mix(vec3(.054,.16,.136),vec3(.27,.384,.195),forest);
      hills=mix(hills,vec3(.49,.42,.246),.31*(1.-worldN.y)+.13*smoothstep(.85,.99,stripe));
      diffuseColor.rgb=mix(diffuseColor.rgb,hills,.79);
    }`,
    coast:`if(abs(wp.x)>99. || wp.z< -1782. || wp.z> -1590.) {
      float mask=smoothstep(7.2,19.,wp.y)*smoothstep(.12,.42,worldN.y);
      vec3 land=mix(vec3(.032,.112,.118),vec3(.098,.24,.185),smoothstep(.26,.72,speck.r));
      diffuseColor.rgb=mix(diffuseColor.rgb,land,.68*mask);
    }`,
    glass:`float sky=smoothstep(2.,36.,wp.y);
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.09,.185,.194),.26+.16*sky);`,
    facadeGlass:`vec3 viewToEye=normalize(cameraPosition-wp);
      vec3 facadeN=normalize(cross(dFdx(wp),dFdy(wp)));
      vec3 ray=reflect(-viewToEye,facadeN);
      float u=1.-abs(mod(.51+atan(ray.x,-ray.z)/3.14159265,2.)-1.);
      float v=clamp(.15+asin(clamp(ray.y,-1.,1.))*.92,.025,.94);
      vec3 skyline=texture2D(pigmentPlate,vec2(u,v)).rgb;
      float grazing=pow(1.-abs(dot(viewToEye,facadeN)),2.);
      float warm=smoothstep(.025,.145,diffuseColor.r-diffuseColor.b);
      diffuseColor.rgb=mix(diffuseColor.rgb,skyline*vec3(.66,.78,.81),(.22+.39*grazing)*(1.-warm));`,
    ceramic:`diffuseColor.rgb*=vec3(.76,.88,.94)*(.86+.18*speck.r);`,
    plaster:`float pale=smoothstep(.20,.55,dot(diffuseColor.rgb,vec3(.25,.55,.2)));
      vec3 plaster=texture2D(pigmentPlate,vec2(projected.x*.13,clamp(wp.y*.095,.04,.98))).rgb;
      diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*(.50+.70*plaster),pale*(1.-abs(worldN.y))*.75);`,
    nightMasonry:`float wash=dot(texture2D(pigmentPlate,projected*vec2(.104,.064)).rgb,vec3(.28,.58,.14));
      float seam=abs(fract(wp.y/2.95+.27)-.5);
      diffuseColor.rgb*=(.58+.70*wash+.18*speck.r)*(1.-.11*(1.-smoothstep(.0,.023+fwidth(seam),seam)));`,
    concrete:`diffuseColor.rgb*=vec3(.77,.81,.99)*(.72+.49*texture2D(pigmentPlate,projected*.10).r);`
  };
  mat.onBeforeCompile=(s,renderer)=>{
    previous(s,renderer);
    if(surface==='facadeGlass'){
      s.fragmentShader=s.fragmentShader.replace('#include <emissivemap_fragment>',`#include <emissivemap_fragment>
        #ifdef USE_COLOR
          float occupied=smoothstep(.042,.18,vColor.r-vColor.b);
          totalEmissiveRadiance+=occupied*vec3(.23,.105,.036);
        #endif`);
    }
    s.uniforms.paintGranules={value:grain};
    if(plate) s.uniforms.pigmentPlate={value:plates[plate]};
    s.vertexShader='varying vec3 plateWorld;\n'+s.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nplateWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
    s.fragmentShader='varying vec3 plateWorld; uniform sampler2D paintGranules; '+(plate?'uniform sampler2D pigmentPlate;':'')+'\n'+s.fragmentShader.replace('#include <alphamap_fragment>',`
      {vec3 wp=plateWorld;
       vec3 worldN=abs(normalize(cross(dFdx(wp),dFdy(wp))));
       vec2 projected=worldN.y>.67?wp.xz:(worldN.x>worldN.z?wp.zy:wp.xy);
       vec3 speck=texture2D(paintGranules,wp.xz*.032+wp.y*.006).rgb;
       ${coatings[surface]}
      }
      #include <alphamap_fragment>`);
  };
}

export function finishMasonry(mat, facade) {
  mat.customProgramCacheKey=()=>facade?'town-plaster':'stone-grain';
  mat.onBeforeCompile=shader=>{
    shader.uniforms.surfaceGrain={value:grain};
    shader.vertexShader='varying vec3 surfaceWorld;\n'+shader.vertexShader.replace('#include <worldpos_vertex>',
      '#include <worldpos_vertex>\n surfaceWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
    shader.fragmentShader='uniform sampler2D surfaceGrain; varying vec3 surfaceWorld;\n'+shader.fragmentShader.replace(
      '#include <color_fragment>',`#include <color_fragment>
        vec3 faceN=abs(normalize(cross(dFdx(surfaceWorld),dFdy(surfaceWorld))));
        vec2 sw=faceN.y>.62?surfaceWorld.xz:(faceN.x>faceN.z?surfaceWorld.zy:surfaceWorld.xy);
        vec3 grit=texture2D(surfaceGrain,sw*.51).rgb;
        float stain=texture2D(surfaceGrain,sw*.078).r;
        float stoneTone=(stain-.5)*.34+(grit.r-.5)*.28+(grit.g-.5)*.30;
        diffuseColor.rgb*=1.+stoneTone;
        diffuseColor.rgb*=1.-.16*(1.-smoothstep(.12,1.3,surfaceWorld.y))*(1.-faceN.y);
        ${facade?`if(faceN.y<.35 && surfaceWorld.y>.6 && surfaceWorld.y<22.){
          float pale=smoothstep(.25,.50,dot(diffuseColor.rgb,vec3(.28,.52,.20)));
          vec2 cell=sw/vec2(.48,.25); cell.x+=.5*mod(floor(cell.y),2.);
          vec2 line=abs(fract(cell+.5)-.5);
          vec2 aa=max(fwidth(cell),vec2(.001));
          vec2 joint=1.-smoothstep(vec2(.010),vec2(.010)+aa,line);
          float mortar=max(joint.x,joint.y)*(1.-smoothstep(.14,.58,max(aa.x,aa.y)));
          diffuseColor.rgb*=1.-mortar*.24*pale;
        }`:''}`);
  };
}

// A small, linear radiance panorama for sky fill and specular reflections.
// Its two broad highlights describe the sky and horizon on curved paintwork.
export function studioSky(renderer) {
  const width=256, height=128, data=new Float32Array(width*height*4);
  for(let y=0; y<height; y++) {
    const lat=((y+.5)/height-.5)*Math.PI, h=Math.sin(lat);
    for(let x=0; x<width; x++) {
      const lon=(x/width-.5)*2*Math.PI, dx=Math.cos(lat)*Math.cos(lon), dz=Math.cos(lat)*Math.sin(lon);
      const altitude=Math.max(0,h);
      const horizon=Math.exp(-((h-.10)**2)/.019);
      const key=3.8*Math.max(0,dx*.58+h*.64+dz*.50)**24;
      const rim=1.7*Math.max(0,-dx*.72+h*.64-dz*.27)**15;
      const i=(y*width+x)*4;
      data[i]=.10+altitude*.33+horizon*.74+key+rim*.53;
      data[i+1]=.12+altitude*.47+horizon*.62+key*.86+rim*.69;
      data[i+2]=.13+altitude*.69+horizon*.48+key*.65+rim;
      data[i+3]=1;
    }
  }
  const map=new THREE.DataTexture(data,width,height,THREE.RGBAFormat,THREE.FloatType);
  map.mapping=THREE.EquirectangularReflectionMapping; map.needsUpdate=true;
  const generator=new THREE.PMREMGenerator(renderer);
  const target=generator.fromEquirectangular(map);
  generator.dispose(); map.dispose();
  return target.texture;
}

export function rainOnAvenue(lowQuality,plate) {
  plate.wrapS=plate.wrapT=THREE.MirroredRepeatWrapping;plate.needsUpdate=true;
  const shader={
    name:'Rain on asphalt',
    uniforms:{...Reflector.ReflectorShader.uniforms, time:{value:0},paintedPuddles:{value:plate}},
    vertexShader:`uniform mat4 textureMatrix; varying vec4 mirrorUV; varying vec3 worldP;
      void main(){mirrorUV=textureMatrix*vec4(position,1.0); worldP=(modelMatrix*vec4(position,1.0)).xyz;
      gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader:`uniform sampler2D tDiffuse,paintedPuddles; uniform vec3 color; uniform float time;
      varying vec4 mirrorUV; varying vec3 worldP;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float noise(vec2 p){vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}
      void main(){
        vec2 p=worldP.xz, uv=mirrorUV.xy/mirrorUV.w;
        float pools=smoothstep(.29,.74,noise(p*vec2(.44,.23))*.72+noise(p*1.1)*.28);
        float dist=length(worldP-cameraPosition);
        float rain=(noise(p*vec2(4.,12.)+vec2(0.,time*.38))-.5)*.003/(1.+dist*.008);
        float rippleDetail=1.-smoothstep(.12,.9,max(fwidth(p.x*4.),fwidth(p.y*12.)));
        vec2 offset=vec2(rain,sin(p.y*10.+time*1.4)*.00065)*rippleDetail;
        float blur=mix(.004,.001,pools);
        vec3 ref=texture2D(tDiffuse,uv+offset).rgb*.5+
          (texture2D(tDiffuse,uv+offset+vec2(blur,blur*.6)).rgb+
           texture2D(tDiffuse,uv+offset-vec2(blur,blur*.6)).rgb)*.25;
        float grazing=pow(1.-max(0.,normalize(cameraPosition-worldP).y),3.);
        float curb=smoothstep(5.7,8.9,abs(p.x));
        float wet=(.09+(.33+.21*curb)*pools)*(.36+.64*grazing);
        vec3 paint=texture2D(paintedPuddles,p*vec2(.055,.035)).rgb;
        vec3 asphalt=mix(color,mix(vec3(dot(paint,vec3(.26,.60,.14))),paint,.43)*.66,.24+.14*curb)*(.89+.18*noise(p*vec2(3.,5.)));
        gl_FragColor=vec4(mix(asphalt,ref,wet),1.);
      }`
  };
  const road=new Reflector(new THREE.PlaneGeometry(18,300),{
    color:'#25313b',textureWidth:lowQuality?288:640,textureHeight:lowQuality?160:360,clipBias:.001,multisample:0,shader
  });
  road.name='Wet avenue'; road.rotation.x=-Math.PI/2;
  road.position.set(0,.075,0); road.userData.noNormal=true;
  return road;
}

export function villagePond(lowQuality) {
  const shader={
    name:'Willows reflected in the pond',
    uniforms:{...Reflector.ReflectorShader.uniforms,time:{value:0}},
    vertexShader:'uniform mat4 textureMatrix; varying vec4 projected; varying vec3 world; void main(){projected=textureMatrix*vec4(position,1.);world=(modelMatrix*vec4(position,1.)).xyz;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader:`uniform sampler2D tDiffuse; uniform float time; varying vec4 projected; varying vec3 world;
      void main(){
        vec2 p=world.xz;vec2 uv=projected.xy/projected.w;
        float waves=sin(p.y*3.2+p.x*.31+sin(p.x*.47)+time*.68);
        vec2 d=vec2(.0018*waves,.0038*sin(p.y*1.18+p.x*.24+time*.36));
        vec3 reflection=texture2D(tDiffuse,uv+d).rgb*.5+
           .25*(texture2D(tDiffuse,uv+d+vec2(.0018,.0024)).rgb+texture2D(tDiffuse,uv+d-vec2(.0018,.0024)).rgb);
        float bank=clamp(length((p-vec2(48.,-38.))/vec2(25.,16.)),0.,1.);
        vec3 pigment=mix(vec3(.072,.201,.169),vec3(.239,.362,.230),bank*.72);
        float fresnel=pow(1.-max(0.,normalize(cameraPosition-world).y),2.);
        vec3 water=mix(pigment,reflection,.26+.36*fresnel);
        float fleck=smoothstep(.88,.99,waves)*smoothstep(.44,.79,sin(p.x*.77+sin(p.y*.46)));
        gl_FragColor=vec4(water+vec3(.071,.084,.059)*fleck,1.);
      }`
  };
  const pond=new Reflector(new THREE.CircleGeometry(1,80),{textureWidth:lowQuality?256:512,textureHeight:lowQuality?144:288,clipBias:.0003,multisample:0,shader});
  pond.position.set(48,.079,-38);pond.rotation.x=-Math.PI/2;pond.scale.set(25,16,1);
  pond.name='Willow pond surface';pond.userData.noNormal=true;
  return pond;
}

export function passingRain(lowQuality) {
  const count=lowQuality?520:1350;
  const positions=[], tips=[];
  let seed=2010;
  const rand=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
  for(let i=0;i<count;i++){
    const pos=[(rand()-.5)*82,rand()*43,(rand()-.5)*136];
    positions.push(...pos,...pos); tips.push(0,1);
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('tip',new THREE.Float32BufferAttribute(tips,1));
  const material=new THREE.ShaderMaterial({
    uniforms:{time:{value:0}}, transparent:true,depthWrite:false,
    vertexShader:`attribute float tip; uniform float time; varying float opacity;
      void main(){vec3 p=position; p.y=mod(p.y-time*11.0,43.0)+.38*tip;
        p.x+=p.y*.13; vec4 mv=modelViewMatrix*vec4(p,1.0);
        opacity=(1.-smoothstep(16.,92.,-mv.z))*.17*(.55+.45*tip);
        gl_Position=projectionMatrix*mv;}`,
    fragmentShader:`varying float opacity; void main(){gl_FragColor=vec4(.24,.34,.40,opacity);}`
  });
  const rain=new THREE.LineSegments(geometry,material);
  rain.name='City rainfall'; rain.userData.noNormal=true;
  return rain;
}
