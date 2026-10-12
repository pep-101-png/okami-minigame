import * as THREE from "three";

function brushTexture(kind = "stroke") {
  const canvas = document.createElement("canvas");
  canvas.width = 128; canvas.height = 64;
  const ctx = canvas.getContext("2d");
  if (kind === "paper") {
    ctx.fillStyle="#f5e7bd";
    ctx.beginPath(); ctx.moveTo(8,2); ctx.lineTo(120,7); ctx.lineTo(115,60); ctx.lineTo(13,63); ctx.closePath(); ctx.fill();
    ctx.strokeStyle="#786348"; ctx.lineWidth=3;
    for (let i=0;i<3;i++) {ctx.beginPath();ctx.moveTo(32,15+i*14);ctx.lineTo(58,13+i*14);ctx.lineTo(72,22+i*12);ctx.lineTo(88,15+i*13);ctx.stroke();}
  } else {
    ctx.fillStyle="white";
    ctx.beginPath(); ctx.moveTo(1,34);
    for(let i=0;i<9;i++) ctx.lineTo(i*16,13+Math.sin(i*2.9)*6);
    ctx.lineTo(127,30);
    for(let i=8;i>=0;i--) ctx.lineTo(i*16,48+Math.cos(i*3.1)*5);
    ctx.closePath(); ctx.fill();
    ctx.globalCompositeOperation="destination-out";
    for(let i=0;i<90;i++) {ctx.fillStyle=`rgba(0,0,0,${.1+(i%7)*.1})`;ctx.fillRect((i*47)%128,(i*29)%64,2+(i%5),1);}
  }
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  return map;
}

