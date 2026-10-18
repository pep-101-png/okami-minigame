import * as THREE from 'three';
import { batchFixedParts } from '../models.js';
import { EnemyController } from '../enemy.js';
import { paint,stroke } from '../art.js';
import { brushRibbon,form } from './painted-forms.js';
export const SPIRITS={
 wisp:{name:'Ashwing',hp:7,damage:9,speed:3.5,scale:.76,windup:.42,reward:8,xp:8},
 reed:{name:'Reed sentinel',hp:11,damage:13,speed:2.2,scale:1,windup:.67,reward:10,xp:11},
 heavy:{name:'Stonejaw',hp:27,damage:23,speed:1.4,scale:1.65,windup:1.08,reward:18,xp:17},
 ranged:{name:'Paper kite',hp:12,damage:12,speed:1.9,scale:1,windup:.9,reward:13,xp:14},
 elite:{name:'Crimson oathkeeper',hp:32,damage:21,speed:2.8,scale:1.25,windup:.48,reward:23,xp:23},
 boss:{name:'KUROGANE · THE HOLLOW BELL',hp:145,damage:28,speed:1.65,scale:2.75,windup:1.1,reward:45,xp:55},
};
export function createSpirit(scene,kind,index,home,difficulty=1){
 const spec=SPIRITS[kind],visual=new EnemyController(scene,{index,home}),mesh=visual.root;mesh.name=spec.name;
 const rig=visual.rig;const ornaments=new THREE.Group();rig.torso.add(ornaments);let wing=[];
 if(['wisp','ranged'].includes(kind))for(const sign of[-1,1]){
  const g=new THREE.Group();g.position.set(sign*.30,.44,.10);ornaments.add(g);wing.push(g);
  for(let i=0;i<4;i++){const pts=Array.from({length:8},(_,j)=>{const t=j/7;return[sign*t*(.6+i*.10),Math.sin(t*2.8)*(.18+i*.04)-i*.05,t*(.13+i*.12)];});g.add(brushRibbon(pts,.11,kind==='ranged'?'#cebcac':'#7d8899'));}
 }
 if(['heavy','elite','boss'].includes(kind)){
  form(ornaments,[[.12,.37,.25],[.25,.45,.28],[.50,.39,.24],[.62,.18,.16]],kind==='elite'?'#925056':'#707978',{sides:16});
  for(const sign of[-1,1]){
   const p=rig.head;stroke(p,[[sign*.20,.16,.03],[sign*.33,.47,.08],[sign*.23,.65,.12],[sign*.14,.72,.08]],kind==='elite'?'#b7794c':'#d2c49f',.06);
   for(let i=0;i<3;i++){stroke(p,[[sign*.31,.4,.06],[sign*(.41+i*.07),.47+i*.08,.12]],'#514b48',.025);}
  }
 }
 if(kind==='boss'){
  // A broad bell-shaped mantle, antler crown and dangling shrine seals.
  form(ornaments,[[-.35,.45,.31],[-.24,.63,.40],[.14,.55,.38],[.58,.39,.28],[.70,.16,.15]],'#5d6572',{sides:24});
  for(let i=0;i<9;i++){const a=(i-4)*.23;const g=new THREE.Group();g.position.set(Math.sin(a)*.54,.08,.28+Math.cos(a)*.18);ornaments.add(g);g.add(brushRibbon([[0,0,0],[.03,-.3,.03],[-.02,-.65,.14],[.06,-.91,.25]],.09,i%2?'#c6b68f':'#825864'));}
  const crest=new THREE.Group();crest.position.set(0,.72,.23);ornaments.add(crest);
  for(let i=0;i<12;i++){let a=i*Math.PI/6;stroke(crest,[[Math.sin(a)*.45,Math.cos(a)*.45,.1],[Math.sin(a)*.60,Math.cos(a)*.60,.1]],'#d2b36b',.018);}
 }
 batchFixedParts(ornaments);
 const animate=visual.animate.bind(visual);
 visual.animate=(dt,state)=>{animate(dt,state);if(!visual.dead){mesh.scale.setScalar(spec.scale);if(kind==='ranged')rig.visual.position.y+=.48+Math.sin(visual.time*2)*.10;for(let i=0;i<wing.length;i++)wing[i].rotation.z=Math.sin(visual.time*3.5+i*Math.PI)*.18;ornaments.rotation.z=Math.sin(visual.time*1.8+index)*.025;}};
 const canvas=document.createElement('canvas');canvas.width=128;canvas.height=16;const texture=new THREE.CanvasTexture(canvas),bar=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,transparent:true,depthTest:false}));bar.position.y=2.25;bar.scale.set(1.2,.1,1);mesh.add(bar);
 const hp=Math.ceil(spec.hp*difficulty);const e={visual,mesh,home,kind,spec,hp,maxHp:hp,cooldown:.9+index*.13,texture,canvas,bar,state:'approach',timer:0,stateDuration:1,stun:0,deathTime:0,deathEffect:false,attackDirection:new THREE.Vector3(),knockback:new THREE.Vector3(),previous:home.clone(),hitPlayer:false,paid:false,attacks:0,phase2:false};
 e.dispose=()=>{scene.remove(mesh);const geos=new Set(),mats=new Set();mesh.traverse(o=>{if(o.geometry)geos.add(o.geometry);if(o.material)mats.add(o.material);});for(const g of geos)g.dispose();for(const m of mats)m.dispose();texture.dispose();};return e;
}
export function dangerMark(scene,position,radius=2){
 const root=new THREE.Group();root.position.copy(position);root.position.y=.09;scene.add(root);
 const points=Array.from({length:38},(_,i)=>{let a=i/37*Math.PI*2;return[Math.sin(a)*radius,0,Math.cos(a)*radius];});
 const outline=stroke(root,points,'#a64e4b',.045);outline.material.transparent=true;outline.material.opacity=.7;
 return{root,update(phase){root.scale.setScalar(.8+Math.min(1,phase)*.2);outline.material.opacity=.35+Math.min(1,phase)*.5;},dispose(){root.removeFromParent();outline.geometry.dispose();outline.material.dispose();}};
}
export function inkBolt(scene,position,direction,damage){
 const root=new THREE.Group();root.position.copy(position);root.position.y=.8;root.rotation.y=Math.atan2(direction.x,direction.z);const mesh=brushRibbon([[0,0,-.55],[.07,.03,-.28],[0,0,0],[.03,0,.45]],.13,'#6b465c');root.add(mesh);scene.add(root);return{root,direction:direction.clone(),damage,time:3.6,dispose(){root.removeFromParent();mesh.geometry.dispose();mesh.material.dispose();}};
}
