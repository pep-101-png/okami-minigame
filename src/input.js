import {requestPointer} from './pointer.js';
export class Input {
  constructor(canvas) {
    this.keys = new Set(); this.attack = false; this.jump = false; this.yaw = 0; this.pitch = .38;
    window.addEventListener('keydown', e => { if(['Space','KeyW','KeyA','KeyS','KeyD'].includes(e.code)) e.preventDefault(); this.keys.add(e.code); if(e.code==='Space'&&!e.repeat)this.jump=true; if(e.code==='KeyJ'&&!e.repeat)this.attack=true; });
    window.addEventListener('keyup', e=>this.keys.delete(e.code));
    window.addEventListener('blur',()=>this.keys.clear());
    let dragging=false;
    canvas.addEventListener('mousedown',()=>{dragging=true;this.attack=true;if(document.pointerLockElement!==canvas)requestPointer(canvas);});
    window.addEventListener('mouseup',()=>dragging=false);
    window.addEventListener('mousemove',e=>{if(document.pointerLockElement===canvas||dragging){this.yaw-=e.movementX*.003;this.pitch=Math.max(.12,Math.min(.85,this.pitch+e.movementY*.002));}});
  }
  consume(name){const value=this[name];this[name]=false;return value;}
}
