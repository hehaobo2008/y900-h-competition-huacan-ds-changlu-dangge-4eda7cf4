import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import shopLetters from './shop_letters.json';
import futureHeights from './future_ground.json';

const UP=new THREE.Vector3(0,1,0);
const box=new THREE.BoxGeometry(1,1,1).toNonIndexed();
const tube=new THREE.CylinderGeometry(1,1,1,7).toNonIndexed();
const fruit=new THREE.IcosahedronGeometry(1,1);
fruit.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(fruit.attributes.position.count*2),2));
const card=new THREE.PlaneGeometry(1,1);
const v=(x,y,z)=>new THREE.Vector3(x,y,z);
function seeded(seed) {
  return ()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
}

// Several hundred painted trees share four draw calls per island. The foot is
// fixed to the ground, with limited tilt when viewed from the overhead scroll.
function grove(group, lists, plates, chapter, clock) {
  const night=chapter==='city'||chapter==='future';
  const key = {rural:[1.07,1.02,.86],town:[1.10,.79,.63],city:[.28,.40,.64],
    rail:[.79,.98,.83],future:[.22,.57,.67]}[chapter];
  const stamp=()=>new THREE.Object3D();
  const transform=stamp();
  for(const [type,items] of Object.entries(lists)){
    if(!items.length) continue;
    const material=new THREE.ShaderMaterial({
      uniforms:THREE.UniformsUtils.merge([THREE.UniformsLib.fog,{
        inkPlate:{value:null},tint:{value:new THREE.Vector3(...key)},time:{value:0}
      }]),fog:true,side:THREE.DoubleSide,
      vertexShader:`varying vec2 paperUV; varying float variation;
        uniform float time;
        #include <common>
        #include <fog_pars_vertex>
        void main(){
          vec3 anchor=(modelMatrix*instanceMatrix*vec4(0.,0.,0.,1.)).xyz;
          float width=instanceMatrix[0].x, height=instanceMatrix[1].y;
          vec3 eye=normalize(cameraPosition-anchor);
          vec3 right=normalize(vec3(eye.z,0.,-eye.x)+vec3(.00001,0.,0.));
          float tilt=clamp(eye.y,0.,.82)*.72;
          vec3 up=normalize(mix(vec3(0.,1.,0.),cross(eye,right),tilt));
          float seed=dot(anchor.xz,vec2(.373,.179));
          variation=fract(sin(seed)*241.61);
          float bend=(sin(time*1.02+seed)+.4*sin(time*1.67+seed*1.7))*height*.009*uv.y*uv.y;
          vec3 p=anchor+right*(position.x*width+bend)+up*(uv.y*height);
          paperUV=vec2(variation>.5?1.-uv.x:uv.x,uv.y);
          vec4 mvPosition=viewMatrix*vec4(p,1.);
          gl_Position=projectionMatrix*mvPosition;
          #include <fog_vertex>
        }`,
      fragmentShader:`uniform sampler2D inkPlate; uniform vec3 tint; varying vec2 paperUV; varying float variation;
        #include <common>
        #include <fog_pars_fragment>
        void main(){vec4 leaf=texture2D(inkPlate,paperUV);
          if(leaf.a<.39) discard;
          vec3 col=leaf.rgb*tint*(.88+.22*variation);
          col=mix(col,col*vec3(.81,.90,1.02),.55*(1.-paperUV.y));
          ${night?'col+=vec3(.008,.013,.03);':''}
          gl_FragColor=vec4(col,1.);
          #include <fog_fragment>
        }`
    });
    material.uniforms.inkPlate.value=plates[type];material.uniforms.time=clock;
    const mesh=new THREE.InstancedMesh(card,material,items.length);
    mesh.name='Painted '+type; mesh.userData.noNormal=true;
    mesh.frustumCulled=false;
    items.forEach(([x,y,z,w,h],i)=>{
      transform.position.set(x,y,z);transform.scale.set(w,h,1);transform.updateMatrix();
      mesh.setMatrixAt(i,transform.matrix);
    });
    group.add(mesh);
  }
}

