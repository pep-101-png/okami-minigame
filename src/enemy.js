import * as THREE from "three";
import { demon } from "./models.js";
import { ink } from "./art.js";

const smooth = (a, b, t) => THREE.MathUtils.lerp(a, b, THREE.MathUtils.smoothstep(t, 0, 1));
const pose = () => ({hip:0,knee:0,foot:0,shoulder:0,elbow:0});

/** Visual controller only: game AI owns world motion, collision and damage. */
export class EnemyController {
  constructor(scene, {index = 0, home} = {}) {
    this.root = this.mesh = demon();
    this.rig = this.root.userData.rig;
    this.index = index;
    this.phase = index * 1.17;
    this.time = index * .9;
    this.recoil = 0;
    this.recoilStrength = 1;
    this.recoilSide = 1;
    this.deathTime = -1;
    this.dead = false;
    this.finished = false;
    this.materials = [];
    const materialMap = new Map();
    // Outlines share an ink material elsewhere; clone them before dissolving.
    this.root.traverse(object => {
      if (!object.isMesh) return;
      const source = object.material;
      if (!materialMap.has(source)) materialMap.set(source, source === ink ? source.clone() : source);
      object.material = materialMap.get(source);
    });
    this.materials = [...materialMap.values()];
    if (home) this.root.position.copy(home);
    scene?.add(this.root);
    this.animate(0, {state:"idle"});
  }

  hit(direction, strength = 1) {
    this.recoil = .38;
    this.recoilStrength = Math.min(1.4, .7 + strength * .2);
    this.recoilSide = direction ? Math.sign(direction.x * Math.cos(this.root.rotation.y) - direction.z * Math.sin(this.root.rotation.y)) || 1 : 1;
  }

  kill() {
    if (this.dead) return;
    this.dead = true;
    this.deathTime = 0;
    this.finished = false;
    this.root.visible = true;
    for (const material of this.materials) {
      material.transparent = true;
      material.depthWrite = false;
      material.needsUpdate = true;
    }
  }

  reset() {
    this.dead = this.finished = false;
    this.deathTime = -1;
    this.recoil = 0;
    this.root.visible = true;
    this.root.scale.setScalar(1);
    for (const material of this.materials) {
      material.opacity = 1;
      material.transparent = false;
      material.depthWrite = true;
      material.needsUpdate = true;
    }
    this.animate(0, {state:"idle"});
  }

