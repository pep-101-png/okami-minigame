import * as THREE from 'three';
import {paint} from '../art.js';
import {pigment,random,gardenWash} from './pigment.js';
import {batchDecoration} from '../town.js';
function stroke(root,points,color,radius=.03){const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),segments=24,radial=5,g=new THREE.TubeGeometry(curve,segments,radius,radial,false),a=g.attributes.position;for(let i=0;i<=segments;i++){const t=i/segments,c=curve.getPointAt(t),taper=.18+.82*Math.pow(1-t,.65);for(let j=0;j<=radial;j++){let k=i*(radial+1)+j;a.setXYZ(k,c.x+(a.getX(k)-c.x)*taper,c.y+(a.getY(k)-c.y)*taper,c.z+(a.getZ(k)-c.z)*taper);}}g.computeVertexNormals();const m=new THREE.Mesh(g,paint(color,'wood'));root.add(m);return m;}
const textures=new Map();
export function foliageTexture(kind='cherry'){
 if(textures.has(kind))return textures.get(kind);
 const c=document.createElement('canvas');c.width=512;c.height=384;const x=c.getContext('2d'),r=random(912+kind.length);
 const colours={cherry:['#f4c2c4','#f5d9d3','#e3a9ba','#fff3df'],maple:['#b5574b','#ce7e5c','#e3b881','#8e4f4a'],pine:['#4f766d','#7b9d83','#9bb299','#bac4a3'],bamboo:['#698c71','#8fa67c','#b1be90','#567e6b']};const colors=colours[kind]||colours.pine;
 // Translucent brush clusters with scattered individual petals/needles at their edges.
 for(let i=0;i<180;i++){let a=r()*Math.PI*2,rr=Math.sqrt(r()),px=256+Math.cos(a)*rr*228,py=192+Math.sin(a)*rr*144;
  x.globalAlpha=.10+r()*.18;x.fillStyle=colors[i%4];x.beginPath();x.ellipse(px,py,13+r()*33,7+r()*18,(r()-.5)*.9,0,7);x.fill();}
 x.globalAlpha=1;
 for(let i=0;i<430;i++){
  let a=r()*Math.PI*2,rr=Math.sqrt(r()),px=256+Math.cos(a)*rr*232,py=192+Math.sin(a)*rr*153;
  x.fillStyle=colors[i%4];x.strokeStyle='#68536940';x.lineWidth=.8;
  if(kind==='cherry'){let size=3+r()*5;x.beginPath();for(let j=0;j<5;j++){let b=j*6.283/5;x.ellipse(px+Math.cos(b)*size*.7,py+Math.sin(b)*size*.7,size*.65,size*.43,b,0,7);}x.fill();if(i%3===0)x.stroke();}
  else{const len=kind==='pine'?11:8;x.save();x.translate(px,py);x.rotate(r()*6);x.beginPath();x.moveTo(0,-len);x.quadraticCurveTo(5,0,0,len);x.quadraticCurveTo(-4,0,0,-len);x.fill();x.restore();}
 }
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;textures.set(kind,t);return t;
}
function crown(root,kind,seed=0,scale=1){
 const r=random(seed+61),g=new THREE.PlaneGeometry(2.8,1.8,4,2),p=g.attributes.position;
 for(let i=0;i<p.count;i++)p.setZ(i,Math.cos(p.getX(i)*1.4)*.16+Math.sin(p.getY(i)*2)*.10);g.computeVertexNormals();
 const mat=pigment(new THREE.MeshBasicMaterial({map:foliageTexture(kind),side:THREE.DoubleSide,transparent:true,alphaTest:.12,depthWrite:false,color:'#ffffff'}),'leaves');
 const count=kind==='pine'?20:22,leaves=new THREE.InstancedMesh(g,mat,count),dummy=new THREE.Object3D();leaves.userData.foliage=true;leaves.name=kind+' · layered pigment canopy';
 for(let i=0;i<count;i++){const a=i*2.399,rad=.3+Math.sqrt(i/count)*1.8;dummy.position.set(Math.sin(a)*rad,(kind==='pine'?4.5-i/count*2:3.6+Math.sin(i*2.3)*.48),Math.cos(a)*rad*.8);dummy.rotation.set(-.2-r()*.65,a*.5,Math.sin(a)*.13);dummy.scale.setScalar((.67+r()*.43)*scale);dummy.updateMatrix();leaves.setMatrixAt(i,dummy.matrix);}
 root.add(leaves);return leaves;
}
export function paintedTree(root,kind='cherry',seed=0){
 const branches=new THREE.Group();root.add(branches);branches.name='Calligraphic branching';branches.userData.windBranch=true;
 const palette=kind==='pine'?'#62756b':'#7b6963';
 stroke(branches,[[0,0,0],[.18,1.1,.05],[-.16,2.1,.06],[.32,3.0,.10],[.55,4.1,.03]],palette,.115);
 stroke(branches,[[.10,.25,.11],[.05,1.1,.15],[-.24,2.1,.17],[.18,3.2,.20]],'#b7b0a0',.025);
 for(let i=0;i<7;i++){const a=i*2.399,xx=Math.sin(a)*(1.2+i*.12),zz=Math.cos(a)*(1+i*.1);stroke(branches,[[0,1.6+i*.10,0],[xx*.35,2.4+i*.09,zz*.45],[xx,3.2+Math.sin(i)*.35,zz],[xx*1.2,3.4+Math.sin(i)*.35,zz*1.13]],palette,.04+(7-i)*.005);}
 batchDecoration(branches);crown(root,kind,seed);const shade=new THREE.Mesh(new THREE.PlaneGeometry(3.6,2.4),new THREE.MeshBasicMaterial({map:gardenWash(),transparent:true,opacity:.40,depthWrite:false,color:'#5b746d'}));shade.rotation.x=-Math.PI/2;shade.position.y=.012;root.add(shade);root.userData.paintedTree=true;return root;
}
export function grassMeadows(scene,world){
 const r=random(982),sh=new THREE.Shape();sh.moveTo(-.045,0);sh.bezierCurveTo(-.03,.20,.04,.38,.15,.48);sh.quadraticCurveTo(.06,.20,.045,0);sh.closePath();const geo=new THREE.ShapeGeometry(sh,5);
 const mat=paint('#759c7c','grass-blade');mat.side=THREE.DoubleSide;const positions=[];
 for(let i=0;i<1900;i++){
  const x=-46+r()*101,z=-31+r()*61;
  if(Math.abs(x+34)<5.5&&Math.abs(z-16)<5||Math.pow((x+15)/3.1,2)+Math.pow((z-22)/2.1,2)<1)continue;
  if(Math.abs(x)<5.0||Math.abs(z)<3.4||Math.hypot(x-35,z)<18.8||Math.abs(z-12)<3||Math.abs(z+14)<2.6||Math.abs(x+32)<2.8||Math.abs(x+23)<3.5||world.boxes.some(b=>Math.abs(x-b.x)<b.halfX+.5&&Math.abs(z-b.z)<b.halfZ+.5))continue;
  positions.push([x,z]);
 }
 const m=new THREE.InstancedMesh(geo,mat,positions.length),dummy=new THREE.Object3D();positions.forEach(([x,z],i)=>{dummy.position.set(x,.015,z);dummy.rotation.y=r()*6.28;dummy.scale.setScalar(.5+r()*.8);dummy.updateMatrix();m.setMatrixAt(i,dummy.matrix);});m.name='Instanced grass brush blades';scene.add(m);
 // Wildflowers use a shared transparent atlas with original painted petal forms.
 const tex=foliageTexture('cherry'),fm=pigment(new THREE.MeshBasicMaterial({map:tex,transparent:true,alphaTest:.15,side:THREE.DoubleSide,depthWrite:false,color:'#ffe5ce'}),'grass-blade'),flower=new THREE.InstancedMesh(new THREE.PlaneGeometry(.32,.20),fm,positions.length),d=new THREE.Object3D();positions.forEach(([x,z],i)=>{d.position.set(x+.1,.15,z);d.rotation.set(-.7,r()*6.28,0);d.updateMatrix();flower.setMatrixAt(i,d.matrix);});flower.name='Meadow petals';scene.add(flower);
 return positions.length;
}

