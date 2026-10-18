import{timberGeometry}from'./joinery.js';
import * as THREE from 'three';
import {paint,outline} from '../art.js';
// Thin architectural ink curves need a fraction of the tessellation of body ribbons.
function stroke(root,points,color,radius=.025){const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));const g=new THREE.TubeGeometry(curve,Math.min(24,Math.max(8,points.length*2)),radius,3,false);const m=new THREE.Mesh(g,paint(color));root.add(m);return m;}
const materials=new Map();
function material(c,k){const key=c+k;if(!materials.has(key))materials.set(key,paint(c,k));return materials.get(key);}
function beam(root,size,pos,color='#73594b',kind='wood',rot=[0,0,0]){const m=new THREE.Mesh(timberGeometry(size),material(color,kind));m.position.set(...pos);m.rotation.set(...rot);m.castShadow=true;m.receiveShadow=true;root.add(m);return m;}
export function paintedRoof(root,w,d,y,color,height=1.1){
 if(height>.7)height*=1.4;
 // Sweeping hipped roof: the corners kick upward, while the eave belly dips.
 const slate=['#617b80','#6e777f','#776f7d','#6c827e'];const tint=slate[Math.abs(Math.round(w*11+d*7))%slate.length];
 const rise=(x,z)=>{let t=Math.min(1,Math.max(Math.abs(x)/(w/2),Math.max(0,(Math.abs(z)/(d/2)-.48)/.52)));return y+height*Math.pow(1-t,1.25)+.47*Math.pow(t,6)+.17*Math.pow(Math.abs(x*z)/(w*d*.25),3);};
 const g=new THREE.PlaneGeometry(w,d,24,20),a=g.attributes.position;
 for(let i=0;i<a.count;i++){const x=a.getX(i),z=a.getY(i);a.setXYZ(i,x,rise(x,z),z);}g.computeVertexNormals();
 const m=new THREE.Mesh(g,material(tint,'roof'));m.material.side=THREE.DoubleSide;m.castShadow=true;m.receiveShadow=true;root.add(m);
 const perimeter=[];for(let side=0;side<4;side++)for(let i=0;i<=12;i++){let t=i/12,x,z;if(side===0){x=-w/2+t*w;z=-d/2;}if(side===1){x=w/2;z=-d/2+t*d;}if(side===2){x=w/2-t*w;z=d/2;}if(side===3){x=-w/2;z=d/2-t*d;}perimeter.push([x,rise(x,z)-.035,z]);}
 stroke(root,perimeter,'#414f53',.085);stroke(root,perimeter.map(p=>[p[0],p[1]-.13,p[2]]),'#a19a85',.055);
 // Raised clay tile ribs follow the roof's actual curved slope; one mesh per tint.
 for(let tone=0;tone<3;tone++){const verts=[],uv=[],indices=[];for(let side of[-1,1])for(let row=0;row<Math.ceil(d/.40);row++){if(row%3!==tone)continue;const z=-d/2+.19+row*.40,base=verts.length/3;for(let j=0;j<=12;j++)for(let k=0;k<=4;k++){const xx=side*(.02+j/12*(w/2-.07)),a=k/4*Math.PI,zz=z+Math.cos(a)*.075;verts.push(xx,rise(xx,zz)+.025+Math.sin(a)*.035,zz);uv.push(j/12,k/4);if(j<12&&k<4){let n=base+j*5+k;indices.push(n,n+5,n+1,n+1,n+5,n+6);}}}const geom=new THREE.BufferGeometry();geom.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));geom.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geom.setIndex(indices);geom.computeVertexNormals();const capMat=material(['#758d8b','#5b767c','#889b94'][tone],'roof');capMat.side=THREE.DoubleSide;root.add(new THREE.Mesh(geom,capMat));}
 for(const sign of[-1,1]){const pts=Array.from({length:18},(_,i)=>{const z=-d/2+i/17*d;return[0,rise(0,z)+.065,z];});stroke(root,pts,'#405456',.07);break;}
 for(const z of[-d*.28,d*.28])stroke(root,[[-.38,y+height+.03,z],[-.16,y+height+.15,z],[.13,y+height+.15,z],[.4,y+height+.02,z]],'#a7b1a0',.04);
 return m;
}
const scrolls=new Map();
function wallScroll(seed){
 if(scrolls.has(seed))return scrolls.get(seed);
 const c=document.createElement('canvas');c.width=256;c.height=384;const x=c.getContext('2d');
 x.fillStyle='#ece6d5';x.fillRect(0,0,256,384);x.strokeStyle='#9c8871';x.lineWidth=8;x.strokeRect(3,3,250,378);
 for(let i=0;i<6;i++){let px=35+i*38,top=80+Math.sin(i*3+seed)*35;x.fillStyle=['#94aaa180','#b0bbae70','#687f7a75'][i%3];x.beginPath();x.moveTo(px-40,295);x.bezierCurveTo(px-12,180,px-20,top,px,top);x.bezierCurveTo(px+20,top,px+8,190,px+40,295);x.fill();}
 x.strokeStyle='#56675d';x.lineWidth=3;for(let i=0;i<3;i++){const px=40+i*22;x.beginPath();x.moveTo(px,310);x.bezierCurveTo(px+7,230,px-5,190,px+6,160);x.stroke();for(let j=0;j<5;j++){let yy=180+j*23;x.beginPath();x.moveTo(px,yy);x.quadraticCurveTo(px+20,yy-22,px+28,yy-17);x.moveTo(px,yy);x.quadraticCurveTo(px-10,yy-15,px-23,yy-11);x.stroke();}}
 x.fillStyle='#ae6352';x.fillRect(198,298,17,21);x.strokeStyle='#e8d5b4';x.lineWidth=1;x.strokeRect(201,301,11,15);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;scrolls.set(seed,t);return t;
}
export function enrichHouse(root,w,d,h,role='home'){
 root.userData.architecture={w,d,h,role};
 const scroll=new THREE.Mesh(new THREE.PlaneGeometry(.73,1.13),new THREE.MeshBasicMaterial({map:wallScroll(Math.round(w+d))}));scroll.position.set(w/2+.105,1.45,-d*.32);scroll.rotation.y=Math.PI/2;root.add(scroll);
 // An articulated stone plinth, deep veranda and exposed rafters break the box silhouette.
 for(let i=0;i<Math.ceil(w/1.1);i++)beam(root,[1.02,.28,.32],[-w/2+.5+i*1.08,.15,d/2+.06],i%2?'#85948c':'#9daba0','stone');
 beam(root,[w+.7,.15,1.15],[0,.15,d/2+.3],'#a78c70');
 for(let i=0;i<Math.ceil(w/.45);i++)beam(root,[.018,.015,1.08],[-w/2+i*.45,.235,d/2+.3],'#6d6959');
 beam(root,[1.5,.09,.6],[0,.07,d/2+1.05],'#a8ada0','stone');
 for(let i=0;i<Math.ceil(w/.48);i++)beam(root,[.07,.1,.58],[-w/2+i*.48,h+.03,d/2+.17],'#6c6254','wood',[.13,0,0]);
 for(const s of[-1,1]){
  beam(root,[.16,h+.12,.18],[s*(w/2-.15),h/2+.18,d/2+.2],'#675c4c');
  beam(root,[.12,.8,.12],[s*(w/2-.36),h-.20,d/2+.18],'#82715c','wood',[0,0,-s*.62]);
  for(let j=0;j<8;j++)beam(root,[.025,.85,.06],[s*w*.31-.35+j*.1,1.46,d/2+.19],'#776e5a');
 }
 // Shoji door rails, plaster frieze and asymmetric timber shutters.
 beam(root,[w-.5,.18,.12],[0,h-.2,d/2+.13],'#eee5d2','wash');
 for(const x of[-.51,.51])beam(root,[.065,1.95,.12],[x,1.15,d/2+.15],'#786451');
 const canopy=new THREE.Group();canopy.position.set(0,0,d/2+.38);root.add(canopy);paintedRoof(canopy,w*.65,1.25,2.12,'#648582',.35);
 for(const s of[-1,1]){
  const l=new THREE.Group();l.position.set(s*w*.40,1.77,d/2+.35);root.add(l);
  const g=new THREE.SphereGeometry(.20,12,12);g.scale(.92,1.45,.85);const paper=new THREE.Mesh(g,material('#f4dcaf','wash'));l.add(paper);
  for(let i=0;i<6;i++){let yy=(i/5-.5)*.47,rr=.20*Math.sqrt(Math.max(.05,1-(yy/.29)**2));const ring=new THREE.Mesh(new THREE.TorusGeometry(rr,.007,3,14),material('#9a7961','wood'));ring.rotation.x=Math.PI/2;ring.position.y=yy;l.add(ring);}
  beam(l,[.17,.04,.17],[0,.30,0],'#696151');beam(l,[.015,.2,.02],[0,.42,0],'#615f55');
 }
 if(role==='shrine'){
  for(const sign of[-1,1])beam(root,[.18,2.7,.18],[sign*w*.30,1.45,d/2+.75],'#ad554b');
  stroke(root,[[-w*.36,2.52,d/2+.78],[0,2.27,d/2+.86],[w*.36,2.52,d/2+.78]],'#c4ab74',.045);
  for(const x of[-1.2,-.4,.4,1.2]){const sh=new THREE.Shape();sh.moveTo(-.1,0);sh.lineTo(.11,0);sh.lineTo(.02,-.15);sh.lineTo(.13,-.21);sh.lineTo(-.05,-.38);sh.lineTo(-.14,-.21);const paper=new THREE.Mesh(new THREE.ShapeGeometry(sh),material('#f3eedb','wash'));paper.position.set(x,2.3,d/2+.87);root.add(paper);}
 }
}
export function enrichHome(home){
 const veranda=new THREE.Group();veranda.position.z=4.3;home.add(veranda);
 beam(veranda,[10.6,.12,1.25],[0,.1,0],'#ac957b');
 for(let i=0;i<23;i++)beam(veranda,[.018,.015,1.2],[-5+i*.45,.17,0],'#736957');
 beam(veranda,[2.2,.08,.8],[0,.04,.9],'#a0aaa0','stone');
 for(const s of[-1,1]){
  beam(veranda,[.17,3.5,.17],[s*4.7,1.75,.1],'#645d50');
  stroke(veranda,[[s*4.7,2.6,.1],[s*4.35,2.87,.1],[s*4.0,2.95,.1]],'#81745d',.065);
 }
 const awning=new THREE.Group();awning.position.z=4.4;home.add(awning);paintedRoof(awning,11,2.4,3.05,'#6f807b',.45);
 // A circular moon window in the rear alcove and a painted scroll panel.
 const frame=new THREE.Mesh(new THREE.TorusGeometry(.65,.045,5,40),material('#675c50','wood'));frame.position.set(-2.9,1.9,-3.87);home.add(frame);
 const disc=new THREE.Mesh(new THREE.CircleGeometry(.62,40),material('#e5e4cd','wash'));disc.position.set(-2.9,1.9,-3.9);home.add(disc);
 for(let i=-2;i<=2;i++)beam(home,[.025,.9,.03],[-2.9+i*.19,1.9,-3.83],'#8c9178');
}
