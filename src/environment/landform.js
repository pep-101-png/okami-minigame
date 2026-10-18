import * as THREE from 'three';
export const smooth=(a,b,x)=>{const t=THREE.MathUtils.clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);};
export const BRIDGES=[12,-14];
function riverRaw(z){return 1.1*Math.sin(z*.13)+.45*Math.sin(z*.31)+2*Math.exp(-Math.pow((z+8)/4,2));}
const cross=Math.exp(-Math.pow(26/4,2)),aa=(riverRaw(12)-riverRaw(-14)*cross)/(1-cross*cross),bb=riverRaw(-14)-aa*cross;
export function riverAt(z){const x=-23+riverRaw(z)-aa*Math.exp(-Math.pow((z-12)/4,2))-bb*Math.exp(-Math.pow((z+14)/4,2));return{x,width:2.45+.40*Math.sin(z*.17+.4)+.25*Math.cos(z*.31),waterY:-.34,depth:1.15+.35*Math.sin(z*.10+.4)};}
export function bridgeAt(x,z){const index=BRIDGES.findIndex(b=>Math.abs(z-b)<1.28);if(index<0||x< -27.8||x> -18.2)return null;let t=(x+27.8)/9.6;return{index,t,y:.10+.42*Math.pow(Math.sin(Math.PI*t),1.5)};}
export function waterAt(x,z){const r=riverAt(z),n=Math.abs(x-r.x)/r.width;if(n>=1.12||bridgeAt(x,z))return{depth:0,deep:false,river:false};const bank=smooth(.56,1.12,n),bed=(r.waterY-r.depth)*(1-bank)+.10*bank;return{...r,channelDepth:r.depth,bed,n,depth:Math.max(0,r.waterY-bed),deep:bed<r.waterY-.34,river:bed<r.waterY};}
export function resolveRiver(pos,radius=.43){if(bridgeAt(pos.x,pos.z))return;const w=waterAt(pos.x,pos.z);if(!w.deep)return;const sign=pos.x<w.x?-1:1;let lo=.56,hi=1.12;for(let i=0;i<13;i++){const t=(lo+hi)/2,bed=(w.waterY-w.channelDepth)*(1-smooth(.56,1.12,t))+.10*smooth(.56,1.12,t);if(bed<w.waterY-.31)lo=t;else hi=t;}pos.x=w.x+sign*(w.width*hi+Math.min(.10,radius*.18));}
function route(points,width,id){const curve=new THREE.CatmullRomCurve3(points.map(([x,z])=>new THREE.Vector3(x,0,z)),false,'centripetal');const samples=curve.getSpacedPoints(80).map((p,i)=>({x:p.x,z:p.z,width:width*(1+.11*Math.sin(i*.23)+.06*Math.sin(i*.67)),u:i/80}));return{id,curve,samples,width};}
export function createLandform(world){
 const paths=[route([[0,-30],[-.8,-19],[.5,-9],[-.2,0],[.9,9],[0,21],[-.6,30]],5.2,'shrine-road'),route([[-45,12],[-35,11.4],[-23,12],[-12,13],[0,12],[7,7],[14,0],[24,-.3]],4.0,'west-road'),route([[-34,-18],[-29,-14],[-23,-14],[-16,-13.7],[-8,-16],[0,-17]],3.4,'mill-road'),route([[-34,25],[-33.5,17],[-32,7],[-32.6,-7],[-32,-23]],3.5,'westbank')];
 const foundations=world.boxes.filter(b=>b.halfX>1&&b.halfZ>1).map(b=>({...b}));foundations.push({x:-34,z:16,halfX:5.5,halfZ:4.8},{x:0,z:0,halfX:6,halfZ:4});
 const nearest=(x,z)=>{let best={distance:1e5,width:1,u:0,id:''};for(const p of paths)for(let i=0;i<p.samples.length-1;i++){const a=p.samples[i],b=p.samples[i+1],dx=b.x-a.x,dz=b.z-a.z,t=THREE.MathUtils.clamp(((x-a.x)*dx+(z-a.z)*dz)/(dx*dx+dz*dz||1),0,1),distance=Math.hypot(x-a.x-t*dx,z-a.z-t*dz);if(distance<best.distance)best={distance,width:a.width,u:a.u,id:p.id};}return best;};
 function rawHeight(x,z){let h=.25*Math.sin(x*.12+z*.055)+.18*Math.sin(z*.16-x*.075)+.10*Math.sin(x*.24)*Math.cos(z*.21);const p=nearest(x,z),inPath=1-smooth(p.width*.30,p.width*.70,p.distance);h=h*(1-inPath*.65)-inPath*.065;h-=.02*Math.cos(p.distance*9)*inPath;
  for(const f of foundations){const d=Math.max(Math.abs(x-f.x)-f.halfX,Math.abs(z-f.z)-f.halfZ);h*=smooth(.25,2,d);}
  const pond=Math.hypot((x+15)/2.7,(z-22)/1.7);if(pond<1.25)h=THREE.MathUtils.lerp(-.34,h,smooth(.75,1.25,pond));
  const arena=1-smooth(18,20,Math.hypot(x-35,z));h*=1-arena;
  const r=riverAt(z),n=Math.abs(x-r.x)/r.width;if(n<1.8){const bed=(r.waterY-r.depth)*(1-smooth(.56,1.12,n))+.10*smooth(.56,1.12,n);h=THREE.MathUtils.lerp(bed,h,smooth(1.10,1.8,n));}return h;
 }
 const minX=-60,minZ=-48,step=.5,nx=261,nz=193,heights=new Float32Array(nx*nz);for(let j=0;j<nz;j++)for(let i=0;i<nx;i++)heights[j*nx+i]=rawHeight(minX+i*step,minZ+j*step);
 function terrainHeight(x,z){const fx=THREE.MathUtils.clamp((x-minX)/step,0,nx-1.001),fz=THREE.MathUtils.clamp((z-minZ)/step,0,nz-1.001),i=Math.floor(fx),j=Math.floor(fz),u=fx-i,v=fz-j;return THREE.MathUtils.lerp(THREE.MathUtils.lerp(heights[j*nx+i],heights[j*nx+i+1],u),THREE.MathUtils.lerp(heights[(j+1)*nx+i],heights[(j+1)*nx+i+1],u),v);}
 function groundHeight(x,z){const b=bridgeAt(x,z);if(b)return b.y;if(Math.abs(x+34)<5.2&&Math.abs(z-16)<4.25)return .105;return terrainHeight(x,z);}
 return{paths,nearest,groundHeight,terrainHeight,waterAt,resolveRiver,grid:{minX,minZ,step,nx,nz,heights}};
}
