import * as THREE from 'three';
import { form,floralMap,inscription } from './painted-forms.js';
import { batchFixedParts } from '../models.js';
import { paint,stroke } from '../art.js';
export function createVillager(scene,x,z,name,color,lines,route=null){
 const root=new THREE.Group();root.position.set(x,0,z);root.name=name;scene.add(root);const body=new THREE.Group();body.position.y=.88;root.add(body);
 const robe=form(body,[[-.78,.31,.23],[-.70,.37,.27],[-.30,.30,.22],[.05,.23,.18],[.30,.25,.18],[.53,.31,.18],[.64,.23,.15],[.68,.08,.08]],color);robe.material.map=floralMap(color);
 const obi=form(body,[[.05,.245,.19],[.10,.255,.20],[.27,.255,.20],[.30,.23,.18]],'#b99c53');
 stroke(body,[[-.22,.62,.13],[-.09,.39,.195],[.10,.20,.20]],'#f7e6c7',.023);stroke(body,[[.22,.60,.12],[.02,.28,.20],[-.08,.08,.205]],'#f7e6c7',.018);
 form(body,[[.62,.065,.06],[.78,.063,.06]],'#edcfb3');
 const head=new THREE.Group();head.position.set(0,.94,0);body.add(head);
 const face=form(head,[[-.22,.035,.04],[-.18,.10,.09],[-.09,.15,.13],[.03,.16,.135],[.15,.145,.12],[.22,.09,.07],[.24,0,0]],'#f0d6be');
 const canvas=document.createElement('canvas');canvas.width=512;canvas.height=256;const c=canvas.getContext('2d');c.clearRect(0,0,512,256);c.strokeStyle='#3a2d30';c.lineWidth=5;
 for(const sign of [-1,1]){let xx=256+sign*97;c.beginPath();c.moveTo(xx-34,109);c.quadraticCurveTo(xx,91,xx+34,108);c.stroke();c.lineWidth=2;c.beginPath();c.moveTo(xx-34,82);c.quadraticCurveTo(xx,67,xx+29,79);c.stroke();c.lineWidth=5;}
 c.strokeStyle='#b85d60';c.lineWidth=5;c.beginPath();c.moveTo(229,179);c.quadraticCurveTo(256,193,283,179);c.stroke();
 for(const x0 of [117,395]){const g=c.createRadialGradient(x0,151,2,x0,151,35);g.addColorStop(0,'#c777644c');g.addColorStop(1,'#c7776400');c.fillStyle=g;c.fillRect(x0-36,115,72,72);}
 const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;const features=new THREE.Mesh(new THREE.PlaneGeometry(.32,.26),new THREE.MeshBasicMaterial({map:tex,transparent:true,depthWrite:false}));features.position.set(0,-.025,.136);head.add(features);
 form(head,[[.07,.17,.137],[.14,.18,.14],[.22,.15,.12],[.26,.06,.07],[.27,0,0]],'#302b30');
 const bun=form(head,[[.18,.10,.09],[.28,.13,.12],[.38,.09,.09],[.40,0,0]],'#29262b',{position:[0,0,-.06]});
 for(let i=0;i<4;i++)stroke(head,[[-.12+i*.07,.23,-.015],[-.09+i*.05,.32,-.10],[.04,.35,-.14]],'#6a5d58',.005);
 stroke(head,[[-.22,.24,-.04],[.23,.34,-.04]],'#c6a765',.012);
 for(let i=0;i<3;i++)form(head,[[-.03,0,0],[0,.027,.025],[.045,0,0]],i%2?'#ecd3bb':'#c66c78',{sides:10,position:[.18+i*.018,.29-i*.05,.015]});
 const arms=[],legs=[];
 for(const sign of [-1,1]){
  const arm=new THREE.Group();arm.position.set(sign*.25,.53,0);arm.rotation.z=sign*.15;body.add(arm);
  const sleeve=form(arm,[[.06,.10,.10],[-.08,.14,.13],[-.28,.17,.15],[-.56,.20,.13],[-.61,.14,.11]],color);sleeve.material.map=robe.material.map;
  form(arm,[[-.58,.055,.045],[-.70,.042,.035],[-.73,.01,.02]],'#edd0b1',{position:[sign*.04,0,.025]});arms.push(arm);
  const leg=new THREE.Group();leg.position.set(sign*.13,.36,0);root.add(leg);form(leg,[[-.29,.05,.05],[-.02,.06,.05]],'#e6d5ba');const shoe=form(leg,[[-.35,.08,.15],[-.29,.09,.16],[-.27,.06,.11]],'#69513f',{position:[0,0,.04]});legs.push(leg);
 }
 batchFixedParts(root);
 const tag=inscription(name,2.7,.43);tag.position.y=2.42;root.add(tag);
 return{root,name,lines,route,index:0,home:new THREE.Vector3(x,0,z),body,head,arms,legs,tag,phase:x,walking:false};
}
