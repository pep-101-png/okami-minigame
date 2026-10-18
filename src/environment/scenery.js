import * as THREE from 'three';
import {rockGeometry} from './rocks.js';
import {paint,stroke} from '../art.js';
import {random,paintingTime,pigment} from './pigment.js';
import {batchDecoration} from '../town.js';
import {foliageTexture} from './vegetation.js';
function mountainTexture(layer){
 const c=document.createElement('canvas');c.width=512;c.height=768;const x=c.getContext('2d'),r=random(63+layer);
 const colors=[['#829e98','#bdc6b4'],['#9bb2ae','#d1d4c5'],['#b6c8c5','#e4e5d7']][layer];
 const g=x.createLinearGradient(0,0,0,768);g.addColorStop(0,colors[0]);g.addColorStop(.55,colors[1]);g.addColorStop(1,'#e6e5d600');x.fillStyle=g;x.fillRect(0,0,512,768);
 for(let i=0;i<260;i++){let px=r()*512,py=r()*600;x.strokeStyle=i%3?'#3f6b7012':'#eff1de25';x.lineWidth=.6+r()*4;x.beginPath();x.moveTo(px,py);x.bezierCurveTo(px-15,py+25,px+9,py+40,px-25,py+80+r()*90);x.stroke();}
 // Tree-shaped dry-brush silhouettes descend the ridges.
 for(let i=0;i<110;i++){const px=r()*512,py=150+r()*360,h=5+r()*17;x.strokeStyle='#3d696d25';x.lineWidth=.8;x.beginPath();x.moveTo(px,py);x.lineTo(px,py+h);for(let j=0;j<4;j++){let y=py+j*h/5;x.moveTo(px-(j+1)*1.4,y+4);x.quadraticCurveTo(px,y-1,px+(j+1)*1.4,y+4);}x.stroke();}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;
}
export function mountainScrolls(scene){
 const root=new THREE.Group();root.name='Layered sumi-e mountain scrolls';scene.add(root);
 for(let layer=2;layer>=0;layer--){const texture=mountainTexture(layer);for(let i=0;i<16;i++){
  let a=i/16*Math.PI*2+.11*layer,w=23+layer*5,h=13+layer*9+Math.sin(i*2.5)*5;
  const sh=new THREE.Shape();sh.moveTo(-w*.65,-3);sh.bezierCurveTo(-w*.40,h*.14,-w*.35,h*.68,-w*.19,h*.62);sh.bezierCurveTo(-w*.14,h*.63,-w*.11,h*.98,-w*.02,h);sh.bezierCurveTo(w*.10,h*1.04,w*.07,h*.60,w*.22,h*.57);sh.bezierCurveTo(w*.38,h*.68,w*.35,h*.16,w*.65,-3);sh.closePath();
  const geo=new THREE.ShapeGeometry(sh,18),uv=geo.attributes.uv,pos=geo.attributes.position;for(let j=0;j<uv.count;j++)uv.setXY(j,(pos.getX(j)/w/1.3)+.5,(pos.getY(j)+3)/(h+3));
  const mat=new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false,side:THREE.DoubleSide,fog:false,color:'#ffffff'}),m=new THREE.Mesh(geo,mat);m.position.set(5+Math.sin(a)*(77+layer*22),-.8,Math.cos(a)*(59+layer*21));m.rotation.y=a;m.renderOrder=-10-layer;root.add(m);
 }}
 return root;
}
function cloudTexture(){const c=document.createElement('canvas');c.width=1024;c.height=256;const x=c.getContext('2d'),r=random(36);for(let i=0;i<100;i++){x.fillStyle=i%3?'#fffaf223':'#d3ddd21a';x.beginPath();x.ellipse(512+(r()-.5)*830,135+(r()-.5)*100,30+r()*190,4+r()*18,-.07,0,7);x.fill();}const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;}
export function paintedSky(scene){
 const geo=new THREE.SphereGeometry(205,40,20),mat=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms:{top:{value:new THREE.Color('#9ec5c4')},horizon:{value:new THREE.Color('#eee7d5')}},vertexShader:'varying vec3 direction; void main(){direction=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'varying vec3 direction;uniform vec3 top;uniform vec3 horizon;void main(){float h=normalize(direction).y;vec3 c=mix(horizon,top,smoothstep(-.02,.75,h));float fiber=sin(direction.y*33.+sin(direction.x*.2))*sin(direction.z*36.);gl_FragColor=vec4(c+fiber*.004,1.);#include <colorspace_fragment>\n}'});
 // Shader includes must start on a new line.
 mat.fragmentShader=mat.fragmentShader.replace('#include','\n#include');
 const sky=new THREE.Mesh(geo,mat);sky.position.set(5,0,0);sky.renderOrder=-100;sky.name='Painted porcelain sky';scene.add(sky);
 const map=cloudTexture(),clouds=[];
 for(let i=0;i<11;i++){let a=i/11*Math.PI*2,m=new THREE.Mesh(new THREE.PlaneGeometry(45+(i%3)*15,8),new THREE.MeshBasicMaterial({map,transparent:true,depthWrite:false,side:THREE.DoubleSide,fog:false,opacity:.8}));m.position.set(5+Math.sin(a)*108,23+(i%4)*7,Math.cos(a)*98);m.rotation.y=a;m.renderOrder=-20;scene.add(m);clouds.push(m);}
 for(let i=0;i<12;i++){const a=i/12*Math.PI*2,mist=new THREE.Mesh(new THREE.PlaneGeometry(26,3.0),new THREE.MeshBasicMaterial({map,transparent:true,opacity:.45,depthWrite:false,side:THREE.DoubleSide,fog:false}));mist.position.set(5+Math.sin(a)*61,3.8+Math.sin(i),Math.cos(a)*42);mist.rotation.y=a;mist.name='Valley mist wash';mist.renderOrder=-4;scene.add(mist);}
 const sun=new THREE.Mesh(new THREE.CircleGeometry(4.0,64),new THREE.MeshBasicMaterial({color:'#e9b79b',transparent:true,opacity:.5,depthWrite:false,fog:false}));sun.position.set(-48,30,-91);scene.add(sun);return clouds;
}
export function valleyBoundaries(scene,world){
 const root=new THREE.Group();root.name='Painted cliff terraces · physical map edges';scene.add(root);const b=world.bounds;
 for(let side=0;side<4;side++){
  const length=side%2?b.maxZ-b.minZ:b.maxX-b.minX,N=Math.ceil(length/2),vertices=[],uv=[],indices=[],colors=[];
  for(let i=0;i<=N;i++)for(let j=0;j<=5;j++){
   const t=i/N,depth=j/5,edge=.30+depth*11,height=Math.pow(depth,.48)*(3.7+Math.sin(t*19+side)*1.2+Math.sin(t*42)*.4);
   let x,z;if(side===0){x=b.minX+t*length;z=b.minZ-edge;}if(side===1){x=b.maxX+edge;z=b.minZ+t*length;}if(side===2){x=b.minX+t*length;z=b.maxZ+edge;}if(side===3){x=b.minX-edge;z=b.minZ+t*length;}
   vertices.push(x,height-.035,z);uv.push(t*9,depth*2);const c=new THREE.Color(j>3?'#8ba58a':j%2?'#929f96':'#aab4a2');colors.push(c.r,c.g,c.b);
   if(i<N&&j<5){let k=i*6+j;indices.push(k,k+1,k+6,k+1,k+7,k+6);}
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(new Array(vertices.length).fill(0),3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeVertexNormals();const m=paint('#ffffff','stone');m.vertexColors=true;m.side=THREE.DoubleSide;const cliff=new THREE.Mesh(g,m);cliff.receiveShadow=true;root.add(cliff);
 }
 const stones=new THREE.Group();root.add(stones);
 // Ink-drawn garden walls and irregular basalt banks, outside existing routes.
 for(const z of[-31.8,30.8])for(let i=0;i<14;i++){
  let x=-46+i*7.1;if(Math.abs(x)<5.5)continue;
  const g=rockGeometry(.9);const m=new THREE.Mesh(g,paint(i%2?'#899b91':'#a3ae9a','stone'));m.position.set(x,.37,z);m.scale.set(1.8,.7,1.0);m.rotation.y=i*.7;m.receiveShadow=true;stones.add(m);world.obstacles.push({x,z,r:.85});
 }
 for(let i=0;i<30;i++){const side=i%4,t=(Math.floor(i/4)+.4)/8;let x,z;if(side===0){x=b.minX+(b.maxX-b.minX)*t;z=b.minZ-1.8;}if(side===1){x=b.maxX+1.6;z=b.minZ+(b.maxZ-b.minZ)*t;}if(side===2){x=b.minX+(b.maxX-b.minX)*t;z=b.maxZ+1.8;}if(side===3){x=b.minX-1.8;z=b.minZ+(b.maxZ-b.minZ)*t;}const rock=new THREE.Mesh(rockGeometry(1.6+(i%3)*.35),paint(i%3?'#82998f':'#a2af9c','stone'));rock.position.set(x,.05,z);rock.rotation.y=i*.8;rock.scale.set(1.1,1.8,.7);stones.add(rock);}
 for(const [x,z,rad,h]of[[-40,-6,2.1,1.05],[14,15,2.0,.85]]){
  const v=[],uv=[],ix=[],N=24,R=8;for(let j=0;j<=R;j++)for(let i=0;i<=N;i++){const a=i/N*Math.PI*2,r=j/R,rr=rad*r*(1+.04*Math.sin(a*5));v.push(x+Math.cos(a)*rr,h*Math.pow(1-r*r,2),z+Math.sin(a)*rr*.85);uv.push((Math.cos(a)*r+1)/2,(Math.sin(a)*r+1)/2);if(j<R&&i<N){let k=j*(N+1)+i;ix.push(k,k+N+1,k+1,k+1,k+N+1,k+N+2);}}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();const indices=g.index.array;for(let k=0;k<indices.length;k+=3)[indices[k+1],indices[k+2]]=[indices[k+2],indices[k+1]];g.index.needsUpdate=true;g.computeVertexNormals();const m=new THREE.Mesh(g,paint('#a0b594','grass'));m.name='Garden meadow terrace';m.receiveShadow=true;root.add(m);world.obstacles.push({x,z,r:rad*.9});
 }
 batchDecoration(stones);return root;
}
export function bambooGrove(scene,x,z,seed=0){
 const root=new THREE.Group();root.position.set(x,0,z);root.name='Bamboo ink grove';scene.add(root);const r=random(51+seed);
 for(let i=0;i<19;i++){let px=(r()-.5)*5,pz=(r()-.5)*3,h=3+r()*3;
  for(let j=0;j<5;j++){const stem=new THREE.Mesh(new THREE.CylinderGeometry(.045,.055,h/5-.025,7),paint(i%3?'#799b81':'#a2b28b','wood'));stem.position.set(px,h/5*(j+.5),pz);root.add(stem);const node=new THREE.Mesh(new THREE.CylinderGeometry(.061,.061,.04,7),paint('#b2bc94','wash'));node.position.set(px,h/5*(j+1),pz);root.add(node);}
  for(let j=0;j<3;j++){let side=j%2?1:-1;stroke(root,[[px,h*.5+j*.5,pz],[px+side*.5,h*.7+j*.5,pz+.15],[px+side*.9,h*.67+j*.5,pz+.1]],'#637f6a',.015);}
 }
 batchDecoration(root);
 const mat=pigment(new THREE.MeshBasicMaterial({map:foliageTexture('bamboo'),side:THREE.DoubleSide,transparent:true,alphaTest:.15,depthWrite:false}),'leaves'),m=new THREE.InstancedMesh(new THREE.PlaneGeometry(1.6,.8),mat,24),d=new THREE.Object3D();for(let i=0;i<24;i++){d.position.set((r()-.5)*5,2+r()*3,(r()-.5)*3);d.rotation.set(-.3,r()*6,0);d.updateMatrix();m.setMatrixAt(i,d.matrix);}root.add(m);return root;
}
export function paintedWater(scene){
 const points=[],uv=[],ix=[];for(let i=0;i<=90;i++){let z=-43+i*86/90,cx=-23+Math.sin(z*.12)*.38;for(const side of[-1,1]){points.push(cx+side*2.55,.016,z);uv.push(side<0?0:1,i/90);}if(i<90){let k=i*2;ix.push(k,k+2,k+1,k+1,k+2,k+3);}}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();
 const mat=new THREE.ShaderMaterial({side:THREE.DoubleSide,uniforms:{time:paintingTime},vertexShader:'varying vec3 p;void main(){p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:`varying vec3 p;uniform float time;void main(){float flow=sin(p.z*3.2+sin(p.x*6.)*.8-time*.8);float brush=smoothstep(.88,.99,flow)*(.3+.3*sin(p.x*23.));vec3 c=mix(vec3(.38,.64,.64),vec3(.83,.89,.79),brush);c+=sin(p.x*24.+p.z*9.)*.015;gl_FragColor=vec4(c,1.);\n#include <colorspace_fragment>\n}`});const river=new THREE.Mesh(g,mat);river.name='Brush-current river';scene.add(river);
 const falls=new THREE.Group();falls.position.set(-23,0,-35);scene.add(falls);
 for(let i=0;i<10;i++){const x=(i/9-.5)*2;const sh=new THREE.Shape();sh.moveTo(x-.15,0);sh.bezierCurveTo(x-.30,2,x+.10,4,x-.13,6.5);sh.lineTo(x+.1,6.5);sh.bezierCurveTo(x+.3,4,x-.05,2,x+.15,0);sh.closePath();const m=new THREE.Mesh(new THREE.ShapeGeometry(sh,12),new THREE.MeshBasicMaterial({color:i%3?'#e9ecdc':'#b4d4cb',transparent:true,opacity:.72,side:THREE.DoubleSide,depthWrite:false}));m.material.onBeforeCompile=shader=>{shader.uniforms.fallTime=paintingTime;shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying float vFallY;').replace('#include <begin_vertex>','#include <begin_vertex>\nvFallY=position.y;');shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying float vFallY;uniform float fallTime;').replace('#include <color_fragment>','#include <color_fragment>\ndiffuseColor.rgb*=.94+.06*sin(vFallY*8.+fallTime*3.);');};m.material.customProgramCacheKey=()=>"brush-waterfall";m.position.z=i*.02;falls.add(m);}
 const sh=new THREE.Shape();sh.absellipse(-15,22,2.7,1.7,0,Math.PI*2,false,0);const pondGeo=new THREE.ShapeGeometry(sh,48);pondGeo.rotateX(-Math.PI/2);
 // Shape's vertical coordinate maps to -Z when laid down.
 const pp=pondGeo.attributes.position;for(let i=0;i<pp.count;i++)pp.setXYZ(i,pp.getX(i),.020,-pp.getZ(i));pondGeo.computeVertexNormals();
 const pond=new THREE.Mesh(pondGeo,mat);pond.name='Lotus garden pond';scene.add(pond);
 const bank=new THREE.Group();scene.add(bank);
 for(let i=0;i<13;i++){const a=i/13*Math.PI*2,m=new THREE.Mesh(rockGeometry(.30+(i%3)*.06),paint(i%2?'#9daa98':'#879e93','stone'));m.position.set(-15+Math.cos(a)*2.8,.015,22+Math.sin(a)*1.8);m.scale.set(1.1,.6,.8);m.rotation.y=a;bank.add(m);}
 for(let i=0;i<5;i++){const leaf=new THREE.Shape();leaf.moveTo(0,0);leaf.absarc(0,0,.24+i*.015,.20,Math.PI*2-.20,false);leaf.lineTo(0,0);const m=new THREE.Mesh(new THREE.ShapeGeometry(leaf,18),paint('#729b7d','wash'));m.rotation.x=-Math.PI/2;m.position.set(-15+Math.sin(i*2.4)*1.5,.027,22+Math.cos(i*2.4)*.85);bank.add(m);if(i%2===0)for(let j=0;j<5;j++){const petal=new THREE.Mesh(new THREE.SphereGeometry(.065,8,5),paint('#f0c6c0','wash'));petal.scale.set(.65,.45,1.5);petal.position.set(m.position.x+Math.sin(j*1.257)*.06,.07,m.position.z+Math.cos(j*1.257)*.06);bank.add(petal);}}
 batchDecoration(bank);
 return {river,falls,pond};
}
