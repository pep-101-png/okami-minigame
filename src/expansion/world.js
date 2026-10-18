import * as THREE from 'three';
import { house,roof,lantern,garden,batchHouse,batchDecoration } from '../town.js';
import { blossomTexture } from '../world.js';
import { part } from '../models.js';
import { paint,stroke,paintedTexture } from '../art.js';
import { inscription,brushRibbon } from './painted-forms.js';
import { createVillager } from './villagers.js';
function block(p,size,col,pos,kind='wood'){return part(p,new THREE.BoxGeometry(...size),paint(col,kind),pos,undefined,false);}
export function expandVillage(scene,world){
 scene.background=new THREE.Color('#d2d4bd');scene.fog=new THREE.Fog('#d2d4bd',52,145);
 world.bounds={minX:-48,maxX:57,minZ:-33,maxZ:32};world.arena={center:new THREE.Vector3(35,0,0),radius:18};
 for(const tree of world.trees||[]){const old=tree.position.clone(),d=tree.position.clone().sub(world.arena.center);d.y=0;if(d.length()<17){d.setLength(20);tree.position.x=35+d.x;tree.position.z=d.z;const obstacle=world.obstacles.find(o=>Math.abs(o.x-old.x)<.01&&Math.abs(o.z-old.z)<.01);if(obstacle){obstacle.x=tree.position.x;obstacle.z=tree.position.z;}}}
 const town=new THREE.Group();town.name='Westbank · expanded village';scene.add(town);
 const path=part(town,new THREE.PlaneGeometry(35,4.2),paint('#c8b282','stone'),[-27,.055,12],[-Math.PI/2,0,0],false);
 part(town,new THREE.PlaneGeometry(4.2,43),paint('#c8b282','stone'),[-32,.055,-3],[-Math.PI/2,0,0],false);
 const homes=[[-41,-12,6,5,'#777f6c'],[-32,-24,7,5,'#b57550'],[-43,0,5,6,'#9e705b'],[-41,27,6,5,'#8c8b6e'],[-27,-8,5,4,'#a27750']];
 for(const[x,z,w,d,c]of homes){const h=house(scene,x,z,w,d,c,0,(z===-24));batchHouse(h);world.houses.push(h);world.boxes.push({x,z,halfX:w/2+.2,halfZ:d/2+.2});garden(scene,x+3,z+4,Math.round(x*z+900));}
 // Bridges remain part of this continuous world, with flat accessible decks.
 for(const z of[12,-14]){
  block(town,[8,.10,3.2],'#a57b52',[-23,.065,z]);for(let i=0;i<14;i++)stroke(town,[[-27+i*.58,.125,z-1.5],[-27+i*.58,.125,z+1.5]],'#5f5140',.012);
  for(const s of[-1,1])for(let i=0;i<5;i++){let x=-26.8+i*1.9;block(town,[.11,.72,.11],'#914a36',[x,.42,z+s*1.6]);if(i<4)stroke(town,[[x,.75,z+s*1.6],[x+.95,.87,z+s*1.6],[x+1.9,.75,z+s*1.6]],'#a65a40',.045);}
 }
 // A home with real openings and separate collision walls, not a solid house box.
 const home=new THREE.Group();home.position.set(-34,0,16);home.name='Amaterasu · home';scene.add(home);
 block(home,[10,.10,8],'#ac855b',[0,.01,0]);
 const walls=[];
 for(const [size,pos]of[[[.15,3.2,8],[-5,1.6,0]],[[.15,3.2,8],[5,1.6,0]],[[10,3.2,.15],[0,1.6,-4]],[[3.5,3.2,.15],[-3.25,1.6,4]],[[3.5,3.2,.15],[3.25,1.6,4]]]){
  const wall=block(home,size,'#e2caa5',pos,'shoji');wall.traverse(o=>{if(o.material)o.material=o.material.clone();});walls.push(wall);world.boxes.push({x:-34+pos[0],z:16+pos[2],halfX:size[0]/2,halfZ:size[2]/2});
 }
 for(const x of[-4.9,0,4.9])for(const z of[-3.9,3.9]){if(x===0&&z>0)continue;block(home,[.16,3.6,.16],'#6d4d37',[x,1.8,z]);}
 // Timber framing and paper lattice define the open facade and inner alcove.
 for(const x of[-4.92,-1.55,1.55,4.92])block(home,[.13,3.3,.16],'#76563b',[x,1.65,4.06]);
 for(const y of[.35,2.85])for(const x of[-3.25,3.25])block(home,[3.4,.10,.18],'#8c6947',[x,y,4.08]);
 for(const cx of[-3.25,3.25])for(let i=-2;i<=2;i++)block(home,[.025,1.3,.04],'#a58a63',[cx+i*.36,1.68,4.10]);
 const roofGroup=new THREE.Group();home.add(roofGroup);roof(roofGroup,11.2,9,3.35,'#607963',1.15);
 const roofMaterials=new Set();roofGroup.traverse(o=>{if(o.material){o.material=o.material.clone();roofMaterials.add(o.material);}});
 for(const[x,z]of[[-2.5,-1],[.5,-1],[-2.5,1],[.5,1]]){const m=block(home,[2.8,.05,1.8],'#a9aa79',[x,.09,z],'grass');for(const side of[-1,1])block(home,[.04,.012,1.8],'#58684b',[x+side*1.37,.12,z]);}
 // Open front, warm furnishings and legible progression/equipment alcoves.
 const rest=part(home,new THREE.CylinderGeometry(.85,.85,.08,40),paint('#ac7b78'),[-2,.12,-2.6],undefined,false);rest.scale.z=.65;
 for(const[x,z]of[[-4,-2.8],[4,-2.8]]){const l=lantern(home,x,z);l.scale.setScalar(.7);}
 const scroll=inscription('REST · RISE · RETURN',4,.65);scroll.position.set(0,2.3,-3.82);home.add(scroll);
 for(const x of[2.8,3.8]){block(home,[.08,1.4,.08],'#614936',[x,.7,-2]);block(home,[1.25,.07,.26],'#a37d50',[3.3,.7,-2]);}
 const homeSign=inscription('AMATERASU’S HOME',4.2,.65);homeSign.position.set(-34,3.1,20.1);scene.add(homeSign);
 for(const[x,z]of[[-29,11],[-39,11],[-32,-16],[-42,18],[-17,11],[-17,-15]]){lantern(scene,x,z);world.obstacles.push({x,z,r:.27});}
 for(let i=0;i<10;i++){let x=-45+(i%3)*2,z=-26+Math.floor(i/3)*2.4;for(let j=0;j<4;j++){const y=.05+j*.65;part(town,new THREE.CylinderGeometry(.045,.06,.66,8),paint('#57765d'),[x,y+.33,z],undefined,false);stroke(town,[[x,y+.5,z],[x+.4,y+.7,z+.05]],'#4b634a',.013);}stroke(town,[[x,.7,z],[x-.6,1.15,z],[x-.9,1.18,z]],'#789258',.04);}
 for(const[x,z]of[[-43,12],[-37,-17],[-28,24],[-45,-25]])garden(scene,x,z,Math.abs(x*z));
 const canopy=blossomTexture();
 for(const [x,z]of[[-43,17],[-27,25],[-39,-18],[-29,-18],[-44,-25],[-15,24]]){
  const tree=new THREE.Group();tree.position.set(x,0,z);scene.add(tree);stroke(tree,[[0,0,0],[.12,1.3,.04],[-.08,2.6,.1],[.22,3.6,.16]],'#625448',.14);
  for(let i=0;i<5;i++){let a=i*2.4;const point=[Math.sin(a)*1.65,3.1+i*.17,Math.cos(a)*1.3];stroke(tree,[[0,1.8,0],[point[0]*.6,2.7,point[2]*.6],point],'#625448',.065);const s=new THREE.Sprite(new THREE.SpriteMaterial({map:canopy,transparent:true,depthWrite:false}));s.position.set(...point);s.scale.set(3.2,2.3,1);tree.add(s);}world.obstacles.push({x,z,r:.4});world.trees.push(tree);
 }
 const banners=[];
 for(let i=0;i<9;i++){const g=new THREE.Group();g.position.set(-31+i*3.5,3.6,7);town.add(g);const m=brushRibbon([[0,0,0],[.1,-.2,.01],[0,-.6,.1],[.08,-.95,.14]],.23,i%2?'#a55b5a':'#637f74');g.add(m);banners.push(g);}
 world.npcs.push(createVillager(scene,-31,8,'Akari · shrine musician','#94719a',['The westbank bridges lead home. Rest there after each trial.','Your spirit keeps every earned coin, even after defeat.']),createVillager(scene,-38,-10,'Mio · lantern keeper','#568790',['The Hollow Bell awakens beyond three waves.','Jump its ground shock, dodge its charge, and watch for ink bolts.']),createVillager(scene,-31,22,'Ren · pilgrim','#ab7860',['A guardian’s strength is remembered in ink.','Your shoulder and ankle fur will blossom with permanent power.']));
 const arenaFloor=part(scene,new THREE.CircleGeometry(18.4,96),paint('#c9b17e','stone'),[35,.052,0],[-Math.PI/2,0,0],false);arenaFloor.material.map=paintedTexture('stone').clone();arenaFloor.material.map.repeat.set(5,5);
 for(let i=0;i<16;i++){let a=i/16*Math.PI*2;stroke(scene,[[35+17.4*Math.sin(a),.07,17.4*Math.cos(a)],[35+17.4*Math.sin(a+.22),.07,17.4*Math.cos(a+.22)]],'#736956',.035);}
 for(const [x,z]of[[26,-15],[44,-15],[50,10],[30,16]]){
  const gate=new THREE.Group();gate.position.set(x,0,z);scene.add(gate);
  for(const sign of[-1,1])part(gate,new THREE.CylinderGeometry(.14,.23,3,12),paint('#9b5946','wood'),[sign*.85,1.5,0]);
  stroke(gate,[[-1.5,3.4,0],[-.8,3.2,0],[.8,3.2,0],[1.5,3.4,0]],'#4e4a40',.12);
 }
 const sign=inscription('E · ENTER THE HOLLOW BELL TRIAL',4.5,.58);sign.position.set(12.3,2.8,0);scene.add(sign);
 const shop=inscription('TARO · WEAPONS & BLESSINGS',4,.55);shop.position.set(4.8,2.75,0);scene.add(shop);
 // Batch only the new static district. Home roof stays independent for interior visibility.
 batchDecoration(town);
 const water=[];scene.traverse(o=>{if(o.isMesh&&o.material?.color?.getHexString()==='56b3b3'){o.material=o.material.clone();if(o.material.map)o.material.map=o.material.map.clone();water.push(o);}});
 const oldUpdate=world.update;
 world.update=(dt,t)=>{oldUpdate(dt,t);const inside=world.player&&Math.abs(world.player.position.x+34)<5.6&&Math.abs(world.player.position.z-16)<5;
  scroll.visible=!!inside;homeSign.visible=!inside;
  if(world.player&&world.camera){const p=world.player.position,c=world.camera.position,dx=c.x-p.x,dz=c.z-p.z,l2=dx*dx+dz*dz;
   for(const tree of world.trees){const v=tree.position.clone().sub(p),u=(v.x*dx+v.z*dz)/(l2||1),side=Math.abs(v.x*dz-v.z*dx)/Math.sqrt(l2||1),occludes=u>0&&u<1.05&&side<2.7;
    for(const child of tree.children)if(child.isSprite)child.material.opacity=THREE.MathUtils.damp(child.material.opacity,occludes?.10:1,8,dt);
   }
  }
  for(const wall of walls){wall.visible=!inside||wall.position.z<0;wall.traverse(o=>{if(o.material){o.material.transparent=false;o.material.opacity=1;o.material.depthWrite=true;}});}
  for(const m of roofMaterials){m.transparent=true;m.opacity=THREE.MathUtils.damp(m.opacity,inside?.07:1,7,dt);m.depthWrite=m.opacity>.95;}
  for(let i=0;i<banners.length;i++)banners[i].rotation.x=Math.sin(t*1.3+i*.5)*.10;
  for(const o of water)if(o.material.map)o.material.map.offset.y=t*.018;
 };
 return{home,rest:new THREE.Vector3(-36,0,13.5),altar:new THREE.Vector3(-30.8,0,14),shop:new THREE.Vector3(3,0,-2),portal:new THREE.Vector3(12.8,0,0),homeSpawn:new THREE.Vector3(-34,0,22)};
}
export class BattleBarrier{
 constructor(scene,arena){this.root=new THREE.Group();this.root.position.copy(arena.center);scene.add(this.root);this.amount=0;this.target=0;this.strips=[];
  for(let i=0;i<42;i++){const a=i/42*Math.PI*2,g=new THREE.Group();g.position.set(Math.sin(a)*arena.radius,0,Math.cos(a)*arena.radius);g.rotation.y=a;g.userData.angle=a;this.root.add(g);let pts=Array.from({length:15},(_,j)=>{let t=j/14;return[Math.sin(t*9+i)*(.1+t*.22),t*(5.8+(i%4)*.4),Math.sin(t*6+i)*.16];});let m=brushRibbon(pts,.45,i%3?'#3c3948':'#a76d76',.7);g.add(m);this.strips.push(g);}
 }
 update(dt,t,yaw=0){this.amount=THREE.MathUtils.damp(this.amount,this.target,3,dt);this.root.visible=this.amount>.005;for(let i=0;i<this.strips.length;i++){let g=this.strips[i];g.scale.y=this.amount*(1+Math.sin(t*1.8-i*.4)*.07);g.rotation.z=Math.sin(t*1.4+i)*.08;g.children[0].material.opacity=this.amount*.78*(Math.cos(g.userData.angle-yaw)>.35?.12:1);}}
}
