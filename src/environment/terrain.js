import * as THREE from 'three';
import {random} from './pigment.js';
import {paint} from '../art.js';
export function groundAtlas(){
 const c=document.createElement('canvas');c.width=2048;c.height=1536;const x=c.getContext('2d'),r=random(817);
 const sx=2048/130,sz=1536/96,X=v=>(v+60)*sx,Z=v=>(v+48)*sz;
 x.fillStyle='#a9b995';x.fillRect(0,0,c.width,c.height);
 // Large irregular washes establish meadows. Fine strokes never repeat as tiles.
 const wash=['#88aa8c','#c3c99c','#7f9e85','#b5c7aa','#e6d8af','#99b69b'];
 for(let i=0;i<1100;i++){x.globalAlpha=.025+r()*.10;x.fillStyle=wash[i%wash.length];x.beginPath();x.ellipse(r()*2048,r()*1536,30+r()*180,8+r()*65,(r()-.5)*.8,0,7);x.fill();}
 x.globalAlpha=1;
 function path(points,w,color){for(const[extra,alpha]of[[1.8,.06],[1.4,.10],[1.1,.18],[1,.85]]){x.strokeStyle=color;x.globalAlpha=alpha;x.lineWidth=(w+extra-.8)*sx;x.lineCap='round';x.lineJoin='round';x.beginPath();points.forEach(([a,b],i)=>i?x.lineTo(X(a),Z(b)):x.moveTo(X(a),Z(b)));x.stroke();}x.globalAlpha=1;}
 path([[0,-28],[-.7,-16],[.3,-5],[0,7],[.4,17],[0,30]],6.6,'#d8ccb1');
 path([[-5,0],[5,.3],[12.5,0],[21,-.6],[35,0]],4.8,'#d8ccb1');
 path([[-45,12],[-34,12],[-24,12],[-13,12],[-4,12]],4.2,'#d8ccb1');
 path([[-34,23],[-33,17],[-32,10],[-32,-4],[-33,-23]],3.8,'#cfd1b5');
 path([[-30,-14],[-23,-14],[-15,-14],[-3,-14]],3.5,'#cfd1b5');
 // Ink-stippled arena wash with a ragged edge, rather than a hard material seam.
 for(let k=0;k<6;k++){x.globalAlpha=k===5?.9:.08;x.fillStyle=k%2?'#d5c6aa':'#e0d3b6';x.beginPath();for(let i=0;i<=160;i++){const a=i/160*7,rr=18.05+Math.sin(a*13)*.07+(5-k)*.15;const px=X(35+Math.cos(a)*rr),py=Z(Math.sin(a)*rr);i?x.lineTo(px,py):x.moveTo(px,py);}x.fill();}x.globalAlpha=1;
 // Sweep marks, tiny stones, grassy dry-brush fringes and pigment pooling.
 const pixels=x.getImageData(0,0,2048,1536).data;
 for(let i=0;i<8000;i++){let px=r()*2048,py=r()*1536,index=(Math.floor(py)*2048+Math.floor(px))*4,green=pixels[index+1]>pixels[index]*.95;
  x.strokeStyle=green?(i%3?'#5c836b14':'#e4e7bb20'):(i%3?'#a1937a15':'#fff0cc20');x.lineWidth=.5+r()*1.5;x.beginPath();x.moveTo(px,py);x.bezierCurveTo(px+3,py-1,px+9,py-3,px+14+r()*15,py-2+r()*3);x.stroke();
 }
 for(let i=0;i<160;i++){let z=-24+i*.31,px=(i%2?2.7:-2.7)+Math.sin(i)*.15;x.strokeStyle='#8d9c8875';x.lineWidth=1.6;x.beginPath();x.ellipse(X(px),Z(z),4+r()*4,5+r()*5,r()*3,0,7);x.stroke();}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;
}
export function createTerrain(scene){
 const mat=paint('#ffffff','landscape');mat.map=groundAtlas();
 const g=new THREE.PlaneGeometry(130,96,1,1),mesh=new THREE.Mesh(g,mat);mesh.rotation.x=-Math.PI/2;mesh.position.set(5,-.008,0);mesh.receiveShadow=true;mesh.name='Unrepeated hand-painted valley atlas';scene.add(mesh);return mesh;
}
