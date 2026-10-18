import * as THREE from 'three';import{riverAt}from'./landform.js';import{random}from'./pigment.js';import{paint}from'../art.js';
export function groundAtlas(land){
 const c=document.createElement('canvas');c.width=2048;c.height=1536;const x=c.getContext('2d'),r=random(817),sx=2048/130,sz=1536/96,X=v=>(v+60)*sx,Z=v=>(v+48)*sz;
 x.fillStyle='#a1b693';x.fillRect(0,0,2048,1536);
 for(let i=0;i<1600;i++){x.globalAlpha=.04+r()*.09;x.fillStyle=['#79a58a','#c6cda0','#85a291','#b9c5a0','#acb491'][i%5];x.beginPath();x.ellipse(r()*2048,r()*1536,20+r()*130,8+r()*65,r()*2,0,7);x.fill();}x.globalAlpha=1;
 for(const route of land.paths)for(const p of route.samples){for(const[k,alpha,col]of[[1.0,.06,'#d0c5a2'],[.80,.16,'#d3c6aa'],[.62,.24,'#d4c4a6'],[.43,.35,'#c5b79c']]){x.globalAlpha=alpha;x.fillStyle=col;x.beginPath();x.ellipse(X(p.x),Z(p.z),p.width*sx*k,p.width*sz*k,0,0,7);x.fill();}}x.globalAlpha=1;
 const a=x.createRadialGradient(X(35),Z(0),16*sx,X(35),Z(0),19.5*sx);a.addColorStop(0,'#d8c9ac');a.addColorStop(.9,'#d8c9acf0');a.addColorStop(1,'#d8c9ac00');x.fillStyle=a;x.fillRect(X(14),Z(-22),43*sx,44*sz);
 for(let z=-47;z<=47;z+=.4){const w=riverAt(z);x.globalAlpha=.4;x.fillStyle='#a9ac93';x.beginPath();x.ellipse(X(w.x),Z(z),w.width*sx*.98,1.8*sz,0,0,7);x.fill();}x.globalAlpha=1;
 // Moss blooms, stone inclusions, broad dry pigment; no uniform scratched hatching.
 for(let i=0;i<6500;i++){let px=r()*2048,py=r()*1536;x.fillStyle=i%3?'#667f6c0b':'#f4e7c510';x.beginPath();x.ellipse(px,py,2+r()*14,1+r()*4,r()*3,0,7);x.fill();}
 for(const route of land.paths)for(let i=4;i<route.samples.length;i+=3){const p=route.samples[i],px=X(p.x+(i%2?1:-1)*p.width*.40),py=Z(p.z);x.strokeStyle='#8c938064';x.lineWidth=.7;x.fillStyle='#a7aa9060';x.beginPath();x.ellipse(px,py,2+r()*4,2+r()*5,r()*3,0,7);x.fill();x.stroke();}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;
}
export function createTerrain(scene,land){
 const mat=paint('#ffffff','landscape');mat.map=groundAtlas(land);const{nx,nz,heights}=land.grid;
 const g=new THREE.PlaneGeometry(130,96,nx-1,nz-1),p=g.attributes.position;
 for(let i=0;i<p.count;i++){const x=p.getX(i)+5,z=-p.getY(i);p.setXYZ(i,x,land.terrainHeight(x,z),z);}g.computeVertexNormals();
 const mesh=new THREE.Mesh(g,mat);mesh.receiveShadow=true;mesh.name='Sculpted valley · shared physical height field';scene.add(mesh);return mesh;
}
