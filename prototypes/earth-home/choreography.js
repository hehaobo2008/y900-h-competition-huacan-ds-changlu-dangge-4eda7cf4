// The visible flight is in metres. The orbital world is in kilometres.
// Change worlds only while looking straight up, after the rocket has vanished.
export const DURATION=26,SWITCH_TIME=9.4,RADIUS=6371;
export const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
export const smooth=(a,b,t)=>{const u=clamp((t-a)/(b-a));return u*u*u*(10+u*(-15+6*u));};
const radians=Math.PI/180;
export function flightPose(t){
 const s=Math.max(0,t-1.2),c=Math.max(0,t-2);
 const rocket=7+.9*s*s+s**4+1.3*Math.max(0,s-2)**5;
 const camera=19+.50*c*c+.30*c*c*c;
 const range=100+40*smooth(2,7,t);
 return {rocket,camera,range,pitch:Math.atan2(rocket+30-camera,range),fade:1-smooth(8.6,9.2,t)};
}
const firstPitch=flightPose(SWITCH_TIME).pitch/radians;
const pitchKeys=[[9.6,firstPitch],[12,30],[14,-36],[15,-51],[16.5,-65],[18,-80],[20,-93],[21.8,-96],[26,-96]];
// Shape-preserving Hermite interpolation, with zero velocity at both ends.
function curve(keys,t){
 if(t<=keys[0][0])return keys[0][1];
 if(t>=keys.at(-1)[0])return keys.at(-1)[1];
 const slopes=keys.slice(1).map((p,i)=>(p[1]-keys[i][1])/(p[0]-keys[i][0]));
 const derivative=i=>i===0||i===keys.length-1?0:slopes[i-1]*slopes[i]<=0?0:2/(1/slopes[i-1]+1/slopes[i]);
 const i=keys.findIndex((p,j)=>j<keys.length-1&&t>=p[0]&&t<=keys[j+1][0]);
 const [x,y]=keys[i],[xx,yy]=keys[i+1],d=xx-x,u=(t-x)/d;
 return (2*u**3-3*u*u+1)*y+(u**3-2*u*u+u)*d*derivative(i)+(-2*u**3+3*u*u)*yy+(u**3-u*u)*d*derivative(i+1);
}
const altitudeKeys=[[9.4,Math.log(60)],[13.2,Math.log(450)],[14.6,Math.log(600)],[16,Math.log(1800)],[18,Math.log(7500)],[20,Math.log(21000)],[21.8,Math.log(26000)],[26,Math.log(26000)]];
export function orbitalPose(t,aspect,height){
 const tall=aspect<.8,compact=tall&&height<650;
 const fitting=1+(compact?.38:tall?.20:0)*smooth(17,21.8,t);
 return {altitude:Math.exp(curve(altitudeKeys,t))*fitting,pitch:(curve(pitchKeys,t)-(compact?2:0)*smooth(18,21.8,t))*radians,fov:52-4*smooth(15,21.5,t),arc:.042*smooth(9.6,21.8,t)};
}