export function driftingPetals(scene,trees){
 const shape=new THREE.Shape();shape.moveTo(0,-.05);shape.bezierCurveTo(-.07,-.02,-.05,.035,-.018,.05);shape.quadraticCurveTo(0,.025,.015,.05);shape.bezierCurveTo(.06,.035,.07,-.015,0,-.05);const g=new THREE.ShapeGeometry(shape,5),mat=new THREE.MeshBasicMaterial({color:'#efc5c4',side:THREE.DoubleSide,transparent:true,opacity:.8,depthWrite:false}),count=trees.length*4,m=new THREE.InstancedMesh(g,mat,count),d=new THREE.Object3D();m.name='Falling brush-painted cherry petals';m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);scene.add(m);
 return t=>{for(let i=0;i<count;i++){const tree=trees[Math.floor(i/4)],seed=i*2.399,phase=(t*.065+i*.173)%1;d.position.set(tree.position.x+Math.sin(seed)*1.7+Math.sin(t*.4+i)*.65,4.2-phase*4.0,tree.position.z+Math.cos(seed)*1.5+Math.sin(t*.23+i)*.4);d.rotation.set(t*.8+seed,t*.45+seed,t*.33+seed);d.scale.setScalar(.7+(i%4)*.14);d.updateMatrix();m.setMatrixAt(i,d.matrix);}m.instanceMatrix.needsUpdate=true;};
}