function futureGround(x,z) {
  const u=THREE.MathUtils.clamp((x+160)/4,0,79.999),w=THREE.MathUtils.clamp((z+148)/4,0,73.999);
  const i=Math.floor(u),j=Math.floor(w),mix=THREE.MathUtils.lerp;
  return mix(mix(futureHeights[j][i],futureHeights[j][i+1],u-i),
    mix(futureHeights[j+1][i],futureHeights[j+1][i+1],u-i),w-j);
}

function workshop(group) {
  const solids=[],facets=[],colours=[];
  const add=(geometry,position,scale,colour,q=new THREE.Quaternion())=>{
    const geo=geometry.clone().applyMatrix4(new THREE.Matrix4().compose(position,q,scale));
    const rgb=new THREE.Color(colour),n=geo.attributes.position.count,colourData=new Float32Array(n*3);
    for(let i=0;i<n;i++) rgb.toArray(colourData,3*i);
    geo.setAttribute('color',new THREE.BufferAttribute(colourData,3));solids.push(geo);
  };
  const block=(x,y,z,w,h,d,c)=>add(box,v(x,y,z),v(w,h,d),c);
  const rod=(a,b,r,c)=>{
    const p=v(...a),q=v(...b),axis=q.clone().sub(p);
    add(tube,p.add(q).multiplyScalar(.5),v(r,axis.length(),r),c,new THREE.Quaternion().setFromUnitVectors(UP,axis.normalize()));
  };
  const triangle=(a,b,c,colour)=>{
    facets.push(...a,...b,...c);const k=new THREE.Color(colour);for(let i=0;i<3;i++) colours.push(k.r,k.g,k.b);
  };
  const quad=(a,b,c,d,colour)=>{triangle(a,b,c,colour);triangle(a,c,d,colour);};
  const storefront=(x,z,base,facing,w,h,plate,tint)=>{
    const m=new THREE.MeshBasicMaterial({map:plate,color:tint,side:THREE.FrontSide});
    const face=new THREE.Mesh(card,m);
    face.name='Painted interior / '+plate.name;
    face.rotation.y=facing*Math.PI/2;
    face.position.set(x,base+h/2,z);face.scale.set(w,h,1);
    group.add(face);
    block(x-facing*.19,base+h/2,z,.35,h+.12,w+.16,'#454844');
    block(x+facing*.09,base+.05,z,.42,.14,w+.38,'#a99a7e');
    for(const edge of [-1,1]) block(x+facing*.05,base+h/2,z+edge*(w/2+.06),.20,h+.22,.15,'#764e3c');
  };
  const sign=(words,background,letters,x,y,z,w,h,angle)=>{
    const board=new THREE.Group();
    board.name=words;board.position.set(x,y,z);board.rotation.y=angle;group.add(board);
    const face=new THREE.MeshStandardMaterial({color:background,roughness:.67,metalness:.10});
    const edge=new THREE.MeshStandardMaterial({color:'#a48b65',roughness:.58,metalness:.28});
    const night=words==='灯下面馆';
    const enamel=new THREE.MeshStandardMaterial({color:letters,roughness:.54,emissive:letters,emissiveIntensity:night?.72:.14});
    const piece=(geo,mat,xx,yy,zz)=>{
      const m=new THREE.Mesh(geo,mat);m.position.set(xx,yy,zz);m.castShadow=m.receiveShadow=true;board.add(m);return m;
    };
    const depth=Math.min(.16,h*.19);
    piece(new THREE.BoxGeometry(w,h,depth),edge,0,0,-depth/2);
    piece(new THREE.BoxGeometry(w-.055,h-.055,.033),face,0,0,.004);
    for(const xx of [-1,1]){
      const px=xx*(w/2-.13);
      for(const yy of [-1,1]) piece(new THREE.SphereGeometry(.028,7,4),edge,px,yy*h*.32,.025);
      piece(new THREE.BoxGeometry(.074,h*.38,depth*1.8),edge,px,h*.34,-depth*1.18);
    }
    const geometry=[];
    for(const glyph of shopLetters[words]){
      const path=new THREE.ShapePath();
      for(const [cmd,...p] of glyph){
        if(cmd==='M') path.moveTo(...p);
        else if(cmd==='L') path.lineTo(...p);
        else if(cmd==='Q') path.quadraticCurveTo(...p);
        else if(cmd==='C') path.bezierCurveTo(...p);
        else path.currentPath.closePath();
      }
      geometry.push(...path.toShapes());
    }
    const relief=new THREE.ExtrudeGeometry(geometry,{depth:.046,bevelThickness:.005,bevelSize:.005,bevelSegments:1,curveSegments:4});
    relief.computeBoundingBox();const bounds=relief.boundingBox;
    const size=Math.min((w-.60)/(bounds.max.x-bounds.min.x),h*.68/(bounds.max.y-bounds.min.y));
    relief.translate(-(bounds.min.x+bounds.max.x)/2,-(bounds.min.y+bounds.max.y)/2,0);
    relief.scale(size,size,Math.min(1.7,size));
    piece(relief,enamel,0,0,.029);

  };
  const canopy=(x,z,y,face,w,d,palette)=>{
    const segments=10;
    for(let i=0;i<segments;i++){
      const a=z-w/2+w*i/segments,b=z-w/2+w*(i+1)/segments;
      const outer=x+face*d,c=palette[i%palette.length];
      quad([x,y,a],[x,y,b],[outer,y-.42,b],[outer,y-.42,a],c);
      quad([outer,y-.42,a],[outer,y-.42,b],[outer,y-.66,b],[outer,y-.66,a],c);
    }
    for(const e of [-1,1]) rod([x+face*d,.10,z+e*(w/2-.18)],[x+face*d,y-.43,z+e*(w/2-.18)],.052,'#59635b');
  };
  const finish=()=>{
    if(solids.length){
      const merged=mergeGeometries(solids);solids.forEach(g=>g.dispose());
      const m=new THREE.Mesh(merged,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.9}));
      m.name='Street carpentry';m.castShadow=m.receiveShadow=true;group.add(m);
    }
    if(facets.length){
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(facets,3));
      g.setAttribute('color',new THREE.Float32BufferAttribute(colours,3));g.computeVertexNormals();
      const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,roughness:1}));
      m.name='Cloth and field brushwork';m.castShadow=m.receiveShadow=true;group.add(m);
    }
  };
  const round=(x,y,z,w,h,d,colour)=>add(fruit,v(x,y,z),v(w,h,d),colour);
  return {block,rod,triangle,quad,storefront,canopy,round,sign,finish};
}

