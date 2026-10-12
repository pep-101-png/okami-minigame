import * as THREE from "three";
export class FollowCamera {
  constructor(camera, input) {
    this.camera = camera;
    this.input = input;
    this.focus = new THREE.Vector3(0, 1, 12);
    this.initialized = false;
    input.yaw = 0.65;
  }
  update(player, dt) {
    const target = player.position.clone().add(new THREE.Vector3(0, 0.8, 0));
    this.focus.lerp(target, 1 - Math.exp(-dt * 12));
    const offset = new THREE.Vector3(9, 8.5, 12),
      desired = this.focus.clone().add(offset);
    if (!this.initialized) {
      this.camera.position.copy(desired);
      this.initialized = true;
    } else this.camera.position.lerp(desired, 1 - Math.exp(-dt * 12));
    this.camera.lookAt(this.focus);
    this.camera.fov = 38;
    this.camera.updateProjectionMatrix();
  }
}
