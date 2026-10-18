import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { createDivineSpear } from '../divine-spear.js';
import { createSundial,createAscension } from './weapons.js';
let asset;
export async function loadWolf(){asset??=await new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}models/amaterasu-original.glb`);return asset;}
export function wolf(){
 if(!asset)throw new Error('Original Amaterasu has not loaded');
 const root=new THREE.Group(),body=clone(asset.scene);root.add(body);body.scale.setScalar(.34);body.rotation.y=Math.PI;
 body.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;}});
 const mixer=new THREE.AnimationMixer(body),actions={};
 for(const clip of asset.animations){if(actions[clip.name])continue;const a=mixer.clipAction(clip);actions[clip.name]=a;if(!/^(Idle|Walk|Jog|Sprint|Air_Fall)/.test(clip.name)){a.setLoop(THREE.LoopOnce,1);a.clampWhenFinished=true;}}
 const head=body.getObjectByName('DEF_head');if(!head)throw new Error('Original wolf head bone missing');body.updateMatrixWorld(true);
 function carrier(bone,point){const g=new THREE.Group();bone.add(g);g.position.copy(bone.worldToLocal(body.localToWorld(new THREE.Vector3(...point))));const q=new THREE.Quaternion();bone.getWorldQuaternion(q);g.quaternion.copy(q.invert().multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),Math.PI)));g.scale.setScalar(1/.34);return g;}
 const headCarrier=carrier(head,[0,4.20,4.16]);const{spear,ribbon,tassels,ghost}=createDivineSpear(headCarrier);
 const back=carrier(body.getObjectByName('DEF_chest')||head,[0,4.2,.1]);const sundial=createSundial(back);sundial.root.visible=false;
 const result={root,body,head,spear,ribbon,mixer,actions,state:null,eyes:[],legs:[],footfalls:[],groundLift:0,equipment:'spear',power:0};const ascension=createAscension(result);
 result.equip=weapon=>{result.equipment=weapon;spear.visible=weapon==='spear';sundial.root.visible=weapon==='sundial';};
 result.weaponEndpoints=()=>{root.updateMatrixWorld(true);return result.equipment==='sundial'?{tip:sundial.root.localToWorld(new THREE.Vector3(.5,.3,0)),heel:sundial.root.localToWorld(new THREE.Vector3(-.4,-.3,0))}:{tip:spear.localToWorld(new THREE.Vector3(.3,0,2.08)),heel:spear.localToWorld(new THREE.Vector3(.3,0,-.9))};};
 result.updateDetails=()=>root.updateMatrixWorld(true);
 const rootBone=body.getObjectByName('CTRL_root');let doubleActive=false,doubleClock=0,heavyLand=false,lastVertical=0,previousAir=false,land=0,previousDash=false,dashClock=0,previousAttack=0,attackClock=0,time=0,jump='Jump_Standing',lastSpeed=0;const overlays=new Map();
 result.triggerDouble=()=>{doubleActive=true;doubleClock=0;};
 function restore(){for(const[b,q]of overlays)b.quaternion.copy(q);overlays.clear();}
 function bend(name,x,y,z){const b=body.getObjectByName(name);if(!b)return;overlays.set(b,b.quaternion.clone());b.rotateX(x);b.rotateY(y);b.rotateZ(z);}
 result.animate=({dt=0,speed=0,air=false,attack=0,dash=false,combo=1,attackClip=null,verticalVelocity=0,turnDelta=0,charge=null,voice=null})=>{
  restore();time+=dt;
  if(air&&!previousAir)jump=lastSpeed>5?'Jump_Sprint':lastSpeed>2?'Jump_Jog':lastSpeed>.4?'Jump_Walk':'Jump_Standing';
  if(previousAir&&!air){heavyLand=lastVertical < -9;land=heavyLand?.48:.32;doubleActive=false;}lastVertical=verticalVelocity;previousAir=air;land=Math.max(0,land-dt);
  if(dash&&!previousDash)dashClock=0;previousDash=dash;if(dash)dashClock+=dt;
  if(attack>0&&(!previousAttack||attack<previousAttack))attackClock=0;if(attack>0)attackClock+=dt;previousAttack=attack;
  let state=dash?(result.dodgeClip||'Dodge_Forward'):air?(doubleActive?'Jump_Double':jump):land>0?(heavyLand?'Land_Heavy':'Land_Soft'):speed>5?'Sprint_Fluid':speed>1.45?'Jog_Natural':speed>.12?'Walk_Natural':'Idle_Natural';
  if(!air&&!dash&&!attack&&Math.abs(turnDelta)>.75&&speed>.2){const gait=speed>5?'Sprint':speed>1.45?'Jog':'Walk';state=gait+'_Turn_'+(turnDelta>0?'L':'R');}
  if(attack>0){state=attackClip||['','Thrust','Sweep','Finish'][combo];if(result.equipment==='sundial'&&state!=='AirStrike')state=/Charged/.test(state)?'DiscCharged':/Heavy/.test(state)?'DiscHeavy':['','Disc1','Disc2','Disc3'][combo];}
  else if(charge&&!air&&!dash)state=charge.kind==='heavy'?'ChargeHeavy':'ChargeLight';
  else if(voice?.clip==='Bark'&&speed<.5&&!air&&!dash)state='Bark';
  if(!actions[state])state='Idle_Natural';const a=actions[state];
  if(result.state!==state){const old=actions[result.state];a.reset().setEffectiveWeight(1).setEffectiveTimeScale(1).play();if(old)old.crossFadeTo(a,.13,false);result.state=state;}
  const gait=state.startsWith('Sprint')?'Sprint':state.startsWith('Jog')?'Jog':state.startsWith('Walk')?'Walk':null;
  if(gait)a.setEffectiveTimeScale(THREE.MathUtils.clamp(speed/({Walk:.5667,Jog:2.448,Sprint:4.9725}[gait]),.45,1.7));
  mixer.update(dt);
  if(attack>0){a.time=attack*a.getClip().duration;mixer.update(0);}
  else if(charge&&!air&&!dash){a.time=(.08+.90*charge.ratio)*a.getClip().duration;mixer.update(0);}
  if(air&&doubleActive&&attack<=0){doubleClock+=dt;a.time=Math.min(a.getClip().duration,.23+doubleClock*1.15);mixer.update(0);}
  if(air&&!doubleActive&&attack<=0){const data={Jump_Standing:[26,74],Jump_Walk:[24,68],Jump_Jog:[18,64],Jump_Sprint:[12,62]}[jump];const u=verticalVelocity>=0?(1-THREE.MathUtils.clamp(verticalVelocity/7.7,0,1))*.5:.5+THREE.MathUtils.clamp(-verticalVelocity/7.7,0,1)*.5;a.time=(data[0]+(data[1]-data[0])*u)/60;mixer.update(0);}
  if(dash){a.time=THREE.MathUtils.clamp(dashClock/.28,0,1)*a.getClip().duration;mixer.update(0);}
  if(land>0&&!air&&!dash&&attack<=0&&!charge){a.time=(heavyLand?.2:.14)+((heavyLand?.48:.32)-land)*1.8;mixer.update(0);}
  // Physics owns world travel. Remove the exported root displacement, retaining the exact authored pose.
  if(rootBone)rootBone.position.set(0,0,0);
  if(charge&&!actions.ChargeLight){const v=charge.ratio; bend('CTRL_hips',.12*v,0,0);bend('CTRL_chest',-.10*v,0,0);bend('CTRL_neck_upper',-.08*v,0,0);}
  if(voice&&voice.clip==='Bark'&&!actions.Bark){const w=Math.sin(Math.PI*voice.phase);bend('CTRL_neck_base',.10*w,0,0);bend('CTRL_head',-.14*w,0,0);bend('CTRL_jaw',.14*w,0,0);}
  if(attack>0){const w=Math.sin(attack*Math.PI),native=!!actions.Thrust,twist=result.equipment==='sundial'?Math.sin(attack*Math.PI*2)*.30:(combo===2?Math.sin(attack*Math.PI*2)*.20:0);if(!native){bend('CTRL_chest',-.07*w,0,twist);bend('CTRL_spine_mid',.05*w,0,-twist*.35);bend('CTRL_head',.05*w,0,-twist*.25);bend('DEF_front_upper.L',-.12*w,0,0);bend('DEF_front_upper.R',-.12*w,0,0);}
  spear.rotation.x=-.12*w;spear.rotation.y=combo===2?twist*2:0;}
  else{spear.rotation.x=0;spear.rotation.y=0;}
  for(let i=0;i<tassels.length;i++){tassels[i].rotation.x=Math.sin(time*5-i)*(.12+speed*.015);}
  ghost.material.opacity=.16+attack*.2;sundial.update(time,speed,attack);ascension.update(time,speed,result.power);
  if(!air&&result.equipment==='spear')for(let i=0;i<10;i++){root.updateMatrixWorld(true);const tip=spear.localToWorld(new THREE.Vector3(.3,0,2.08)),heel=spear.localToWorld(new THREE.Vector3(.3,0,-.9));if(Math.min(tip.y,heel.y)>root.position.y+.045)break;spear.rotation.x+=tip.y<heel.y?-.055:.055;}
  result.footfalls=[];if(!air&&!dash&&speed>.2&&Math.floor(time*speed*1.6)!==Math.floor((time-dt)*speed*1.6)){const b=body.getObjectByName(time%1>.5?'DEF_front_pawL':'DEF_front_pawR');if(b){root.updateMatrixWorld(true);const p=b.getWorldPosition(new THREE.Vector3());p.y=root.position.y+.02;result.footfalls.push(p);}}
  if(!dash&&speed>.15)lastSpeed=speed;else if(!air&&!dash)lastSpeed=0;
  root.updateMatrixWorld(true);
 };
 return result;
}
