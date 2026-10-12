import * as THREE from "three";
import { paint } from "./art.js";
export class Effects {
  constructor(scene) {
    this.scene = scene;
    this.items = [];
    this.geometry = new THREE.PlaneGeometry(0.18, 0.07);
    this.material = paint("#c53626");
  }
  burst(position, count = 12, color = "#c53626") {
    for (let i = 0; i < count; i++) {
      const mesh = new THREE.Mesh(
        this.geometry,
        new THREE.MeshBasicMaterial({
          color,
          side: THREE.DoubleSide,
          transparent: true,
        }),
      );
      mesh.position.copy(position);
      mesh.position.y += 0.8;
      mesh.rotation.set(
        Math.random() * 6,
        Math.random() * 6,
        Math.random() * 6,
      );
      this.scene.add(mesh);
      this.items.push({
        mesh,
        life: 0.6,
        velocity: new THREE.Vector3(
          (Math.random() - 0.5) * 5,
          Math.random() * 4,
          (Math.random() - 0.5) * 5,
        ),
      });
    }
  }
  update(dt) {
    for (let i = this.items.length - 1; i >= 0; i--) {
      const p = this.items[i];
      p.life -= dt;
      p.velocity.y -= dt * 7;
      p.mesh.position.addScaledVector(p.velocity, dt);
      p.mesh.rotation.z += dt * 4;
      p.mesh.material.opacity = Math.max(0, p.life / 0.6);
      if (p.life <= 0) {
        this.scene.remove(p.mesh);
        p.mesh.material.dispose();
        this.items.splice(i, 1);
      }
    }
  }
}
