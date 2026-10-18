import * as THREE from 'three';
import { paint,stroke } from '../art.js';
import { brushRibbon } from './painted-forms.js';
export const FLAME_ATTACKS=[null,
 {name:'I · EMBER ORBIT',duration:.36,hit:.42,active:[.28,.62],link:.65,cancel:.58,damage:1.4,range:2.65,arc:-1,lunge:1.5,movement:.38,knockback:.45,stagger:.35,hitStop:.04,sweep:true},
 {name:'II · CROWN OF FIRE',duration:.48,hit:.44,active:[.30,.63],link:.69,cancel:.65,damage:2.1,range:2.9,arc:-1,lunge:2,movement:.3,knockback:.8,stagger:.52,hitStop:.055,sweep:true},
 {name:'III · SOLAR REVOLUTION',duration:.66,hit:.48,active:[.36,.64],link:.8,cancel:.75,damage:3.8,range:3.35,arc:-1,lunge:2.4,movement:.18,knockback:1.5,stagger:.8,hitStop:.08,radial:true,heavy:true}];
export function createSundial(parent){
 const root=new THREE.Group();root.name='Sundial Flame';parent.add(root);const core=new THREE.Mesh(new THREE.CylinderGeometry(.55,.55,.11,40),paint('#b89454','stone'));root.add(core);core.rotation.x=Math.PI/2;
 for(const [radius,col,width]of[[.56,'#403f32',.03],[.44,'#e4bc65',.025],[.29,'#5a806e',.06]]){const o=new THREE.Mesh(new THREE.TorusGeometry(radius,width,5,48),paint(col));root.add(o);}
 for(let i=0;i<12;i++){let a=i*Math.PI/6;stroke(root,[[Math.sin(a)*.34,Math.cos(a)*.34,.08],[Math.sin(a)*.49,Math.cos(a)*.49,.08]],'#3d4c40',.014);}
 stroke(root,[[0,-.27,.10],[.05,.10,.12],[-.15,.29,.10]],'#f0d187',.025);
 const flames=[];
 for(let i=0;i<10;i++){
  const group=new THREE.Group();group.rotation.z=i*Math.PI/5;root.add(group);
  const points=Array.from({length:12},(_,j)=>{let t=j/11;return[.10*Math.sin(t*7+i*.8)*t,.48+t*(.55+(i%3)*.17),.03+Math.sin(t*4+i)*.025];});
  const outer=brushRibbon(points,.12,'#c74926');group.add(outer);const inner=brushRibbon(points.map(([x,y,z])=>[x,y,z+.02]),.065,'#f2b754');group.add(inner);flames.push(group);
 }
 root.rotation.x=-.5;root.scale.setScalar(.9);
 return{root,update(t,speed,attack=0){root.rotation.z=t*(attack?8:.22);root.position.x=Math.sin(attack*Math.PI*2)*.50;root.position.z=Math.sin(attack*Math.PI)*.75;root.rotation.y=Math.sin(t*1.4)*.06+attack*.5;for(let i=0;i<flames.length;i++){const f=flames[i];f.rotation.y=Math.sin(t*3-i*.8)*.15;f.scale.y=1+speed*.018+Math.sin(t*4-i)*.07+attack*.4;}}};
}
export function createAscension(player){
 const fur=[],spectral=[];const shoulderNames=['DEF_shoulder.L','DEF_shoulder.R'];const ankleNames=['DEF_front_paw.L','DEF_front_paw.R','DEF_rear_hock.L','DEF_rear_hock.R'];
 for(const[name,index]of[...shoulderNames,...ankleNames].map((n,i)=>[n,i])){
  const bone=(player.body.getObjectByName(name)||player.body.getObjectByName(name.replaceAll('.','')));if(!bone)continue;const g=new THREE.Group();g.scale.setScalar(1/.34);bone.add(g);player.body.updateMatrixWorld(true);const bq=bone.getWorldQuaternion(new THREE.Quaternion()),desired=player.body.getWorldQuaternion(new THREE.Quaternion());g.quaternion.copy(bq.invert().multiply(desired));const sign=name.endsWith('L')?1:-1;g.position.x=sign*.09;
  for(let layer=0;layer<3;layer++){
   const points=Array.from({length:18},(_,i)=>{let t=i/17;return[sign*(.02+Math.sin(t*5.5)*.12),t*(index<2?.85:.44),t*t*.38+layer*.035];});
   const m=brushRibbon(points,.10-layer*.02,layer%2?'#e0dbc7':'#f5ecda');m.rotation.z=sign*.22;g.add(m);fur.push({m,g,index,layer});
  }
 }
 let wind=0,lastTime=0;
 const halo=new THREE.Group();player.root.add(halo);
 for(let i=0;i<9;i++){const points=Array.from({length:20},(_,j)=>{let t=j/19;return[Math.sin(t*8+i)*(.10+t*.18),1.1+Math.cos(i*1.4)*.55+Math.sin(t*6+i)*.12,.15+t*(1.4+i*.08)];});const m=brushRibbon(points,.026+(i%3)*.012,i%3?'#eee9cf':'#94b6a0',.65);halo.add(m);spectral.push(m);}
 return{update(t,speed,power){const p=THREE.MathUtils.clamp((power-5)/45,0,1);wind=THREE.MathUtils.damp(wind,speed>5?1:speed>2?.22:0,7,Math.min(.05,Math.max(0,t-lastTime)));lastTime=t;for(const f of fur){f.g.visible=p>0;f.m.scale.set(.25+p*.75,.15+p*.85,.25+p*.75);f.m.rotation.x=Math.sin(t*2.3-f.layer*.65-f.index)*(.025+speed*.004);f.m.rotation.z=(f.index%2?-1:1)*(.18+Math.sin(t*1.8-f.layer)*.025);}
  halo.visible=p>0||wind>.01;for(let i=0;i<spectral.length;i++){const m=spectral[i];m.visible=i<Math.max(Math.ceil(p*9),wind>.02?3:0);m.scale.z=.35+wind*.85+p*.45;m.position.x=Math.sin(t*1.8-i*.5)*.10;m.rotation.z=Math.sin(t*1.3-i*.7)*.07;m.material.opacity=Math.min(.8,wind*.20+p*(.36+(i%3)*.13));}
 }};
}
