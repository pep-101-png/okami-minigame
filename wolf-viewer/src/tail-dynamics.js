import * as THREE from 'three';

/** Passive, inextensible tail: hip motion drives inertia; gravity and air drag set posture. */
export function createTailDynamics(model, metadata){
 const bones=metadata.bones.map(n=>model.getObjectByName(n));
 if(bones.some(b=>!b))throw new Error('Continuous tail chain is missing.');
 const segment=metadata.length*model.scale.x/bones.length;
 const legColliders=[];for(const side of ['L','R'])for(const [a,b,radius] of [['hind','hindShin',.125],['hindShin','hindPaw',.10],['hindPaw','hindPaw',.14]])legColliders.push({a:model.getObjectByName(a+side),b:model.getObjectByName(b+side),radius,start:new THREE.Vector3(),end:new THREE.Vector3()});
 const restQ=bones.map(b=>b.quaternion.clone());
 const position=Array.from({length:bones.length+1},()=>new THREE.Vector3());
 const previous=position.map(p=>p.clone());
 const root=new THREE.Vector3(),lastRoot=new THREE.Vector3(),back=new THREE.Vector3(),forwardQ=new THREE.Quaternion(),worldQ=new THREE.Quaternion(),parentQ=new THREE.Quaternion(),direction=new THREE.Vector3(),delta=new THREE.Vector3();
 const axis=new THREE.Vector3(0,1,0),up=new THREE.Vector3(0,1,0);let initialized=false,speed=0,elapsed=0,accumulator=0;
 function noise(t){const i=Math.floor(t),u=t-i,s=u*u*(3-2*u),hash=n=>{const h=Math.sin(n*127.1+311.7)*43758.5453;return (h-Math.floor(h))*2-1};return THREE.MathUtils.lerp(hash(i),hash(i+1),s);}
 function axes(){model.updateMatrixWorld(true);bones[0].getWorldPosition(root);model.getWorldQuaternion(forwardQ);back.set(0,0,-1).applyQuaternion(forwardQ);back.y=0;back.normalize();}
 function reset(velocity=0){
  speed=velocity;elapsed=0;accumulator=0;axes();lastRoot.copy(root);
  position[0].copy(root);
  for(let i=1;i<position.length;i++){const t=i/(position.length-1),lean=THREE.MathUtils.lerp(.5,.98,Math.min(1,speed/1.8));direction.copy(back).multiplyScalar(lean*(1-.65*t)).addScaledVector(up,-Math.sqrt(1-lean*lean*.8)).normalize();position[i].copy(position[i-1]).addScaledVector(direction,segment);}
  previous.forEach((p,i)=>p.copy(position[i]));initialized=true;apply();
 }
 function apply(){
  // A bone's +Y axis follows the segment, while its rest roll is retained.
  for(let i=0;i<bones.length;i++){
   const bone=bones[i];bone.quaternion.copy(restQ[i]);bone.updateWorldMatrix(true,false);bone.getWorldQuaternion(worldQ);direction.copy(axis).applyQuaternion(worldQ);delta.copy(position[i+1]).sub(position[i]).normalize();const swing=new THREE.Quaternion().setFromUnitVectors(direction,delta);worldQ.premultiply(swing);bone.parent.getWorldQuaternion(parentQ);bone.quaternion.copy(parentQ.invert().multiply(worldQ));bone.updateWorldMatrix(false,false);
  }
  model.updateMatrixWorld(true);
 }
 function step(dt,targetSpeed){
  axes();for(const c of legColliders){c.a.getWorldPosition(c.start);c.b.getWorldPosition(c.end);}if(!initialized){reset(targetSpeed);return;}
  // A large teleport should move the whole chain rather than stretching it.
  delta.copy(root).sub(lastRoot);if(delta.length()>.4){position.forEach(p=>p.add(delta));previous.forEach(p=>p.add(delta));}lastRoot.copy(root);
  speed=THREE.MathUtils.damp(speed,targetSpeed,2.2,dt);elapsed+=dt;accumulator+=Math.min(dt,.05);
  const h=1/120;
  while(accumulator>=h){
   accumulator-=h;const ratio=Math.min(1,speed/1.8),drag=21*ratio*ratio*(1+.12*noise(elapsed*1.1+7)),crosswind=(.12+1.1*ratio)*noise(elapsed*.85+32);
   position[0].copy(root);previous[0].copy(root);
   for(let i=1;i<position.length;i++){
    const p=position[i],old=p.clone(),velocity=p.clone().sub(previous[i]).multiplyScalar(Math.exp(-3.8*h));p.add(velocity);p.y-=8*h*h;p.x+=crosswind*h*h;p.addScaledVector(back,drag*h*h);previous[i].copy(old);
   }
   // The rump supports the base; the remaining chain hangs and trails freely.
   const rootLean=THREE.MathUtils.lerp(.60,.98,ratio);direction.copy(back).multiplyScalar(rootLean).addScaledVector(up,-Math.sqrt(1-rootLean*rootLean)).normalize();
   for(let pass=0;pass<14;pass++){
    position[0].copy(root);const first=root.clone().addScaledVector(direction,segment);position[1].lerp(first,.16);
    for(let i=0;i<position.length-1;i++){
     const d=position[i+1].clone().sub(position[i]),length=d.length();if(length<1e-8)continue;d.multiplyScalar((length-segment)/length);if(i===0)position[i+1].sub(d);else{position[i].addScaledVector(d,.5);position[i+1].addScaledVector(d,-.5);}
    }
    // Distributed bending resistance, strongest at the base and soft at the tip.
    for(let i=1;i<position.length-1;i++){
     const a=position[i-1],c=position[i+1],d=c.clone().sub(a),length=d.length(),target=segment*1.995;
     if(length>=target||length<1e-8)continue;d.multiplyScalar((target-length)/length*(.48-.30*i/bones.length));if(i>1)a.addScaledVector(d,-.5);c.addScaledVector(d,.5);
    }
    // Relax excessive local curvature smoothly across neighbouring joints.
    for(let i=1;i<position.length-1;i++){
     const middle=position[i-1].clone().add(position[i+1]).multiplyScalar(.5),offset=position[i].clone().sub(middle),height=offset.length(),allow=segment*(.14+.025*i/bones.length);
     if(height>allow)position[i].addScaledVector(offset,-.16*(1-allow/height));
    }
    for(let i=3;i<position.length;i++)for(const c of legColliders){const segmentDirection=c.end.clone().sub(c.start),lengthSquared=segmentDirection.lengthSq(),t=lengthSquared>1e-8?THREE.MathUtils.clamp(position[i].clone().sub(c.start).dot(segmentDirection)/lengthSquared,0,1):0,nearest=c.start.clone().addScaledVector(segmentDirection,t),separation=position[i].clone().sub(nearest),distance=separation.length(),radius=c.radius+THREE.MathUtils.lerp(.065,.012,i/bones.length);if(distance<radius){if(distance<1e-6)separation.copy(back);else separation.divideScalar(distance);position[i].addScaledVector(separation,(radius-distance)*.75);}}
    for(let i=2;i<position.length;i++){position[i].y=Math.max(.06,position[i].y);const rear=position[i].clone().sub(root).dot(back);if(rear<.018)position[i].addScaledVector(back,.018-rear);}
   }
  }
  apply();
 }
 return {reset,step,apply,get points(){return position.map(p=>p.clone())},get speed(){return speed},get lengths(){return position.slice(1).map((p,i)=>p.distanceTo(position[i]))},segment};
}
