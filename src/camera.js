import * as THREE from "three";
export class FollowCamera {
  constructor(camera, input) {
    this.camera = camera;
    this.input = input;
    this.focus = new THREE.Vector3(0, 1.1, 6);
    this.initialized = false;
  }
  update(player, dt, speed = 0) {
    const target = player.position.clone().add(new THREE.Vector3(0, 1.05, 0));
    this.focus.lerp(target, 1 - Math.exp(-dt * 16));
    const distance = 7 + Math.min(speed / 8, 1) * 0.65,
      pitch = this.input.pitch;
    const offset = new THREE.Vector3(
      Math.sin(this.input.yaw) * distance * Math.cos(pitch),
      0.65 + distance * Math.sin(pitch),
      Math.cos(this.input.yaw) * distance * Math.cos(pitch),
    );
    const desired = this.focus.clone().add(offset);
    if (!this.initialized) {
      this.camera.position.copy(desired);
      this.initialized = true;
    } else this.camera.position.lerp(desired, 1 - Math.exp(-dt * 14));
    this.camera.lookAt(this.focus);
    this.camera.fov = THREE.MathUtils.damp(
      this.camera.fov,
      52 + speed * 0.65,
      5,
      dt,
    );
    this.camera.updateProjectionMatrix();
  }
}
