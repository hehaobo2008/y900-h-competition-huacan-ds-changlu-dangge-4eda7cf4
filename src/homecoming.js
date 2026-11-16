import * as THREE from 'three';

export const HOMECOMING_PULLBACK=10.15;
export const HOMECOMING_END=21;
const LIGHT_START=12.8;
const LIGHT_INTERVAL=.95;
const locations=[
  [-12,10,23],
  [11,11,-480],
  [-6,24,-848],
  [-3,38,-1260],
  [102,15,-1760],
];
const names=['灶火','东街霓虹','万家灯火','桥灯','火箭尾焰'];

export function fillHomeTickets(container,pages,visible=false){
  container.replaceChildren();
  return pages.map((page,i)=>{
    const ticket=document.createElement('div');
    ticket.className='home-ticket';
    ticket.dataset.page=String(i);
    ticket.classList.toggle('lit',visible);
    const date=document.createElement('small');
    date.textContent=page.year;
    const words=document.createElement('span');
    words.textContent=page.words;
    if(!page.words){
      words.className='empty-ticket';
      words.setAttribute('aria-label','留白');
    }
    ticket.append(date,words);container.append(ticket);
    return ticket;
  });
}

export function createHomecoming(scene,glowTexture,pages){
  const root=new THREE.Group();
  root.name='Five lights on the way home';
  root.visible=false;root.userData.noNormal=true;scene.add(root);
  const lamps=locations.map(xyz=>{
    const material=new THREE.SpriteMaterial({map:glowTexture,color:'#ffbd70',
      transparent:true,depthWrite:false,depthTest:false,fog:false,toneMapped:false,opacity:0,blending:THREE.AdditiveBlending});
    const sprite=new THREE.Sprite(material);
    sprite.position.set(...xyz);sprite.scale.setScalar(80);sprite.renderOrder=6;root.add(sprite);
    const centre=new THREE.Mesh(new THREE.SphereGeometry(3.1,10,6),
      new THREE.MeshBasicMaterial({color:'#ffcd83',transparent:true,fog:false,toneMapped:false,opacity:0,depthTest:false,depthWrite:false}));
    centre.position.copy(sprite.position);centre.renderOrder=7;root.add(centre);
    return {sprite,centre};
  });
  const threads=locations.slice(1).map((xyz,i)=>{
    const a=new THREE.Vector3(...locations[i]),b=new THREE.Vector3(...xyz);
    const control=a.clone().lerp(b,.5).add(new THREE.Vector3(i%2?-43:43,35,0));
    const curve=new THREE.QuadraticBezierCurve3(a,control,b);
    const geometry=new THREE.TubeGeometry(curve,96,1.6,6,false);
    geometry.setDrawRange(0,0);
    const thread=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({
      color:'#d36b4e',transparent:true,fog:false,toneMapped:false,opacity:.90,depthTest:false,depthWrite:false
    }));
    thread.renderOrder=4;root.add(thread);
    return thread;
  });
  const overlay=document.querySelector('#homecoming');
  const caption=document.querySelector('#homecomingWords');
  const verse=document.querySelector('#homecomingVerse');
  const tickets=fillHomeTickets(document.querySelector('#flightTickets'),pages);
  let previous=-1;
  return {
    framingRect(){
      // Measure the real ticket rows before framing; opacity avoids a visible flash.
      const hidden=overlay.hidden,opacity=overlay.style.opacity;
      overlay.style.opacity='0';overlay.hidden=false;
      const rect=document.querySelector('#flightTickets').getBoundingClientRect();
      overlay.hidden=hidden;overlay.style.opacity=opacity;
      return {top:rect.top,bottom:rect.bottom};
    },
    update(t){
      const elapsed=t-LIGHT_START;
      root.visible=elapsed>=-.3;
      overlay.hidden=elapsed<-.1;
      overlay.style.opacity=String(THREE.MathUtils.smoothstep(elapsed,-.1,.6));
      const current=Math.min(4,Math.floor(Math.max(0,elapsed)/LIGHT_INTERVAL));
      for(let i=0;i<lamps.length;i++){
        const age=elapsed-i*LIGHT_INTERVAL;
        const light=THREE.MathUtils.smoothstep(age,0,.55);
        const pulse=1+.16*Math.sin(Math.max(0,age)*2.8)*Math.exp(-Math.max(0,age)*.36);
        const {sprite,centre}=lamps[i];
        sprite.material.opacity=.76*light;sprite.scale.setScalar(80*pulse);
        centre.material.opacity=light;
        tickets[i].classList.toggle('lit',light>.04);
        tickets[i].classList.toggle('current',i===current && elapsed<5.2);
      }
      for(let i=0;i<threads.length;i++){
        const fraction=THREE.MathUtils.smoothstep((elapsed-i*LIGHT_INTERVAL)/LIGHT_INTERVAL,0,1);
        const triangles=threads[i].geometry.index.count/3;
        threads[i].geometry.setDrawRange(0,Math.floor(triangles*fraction)*3);
      }
      if(current!==previous){
        caption.textContent=names[current]+' · '+(pages[current].words || '这张票背，还留着空白。');
        previous=current;
      }
      caption.style.opacity=String(1-THREE.MathUtils.smoothstep(elapsed,4.8,5.6));
      verse.style.opacity=String(THREE.MathUtils.smoothstep(elapsed,4.8,5.6));
    },
    dispose(){
      scene.remove(root);
      root.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
      overlay.hidden=true;overlay.style.opacity='0';
      document.querySelector('#flightTickets').replaceChildren();
    }
  };
}