  animate(dt, {state = "idle", phase = 0, speed = 0, stun = 0, dead = false} = {}) {
    if ((dead || state === "dead") && !this.dead) this.kill();
    if (this.finished) return;
    dt = Math.min(dt, .05);
    this.time += dt;
    this.phase += dt * Math.max(0, speed) * 5.1;
    this.recoil = Math.max(0, this.recoil - dt);
    const r = this.rig, t = this.time;
    let height = .82, lean = -.1, twist = 0, roll = Math.sin(t * 1.8) * .025, headPitch = .06, headYaw = Math.sin(t * 1.15) * .07;
    const arms = [pose(),pose()], legs = [pose(),pose()];
    const walking = speed > .08 && ["walk","approach","return","patrol","idle"].includes(state);

    if (walking) {
      // Contact occupies 60% of the stride. Foot targets travel backward while
      // planted, then follow a lifted arc; two-bone IK bends knees naturally.
      for (let i = 0; i < 2; i++) {
        const p = ((this.phase / (Math.PI * 2) + i * .5) % 1 + 1) % 1;
        const contact = p < .6;
        const z = contact ? THREE.MathUtils.lerp(-.25,.23,p/.6) : THREE.MathUtils.lerp(.23,-.25,(p-.6)/.4);
        const lift = contact ? 0 : Math.sin((p-.6)/.4*Math.PI) * .18;
        const y = -.64 + lift;
        const d = Math.min(.706, Math.hypot(y,z));
        const knee = -Math.acos(THREE.MathUtils.clamp((d*d-.38*.38-.33*.33)/(2*.38*.33),-1,1));
        const hip = Math.atan2(-z,-y) - Math.atan2(.33*Math.sin(knee),.38+.33*Math.cos(knee));
        legs[i] = {hip,knee,foot:-hip-knee};
        arms[i].shoulder = -.12 - Math.sin(this.phase + i * Math.PI) * .25;
        arms[i].elbow = .15 + Math.sin(this.phase + i * Math.PI) * .1;
      }
      height -= Math.abs(Math.sin(this.phase)) * .025;
      twist = Math.sin(this.phase) * .09;
      roll = Math.sin(this.phase) * .04;
      headYaw = -twist * .6;
    } else {
      legs[0] = {hip:.32,knee:-.62,foot:.3};
      legs[1] = {hip:.12,knee:-.43,foot:.31};
      arms[0] = {shoulder:.1,elbow:.2};
      arms[1] = {shoulder:-.1,elbow:.33};
      height += Math.sin(t * 2.1) * .012;
    }

    if (state === "windup") {
      const p = THREE.MathUtils.smoothstep(phase,0,1);
      height -= .12 * p;
      lean = -.1 + .24 * p;
      twist = -.57 * p;
      headPitch = -.15 * p;
      headYaw = .25 * p;
      arms[0] = {shoulder: .55*p, elbow: .7*p};
      arms[1] = {shoulder: -1.7*p, elbow: 1.3*p};
      legs[0] = {hip:.65*p,knee:-1.03*p-.3,foot:.38*p+.3};
      legs[1] = {hip:-.16*p+.12,knee:-.5,foot:.38+.16*p};
    } else if (state === "lunge") {
      const reach = Math.sin(Math.min(1,phase/.65) * Math.PI*.5);
      height -= .08;
      lean = -.62*reach;
      twist = smooth(-.55,.45,phase);
      headPitch = .27*reach;
      headYaw = -twist*.45;
      arms[0] = {shoulder:1.03*reach, elbow:.12};
      arms[1] = {shoulder:1.55*reach, elbow:.11};
      legs[0] = {hip:.8,knee:-.98,foot:.18};
      legs[1] = {hip:-.64,knee:-.2,foot:.84};
    } else if (state === "recover") {
      const p = 1-THREE.MathUtils.smoothstep(phase,0,1);
      lean -= .42*p;
      twist = .35*p;
      height -= .08*p;
      arms[1] = {shoulder:1.2*p,elbow:.2+.2*p};
      arms[0] = {shoulder:.65*p,elbow:.18};
      legs[0] = {hip:.32+.35*p,knee:-.62-.2*p,foot:.3-.15*p};
    }

    if (this.recoil > 0 || stun > 0) {
      const p = this.recoil > 0 ? this.recoil / .38 : Math.min(1,stun/.4)*.28;
      const impact = Math.sin(Math.min(1,p*2)*Math.PI*.5)*this.recoilStrength;
      lean = .22 + impact*.34;
      roll = this.recoilSide*impact*.19;
      twist = this.recoilSide*impact*.28;
      headPitch = -.24*impact;
      arms[0] = {shoulder:-.3,elbow:1.1*impact};
      arms[1] = {shoulder:-.8*impact,elbow:1.15*impact};
      height -= .07*impact;
    }

    if (this.dead) {
      this.deathTime += dt;
      const fall = THREE.MathUtils.smoothstep(this.deathTime/.65,0,1);
      lean = THREE.MathUtils.lerp(.38,1.26,fall);
      roll = .15*Math.sin(fall*Math.PI);
      twist = -.26*fall;
      height = THREE.MathUtils.lerp(.82,.25,fall);
      headPitch = -.24;
      headYaw = .22;
      arms[0] = {shoulder:.7*fall,elbow:.8*fall};
      arms[1] = {shoulder:.95*fall,elbow:.5*fall};
      legs[0] = {hip:.8*fall,knee:-1.45*fall,foot:.65*fall};
      legs[1] = {hip:.45*fall,knee:-1.18*fall,foot:.73*fall};
      const opacity = 1-THREE.MathUtils.smoothstep(this.deathTime,.45,1.3);
      for (const material of this.materials) material.opacity = opacity;
      if (this.deathTime >= 1.3) {
        this.finished = true;
        this.root.visible = false;
      }
    }

    const damping = 1-Math.exp(-dt*17);
    // Initial evaluation also initializes the rest pose.
    const blend = dt === 0 ? 1 : damping;
    r.pelvis.position.y = THREE.MathUtils.lerp(r.pelvis.position.y,height,blend);
    r.torso.rotation.set(THREE.MathUtils.lerp(r.torso.rotation.x,lean,blend),THREE.MathUtils.lerp(r.torso.rotation.y,twist,blend),THREE.MathUtils.lerp(r.torso.rotation.z,roll,blend));
    r.head.rotation.set(THREE.MathUtils.lerp(r.head.rotation.x,headPitch,blend),THREE.MathUtils.lerp(r.head.rotation.y,headYaw,blend),-roll*.7);
    r.mantle.rotation.x = -.1 + Math.sin(t*3.4)*.045 - lean*.35;
    r.talisman.rotation.x = Math.sin(t*4.1)*.1 - lean*.25;
    for (let i=0;i<2;i++) {
      const a=r.arms[i], l=r.legs[i];
      a.shoulder.rotation.x = THREE.MathUtils.lerp(a.shoulder.rotation.x,arms[i].shoulder,blend);
      a.elbow.rotation.x = THREE.MathUtils.lerp(a.elbow.rotation.x,arms[i].elbow,blend);
      a.shoulder.rotation.z = a.side*(.14+Math.sin(t*1.9+i)*.015);
      l.hip.rotation.x = THREE.MathUtils.lerp(l.hip.rotation.x,legs[i].hip,blend);
      l.knee.rotation.x = THREE.MathUtils.lerp(l.knee.rotation.x,legs[i].knee,blend);
      l.foot.rotation.x = THREE.MathUtils.lerp(l.foot.rotation.x,legs[i].foot,blend);
    }
    const alert = state === "windup" ? .5+.5*Math.sin(t*22) : 0;
    for (const eye of r.eyes) eye.material.color.set(alert>.5 ? "#ffe6a1" : "#dcb16d");
  }

  dispose() {
    this.root.removeFromParent();
    const geometry=new Set();
    this.root.traverse(object=>{if(object.isMesh)geometry.add(object.geometry);});
    for(const item of geometry)item.dispose();
    for(const material of this.materials)material.dispose();
  }
}
