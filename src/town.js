import { createVillager as npc } from './expansion/villagers.js';
import * as THREE from "three";
import { createWorld } from "./world.js";
import { part } from "./models.js";
import { stroke, paint, paintedTexture, seededRandom } from "./art.js";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";

const palette = { ink:"#322a20", timber:"#865b32", cream:"#e9c794", roof:"#b98a42", red:"#bd442b", green:"#769747", stone:"#939372" };
const architectureMaterials = new Map();
function architectureMaterial(color,kind) {
  const key = `${color}:${kind}`;
  if(!architectureMaterials.has(key))architectureMaterials.set(key,paint(color,kind));
  return architectureMaterials.get(key);
}
function block(parent,size,color,pos,kind="wash",rot=[0,0,0],lined=true) {
  return part(parent,new THREE.BoxGeometry(...size),architectureMaterial(color,kind),pos,rot,lined);
}
function geometryForBatch(node,inverse) {
  // ShapeGeometry is non-indexed while boxes/tubes are indexed. Normalize the
  // topology before merging so no scenery batch is silently dropped.
  const geometry=node.geometry.index?node.geometry.toNonIndexed():node.geometry.clone();
  for(const name of Object.keys(geometry.attributes))if(!["position","normal","uv"].includes(name))geometry.deleteAttribute(name);
  if(!geometry.attributes.normal)geometry.computeVertexNormals();
  if(!geometry.attributes.uv)geometry.setAttribute("uv",new THREE.BufferAttribute(new Float32Array(geometry.attributes.position.count*2),2));
  return geometry.applyMatrix4(inverse.clone().multiply(node.matrixWorld));
}
export function batchHouse(root) {
  // Facades are static. Batch their beams and ink shells by material instead of
  // submitting a draw call for every window bar. NPC joints remain independent.
  root.updateMatrixWorld(true);
  const localMaterials=new Map();
  root.traverse(node=>{if(!node.isMesh)return;const source=node.material,key=[source.type,source.color?.getHexString(),source.map?.uuid,source.side,source.transparent,source.opacity].join(":");if(!localMaterials.has(key))localMaterials.set(key,source.clone());node.material=localMaterials.get(key);});
  root.userData.fade.materials=[...localMaterials.values()];
  const inverse=root.matrixWorld.clone().invert(),groups=new Map(),meshes=[];
  root.traverse(node=>{
    if(!node.isMesh)return;
    if(!groups.has(node.material))groups.set(node.material,[]);
    groups.get(node.material).push(geometryForBatch(node,inverse));
    meshes.push(node);
  });
  for(const mesh of meshes)mesh.parent.remove(mesh);
  for(const [material,geometries]of groups) {
    const merged=mergeGeometries(geometries,false);
    if(!merged)continue;
    const mesh=new THREE.Mesh(merged,material);
    mesh.castShadow=material.side!==THREE.BackSide;mesh.receiveShadow=true;
    root.add(mesh);
    for(const geometry of geometries)geometry.dispose();
  }
}
export function batchDecoration(root) {
  root.updateMatrixWorld(true);
  const inverse=root.matrixWorld.clone().invert(),groups=new Map(),meshes=[];
  root.traverse(node=>{
    if(!node.isMesh)return;
    const m=node.material,key=[m.type,m.color.getHexString(),m.map?.uuid,m.side,m.transparent,m.opacity].join(":");
    if(!groups.has(key))groups.set(key,{material:m,geometry:[],cast:false,receive:false});
    const group=groups.get(key);group.geometry.push(geometryForBatch(node,inverse));group.cast ||=node.castShadow;group.receive ||=node.receiveShadow;meshes.push(node);
  });
  for(const node of meshes)node.parent.remove(node);
  for(const group of groups.values()) {
    const geometry=mergeGeometries(group.geometry,false);if(!geometry)continue;
    const mesh=new THREE.Mesh(geometry,group.material);mesh.castShadow=group.cast;mesh.receiveShadow=group.receive;root.add(mesh);
    for(const g of group.geometry)g.dispose();
  }
}
export function roof(parent,w,d,y,color,height=1.05) {
  const positions=[],uv=[],indices=[];
  for(let side=0;side<2;side++) {
    const sign=side?1:-1,base=positions.length/3;
    for(let i=0;i<6;i++) {
      const t=i/5;
      for(const z of [-d/2,d/2]) {
        positions.push(sign*t*w/2,y+height*(1-t)+.24*t*t*t,z);
        uv.push(z/d+.5,t);
      }
    }
    for(let i=0;i<5;i++){const a=base+i*2;indices.push(a,a+1,a+2,a+1,a+3,a+2);}
  }
  const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));g.setAttribute("uv",new THREE.Float32BufferAttribute(uv,2));g.setIndex(indices);g.computeVertexNormals();
  const material=paint(color,"roof");material.side=THREE.DoubleSide;
  part(parent,g,material,undefined,undefined,false);
  const linePoints=(z)=>[[-w/2,y+.24,z],[-w*.3,y+height*.42,z],[0,y+height,z],[w*.3,y+height*.42,z],[w/2,y+.24,z]];
  for(const z of [-d/2,d/2])stroke(parent,linePoints(z),palette.ink,.055);
  for(const s of [-1,1])stroke(parent,[[s*w/2,y+.22,-d/2],[s*w/2,y+.2,0],[s*w/2,y+.24,d/2]],palette.ink,.07);
  block(parent,[.13,.12,d+.3],palette.timber,[0,y+height+.03,0],"wood");
  // Short irregular ink strokes suggest roof fibers without modeling every tile.
  const rand=seededRandom(Math.round(w*100+d*10));
  for(let i=0;i<18;i++) {
    const x=(rand()-.5)*w*.9,z=(rand()-.5)*d*.85,t=Math.abs(x)/(w/2),yy=y+height*(1-t)+.24*t*t*t+.035;
    stroke(parent,[[x,yy,z],[x+.04,yy+.006,z+.24]],"#655137",.012);
  }
}
function shoji(parent,x,y,z,width=.96,height=1.1) {
  block(parent,[width,height,.045],"#f9dfa0",[x,y,z],"shoji",undefined,false);
  for(let i=-1;i<=1;i++)block(parent,[.043,height+.06,.075],palette.ink,[x+i*width/3,y,z+.03],"wood",undefined,false);
  for(let i=-1;i<=1;i++)block(parent,[width+.05,.038,.075],palette.ink,[x,y+i*height/3,z+.04],"wood",undefined,false);
}
export function house(scene,x,z,w=5,d=4,color=palette.roof,turn=0,tier=false) {
  const root=new THREE.Group();root.position.set(x,0,z);root.rotation.y=turn;scene.add(root);
  const height=tier?3.25:2.55;
  block(root,[w+.15,.22,d+.15],palette.stone,[0,.08,0],"stone");
  block(root,[w,height,d],palette.cream,[0,height/2+.15,0],"wood");
  // Front and side timber framing provides readable silhouettes from fixed view.
  for(const sx of [-1,1])for(const sz of [-1,1])block(root,[.17,height+.2,.17],"#503b26",[sx*w/2,height/2+.15,sz*d/2],"wood");
  for(const y of [.35,1.05,height-.1]) {
    block(root,[w,.1,.08],"#69442b",[0,y,d/2+.02],"wood",undefined,false);
    block(root,[.08,.1,d],"#69442b",[w/2+.02,y,0],"wood",undefined,false);
  }
  block(root,[.95,1.85,.06],"#533f27",[0,1.04,d/2+.06],"wood");
  for(let i=-2;i<=2;i++)block(root,[.035,1.7,.03],"#aa7846",[i*.16,1.04,d/2+.11],"wood",undefined,false);
  for(const sx of [-1,1])shoji(root,sx*w*.3,1.5,d/2+.09);
  const sideWindow=new THREE.Group();sideWindow.position.set(w/2+.07,1.45,0);sideWindow.rotation.y=Math.PI/2;root.add(sideWindow);shoji(sideWindow,0,0,0,1.5,1.05);
  const eaves=new THREE.Group();root.add(eaves);roof(eaves,w+1.05,d+1,height+.12,color);
  if(tier) {
    block(root,[w*.56,1.3,d*.6],palette.cream,[0,height+.72,-.15],"wood");
    for(const sx of [-1,1])block(root,[.12,1.4,.12],palette.red,[sx*w*.27,height+.72,d*.27],"wood");
    shoji(root,0,height+.82,d*.3+.03,1.7,.9);
    roof(eaves,w*.7,d*.76,height+1.39,"#a15c34",.8);
  }
  // All facade materials are local so a foreground house can fade independently.
  root.userData.fade={materials:[],value:1,x,z,w:w+1.2,d:d+1.2};
  return root;
}
function label(text,width=3.1) {
  const c=document.createElement("canvas");c.width=512;c.height=96;
  const ctx=c.getContext("2d");ctx.fillStyle="#efe0ba";ctx.beginPath();ctx.moveTo(8,16);ctx.lineTo(493,9);ctx.lineTo(504,78);ctx.lineTo(15,86);ctx.closePath();ctx.fill();ctx.strokeStyle="#67543a";ctx.lineWidth=3;ctx.stroke();
  ctx.fillStyle="#433325";ctx.font="29px Georgia";ctx.textAlign="center";ctx.fillText(text,256,59);
  const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;
  const tag=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,transparent:true,depthWrite:false}));tag.scale.set(width,.59,1);return tag;
}
function boardLabel(text,width) {
  const sprite=label(text,width);
  return new THREE.Mesh(new THREE.PlaneGeometry(width,.59),new THREE.MeshBasicMaterial({map:sprite.material.map,transparent:true}));
}
function legacyNpc(scene,x,z,name,color,lines,route=null) {
  const root=new THREE.Group();root.position.set(x,0,z);scene.add(root);
  const body=new THREE.Group();body.position.y=.88;root.add(body);
  // Layered kimono silhouette, wide sleeves, separate calves and sandal feet.
  const robe=part(body,new THREE.CylinderGeometry(.25,.38,.97,7),paint(color),[0,.02,0]);robe.scale.z=.7;
  const chest=block(body,[.55,.5,.35],color,[0,.48,0]);
  block(body,[.57,.13,.38],"#e6bd59",[0,.18,0],"wash");
  stroke(body,[[-.22,.73,.19],[0,.34,.22],[.11,.2,.22]],"#f7dca6",.025);
  stroke(body,[[.22,.73,.19],[.05,.42,.22]],"#493c33",.022);
  const head=new THREE.Group();head.position.set(0,.88,0);body.add(head);
  const face=part(head,new THREE.SphereGeometry(.22,8,6),paint("#e9bd8b"),[0,0,0]);face.scale.set(.91,1.14,.85);
  const hair=part(head,new THREE.SphereGeometry(.23,8,6),paint("#353025"),[0,.115,-.045]);hair.scale.set(1,.57,.83);
  part(head,new THREE.SphereGeometry(.085,7,5),paint("#353025"),[0,.27,-.07]);
  for(const s of [-1,1]) {
    block(head,[.04,.016,.016],palette.ink,[s*.085,.016,.18],"wash",undefined,false);
    part(head,new THREE.SphereGeometry(.015,5,4),paint("#c46e56"),[s*.12,-.041,.163],undefined,false);
  }
  stroke(head,[[-.035,-.08,.17],[.008,-.094,.177],[.04,-.079,.16]],"#8f5741",.008);
  const arms=[],legs=[];
  for(const s of [-1,1]) {
    const arm=new THREE.Group();arm.position.set(s*.27,.62,0);body.add(arm);
    block(arm,[.27,.58,.32],color,[s*.11,-.23,0],"wash",[0,0,s*.18]);
    part(arm,new THREE.SphereGeometry(.074,6,4),paint("#e9bd8b"),[s*.17,-.54,.025]);arms.push(arm);
    const leg=new THREE.Group();leg.position.set(s*.15,.37,0);root.add(leg);
    block(leg,[.13,.42,.13],"#554634",[0,-.1,0]);block(leg,[.17,.08,.29],"#b29a65",[0,-.32,.055],"wood");legs.push(leg);
  }
  if(name.startsWith("Elder")) {
    part(head,new THREE.ConeGeometry(.26,.18,6),paint("#c79c56"),[0,.24,0]);
    stroke(root,[[.52,0,.1],[.55,.8,.1],[.61,1.35,.09]],palette.timber,.04);
    arms[1].rotation.x=-.5;
  }
  if(name.startsWith("Taro")) {
    const apron=block(body,[.36,.57,.02],"#dac394",[0,-.07,.29],"wash");
    stroke(apron,[[-.09,0,.02],[.02,-.14,.025],[.1,-.12,.025]],"#52746a",.018);
  }
  const tag=label(name,2.4);tag.scale.y=.46;tag.position.y=2.32;root.add(tag);
  return {root,name,lines,route,index:0,home:new THREE.Vector3(x,0,z),body,head,arms,legs,tag,phase:x,walking:false};
}
function flatPatch(scene,points,color,y=.035,kind="wash") {
  const shape=new THREE.Shape();shape.moveTo(...points[0]);for(const p of points.slice(1))shape.lineTo(...p);shape.closePath();
  const mesh=part(scene,new THREE.ShapeGeometry(shape),paint(color,kind),[0,y,0],[-Math.PI/2,0,0],false);
  // Shape's second coordinate becomes -Z after rotation, so callers give [x,-z].
  return mesh;
}
export function lantern(scene,x,z,color="#f5dba0") {
  const group=new THREE.Group();group.position.set(x,0,z);scene.add(group);
  block(group,[.65,.14,.65],palette.stone,[0,.08,0],"stone");
  part(group,new THREE.CylinderGeometry(.13,.22,1,6),paint(palette.stone,"stone"),[0,.63,0]);
  block(group,[.47,.48,.47],color,[0,1.32,0],"shoji");
  for(const s of [-1,1])block(group,[.045,.52,.49],palette.ink,[s*.21,1.32,0],"wood",undefined,false);
  part(group,new THREE.ConeGeometry(.5,.27,4),paint("#637542","roof"),[0,1.74,0],[0,Math.PI/4,0]);return group;
}
export function garden(scene,x,z,seed=10) {
  const rand=seededRandom(seed),group=new THREE.Group();group.position.set(x,.025,z);scene.add(group);
  const plot=part(group,new THREE.CylinderGeometry(1.4,1.5,.06,10),paint("#577943","grass"),[0,0,0],undefined,false);plot.scale.z=.57;
  // Flower cards are low poly and small enough that the paper-painting reads first.
  for(let i=0;i<14;i++) {
    const a=rand()*6.28,r=rand()*1.1,xx=Math.cos(a)*r,zz=Math.sin(a)*r*.57;
    stroke(group,[[xx,0,zz],[xx+.035,.24+rand()*.12,zz]],"#496136",.014);
    const flower=part(group,new THREE.CircleGeometry(.065+rand()*.035,5),new THREE.MeshBasicMaterial({color:i%4?"#efb9a1":"#f0d26c",side:THREE.DoubleSide}),[xx,.28,zz],[-.4,0,.4],false);
    flower.rotation.z=rand()*6;
  }
  batchDecoration(group);
  return group;
}
export function createTown(scene) {
  const world=createWorld(scene);
  // The grove is its own clearing east of the safe village.
  for(const child of [...scene.children]) {
    if(child.geometry?.type==="ShapeGeometry"){scene.remove(child);continue;}
    if(!child.isLight)child.position.x+=26;
  }
  for(const o of world.obstacles)o.x+=26;
  scene.background=new THREE.Color("#389bc0");scene.fog=new THREE.Fog("#b1cab0",42,115);
  const terrain=paint("#a1ae78","grass");terrain.map=paintedTexture("grass").clone();terrain.map.repeat.set(18,15);terrain.map.needsUpdate=true;
  part(scene,new THREE.PlaneGeometry(110,90),terrain,[8,-.025,0],[-Math.PI/2,0,0],false);
  flatPatch(scene,[[-4.4,-25],[-3.8,-13],[-4.15,-4],[-4.4,6],[-3.8,18],[-3.6,27],[3.6,27],[4.1,18],[4.25,7],[3.8,-4],[4.4,-14],[3.8,-25]],"#cfac69",.035);
  flatPatch(scene,[[-5,-2.5],[4.2,-3.1],[13,-2.6],[19,-3.2],[36,-2.2],[36,2.2],[21,2.6],[12,3.3],[2,2.8],[-5,2.5]],"#d9bb7d",.04);
  // Stone thresholds and a broad market square avoid an obstacle course layout.
  flatPatch(scene,[[-5.6,-4.5],[5.6,-4.5],[5.6,4.5],[-5.6,4.5]],"#d7bc84",.045,"stone");
  world.bounds={minX:-20,maxX:44,minZ:-27,maxZ:27};world.boxes=[];
  const homes=[[-8,15,5,4,"#ad753b"],[8,15,5,4,"#ac723d"],[-9,6,6,4,"#b38842"],[9,6,5,4,"#b77a45"],[-9,-5,5,5,"#a56532"],[9,-9,6,4,"#83934d"],[-8,-18,6,5,"#a57940"],[8,-20,5,5,"#b88441"]];
  const houses=[];
  for(const [x,z,w,d,col]of homes) {
    const h=house(scene,x,z,w,d,col,0,x===-9&&z===6);houses.push(h);
    world.boxes.push({x,z,halfX:w/2+.2,halfZ:d/2+.2});
    // Low porch has no invisible collision; its visual rises less than one paw.
    block(scene,[w*.76,.06,.7],"#9f7545",[x,.06,z+d/2+.45],"wood",undefined,false);
    garden(scene,x+(x<0?-2.3:2.3),z+d/2+.8,Math.round(x*z+700));
    const noren=new THREE.Group();noren.position.set(x,1.94,z+d/2+.12);scene.add(noren);
    for(const s of [-1,1])block(noren,[.39,.4,.025],z===6?"#ac4d3c":"#6d8270",[s*.22,0,0],"wash",[0,0,s*.025],false);
    // Add signs, jars, and stacked split timber only inside each solid house box.
    const jar=part(h,new THREE.SphereGeometry(.24,7,5),paint("#9e704e"),[w*.43,.35,d*.36]);jar.scale.set(1,1.45,.8);
  }
  // The shrine ends the main road, backed by layered indigo/green ink mountains.
  const shrine=house(scene,0,-25,8,4,"#b96b36",0,true);houses.push(shrine);world.boxes.push({x:0,z:-25,halfX:4.2,halfZ:2.2});
  for(const x of [-3.1,3.1])block(shrine,[.23,3,.23],palette.red,[x,1.6,2.11],"wood");
  const shrineSign=boardLabel("WINDFLOWER SHRINE",3.8);shrineSign.position.set(0,3.0,-22.3);scene.add(shrineSign);
  for(const [x,z]of [[-3.9,-20],[3.9,-20],[-3.9,19],[3.9,19],[15,-3.8],[15,3.8]]){lantern(scene,x,z);world.obstacles.push({x,z,r:.3});}
  const mountains=[{z:-48,color:"#759c89",height:7},{z:-63,color:"#97b9a4",height:10},{z:-80,color:"#bed2b2",height:13}];
  for(const[layerIndex,layer]of mountains.entries())for(let i=0;i<10;i++) {
    const shape=new THREE.Shape(),x=-47+i*11,h=layer.height+Math.sin(i*2.7)*4;
    shape.moveTo(-10,0);shape.lineTo(-8,h*.35);shape.lineTo(-4,h*.68);shape.lineTo(-1,h);shape.lineTo(2,h*.72);shape.lineTo(6,h*.54);shape.lineTo(11,0);
    const m=new THREE.Mesh(new THREE.ShapeGeometry(shape),new THREE.MeshBasicMaterial({color:layer.color,side:THREE.DoubleSide}));m.position.set(x,-.5,layer.z);scene.add(m);
    if(!layerIndex)stroke(m,[[-8,h*.35,.02],[-4,h*.68,.02],[-1,h,.02],[2,h*.72,.02],[6,h*.54,.02]],"#526e5a",.06);
  }
  // A river lives outside the walkable bounds, so it needs no hidden blocking wall.
  part(scene,new THREE.PlaneGeometry(5.5,66),paint("#56b3b3"),[-23,.015,0],[-Math.PI/2,0,0],false);
  for(let i=0;i<18;i++)stroke(scene,[[-24+.5*Math.sin(i),.04,-29+i*3.5],[-21.4,.04,-28.3+i*3.5]],"#b8dace",.025);
  for(let i=0;i<20;i++) {
    const rock=part(scene,new THREE.DodecahedronGeometry(.7+(i%3)*.1,0),paint(palette.stone,"stone"),[-19.9,.3,-26+i*2.7],undefined,true);rock.scale.set(.6,.5,1);
    world.obstacles.push({x:-19.9,z:-26+i*2.7,r:.42});
  }
  // Mill wheel sits beside an aqueduct, connected to the river by painted water.
  const wheel=new THREE.Group();wheel.position.set(-12.45,1.5,-5);wheel.rotation.y=Math.PI/2;scene.add(wheel);
  part(wheel,new THREE.TorusGeometry(1.24,.13,5,18),paint("#58462b","wood"));
  part(wheel,new THREE.TorusGeometry(.89,.07,4,16),paint("#98703e","wood"));
  for(let i=0;i<10;i++) {
    block(wheel,[.09,2.5,.14],"#9b7040",[0,0,0],"wood",[0,0,i*Math.PI/5]);
    const a=i*6.28/10;block(wheel,[.32,.15,.44],"#79542f",[Math.sin(a)*1.2,Math.cos(a)*1.2,0],"wood",[0,0,-a]);
  }
  block(scene,[7.5,.12,.65],"#9a6c3d",[-16.7,.9,-5],"wood");block(scene,[7.5,.04,.4],"#5caaa0",[-16.7,.98,-5],"wash",undefined,false);
  world.boxes.push({x:-16.7,z:-5,halfX:3.75,halfZ:.35});world.obstacles.push({x:-12.45,z:-5,r:1.02});
  const stalls=[];
  for(const x of [-4.8,4.8]) {
    const stall=new THREE.Group();stall.position.set(x,0,0);scene.add(stall);stalls.push(stall);
    block(stall,[2.2,.75,1.1],"#a47842",[0,.4,0],"wood");
    for(const sx of [-1,1])block(stall,[.07,2.03,.07],palette.ink,[sx*1.1,1.03,.32],"wood");
    block(stall,[2.55,.08,1.55],x<0?"#c86744":"#6a9275",[0,2.04,0],"wash",[.14,0,0]);
    for(let i=0;i<5;i++){block(stall,[.5,.31,.026],i%2?(x<0?"#ce8758":"#9cab75"):"#edd3a0",[-1+i*.5,1.91,.75],"wash",undefined,false);}
    for(let i=0;i<5;i++){const fruit=part(stall,new THREE.DodecahedronGeometry(.12,0),paint(x<0?"#d78139":"#dfc56c"),[-.82+i*.4,.86,.05]);fruit.scale.y=.82;}
    const sign=label(x<0?"HANA'S FLOWERS":"TARO'S TEA",2.4);sign.position.set(0,1.1,.62);stall.add(sign);
    world.boxes.push({x,z:0,halfX:1.2,halfZ:.7});
  }
  const sign=label("EAST → SPIRIT GROVE",3.1);sign.position.set(12,1.95,0);scene.add(sign);block(scene,[.07,1.9,.07],palette.timber,[12,.95,0],"wood");world.obstacles.push({x:12,z:0,r:.12});
  // A fence frames the southern entrance but leaves the central road open.
  for(const s of [-1,1])for(let i=0;i<5;i++) {
    const x=s*(5+i*2.1),z=25.2;
    block(scene,[.13,.8,.13],"#875b31",[x,.42,z],"wood");
    if(i<4)for(const y of [.3,.65])block(scene,[2.15,.08,.08],"#9d6c39",[x+s*1.05,y,z],"wood",undefined,false);
  }
  for(const[x,z]of[[-15,18],[-16,3],[-14,-19],[15,18],[16,-17],[-6,22]])garden(scene,x,z,Math.round(x*z+1600));
  const grass=new THREE.Group();scene.add(grass);
  const rand=seededRandom(311);
  for(let i=0;i<52;i++) {
    const x=-17+rand()*33,z=-23+rand()*47;
    if(Math.abs(x)<4.9||world.boxes.some(b=>Math.abs(x-b.x)<b.halfX+.7&&Math.abs(z-b.z)<b.halfZ+.7))continue;
    stroke(grass,[[x,.02,z],[x+.05,.23,z+.02],[x+.17,.32,z+.04]],i%3?"#547438":"#798b3f",.015);
    stroke(grass,[[x-.08,.02,z],[x-.13,.18,z-.04]],"#496434",.013);
  }
  batchDecoration(grass);
  // Rough paving seams and stone edges sit flush, so every path remains smooth.
  for(let i=0;i<18;i++) {
    const stone=part(scene,new THREE.CylinderGeometry(.32,.35,.025,6),paint(i%2?"#bbad81":"#b8a77a","stone"),[(i%2?3.55:-3.55)+Math.sin(i)*.16,.065,-20+i*2.5],undefined,false);stone.scale.z=1.4;
  }
  world.npcs=[
    npc(scene,-2,10,"Hana · gardener","#ac7583",["Welcome to Windflower Village, little guardian.","The shadow spirits gather in the grove to the east. Follow the sign."]),
    npc(scene,3,-2,"Taro · merchant","#628d7a",["My stall is open, but the grove has frightened away the travelers.","Try a quick thrust, a sweeping second strike, then a lunging finish."]),
    npc(scene,-3,-17,"Elder Sora","#b19546",["Our shrine watches over this valley.","Restore the five spirits in the eastern grove, then return to wander in peace."]),
    npc(scene,2,19,"Yui · traveler","#bd7054",["Such a fine white wolf!","Hold Shift to run. K dodges. The village is safe; the grove is not."],[new THREE.Vector3(2,0,19),new THREE.Vector3(-2,0,5)])
  ];
  for(const h of houses)batchHouse(h);
  // Static terrain, reeds, stones, lanterns and beams can share a submission.
  // Keep the animated wheel, petals, NPC joints and fading houses independent.
  const trees=[...scene.children].filter(n=>n.isGroup&&n.children.filter(c=>c.isSprite).length>=4);
  const animatedRoots=new Set([...houses,...world.npcs.map(n=>n.root),wheel,world.petals,...trees]);
  const staticMeshes=[];
  scene.updateMatrixWorld(true);
  scene.traverse(node=>{
    if(!node.isMesh)return;
    for(let parent=node;parent;parent=parent.parent)if(animatedRoots.has(parent))return;
    staticMeshes.push(node);
  });
  const scenery=new THREE.Group();scene.add(scenery);
  for(const mesh of staticMeshes)scenery.attach(mesh);
  batchDecoration(scenery);
  world.wheel=wheel;world.houses=houses;world.trees=trees;
  world.update=(dt,time)=>{
    wheel.rotation.z+=dt*.26;
    for(const n of world.npcs) {
      n.tag.visible=!world.player||n.root.position.distanceTo(world.player.position)<4;
      n.walking=false;
      if(n.route) {
        const target=n.route[n.index],delta=target.clone().sub(n.root.position);
        if(delta.length()<.25)n.index=(n.index+1)%n.route.length;
        else{n.root.position.addScaledVector(delta.normalize(),dt*.72);n.root.rotation.y=Math.atan2(delta.x,delta.z);n.walking=true;}
      } else if(world.player) {
        const delta=world.player.position.clone().sub(n.root.position);
        if(delta.length()<4) {const angle=Math.atan2(delta.x,delta.z);n.root.rotation.y+=Math.atan2(Math.sin(angle-n.root.rotation.y),Math.cos(angle-n.root.rotation.y))*(1-Math.exp(-dt*3));}
      }
      n.phase+=dt*(n.walking?5:1.8);
      n.body.position.y=.88+(n.walking?Math.sin(n.phase*2)*.016:Math.sin(n.phase)*.007);
      n.head.rotation.z=Math.sin(time*1.3+n.home.x)*.028;
      for(let i=0;i<2;i++){const s=i?1:-1;n.legs[i].rotation.x=n.walking?Math.sin(n.phase)*s*.3:0;n.arms[i].rotation.x=n.walking?Math.sin(n.phase)*-s*.2:Math.sin(time*1.7+i+n.home.x)*.045;}
    }
    if(world.player)for(const h of houses){
      const f=h.userData.fade,p=world.player.position;
      // Camera is offset +9,+8.5,+12. Test its ground-projected sight line.
      const dx=f.x-p.x,dz=f.z-p.z,cx=world.camera?world.camera.position.x-p.x:9,cz=world.camera?world.camera.position.z-p.z:12,cl=Math.hypot(cx,cz)||1,projection=(dx*cx+dz*cz)/(cl*cl);
      const lateral=Math.abs(dx*cz-dz*cx)/cl;
      const blocked=projection>0&&projection<1.1&&lateral<Math.max(f.w,f.d)*.45&&Math.hypot(dx,dz)<18;
      const target=blocked?.2:1;f.value+=(target-f.value)*(1-Math.exp(-dt*8));
      const faded=f.value<.995;
      for(const m of f.materials){m.transparent=faded;m.opacity=f.value;m.depthWrite=!faded;}
    }
  };
  return world;
}
