import * as THREE from 'three';

// The track is an ellipse. Arc-length sampling keeps the train's speed and
// coach spacing constant through the tight and broad curves.
const samples=2048,arc=new Float64Array(samples+1);
let prev=new THREE.Vector3(52,0,-12);
for(let i=1;i<=samples;i++){
  const theta=i/samples*Math.PI*2,p=new THREE.Vector3(-18+70*Math.cos(theta),0,-12-48*Math.sin(theta));
  arc[i]=arc[i-1]+p.distanceTo(prev);prev=p;
}
const length=arc[samples],pitch=9.45;
function thetaAt(distance){
  const d=((distance%length)+length)%length;let lo=0,hi=samples;
  while(hi-lo>1){const m=(lo+hi)>>1;if(arc[m]<=d)lo=m;else hi=m;}
  return (lo+(d-arc[lo])/(arc[hi]-arc[lo]))/samples*Math.PI*2;
}
export function futureMetro(root){
  const names=['MetroCabFront','MetroCoach01','MetroCoach02','MetroCoach03','MetroCabRear'];
  const cars=names.map(name=>root.getObjectByName(name));
  if(cars.some(x=>!x))throw new Error('Future metro coaches are incomplete');
  root.name='Starport articulated metro';
  let elapsed=0,active=false;
  const origin=length*.81;
  function place(t){
    const distance=origin+t*7.4;
    cars.forEach((car,i)=>{
      const theta=thetaAt(distance-i*pitch);
      car.position.set(-18+70*Math.cos(theta),13.82,-12-48*Math.sin(theta));
      car.rotation.set(0,Math.atan2(48*Math.cos(theta),-70*Math.sin(theta))+(i===4?Math.PI:0),0);
    });
  }
  place(0);
  return {
    root,cars,
    reset(){elapsed=0;active=false;place(0);},
    update(dt,mode,p,reduced){
      const running=['travel','approach','finale'].includes(mode)&&p>=.847;
      if(running&&!reduced){if(!active){elapsed=p>=.930?2:0;active=true;}elapsed+=dt;}
      else if(p<.847&&mode!=='overview'){elapsed=0;active=false;}
      place(elapsed);
    }
  };
}
