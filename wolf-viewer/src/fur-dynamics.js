import * as THREE from 'three';
/** Anchored fur roots, damped flow and tip response to shared gusts. */
export function createFurDynamics(model){
 const groups=['ruffL','ruffR','shoulderFurL','shoulderFurR','foreFurL','foreFurR','hindFurL','hindFurR','haunchFurL','haunchFurR'];
 const controls=groups.flatMap(name=>['','Flow','Tip'].map((suffix,index)=>({bone:model.getObjectByName(name+suffix),index,scale:name.startsWith('fore')||name.startsWith('hind')?.65:1,angle:new THREE.Vector3(),velocity:new THREE.Vector3(),rest:null})));
 for(const c of controls){if(!c.bone)throw new Error('Fur control missing');c.rest=c.bone.quaternion.clone();}
 let time=0;const q=new THREE.Quaternion(),wind=new THREE.Vector3(),local=new THREE.Vector3();
 const noise=t=>{const i=Math.floor(t),u=t-i,s=u*u*(3-2*u),hash=n=>{const v=Math.sin(n*127.1+37.9)*43758.5453;return 2*(v-Math.floor(v))-1};return THREE.MathUtils.lerp(hash(i),hash(i+1),s)};
 return {step(dt,speed=0){
  time+=dt;model.updateMatrixWorld(true);wind.set(.65*noise(time*.7+4),.8*noise(time*.95+11),.35+.15*Math.min(speed,3));
  const steps=Math.max(1,Math.ceil(dt/(1/120))),h=dt/steps;
  for(const c of controls){
   c.bone.parent.getWorldQuaternion(q);local.copy(wind).applyQuaternion(q.invert());const amplitude=[.005,.11,.22][c.index]*c.scale,target=new THREE.Vector3(local.z,0,-local.x).multiplyScalar(amplitude),stiffness=[60,28,16][c.index],damping=[15,10,7.5][c.index];
   for(let i=0;i<steps;i++){const acceleration=target.clone().sub(c.angle).multiplyScalar(stiffness).addScaledVector(c.velocity,-damping);c.velocity.addScaledVector(acceleration,h);c.angle.addScaledVector(c.velocity,h);}
   const bend=new THREE.Quaternion().setFromEuler(new THREE.Euler(c.angle.x,c.angle.y,c.angle.z));c.bone.quaternion.copy(c.rest).multiply(bend);c.bone.updateWorldMatrix(false,true);
  }
 },get angles(){return controls.map(c=>({name:c.bone.name,angle:c.angle.toArray()}))}};
}