/** Bounded, local painted effects. No blood, external textures or assets. */
export class Effects {
  constructor(scene) {
    this.scene = scene;
    this.items = [];
    this.geometry = new THREE.PlaneGeometry(1,1);
    this.strokeMap = brushTexture();
    this.paperMap = brushTexture("paper");
    this.trailLast = null;
    this.trailAge = 0;
    this.limit = 240;
  }
  add(mesh, life, velocity = new THREE.Vector3(), options = {}) {
    if (this.items.length >= this.limit) this.remove(0);
    this.scene.add(mesh);
    this.items.push({mesh,life,total:life,velocity,gravity:options.gravity??0,spin:options.spin??0,grow:options.grow??0,owned:options.owned??false,opacity:mesh.material.opacity});
    return mesh;
  }
  chip(position, color, size, life, velocity, options = {}) {
    const mesh = new THREE.Mesh(this.geometry,new THREE.MeshBasicMaterial({color,map:options.paper?this.paperMap:this.strokeMap,side:THREE.DoubleSide,transparent:true,depthWrite:false,opacity:options.opacity??.9}));
    mesh.position.copy(position);
    mesh.scale.set(size[0],size[1],1);
    mesh.rotation.set(Math.random()*Math.PI,Math.random()*Math.PI,Math.random()*Math.PI*2);
    return this.add(mesh,life,velocity,options);
  }
  burst(position,count=12,color="#bf4935") {
    const p=position.clone().add(new THREE.Vector3(0,.8,0));
    for(let i=0;i<Math.min(count,36);i++) this.chip(p,color,[.15+Math.random()*.18,.055+Math.random()*.06],.35+Math.random()*.35,new THREE.Vector3((Math.random()-.5)*4,1+Math.random()*2.3,(Math.random()-.5)*4),{gravity:5,spin:(Math.random()-.5)*7});
  }
  dust(position,{count=5}={}) {
    const p=position.clone(); p.y+=.06;
    for(let i=0;i<Math.min(count,10);i++) this.chip(p,"#d7c8a0",[.22+Math.random()*.2,.12],.35+Math.random()*.3,new THREE.Vector3((Math.random()-.5)*1.6,.3+Math.random()*.35,(Math.random()-.5)*1.6),{grow:1.5,opacity:.3,spin:.2});
  }
  impact(position,direction=new THREE.Vector3(0,0,-1),{heavy=false}={}) {
    const p=position.clone().add(new THREE.Vector3(0,1,0));
    const count=heavy?22:13;
    for(let i=0;i<count;i++) {
      const a=i/count*Math.PI*2, s=(heavy?3.1:2.1)*( .6+Math.random()*.7 );
      this.chip(p,i%4===0?"#fff6d4":i%3===0?"#59463a":"#deb867",[.18+Math.random()*.25,.05+Math.random()*.045],.24+Math.random()*.3,new THREE.Vector3(Math.cos(a)*s+direction.x,Math.sin(a)*s*.65+1.3,Math.sin(a)*s+direction.z),{gravity:3,spin:Math.random()*9-4});
    }
    this.slash(p,direction,heavy?1.55:1,"#fff3c5");
    if(heavy) this.groundWash(position,"#bb8d4b",1.8,.45);
  }
  slash(position,direction,scale=1,color="#eee3b9") {
    const mesh=new THREE.Mesh(this.geometry,new THREE.MeshBasicMaterial({color,map:this.strokeMap,side:THREE.DoubleSide,transparent:true,depthWrite:false,opacity:.8}));
    mesh.position.copy(position);
    mesh.rotation.y=Math.atan2(direction.x,direction.z);
    mesh.rotation.z=-.55;
    mesh.scale.set(scale,.10*scale,1);
    this.add(mesh,.13,new THREE.Vector3(),{grow:3});
  }
  groundWash(position,color,size,life=.7) {
    const geometry=new THREE.CircleGeometry(1,18);
    const vertices=geometry.getAttribute("position");
    for(let i=1;i<vertices.count;i++) {const m=.88+Math.sin(i*7.3)*.12;vertices.setX(i,vertices.getX(i)*m);vertices.setY(i,vertices.getY(i)*m);}
    const mesh=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color,map:this.strokeMap,side:THREE.DoubleSide,transparent:true,depthWrite:false,opacity:.28}));
    mesh.position.copy(position);mesh.position.y+=.025;
    mesh.rotation.set(-Math.PI/2,0,Math.random()*6);
    mesh.scale.setScalar(size*.4);
    this.add(mesh,life,new THREE.Vector3(),{grow:2,owned:true});
  }
  death(position) {
    const p=position.clone().add(new THREE.Vector3(0,.85,0));
    this.groundWash(position,"#343d3c",1.5,1.25);
    for(let i=0;i<28;i++) {
      const a=i/28*Math.PI*2,r=.4+Math.random()*1.1;
      this.chip(p,i%5===0?"#e8d49f":i%3===0?"#9ca881":"#414d48",[.12+Math.random()*.3,.06+Math.random()*.12],.8+Math.random()*.7,new THREE.Vector3(Math.cos(a)*r,.8+Math.random()*1.6,Math.sin(a)*r),{spin:(Math.random()-.5)*6,grow:.3,gravity:-.1,opacity:.8});
    }
    for(let i=0;i<7;i++) this.chip(p,"#fff3cf",[.1,.24],1.05+Math.random()*.6,new THREE.Vector3((Math.random()-.5)*1.8,1+Math.random()*1.2,(Math.random()-.5)*1.8),{paper:true,spin:(Math.random()-.5)*5,gravity:.5});
    for(let i=0;i<8;i++) this.chip(p,"#efb5a6",[.12,.055],1.4+Math.random()*.5,new THREE.Vector3((Math.random()-.5)*2,.7+Math.random(),(Math.random()-.5)*2),{gravity:.7,spin:2});
  }
  /** Call with two world-space weapon points while its hit window is active. */
  trail(tip,heel,combo=1) {
    if(!tip||!heel) return;
    if(this.trailLast && this.trailLast.combo===combo && this.trailAge<.08 && this.trailLast.tip.distanceToSquared(tip)<16) {
      const last=this.trailLast;
      const geometry=new THREE.BufferGeometry();
      geometry.setAttribute("position",new THREE.Float32BufferAttribute([...tip.toArray(),...heel.toArray(),...last.tip.toArray(),...last.heel.toArray()],3));
      geometry.setAttribute("uv",new THREE.Float32BufferAttribute([1,1,1,0,0,1,0,0],2));
      geometry.setIndex([0,1,2,1,3,2]);geometry.computeVertexNormals();
      const mesh=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color:combo===3?"#f1cf86":"#e8d8ad",map:this.strokeMap,side:THREE.DoubleSide,transparent:true,depthWrite:false,opacity:combo===3?.6:.36}));
      this.add(mesh,.16,new THREE.Vector3(),{owned:true});
    }
    this.trailLast={tip:tip.clone(),heel:heel.clone(),combo};this.trailAge=0;
  }
  remove(index) {
    const p=this.items[index];
    if(!p)return;
    this.scene.remove(p.mesh);p.mesh.material.dispose();
    if(p.owned)p.mesh.geometry.dispose();
    this.items.splice(index,1);
  }
  clear() {
    while(this.items.length)this.remove(this.items.length-1);
    this.trailLast=null;
  }
  update(dt) {
    this.trailAge+=dt;
    if(this.trailAge>.1)this.trailLast=null;
    for(let i=this.items.length-1;i>=0;i--) {
      const p=this.items[i];p.life-=dt;
      if(p.life<=0) {this.remove(i);continue;}
      p.velocity.y-=dt*p.gravity;
      p.mesh.position.addScaledVector(p.velocity,dt);
      p.mesh.rotation.z+=dt*p.spin;
      p.mesh.rotation.x+=dt*p.spin*.23;
      if(p.grow)p.mesh.scale.multiplyScalar(Math.max(.01,1+dt*p.grow));
      p.mesh.material.opacity=p.opacity*Math.pow(Math.max(0,p.life/p.total),.8);
    }
  }
  dispose() {this.clear();this.geometry.dispose();this.strokeMap.dispose();this.paperMap.dispose();}
}
