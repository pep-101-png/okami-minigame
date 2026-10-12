import * as THREE from 'three';
import {mat,part} from './models.js';
export function createWorld(scene){
 scene.background=new THREE.Color('#adc5c6');scene.fog=new THREE.Fog('#adc5c6',22,65);
 scene.add(new THREE.HemisphereLight('#fff3d5','#445b69',2));const sun=new THREE.DirectionalLight('#ffe8bd',3);sun.position.set(-12,23,-8);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-23,right:23,top:23,bottom:-23});scene.add(sun);
 const earth=mat('#8a9b84'),stone=mat('#9ba9a2'),red=mat('#9f3c32'),wood=mat('#3d4440');
 part(scene,new THREE.CylinderGeometry(18,19,1,64),earth,[0,-.55,0]);part(scene,new THREE.CylinderGeometry(12,12,.08,64),mat('#c6c8af'),[0,-.02,0]);
 for(let i=0;i<36;i++){const a=i*Math.PI/18;part(scene,new THREE.BoxGeometry(1.8,.12,.65),stone,[Math.sin(a)*12,.02,Math.cos(a)*12],[0,a,0]);}
 const obstacles=[];
 function torii(x,z,scale=1){const g=new THREE.Group();g.position.set(x,0,z);g.scale.setScalar(scale);scene.add(g);for(const s of [-1,1]){part(g,new THREE.CylinderGeometry(.19,.25,4.5,8),red,[s*2,2.25,0]);part(g,new THREE.BoxGeometry(.65,.3,.65),wood,[s*2,.15,0]);obstacles.push({x:x+s*2*scale,z,r:.35*scale});}part(g,new THREE.BoxGeometry(5.8,.32,.48),wood,[0,4.65,0]);part(g,new THREE.BoxGeometry(5.2,.3,.32),red,[0,4.3,0]);part(g,new THREE.BoxGeometry(4.8,.2,.25),red,[0,3.55,0]);part(g,new THREE.BoxGeometry(.42,.75,.28),mat('#c5a15e'),[0,3.95,0]);}
 torii(0,-14);torii(-14,1,.8);
 for(const [x,z] of [[-9,-8],[10,-6],[-11,8],[11,9]]){obstacles.push({x,z,r:.8});part(scene,new THREE.CylinderGeometry(.18,.45,3,7),wood,[x,1.5,z]);for(let j=0;j<5;j++){part(scene,new THREE.IcosahedronGeometry(1.6,1),mat(j%2?'#d7a2aa':'#e8bbc1'),[x+Math.sin(j*2)*1.1,3.4+(j%2)*.5,z+Math.cos(j*2)]).scale.set(1,.6,1);} }
 for(const [x,z] of [[-6,-11],[6,-11],[-8,5],[8,5]]){part(scene,new THREE.BoxGeometry(.65,.25,.65),stone,[x,.12,z]);part(scene,new THREE.CylinderGeometry(.14,.2,1.2,6),stone,[x,.8,z]);part(scene,new THREE.BoxGeometry(.6,.65,.6),mat('#edcf8f'),[x,1.65,z]);part(scene,new THREE.ConeGeometry(.65,.4,4),wood,[x,2.15,z],[0,Math.PI/4,0]);}
 for(let i=0;i<20;i++){const a=i*2.4;part(scene,new THREE.ConeGeometry(5+(i%3),10+(i%4)*3,5),mat('#738f91'),[Math.sin(a)*40,3,Math.cos(a)*40]);}
 const petals=new THREE.Group();scene.add(petals);for(let i=0;i<90;i++)part(petals,new THREE.PlaneGeometry(.13,.08),new THREE.MeshBasicMaterial({color:'#f5ccd1',side:THREE.DoubleSide}),[(Math.random()-.5)*34,Math.random()*8,(Math.random()-.5)*34],[Math.random()*3,0,Math.random()*3]);
 return {obstacles,petals};
}
