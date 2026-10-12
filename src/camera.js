import * as THREE from "three";

export class FollowCamera {
  constructor(camera, input) {
    this.camera = camera;
    this.input = input;
    this.focus = new THREE.Vector3(0, 0.8, 12);
    this.offset = new THREE.Vector3(9, 7.2, 12);
    this.lookAhead = new THREE.Vector3();
    this.initialized = false;
    this.shake = 0;
    this.zoom = 1;
    input.yaw = Math.atan2(this.offset.x, this.offset.z);
    camera.fov = 38;
    camera.updateProjectionMatrix();
  }
  impact(strength = 0.15) {
    this.shake = Math.max(this.shake, strength);
  }
  update(player, dt, speed = 0, velocity = null) {
    const ahead = velocity ? velocity.clone().multiplyScalar(0.17) : new THREE.Vector3();
    ahead.y = 0;
    this.lookAhead.lerp(ahead, 1 - Math.exp(-dt * 3.5));
    const target = player.position.clone();
    target.y = 0.85 + player.position.y * 0.35;
    target.add(this.lookAhead);
    this.focus.lerp(target, 1 - Math.exp(-dt * 9));
    const desiredZoom = this.input.zoom * (1 + Math.max(0, speed - 5) * 0.009);
    this.zoom = THREE.MathUtils.damp(this.zoom, desiredZoom, 5, dt);
    const desired = this.focus.clone().addScaledVector(this.offset, this.zoom);
    if (!this.initialized) {
      this.focus.copy(target);
      this.camera.position.copy(desired);
      this.initialized = true;
    } else this.camera.position.lerp(desired, 1 - Math.exp(-dt * 9));
    if (this.shake > 0.001) {
      this.camera.position.x += Math.sin(performance.now() * 0.07) * this.shake;
      this.camera.position.y += Math.sin(performance.now() * 0.09) * this.shake * 0.45;
      this.shake *= Math.exp(-dt * 18);
    }
    this.camera.lookAt(this.focus);
  }
}
