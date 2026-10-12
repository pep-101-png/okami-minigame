import * as THREE from 'three';
export const mat=(color)=>new THREE.MeshStandardMaterial({color,roughness:.85});
export function part(parent,geo,material,pos=[0,0,0],rot=[0,0,0]){const m=new THREE.Mesh(geo,material);m.position.set(...pos);m.rotation.set(...rot);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;}
export function wolf(){
 const root=new THREE.Group(),body=new THREE.Group();root.add(body);const white=mat('#eee9d9'),red=mat('#b83135'),black=mat('#24343a'),gold=mat('#bba067');
 part(body,new THREE.SphereGeometry(1,12,8),white,[0,.95,0]).scale.set(.42,.47,.9);
 part(body,new THREE.SphereGeometry(.45,12,8),white,[0,1.35,-.68]).scale.set(.8,1.1,1);
 part(body,new THREE.BoxGeometry(.42,.26,.55),white,[0,1.25,-1.05]);part(body,new THREE.BoxGeometry(.32,.16,.16),black,[0,1.28,-1.36]);
 for(const s of [-1,1]){part(body,new THREE.ConeGeometry(.18,.47,4),white,[s*.24,1.87,-.65],[0,0,s*-.18]);part(body,new THREE.ConeGeometry(.095,.28,3),red,[s*.24,1.88,-.70]);part(body,new THREE.SphereGeometry(.055,8,6),black,[s*.32,1.48,-.93]);part(body,new THREE.BoxGeometry(.035,.12,.38),red,[s*.355,1.32,-.78],[0,0,s*.3]);part(body,new THREE.BoxGeometry(.045,.35,.55),red,[s*.405,1.07,.05],[.25,0,0]);}
 const legs=[];for(const x of [-.29,.29])for(const z of [-.52,.56]){const leg=new THREE.Group();leg.position.set(x,.8,z);body.add(leg);part(leg,new THREE.CylinderGeometry(.1,.075,.65,6),white,[0,-.30,0]);part(leg,new THREE.BoxGeometry(.19,.14,.28),white,[0,-.66,-.05]);part(leg,new THREE.CylinderGeometry(.105,.105,.11,6),red,[0,-.46,0]);legs.push(leg);}
 const tail=part(body,new THREE.ConeGeometry(.22,.9,7),white,[0,1.2,.98],[.85,0,0]);
 const spear=new THREE.Group();spear.position.set(0,1.2,-1.25);body.add(spear);
 // Side handle crosses the mouth along X; the long shaft points forward along -Z.
 part(spear,new THREE.CylinderGeometry(.045,.045,2.7,8),mat('#654937'),[.42,0,-.55],[Math.PI/2,0,0]);
 part(spear,new THREE.CylinderGeometry(.055,.055,.85,8),black,[.04,0,.15],[0,0,Math.PI/2]);
 part(spear,new THREE.ConeGeometry(.16,.65,4),mat('#d1dce0'),[.42,0,-2.22],[-Math.PI/2,0,0]);
 part(spear,new THREE.TorusGeometry(.10,.025,5,12),gold,[.42,0,-1.77]);
 return {root,body,legs,tail,spear};
}
export function demon(){const root=new THREE.Group(),m=mat('#3b5362'),red=mat('#ff8864');part(root,new THREE.IcosahedronGeometry(.62,1),m,[0,.8,0]).scale.set(1,1.2,.85);part(root,new THREE.BoxGeometry(.72,.45,.18),mat('#d6cbb2'),[0,1.18,-.49]);for(const s of [-1,1]){part(root,new THREE.ConeGeometry(.12,.45,5),red,[s*.28,1.65,0],[0,0,s*-.3]);part(root,new THREE.BoxGeometry(.16,.055,.07),red,[s*.19,1.24,-.60]);part(root,new THREE.CylinderGeometry(.12,.15,.4,5),m,[s*.3,.24,0]);}return root;}
