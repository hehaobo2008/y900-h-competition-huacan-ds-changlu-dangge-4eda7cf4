// One camera spline in world metres, including the air between neighbouring islands.
export const route = [
    [0,[4.6,2.38,61.6],[-4.2,2.7,45.1],50],
    [.065,[6.9,2.42,63],[-3.7,2.32,46.3],53],
    [.1,[6.1,2,58.8],[-4.15,2.22,46.5],53],
    [.117,[-.9,2.20,43.9],[-2.9,2.24,16.4],52],
    [.129,[-1.5,2.18,31.0],[-1.4,2.52,8.4],51],
    [.147,[4.6,3.48,19],[23,2.8,-10],52],
    [.172,[13.8,3.7,3.0],[42,2.25,-23],53],
    [.20,[22.0,4.75,-8.5],[48,2.1,-33],52],
    [.204,[24.2,5.6,-11.4],[49,2.1,-37],52],
    [.212,[39,22,-26],[38,6,-73],54],
    [.221,[65,56,-63],[26,10,-160],56],
    [.230,[91,94,-125],[9,19,-260],59],
    [.239,[83,106,-204],[7,21,-365],59],
    [.247,[56,77,-279],[1,12,-418],57],
    [.255,[22,40,-342],[0,8,-422],54],
    [.263,[3.4,12,-389],[-1,3.8,-433],52],
    [.27,[2.0,2.68,-423],[.1,3.3,-450],52],
    [.293,[3.8,2.5,-437],[-.8,2.86,-452.3],54],
    [.315,[2.4,2.35,-446.3],[-2.95,2.84,-456.7],54],
    [.338,[1.65,2.68,-452.8],[-1.15,3.05,-474],54],
    [.365,[-.3,2.7,-464.2],[3.8,3.22,-484],54],
    [.398,[-1.5,2.66,-477],[10.6,3.2,-489.9],55],
    [.405,[-1.9,2.8,-480],[12.5,3.45,-490.1],55],
    [.413,[-1.8,7,-483],[13,4.0,-499],55],
    [.420,[1,23,-492],[12,6,-528],54],
    [.430,[12,55,-525],[10,12,-620],55],
    [.440,[42,88,-570],[6,21,-711],58],
    [.450,[64,104,-627],[2,26,-793],59],
    [.460,[54,98,-685],[1,26,-806],56],
    [.470,[28,85,-720],[1,19,-790],53],
    [.479,[4,58,-744],[2,16,-811],53],
    [.487,[-1,32,-763],[3,13,-819],54],
    [.495,[-1.2,11,-780],[3.5,9.4,-834],54],
    [.504,[-.25,3.4,-788],[4.1,8.6,-836.4],54],
    [.519,[1.85,2.80,-794.6],[5.2,8.25,-836.5],55],
    [.545,[4.1,2.15,-807.7],[8,7.3,-837],56],
    [.568,[3.1,2.7,-813.6],[2.9,9.2,-840.8],54],
    [.592,[1.0,3.35,-817.5],[1.3,11.45,-841.6],54],
    [.626,[-2.7,3.86,-816.6],[1.9,11.65,-842],55],
    [.632,[-2.9,4.9,-815.8],[1.8,12.1,-843.4],55],
    [.640,[-2.0,16,-814.9],[1,16,-854],55],
    [.648,[-3,44,-826],[0,21,-896],55],
    [.656,[1,83,-870],[2,32,-986],55],
    [.665,[2,115,-937],[-5,30,-1093],58],
    [.675,[-29,110,-1009],[-10,29,-1172],58],
    [.684,[-81,95,-1077],[4,36,-1234],55],
    [.695,[-109,64,-1134],[4,32,-1254],52],
    [.706,[-91,38,-1180],[2,30,-1253],50],
    [.715,[-96.5,30,-1194],[2.4,31.5,-1252],49],
    [.751,[-92,31.2,-1200],[2.0,33,-1254],49],
    [.79,[-81,34,-1210],[2,36,-1259],49],
    [.819,[-79,33.5,-1227],[1,33,-1260],49],
    [.847,[-76,32.6,-1243],[1.2,32.2,-1265],50],
    [.854,[-78,36,-1253],[1.7,32,-1273],51],
    [.862,[-85,65,-1292],[-1,30,-1360],54],
    [.871,[-86,101,-1350],[-6,24,-1481],57],
    [.880,[-69,112,-1422],[14,24,-1604],59],
    [.890,[-21,106,-1483],[40,32,-1661],58],
    [.900,[49,96,-1548],[34,27,-1665],56],
    [.909,[102,72,-1581],[20,32,-1667],55],
    [.918,[125,52,-1612],[9,33,-1675],54],
    [.930,[110,32,-1627],[12,23,-1686],53],
    [.937,[102,23,-1631],[8,23,-1689],53],
    [.948,[83,13,-1635],[18,19,-1684],53],
    [.958,[85,15,-1650],[26,23,-1691],54],
    [.968,[105,18,-1678],[86,14,-1706],52],
    [.974,[125,14,-1704],[132,10,-1727],50],
    [.983,[149,16,-1704],[120,20,-1744],51],
    [.991,[157,18,-1690],[106,30,-1758],51],
    [1,[162,19,-1680],[102,33,-1760],51],
].map(([p,pos,look,fov])=>({p,pos,look,fov}));

// Each interval starts at its last ground composition and ends at the next approach.
export const crossings = [[.200,.270],[.405,.504],[.629,.715],[.847,.930]];

