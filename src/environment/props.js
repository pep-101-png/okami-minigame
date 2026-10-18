import * as THREE from'three';import{paint,stroke,outline}from'../art.js';import{timberGeometry}from'./joinery.js';import{rockGeometry}from'./rocks.js';
export function latheForm(profile,sides=16){return new THREE.LatheGeometry(profile.map(([r,y])=>new THREE.Vector2(r,y)),sides);}
export function wood(root,size,pos,col='#8b7059'){const m=new THREE.Mesh(timberGeometry(size),paint(col,'wood'));m.position.set(...pos);m.castShadow=true;m.receiveShadow=true;root.add(m);return m;}
export function stoneLantern(scene,x,z,color='#f5dba0'){
 const root=new THREE.Group();root.position.set(x,0,z);root.name='Carved kasuga lantern';scene.add(root);
 const base=new THREE.Mesh(rockGeometry(.43),paint('#8d9c90','stone'));base.scale.set(1,.35,1);root.add(base);
 const stem=new THREE.Mesh(latheForm([[.19,.1],[.21,.21],[.12,.30],[.11,.89],[.22,.98],[.25,1.06]]),paint('#a3ada0','stone'));stem.receiveShadow=true;root.add(stem);
 const lamp=new THREE.Mesh(latheForm([[.26,1.04],[.29,1.11],[.25,1.52],[.20,1.58]],8),paint('#8d9d93','stone'));root.add(lamp);
 for(let i=0;i<4;i++){const a=i*Math.PI/2,g=new THREE.Group();g.rotation.y=a;root.add(g);const paper=new THREE.Mesh(new THREE.PlaneGeometry(.25,.29),paint(color,'wash'));paper.material.emissive.set('#916b36');paper.material.emissiveIntensity=.18;paper.position.set(0,1.31,.252);g.add(paper);for(const s of[-1,1])wood(g,[.025,.32,.04],[s*.135,1.31,.268],'#607368');}
 const lid=new THREE.Mesh(latheForm([[.44,1.55],[.48,1.59],[.34,1.68],[.23,1.82],[.10,1.85],[.07,1.98],[0,2.03]],20),paint('#718b7e','stone'));root.add(lid);outline(lid,.012);return root;
}
export function paperLantern(root,pos,color='#efd2a3'){
 const g=new THREE.Group();g.position.set(...pos);root.add(g);const shade=new THREE.Mesh(latheForm([[.09,-.26],[.18,-.20],[.21,0],[.18,.20],[.09,.26]],20),paint(color,'wash'));shade.material.emissive.set('#b77b42');shade.material.emissiveIntensity=.15;g.add(shade);for(let i=0;i<7;i++){const y=-.23+i*.076,r=.10+.10*Math.sin((i/6)*Math.PI),ring=new THREE.Mesh(new THREE.TorusGeometry(r,.006,3,20),paint('#9c8264','wood'));ring.rotation.x=Math.PI/2;ring.position.y=y;g.add(ring);}stroke(g,[[0,.27,0],[0,.6,0]],'#716851',.012);return g;
}
export function fence(scene,world,x0,x1,z){const root=new THREE.Group();root.name='Joined split-timber village fence';scene.add(root);const n=Math.ceil(Math.abs(x1-x0)/1.6);for(let i=0;i<=n;i++){let x=x0+(x1-x0)*i/n;wood(root,[.11,.93+(i%3)*.035,.13],[x,.46,z]);for(let j=0;j<2;j++)if(i<n){const xx=x+(x1-x0)/n;stroke(root,[[x,.28+j*.39,z],[x+(xx-x)*.5,.30+j*.39,z+.02],[xx,.27+j*.39,z]],'#927557',.035);}}world.boxes.push({x:(x0+x1)/2,z,halfX:Math.abs(x1-x0)/2,halfZ:.08});return root;}

// Tensioned cloth: a curved canopy and scalloped hanging edge, not a tilted slab.
export function marketCanopy(root,color){
 const v=[],uv=[],ix=[],N=24,K=10;for(let j=0;j<=K;j++)for(let i=0;i<=N;i++){const u=i/N,t=j/K,x=(u-.5)*2.65,z=(t-.5)*1.75,y=2.06+.18*Math.sin(t*Math.PI)-.07*Math.sin(u*Math.PI)+.014*Math.sin(u*28);v.push(x,y,z);uv.push(u,t);if(j<K&&i<N){const k=j*(N+1)+i;ix.push(k,k+N+1,k+1,k+1,k+N+1,k+N+2);}}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();const mat=paint(color,'wash');mat.side=THREE.DoubleSide;const mesh=new THREE.Mesh(g,mat);mesh.castShadow=true;root.add(mesh);
 for(let i=0;i<5;i++){const shape=new THREE.Shape(),x=-1.325+i*.53;shape.moveTo(x,0);shape.lineTo(x+.51,0);shape.lineTo(x+.51,-.25);shape.quadraticCurveTo(x+.255,-.35,x,-.25);shape.closePath();const flag=new THREE.Mesh(new THREE.ShapeGeometry(shape,8),paint(i%2?color:'#e4ccaa','wash'));flag.material.side=THREE.DoubleSide;flag.position.set(0,2.035,.88);root.add(flag);}
}
export function pottery(root,pos,color,scale=.22){const mesh=new THREE.Mesh(latheForm([[0,0],[.52,.02],[.72,.18],[.86,.53],[.69,.78],[.35,.91],[.34,1.04],[.43,1.06],[.43,1.11],[.30,1.11],[.27,.96],[.53,.76],[.65,.53],[.48,.19],[0,.16]],24),paint(color,'wash'));mesh.scale.setScalar(scale);mesh.position.set(...pos);root.add(mesh);return mesh;}
