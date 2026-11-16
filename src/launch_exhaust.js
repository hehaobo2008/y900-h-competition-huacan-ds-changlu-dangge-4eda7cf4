import * as THREE from 'three';

// Native model coordinates use three twin-nozzle boosters around a five-bell core.
function nozzles(){
  const bells=[[0,0,.88,1]];
  for(let i=0;i<4;i++){
    const a=Math.PI*(.25+i*.5);
    bells.push([1.48*Math.cos(a),-1.48*Math.sin(a),.84,1]);
  }
  for(let i=0;i<3;i++){
    const a=Math.PI/2+i*Math.PI*2/3;
    for(const side of [-1,1]){
      bells.push([4.25*Math.cos(a)-side*.72*Math.sin(a),
        -4.25*Math.sin(a)-side*.72*Math.cos(a),.66,.82]);
    }
  }
  return bells;
}

export function launchExhaust(rocket,scene,smokeTexture){
  const positions=[],sections=[],indices=[];
  // Two nested volumes: a short white core and a longer, translucent mixing layer.
  for(const [x,z,r,strength] of nozzles()) for(let layer=0;layer<2;layer++){
    const start=positions.length/3, sides=12, rows=12;
    for(let i=0;i<=rows;i++)for(let j=0;j<=sides;j++){
      const t=i/rows, a=2*Math.PI*j/sides;
      const radius=layer ? r*(1.+.96*Math.sin(t*Math.PI*.8)) : r*(.79-.57*t);
      positions.push(x+Math.cos(a)*radius,-t*(layer?22:8.5)*strength,z+Math.sin(a)*radius);
      sections.push(t,a,x+z*1.71,layer);
      if(i<rows && j<sides){
        const k=start+i*(sides+1)+j;
        indices.push(k,k+1,k+sides+1,k+1,k+sides+2,k+sides+1);
      }
    }
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('section',new THREE.Float32BufferAttribute(sections,4));geometry.setIndex(indices);
  const material=new THREE.ShaderMaterial({
    uniforms:{time:{value:0},power:{value:0}},transparent:true,depthWrite:false,
    side:THREE.DoubleSide,forceSinglePass:true,blending:THREE.AdditiveBlending,
    vertexShader:`attribute vec4 section;varying vec4 plume; uniform float time,power;
      void main(){plume=section;vec3 p=position;
        float flow=sin(section.y*3.+section.x*13.-time*14.+section.z);
        p.xz+=vec2(sin(section.y),cos(section.y))*.26*section.x*section.w*flow;
        p.y*=.30+.70*power;
        gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.);}`,
    fragmentShader:`varying vec4 plume;uniform float time,power;
      void main(){float t=clamp(plume.x,0.,1.);float outer=clamp(plume.w,0.,1.);
        float diamond=.5+.5*cos(t*28.-time*3.+.6*sin(3.*plume.y+plume.z));
        float stream=.5+.5*sin(t*19.+2.*sin(plume.y*3.+plume.z)-time*9.);
        vec3 hot=mix(vec3(1.7,1.45,.98),vec3(1.15,.53,.18),smoothstep(.1,.86,t));
        vec3 gas=mix(vec3(.90,.72,.54),vec3(.76,.32,.12),t);
        float alpha=mix(.75*(.72+.28*diamond),.23*(.45+.55*stream),outer);
        gl_FragColor=vec4(mix(hot,gas,outer),alpha*pow(max(0.,1.-t),1.35)*power);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`
  });
  const jets=new THREE.Mesh(geometry,material);
  jets.name='Engine exhaust';jets.userData.noNormal=true;rocket.add(jets);
  const vapour=[];
  for(let i=0;i<30;i++){
    const m=new THREE.SpriteMaterial({map:smokeTexture,color:i%4?'#d0cbbf':'#afa99d',transparent:true,
      opacity:0,depthWrite:false,rotation:i*2.39996});
    const s=new THREE.Sprite(m);s.userData.noNormal=true;s.visible=false;
    scene.add(s);vapour.push(s);
  }
  const origin=rocket.position.clone();
  return {
    update(t){
      material.uniforms.time.value=t;
      material.uniforms.power.value=THREE.MathUtils.smoothstep(t,0,.38)*(1-THREE.MathUtils.smoothstep(t,7.15,8.65));
      for(let i=0;i<vapour.length;i++){
        const s=vapour[i], age=t-(i%10)*.17, life=4.35+(i%4)*.53;
        s.visible=age>0 && age<life;
        if(!s.visible)continue;
        const a=i*2.39996, spread=2.4+(1-Math.exp(-age*.58))*(12+i%5*2.15);
        s.position.set(origin.x+Math.cos(a)*spread,origin.y-2.25+age*1.23+age*age*.27,
          origin.z+Math.sin(a)*spread);
        const radius=3.1+(i%4)*.64+age*2.3;
        s.scale.set(radius*1.24,radius,1);s.material.rotation=a+.11*age*Math.sin(a);
        s.material.opacity=.36*THREE.MathUtils.smoothstep(age,0,.48)*(1-THREE.MathUtils.smoothstep(age/life,.34,1));
      }
    },
    dispose(){rocket.remove(jets);geometry.dispose();material.dispose();
      for(const s of vapour){scene.remove(s);s.material.dispose();}}
  };
}