function treeShadows(group,groves,floor,texture) {
  const trees=['camphor','willow','pine','copse','conifers'].flatMap(type=>groves[type]);
  if(!trees.length) return;
  const material=new THREE.MeshBasicMaterial({map:texture,color:'#233c45',transparent:true,opacity:.40,
    depthWrite:false,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-1});
  const shade=new THREE.InstancedMesh(card,material,trees.length);
  const matrix=new THREE.Matrix4(),pos=new THREE.Vector3();
  trees.forEach(([x,y,z,w,h],i)=>{
    const sx=x-h*.14,sz=z+h*.09,rx=w*.82,rz=w*.58;
    const a=v(rx,(floor(sx+rx/2,sz)-floor(sx-rx/2,sz)),0);
    const b=v(0,(floor(sx,sz+rz/2)-floor(sx,sz-rz/2)),rz);
    matrix.makeBasis(a,b,UP);matrix.setPosition(pos.set(sx,floor(sx,sz)+.11,sz));shade.setMatrixAt(i,matrix);
  });
  shade.name='Shadow underneath tree crowns';shade.userData.noNormal=true;shade.frustumCulled=false;group.add(shade);
}

function nurserySign(draw) {
  const x=127,z=-48;
  draw.sign('育苗温室','#276164','#f2dfad',x,futureGround(x,z)+3.55,z+6.62,3.1,.49,0);
}

