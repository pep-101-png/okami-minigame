import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone} from 'three/addons/utils/SkeletonUtils.js';
import {createDivineSpear} from './divine-spear.js';
let asset;
export async function loadWolf(){
 asset ??= await new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}models/divine-wolf.glb`);
 return asset;
}
export function wolf(){
 if(!asset) throw new Error('Wolf must load before starting.');
 const root=new THREE.Group(),body=clone(asset.scene);root.add(body);body.scale.setScalar(.34);body.rotation.y=Math.PI;
 const mixer=new THREE.AnimationMixer(body),actions={};
 body.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;}});
 for(const clip of asset.animations){const a=mixer.clipAction(clip);actions[clip.name]=a;if(!['Idle','Walk','Run'].includes(clip.name)){a.setLoop(THREE.LoopOnce,1);a.clampWhenFinished=true;}}
 actions.Trot=actions.Walk;
 const chargeStride=mixer.clipAction(new THREE.AnimationClip('ChargeStride',actions.Walk.getClip().duration,actions.Walk.getClip().tracks.filter(t=>/^(fore|hind)/.test(t.name))));
 chargeStride.play().setEffectiveWeight(0);let strideWeight=0;
 const head=body.getObjectByName('head');body.updateMatrixWorld(true);
 const headCarrier=new THREE.Group();head.add(headCarrier);
 const grip=body.localToWorld(new THREE.Vector3(0,4.17,4.03));headCarrier.position.copy(head.worldToLocal(grip));
 const q=new THREE.Quaternion();head.getWorldQuaternion(q);headCarrier.quaternion.copy(q.invert().multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),Math.PI)));headCarrier.scale.setScalar(1/.34);
 const {spear,ribbon,tassels,ghost}=createDivineSpear(headCarrier);
 const skin=(()=>{let found;body.traverse(o=>{if(o.isSkinnedMesh&&!found)found=o;});return found;})();
 // A restrained ink hull follows the same deforming skin, including ankle and shoulder fur.
 const ink=new THREE.MeshBasicMaterial({color:'#514c40',side:THREE.BackSide});
 ink.onBeforeCompile=shader=>{shader.vertexShader=shader.vertexShader.replace('#include <skinning_vertex>','#include <skinning_vertex>\n transformed += normalize(objectNormal) * .016;');};
 const shell=new THREE.SkinnedMesh(skin.geometry,ink);shell.bind(skin.skeleton,skin.bindMatrix);shell.position.copy(skin.position);shell.quaternion.copy(skin.quaternion);shell.scale.copy(skin.scale);shell.frustumCulled=false;skin.parent.add(shell);
 const result={root,body,head,spear,ribbon,mixer,actions,tail:body.getObjectByName('tail'),state:null,eyes:[],legs:[],footfalls:[],groundLift:0};
 result.weaponEndpoints=()=>{root.updateMatrixWorld(true);return {tip:spear.localToWorld(new THREE.Vector3(.3,0,2.08)),heel:spear.localToWorld(new THREE.Vector3(.3,0,-.9))};};
 result.updateDetails=()=>root.updateMatrixWorld(true);
 let previousAttack=0,previousAir=false,landingTime=0;
 result.animate=({dt,speed=0,air=false,attack=0,dash=false,combo=1,attackClip=null,charge=null,voice=null,verticalVelocity=0,turnDelta=0})=>{
  if(previousAir&&!air)landingTime=.18;previousAir=air;landingTime=Math.max(0,landingTime-dt);
  let state=attack>0?(attackClip||['','Thrust','Sweep','Finish'][combo]):dash?'Dodge':air?(verticalVelocity>=-.25?'JumpRise':'JumpFall'):charge?(charge.kind==='heavy'?'ChargeHeavy':'ChargeLight'):voice&&speed<.6?voice.clip:landingTime>0?'Land':speed>5.6?'Run':speed>.18?'Walk':'Idle';
  if(!actions[state])state='Idle';
  const action=actions[state];
  if(state!==result.state||(attack>0&&attack+.1<previousAttack)){
   const old=actions[result.state];action.reset().setEffectiveWeight(1).setEffectiveTimeScale(1).play();if(old&&old!==action)old.crossFadeTo(action,attack>0?.075:.14,false);
   for(const other of new Set(Object.values(actions)))if(other!==action&&other!==old)other.stop();result.state=state;
  }
  if(state==='Walk')action.setEffectiveTimeScale(THREE.MathUtils.clamp(speed/2.3,.4,2.2));
  if(state==='Run')action.setEffectiveTimeScale(THREE.MathUtils.clamp(speed/6.2,.7,1.6));
  strideWeight=THREE.MathUtils.damp(strideWeight,charge&&speed>.18&&!air&&attack<=0?2.5:0,12,dt);
  chargeStride.setEffectiveWeight(strideWeight).setEffectiveTimeScale(THREE.MathUtils.clamp(speed/2.3,.4,1.8));
  const before=action.time/action.getClip().duration;mixer.update(dt);
  if(attack>0){action.time=attack*action.getClip().duration;mixer.update(0);}
  if(charge&&attack<=0&&!air){action.time=(.1+.85*charge.ratio)*action.getClip().duration;mixer.update(0);}
  if(air&&attack<=0&&!dash){action.time=THREE.MathUtils.clamp(state==='JumpRise'?1-verticalVelocity/7.7:-verticalVelocity/7.7,.04,.96)*action.getClip().duration;mixer.update(0);}
  if(voice&&state===voice.clip){action.time=voice.phase*action.getClip().duration;mixer.update(0);}
  const after=action.time/action.getClip().duration;result.footfalls=[];
  if(['Walk','Run'].includes(state)&&speed>.3&&!air)for(const [phase,bone] of [[.15,'forePawL'],[.65,'forePawR']])if((after>=before&&phase>before&&phase<=after)||(after<before&&(phase>before||phase<=after))){root.updateMatrixWorld(true);const point=body.getObjectByName(bone).getWorldPosition(new THREE.Vector3());point.y=root.position.y+.015;result.footfalls.push(point);}
  body.rotation.z=THREE.MathUtils.damp(body.rotation.z,THREE.MathUtils.clamp(turnDelta*.12,-.06,.06),10,dt);
  body.position.y=0;root.updateMatrixWorld(true);skin.skeleton.update();
  if(!air){let lowest=Infinity;const vertex=new THREE.Vector3();for(let i=0;i<skin.geometry.attributes.position.count;i++){skin.getVertexPosition(i,vertex).applyMatrix4(skin.matrixWorld);lowest=Math.min(lowest,vertex.y);}body.position.y=Math.max(0,root.position.y+.012-lowest);result.groundLift=body.position.y;}
  // Secondary wind remains active even when a combat/charge pose is held.
  for(const [i,name] of ['ruffL','ruffR','shoulderFurL','shoulderFurR','foreFurL','foreFurR','hindFurL','hindFurR'].entries()){
   const bone=body.getObjectByName(name);if(bone)bone.rotation.z+=Math.sin(mixer.time*2.1-i*.65)*.018;
  }
  tassels.forEach((t,i)=>{t.rotation.x=.15+Math.sin(mixer.time*6-i*.6)*(.15+speed*.025);t.rotation.z=-.25+i*.15+Math.sin(mixer.time*4-i)*.2;});
  ghost.material.opacity=.19+Math.sin(mixer.time*3)*.06+(attack>0?.22:0);
  // Full head/body poses lead the weapon; a small grip accent adds whip-through.
  let pitch=0,roll=0;
  if(attack>0){const accent=Math.sin(Math.PI*attack);pitch=['HeavyArc','ChargedHeavy','AirStrike'].includes(state)?.24*accent:state==='HeavyReturn'?-.24*accent:-.08*accent;roll=state==='Sweep'?.18*Math.sin(attack*Math.PI*2):.07*accent;}
  spear.rotation.x=THREE.MathUtils.damp(spear.rotation.x,pitch,24,dt);spear.rotation.z=THREE.MathUtils.damp(spear.rotation.z,roll,24,dt);
  if(!air&&attack>0)for(let i=0;i<14;i++){root.updateMatrixWorld(true);const tip=spear.localToWorld(new THREE.Vector3(.3,0,2.18)),heel=spear.localToWorld(new THREE.Vector3(.3,0,-.97));if(Math.min(tip.y,heel.y)>=root.position.y+.06)break;spear.rotation.x+=tip.y<heel.y?-.065:.065;}
  result.updateDetails();previousAttack=attack;
 };
 result.fur={mode:'skinned',bones:['ruffL','ruffR','shoulderFurL','shoulderFurR','foreFurL','foreFurR','hindFurL','hindFurR'].map(n=>body.getObjectByName(n))};
 return result;
}