export function hermite(field, t) {
  const KEYS = route;
  const n = KEYS.length;
  if (t <= KEYS[0].p) return KEYS[0][field].slice();
  if (t >= KEYS[n-1].p) return KEYS[n-1][field].slice();
  let i = 0;
  while (i < n-1 && KEYS[i+1].p < t) i++;
  const k0 = KEYS[Math.max(0, i-1)], k1 = KEYS[i], k2 = KEYS[i+1], k3 = KEYS[Math.min(n-1, i+2)];
  const dt = k2.p - k1.p;
  const u = (t - k1.p) / dt;
  const t0 = k0.p, t1 = k1.p, t2 = k2.p, t3 = k3.p;
  const out = [];
  for (let j = 0; j < k1[field].length; j++) {
    const p0 = k0[field][j], p1 = k1[field][j], p2 = k2[field][j], p3 = k3[field][j];
    const m1 = (p2 - p0) / Math.max(1e-6, t2 - t0) * dt;
    const m2 = (p3 - p1) / Math.max(1e-6, t3 - t1) * dt;
    const u2 = u*u, u3 = u2*u;
    const h00 = 2*u3 - 3*u2 + 1, h10 = u3 - 2*u2 + u, h01 = -2*u3 + 3*u2, h11 = u3 - u2;
    out.push(h00*p1 + h10*m1 + h01*p2 + h11*m2);
  }
  return out;
}
// Measure actual camera travel in metres. Input is measured in ground metres;
// the flight clock costs progressively less effort towards the middle of each crossing.
const sampleCount = 8192;
const distances = new Float64Array(sampleCount+1), effort = new Float64Array(sampleCount+1);
let previousPosition = hermite('pos',0);
for (let i=1;i<=sampleCount;i++) {
  const here=hermite('pos',i/sampleCount);
  distances[i]=distances[i-1]+Math.hypot(...here.map((v,j)=>v-previousPosition[j]));
  previousPosition=here;
}
function sample(table,p) {
  const at=Math.max(0,Math.min(sampleCount,p*sampleCount)), i=Math.floor(at);
  return i===sampleCount ? table[i] : table[i]+(table[i+1]-table[i])*(at-i);
}
const banks=crossings.map(([lo,hi])=>[sample(distances,lo),sample(distances,hi)]);
for (let i=1;i<=sampleCount;i++) {
  const middle=(distances[i]+distances[i-1])*.5;
  const span=banks.find(([start,end])=>middle>start && middle<end);
  let gain=1;
  if(span) {
    const u=(middle-span[0])/(span[1]-span[0]);
    const ramp=Math.min(1,Math.min(u,1-u)/.25);
    gain+=14*ramp*ramp*(3-2*ramp);
  }
  effort[i]=effort[i-1]+(distances[i]-distances[i-1])/gain;
}
export const travelLength=effort[sampleCount];
export function travelTime(p) { return sample(effort,p); }
export function progressAtTime(value) {
  if(value<=0)return 0;
  if(value>=travelLength)return 1;
  let lo=0,hi=sampleCount;
  while(hi-lo>1){const m=(lo+hi)>>1; if(effort[m]<=value)lo=m;else hi=m;}
  return (lo+(value-effort[lo])/(effort[hi]-effort[lo]))/sampleCount;
}
// Exact critically damped response under a constant target, including a reversal.
export function glide(position, target, velocity, dt) {
  const omega=5.8, offset=position-target, tangent=velocity+omega*offset, decay=Math.exp(-omega*dt);
  const next=target+(offset+tangent*dt)*decay, speed=(velocity-omega*tangent*dt)*decay;
  const limit=12; // Ground speed; the crossing's continuous gain is applied by the route metric.
  return [position+Math.max(-limit*dt,Math.min(limit*dt,next-position)),Math.max(-limit,Math.min(limit,speed))];
}

// A finite stop with matching incoming velocity and zero acceleration at both ends.
// At tangent=2, speed follows 1-smoothstep(t): half the speed is still retained halfway.
export function arrivalCurve(distance, speed, remaining) {
  const duration=speed>1 ? Math.max(3.6,Math.min(5.2,2*remaining/speed)) : 3.6;
  return {distance,remaining,duration,tangent:remaining>0?Math.min(2,speed*duration/remaining):0,elapsed:0};
}
export function sampleArrival(curve,dt) {
  curve.elapsed=Math.min(curve.duration,curve.elapsed+dt);
  const u=curve.elapsed/curve.duration,m=curve.tangent;
  const s=m*u+(10-6*m)*u**3+(8*m-15)*u**4+(6-3*m)*u**5;
  const v=m+3*(10-6*m)*u*u+4*(8*m-15)*u**3+5*(6-3*m)*u**4;
  return [curve.distance+curve.remaining*s,curve.remaining/curve.duration*v,u>=1];
}

export function routeIndex(p) {
  const next = crossings.findIndex(([start,end]) => p < (start+end)/2);
  return next < 0 ? crossings.length : next;
}

export function crossingAt(p) {
  const from = crossings.findIndex(([start,end]) => p > start && p < end);
  if (from < 0) return null;
  const [start,end] = crossings[from];
  const t = (p-start)/(end-start);
  const blend = Math.max(0,Math.min(1,(t-.20)/.60));
  const height = Math.max(0,Math.min(1,t/.38,(1-t)/.36));
  return {from, to:from+1, blend:blend*blend*(3-2*blend), mist:height*height*(3-2*height)};
}