export function stageLandscapes(zones,plates,shadowTexture,ruralGround,ruralWalkable) {
  const time={value:0}, birds=[],people=[];
  for(const [index,id] of ['rural','town','city','rail','future'].entries()){
    const group=zones[id].group, draw=workshop(group), random=seeded(5541+index*913);
    const flora={camphor:[],willow:[],pine:[],reeds:[],copse:[],foreshore:[],conifers:[],rice:[]};
    const floor=id==='rural'?(x,z)=>ruralGround(x,-z):id==='future'?futureGround:()=>.14;
    const plant=(type,x,z,h,wide=1)=>flora[type].push([x,floor(x,z)-.05,z,h*wide,h]);
    const person=(name,x,z,h,tint,pace=0)=>{
      const texture=plates[name],g=new THREE.Group();
      const art=new THREE.Mesh(card,new THREE.MeshBasicMaterial({map:texture,color:tint,alphaTest:.38,side:THREE.DoubleSide}));
      art.scale.set(h*texture.image.width/texture.image.height,h,1);art.position.y=h/2;
      art.userData.noNormal=true;g.name='Figure / '+name;g.position.set(x,floor(x,z)+.065,z);
      g.add(art);group.add(g);
      const shadow=new THREE.Mesh(card,new THREE.MeshBasicMaterial({map:shadowTexture,color:'#283837',transparent:true,opacity:.55,depthWrite:false}));
      shadow.rotation.x=-Math.PI/2;shadow.scale.set(.87,.55,1);shadow.position.y=.02;g.add(shadow);
      people.push({group:g,base:z,pace,offset:group.position.z});
    };
    if(id==='rural'){
      for(const [type,x,z,h,w] of [
        ['camphor',-13,61,12.8,1.03],['willow',13,51,10.5,.85],['camphor',-12,33,9.3,1.1],
        ['camphor',20,22,10.4,.98],['willow',21.8,-35.3,8.4,.84],['willow',56,-54,9,.9],['pine',-24,43,7.2,1.03],
        ['reeds',-4.6,56,1.63,1.14],['reeds',9.3,49.6,1.92,1.20],['reeds',-7.2,37,2.31,1.2],
      ]) plant(type,x,z,h,w);
      for(const [x,z] of [[26,-30],[31,-24],[37,-21],[57,-23],[67,-31],[70,-41],[60,-48]]){
        plant('reeds',x,z,.85+random()*.60,1.18);
        draw.round(x+.52,floor(x+.52,z)+.043,z,.43,.13,.29,'#a39676');
      }
      for(let i=0;i<170;i++){
        const x=19+random()*45,z=-7-random()*43;
        const radius=Math.hypot((x-48)/25,(z+38)/16);
        if(radius<1.06 || Math.abs(x-48-1.6*Math.sin((-z-17)*.14))<4.1 || Math.abs(z+17)<1.7) continue;
        if(i%4===0) plant('rice',x,z,.48+random()*.44,2.7);
        else plant('reeds',x,z,.38+random()*.56,1.8);
      }
      const banks=[[-45,30],[-62,-24],[64,-54],[74,-39],[75,20],[-72,79],[-100,-98],[90,-114]];
      for(const [cx,cz] of banks) for(let i=0;i<22;i++){
        const x=cx+(random()-.5)*30,z=cz+(random()-.5)*26;
        if(!ruralWalkable(x,z)) continue;
        plant(i%5===0?'willow':i%3?'reeds':'camphor',x,z,i%3===0?6+random()*6:1.1+random()*2,1.05);
      }
      const distant=seeded(1984);
      for(let i=0;i<68;i++){
        const along=-140+i*4.15;
        if(Math.sin(along*.073)+Math.cos(along*.16)>.18){
          plant(i%3?'conifers':'copse',along,-96-distant()*7,3.4+distant()*4.6,2.19);
          plant(i%3?'copse':'pine',112+distant()*9,along,3.1+distant()*5.4,1.9);
        }
      }
      for(let j=0;j<920;j++){
        const z=random()*199-99,side=j%2?1:-1;
        const road=3*Math.sin((-z+145)/52)+1.2*Math.sin((-z+20)/19);
        const x=road+side*(4.8+random()*(j%3===0?25:4.7));
        if(!ruralWalkable(x,z))continue;
        const y=floor(x,z)+.04,h=.14+random()*.49,w=.05+random()*.13;
        draw.triangle([x-w,y,z],[x+w,y,z],[x+w*2.6,y+h,z-.06],
          ['#b69a4b','#748c55','#aabb67','#d4bd68'][j%4]);
      }
      draw.storefront(-5.21,49,.28,1,7.05,2.98,plates.granary,'#fff2d7');
      draw.sign('供销合作社','#573e30','#ead09a',-3.17,3.02,49,5.83,.75,Math.PI/2);
      const cottage=new THREE.Mesh(card,new THREE.MeshBasicMaterial({map:plates.cottage,color:'#fff2da'}));
      cottage.name='Granary courtyard wall';cottage.scale.set(4.82,2.84,1);cottage.position.set(-7.81,1.72,53.065);group.add(cottage);
      person('harvester',-2.42,50.3,1.67,'#faf0da');
      for(let i=0;i<140;i++){
        const z=-100+random()*214,road=3*Math.sin((-z+145)/52)+1.2*Math.sin((-z+20)/19);
        const x=road+(i%2?1:-1)*(5.0+random()*3.9);
        if(ruralWalkable(x,z) && !(x<0 && z>41 && z<55)) plant('rice',x,z,.48+random()*.63,2.47);
      }
      for(const [x,z,h] of [[-26,56,5],[-32,36,7],[-35,6,7],[18,35,5],[34,19,5],[-70,75,9],[-95,48,9]])
        plant('copse',x,z,h,2.54);
      for(const z of [35,42.4]) draw.rod([-8.4,.05,z],[-8.35,3.04,z],.06,'#a28954');
      draw.rod([-8.35,2.90,35],[-8.35,2.73,38.7],.022,'#4e4a43');
      draw.rod([-8.35,2.73,38.7],[-8.35,2.90,42.4],.022,'#4e4a43');
      for(let i=0;i<4;i++) {
        const z=35.6+i*1.55,h=2.82-Math.sin(i*Math.PI/3)*.09;
        draw.quad([-8.34,h,z],[-8.34,h,z+1.13],[-8.16,h-1.32,z+1.08],[-8.28,h-1.29,z+.04],
          ['#477c86','#f0dca7','#a5523f','#52888a'][i]);
      }
    } else if(id==='town'){
      draw.storefront(-5.30,-35,.20,1,6.1,3.25,plates.market,'#fff2cf');
      draw.storefront(-5.46,-35,3.75,1,6.1,3.45,plates.balcony,'#ffeac6');
      draw.sign('东街副食','#344b54','#f4dda7',-4.98,4.14,-35,6.17,.87,Math.PI/2);
      draw.canopy(-5.30,-35,3.75,1,6.4,1.35,['#b64e39','#edd5aa']);
      for(let i=0;i<4;i++){
        const zz=-37.12+i*1.32,xx=-4.78;
        draw.block(xx,.49,zz,.78,.61,1.18,'#8f6849');
        for(const a of [-1,1]){
          draw.block(xx+a*.37,.88,zz,.067,.22,1.20,'#c69b69');
          draw.block(xx,.89,zz+a*.56,.76,.23,.06,'#b98659');
        }
        for(let j=0;j<19;j++){
          const dx=(random()-.5)*.63,dz=(random()-.5)*.97;
          draw.round(xx+dx,.98+random()*.15,zz+dz,.123,.117,.13,['#eaaa42','#b84c31','#afc66e','#e2a24b'][i]);
        }
        for(const y of [.34,.52,.71]) draw.block(xx+.405,y,zz,.045,.11,1.16,'#be8b52');
      }
      person('family',-3.33,-34.5,1.74,'#ffdec0');
    } else if(id==='city'){
      // The elevated line enters a covered cutting beyond the inhabited blocks.
      for(const side of [-1,1]){
        const x=side*145;
        for(const z of [-8.25,-1.75]) draw.block(x,16.0,z,28,6.7,.47,'#535c67');
        draw.block(x,19.68,-5,28.5,.7,7.55,'#676977');
        for(const d of [132,141,151]) {
          for(const z of [-8.0,-2.0]) draw.block(side*d,16.3,z,.53,6.15,.48,'#737987');
          draw.block(side*d,19.13,-5,.52,.48,6.6,'#83838a');
        }
      }
      draw.storefront(10.47,18,.24,-1,7.6,3.15,plates.noodles,'#ffce9b');
      draw.canopy(10.47,18,3.78,-1,7.9,1.20,['#24747a','#477778']);
      draw.sign('灯下面馆','#345557','#ffdb98',9.18,3.50,18,4.85,.73,-Math.PI/2);
      person('umbrella',9.48,23.9,1.96,'#f6c1ae',1.45);
      // The upper storeys are part of the rounded apartment block in the city model.
      // An interior painting backs the recessed shop, inside its street arcade.
      for(const side of [-1,1]){
        draw.rod([10.80,3.52,18+side*3.65],[9.30,3.20,18+side*3.65],.047,'#6b7569');
        draw.rod([10.80,2.67,18+side*3.65],[9.30,3.20,18+side*3.65],.044,'#697768');
      }
      // Reflective protection at the traffic island around the railway pier.
      draw.block(0,.20,-4.95,2.94,.25,6.1,'#777c76');
      for(const zz of [-8.01,-1.9]){
        draw.round(0,.18,zz,1.46,.17,.72,'#929080');
        for(const xx of [-.85,.85]){
          draw.block(xx,.56,zz,.13,.78,.13,'#736d59');
          draw.block(xx,.75,zz,.14,.16,.14,'#cfad6d');
        }
      }
      for(const z of [34,30,-8,-38,61]){
        const x=z===30?-9.6:10.8;
        draw.block(x,2.4,z,.08,4.5,.08,'#644953');
        for(let i=0;i<8;i++){
          const a=i*Math.PI/4,b=(i+1)*Math.PI/4,r=1.48;
          draw.triangle([x,3.20,z],[x+Math.cos(a)*r,2.65,z+Math.sin(a)*r],[x+Math.cos(b)*r,2.65,z+Math.sin(b)*r],
            (z%3===0?['#d06b41','#a43d47']:['#267b84','#4d8b90'])[i%2]);
        }
      }
    } else if(id==='future'){
      nurserySign(draw);
      person('scientist',134.8,-43.8,1.68,'#d7e4d5');
    }
    if(id==='rural'){
      // Each V is two tapered wings, readable even when the camera is at river level.
      const geometry=new THREE.BufferGeometry(),points=[];
      for(let i=0;i<9;i++){
        const x=i*1.38,z=-i*.82+Math.sin(i)*1.9,y=.45*Math.sin(i*1.5);
        points.push(x-.85,y+.19,z+.24,x-.35,y+.07,z-.04,x,y,z+.11,
          x,y,z+.11,x+.45,y+.20,z-.10,x+.92,y+.25,z+.02);
      }
      geometry.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
      const flock=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color:'#42596a',side:THREE.DoubleSide}));
      flock.name='Swallows over '+id;flock.userData.noNormal=true;
      flock.position.set(0,14,16);
      group.add(flock);birds.push({flock,x:flock.position.x,y:flock.position.y});
    }
    draw.finish();
    if(id==='rural'){treeShadows(group,flora,floor,shadowTexture);grove(group,flora,plates,id,time);}
  }
  return (seconds,camera)=>{
    time.value=seconds;
    for(const {group,base,pace,offset} of people){
      group.position.z=base+Math.sin(seconds*.17)*pace;
      group.rotation.y=Math.atan2(camera.position.x-group.position.x,camera.position.z-offset-group.position.z);
    }
    for(const {flock,x,y} of birds){
      flock.position.x=x+Math.sin(seconds*.09)*9;flock.position.y=y+Math.sin(seconds*.32)*.68;
      flock.rotation.z=Math.sin(seconds*.49)*.09;
    }
  };
}
