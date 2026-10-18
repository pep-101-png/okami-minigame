import * as THREE from 'three';
import { paint, outline, stroke, seededRandom } from '../art.js';
export function form(parent,rings,color,{sides=20,kind='wash',position=[0,0,0]}={}) {
 const v=[],uv=[],ix=[];
 rings.forEach(([y,rx,rz,z=0],j)=>{for(let i=0;i<=sides;i++){const a=i/sides*Math.PI*2;v.push(Math.cos(a)*rx,y,Math.sin(a)*rz+z);uv.push(i/sides,j/(rings.length-1));}});
 for(let j=0;j<rings.length-1;j++)for(let i=0;i<sides;i++){const a=j*(sides+1)+i;ix.push(a,a+sides+1,a+1,a+1,a+sides+1,a+sides+2);}
 if(rings[0][0]>rings.at(-1)[0])for(let i=0;i<ix.length;i+=3)[ix[i+1],ix[i+2]]=[ix[i+2],ix[i+1]];
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();const m=new THREE.Mesh(g,paint(color,kind));m.position.set(...position);m.castShadow=true;m.receiveShadow=true;parent.add(m);outline(m,.014);return m;
}
export function brushRibbon(points,width,color,opacity=1) {
 const v=[],uv=[],idx=[];
 points.forEach((p,i)=>{const t=i/(points.length-1),w=width*Math.pow(Math.sin(Math.PI*Math.min(.98,Math.max(.02,t))),.65);v.push(p[0]-w,p[1],p[2],p[0]+w,p[1],p[2]+.015);uv.push(0,t,1,t);if(i<points.length-1){let a=i*2;idx.push(a,a+1,a+2,a+1,a+3,a+2);}});
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(idx);g.computeVertexNormals();const m=paint(color);m.side=THREE.DoubleSide;m.transparent=opacity<1;m.opacity=opacity;m.depthWrite=opacity===1;return new THREE.Mesh(g,m);
}
export function inscription(text,width=2.6,height=.52) {
 const c=document.createElement('canvas');c.width=768;c.height=160;const x=c.getContext('2d');x.fillStyle='#ede0bd';x.fillRect(0,0,c.width,c.height);x.strokeStyle='#75674c';x.lineWidth=7;x.strokeRect(8,8,752,144);x.fillStyle='#483a32';x.font='38px Georgia';x.textAlign='center';x.fillText(text,384,98,720);const map=new THREE.CanvasTexture(c);map.colorSpace=THREE.SRGBColorSpace;const o=new THREE.Sprite(new THREE.SpriteMaterial({map,depthWrite:false}));o.scale.set(width,height,1);return o;
}
export function floralMap(color) {
 const c=document.createElement('canvas');c.width=c.height=256;const x=c.getContext('2d'),rand=seededRandom(45);x.fillStyle=color;x.fillRect(0,0,256,256);
 for(let i=0;i<80;i++){x.globalAlpha=.05;x.fillStyle=i%2?'#fff7db':'#362f39';x.beginPath();x.ellipse(rand()*256,rand()*256,20+rand()*45,4+rand()*20,rand()*4,0,7);x.fill();}
 x.globalAlpha=.7;
 for(let i=0;i<14;i++){const px=rand()*256,py=rand()*256;x.strokeStyle='#efce9f';x.lineWidth=1;x.beginPath();x.moveTo(px,py);x.bezierCurveTo(px+8,py-10,px-9,py-24,px+3,py-40);x.stroke();for(let j=0;j<5;j++){x.fillStyle=j%2?'#ead3b4':'#d4a0a1';x.beginPath();x.ellipse(px+Math.sin(j*1.256)*5,py-27+Math.cos(j*1.256)*5,4,7,j*1.256,0,7);x.fill();}}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;
}
