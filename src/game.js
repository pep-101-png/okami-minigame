import * as THREE from 'three';
import {wolf,demon} from './models.js';
export class Game {
 constructor(scene,input,world,onEnd){this.scene=scene;this.input=input;this.world=world;this.onEnd=onEnd;this.player=wolf();scene.add(this.player.root);this.player.root.position.set(0,0,6);this.hp=100;this.kills=0;this.enemies=[];this.active=false;this.time=0;this.velocityY=0;this.attackTime=0;this.combo=0;this.comboWindow=0;this.invulnerable=0;
 for(const [x,z] of [[-5,-5],[5,-5],[0,-9],[-7,1],[7,1]]){const mesh=demon();mesh.position.set(x,0,z);scene.add(mesh);const canvas=document.createElement('canvas');canvas.width=128;canvas.height=16;const texture=new THREE.CanvasTexture(canvas);const bar=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,depthTest:false}));bar.scale.set(1.1,.14,1);bar.position.y=2;mesh.add(bar);this.enemies.push({mesh,hp:3,cooldown:1,texture,canvas,bar});this.drawBar(this.enemies.at(-1));} }
 drawBar(e){const c=e.canvas.getContext('2d');c.clearRect(0,0,128,16);c.fillStyle='#253b44';c.fillRect(0,0,128,16);c.fillStyle='#e79d7a';c.fillRect(2,2,124*e.hp/3,12);e.texture.needsUpdate=true;}
 collide(pos,r=.5){const len=Math.hypot(pos.x,pos.z);if(len>11.4){pos.x*=11.4/len;pos.z*=11.4/len;}for(const o of this.world.obstacles){const dx=pos.x-o.x,dz=pos.z-o.z,d=Math.hypot(dx,dz),min=r+o.r;if(d<min){pos.x=o.x+(d?dx/d:1)*min;pos.z=o.z+(d?dz/d:0)*min;}}}
 update(dt){this.time+=dt;for(const p of this.world.petals.children){p.position.y-=dt*.3;p.position.x+=Math.sin(this.time+p.position.z)*dt*.1;p.rotation.z+=dt;if(p.position.y<0)p.position.y=8;}
 if(!this.active)return;const root=this.player.root;this.invulnerable=Math.max(0,this.invulnerable-dt);this.comboWindow=Math.max(0,this.comboWindow-dt);
 let x=Number(this.input.keys.has('KeyD'))-Number(this.input.keys.has('KeyA')),z=Number(this.input.keys.has('KeyS'))-Number(this.input.keys.has('KeyW'));const moving=x!==0||z!==0;
 if(moving){const direction=new THREE.Vector3(x,0,z).normalize().applyAxisAngle(new THREE.Vector3(0,1,0),this.input.yaw);root.position.addScaledVector(direction,dt*(this.attackTime>0?2:5));const target=Math.atan2(-direction.x,-direction.z);root.rotation.y+=Math.atan2(Math.sin(target-root.rotation.y),Math.cos(target-root.rotation.y))*Math.min(1,dt*12);}
 this.collide(root.position);if(this.input.consume('jump')&&root.position.y<=.001)this.velocityY=6;this.velocityY-=16*dt;root.position.y=Math.max(0,root.position.y+this.velocityY*dt);if(root.position.y===0)this.velocityY=0;
 this.player.legs.forEach((leg,i)=>leg.rotation.x=moving?Math.sin(this.time*14+(i===0||i===3?0:Math.PI))*.55:0);this.player.tail.rotation.z=Math.sin(this.time*4)*.1;
 if(this.input.consume('attack')&&this.attackTime<=0){this.combo=this.comboWindow>0?this.combo%3+1:1;this.comboWindow=1;this.attackTime=.42;this.didHit=false;}
 if(this.attackTime>0){this.attackTime=Math.max(0,this.attackTime-dt);const phase=1-this.attackTime/.42;this.player.spear.position.z=-1.25-Math.sin(phase*Math.PI)*(.45+this.combo*.18);this.player.body.position.z=-Math.sin(phase*Math.PI)*.12;
 if(phase>.35&&!this.didHit){this.didHit=true;const forward=new THREE.Vector3(0,0,-1).applyAxisAngle(new THREE.Vector3(0,1,0),root.rotation.y);for(const e of this.enemies){if(e.hp<=0)continue;const diff=e.mesh.position.clone().sub(root.position);diff.y=0;const distance=diff.length();if(distance<3.8&&diff.normalize().dot(forward)>.65&&root.position.y<1.3){e.hp-=this.combo===3?2:1;e.mesh.position.addScaledVector(forward,.7);e.cooldown=.6;this.drawBar(e);if(e.hp<=0){e.mesh.visible=false;this.kills++;if(this.kills===5)this.end(true);}}}}
 }else{this.player.spear.position.z=-1.25;this.player.body.position.z=0;}
 for(let i=0;i<this.enemies.length;i++){const e=this.enemies[i];if(e.hp<=0)continue;e.cooldown-=dt;const delta=root.position.clone().sub(e.mesh.position);delta.y=0;const distance=delta.length();if(distance>1.35){delta.normalize();e.mesh.position.addScaledVector(delta,dt*(1.15+i*.09));this.collide(e.mesh.position,.6);}e.mesh.rotation.y=Math.atan2(-delta.x,-delta.z);e.mesh.position.y=Math.sin(this.time*3+i)*.05;
 for(let j=0;j<i;j++){const other=this.enemies[j];if(other.hp<=0)continue;const d=e.mesh.position.clone().sub(other.mesh.position);d.y=0;if(d.length()<1.2&&d.length()>.001)e.mesh.position.addScaledVector(d.normalize(),dt*1.5);}
 if(distance<1.65&&e.cooldown<=0&&root.position.y<.7&&this.invulnerable<=0){this.hp=Math.max(0,this.hp-12);this.invulnerable=.7;e.cooldown=1.3;if(this.hp===0)this.end(false);}}
 this.player.body.visible=this.invulnerable<=0||Math.floor(this.time*15)%2===0;
 }
 end(win){this.active=false;document.exitPointerLock?.();this.onEnd(win);}
}
