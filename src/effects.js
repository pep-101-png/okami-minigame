import * as THREE from "three";

function brushTexture(kind = "stroke") {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  if (kind === "paper") {
    ctx.fillStyle = "#f5e7bd";
    ctx.beginPath();
    ctx.moveTo(8, 2);
    ctx.lineTo(120, 7);
    ctx.lineTo(115, 60);
    ctx.lineTo(13, 63);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = "#786348";
    ctx.lineWidth = 3;
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.moveTo(32, 15 + i * 14);
      ctx.lineTo(58, 13 + i * 14);
      ctx.lineTo(72, 22 + i * 12);
      ctx.lineTo(88, 15 + i * 13);
      ctx.stroke();
    }
  } else if (kind === "leaf") {
    ctx.fillStyle = "#fff9e2";
    ctx.beginPath();
    ctx.moveTo(6, 52);
    ctx.quadraticCurveTo(24, 0, 115, 8);
    ctx.quadraticCurveTo(108, 57, 6, 52);
    ctx.fill();
    ctx.strokeStyle = "#526b4055";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(11, 49);
    ctx.lineTo(100, 15);
    ctx.stroke();
  } else if (kind === "flower") {
    ctx.fillStyle = "#fff7df";
    for (let i = 0; i < 5; i++) {
      const a = (i * Math.PI * 2) / 5;
      ctx.beginPath();
      ctx.ellipse(
        64 + Math.cos(a) * 20,
        32 + Math.sin(a) * 18,
        17,
        10,
        a,
        0,
        Math.PI * 2,
      );
      ctx.fill();
    }
    ctx.fillStyle = "#dfb54f";
    ctx.beginPath();
    ctx.arc(64, 32, 7, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.fillStyle = "white";
    ctx.beginPath();
    ctx.moveTo(1, 34);
    for (let i = 0; i < 9; i++) ctx.lineTo(i * 16, 13 + Math.sin(i * 2.9) * 6);
    ctx.lineTo(127, 30);
    for (let i = 8; i >= 0; i--) ctx.lineTo(i * 16, 48 + Math.cos(i * 3.1) * 5);
    ctx.closePath();
    ctx.fill();
    ctx.globalCompositeOperation = "destination-out";
    for (let i = 0; i < 90; i++) {
      ctx.fillStyle = `rgba(0,0,0,${0.1 + (i % 7) * 0.1})`;
      ctx.fillRect((i * 47) % 128, (i * 29) % 64, 2 + (i % 5), 1);
    }
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
    this.geometry = new THREE.PlaneGeometry(1, 1);
    this.strokeMap = brushTexture();
    this.paperMap = brushTexture("paper");
    this.leafMap = brushTexture("leaf");
    this.flowerMap = brushTexture("flower");
    this.trailLast = null;
    this.trailAge = 0;
    this.spectralAge = 0;
    this.limit = 240;
  }
  add(mesh, life, velocity = new THREE.Vector3(), options = {}) {
    if (this.items.length >= this.limit) this.remove(0);
    this.scene.add(mesh);
    this.items.push({
      mesh,
      life,
      total: life,
      velocity,
      gravity: options.gravity ?? 0,
      spin: options.spin ?? 0,
      grow: options.grow ?? 0,
      owned: options.owned ?? false,
      opacity: mesh.material.opacity,
      wind: options.wind ?? 0,
      phase: Math.random() * Math.PI * 2,
    });
    return mesh;
  }
  chip(position, color, size, life, velocity, options = {}) {
    const mesh = new THREE.Mesh(
      this.geometry,
      new THREE.MeshBasicMaterial({
        color,
        map: options.paper ? this.paperMap : this.strokeMap,
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: false,
        opacity: options.opacity ?? 0.9,
      }),
    );
    mesh.position.copy(position);
    mesh.scale.set(size[0], size[1], 1);
    mesh.rotation.set(
      Math.random() * Math.PI,
      Math.random() * Math.PI,
      Math.random() * Math.PI * 2,
    );
    return this.add(mesh, life, velocity, options);
  }
  burst(position, count = 12, color = "#bf4935") {
    const p = position.clone().add(new THREE.Vector3(0, 0.8, 0));
    for (let i = 0; i < Math.min(count, 36); i++)
      this.chip(
        p,
        color,
        [0.15 + Math.random() * 0.18, 0.055 + Math.random() * 0.06],
        0.35 + Math.random() * 0.35,
        new THREE.Vector3(
          (Math.random() - 0.5) * 4,
          1 + Math.random() * 2.3,
          (Math.random() - 0.5) * 4,
        ),
        { gravity: 5, spin: (Math.random() - 0.5) * 7 },
      );
  }
  dust(position, { count = 5 } = {}) {
    const p = position.clone();
    p.y += 0.06;
    for (let i = 0; i < Math.min(count, 10); i++)
      this.chip(
        p,
        "#d7c8a0",
        [0.22 + Math.random() * 0.2, 0.12],
        0.35 + Math.random() * 0.3,
        new THREE.Vector3(
          (Math.random() - 0.5) * 1.6,
          0.3 + Math.random() * 0.35,
          (Math.random() - 0.5) * 1.6,
        ),
        { grow: 1.5, opacity: 0.3, spin: 0.2 },
      );
  }
  impact(
    position,
    direction = new THREE.Vector3(0, 0, -1),
    { heavy = false } = {},
  ) {
    const p = position.clone().add(new THREE.Vector3(0, 1, 0));
    const count = heavy ? 22 : 13;
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2,
        s = (heavy ? 3.1 : 2.1) * (0.6 + Math.random() * 0.7);
      this.chip(
        p,
        i % 4 === 0 ? "#fff6d4" : i % 3 === 0 ? "#59463a" : "#deb867",
        [0.18 + Math.random() * 0.25, 0.05 + Math.random() * 0.045],
        0.24 + Math.random() * 0.3,
        new THREE.Vector3(
          Math.cos(a) * s + direction.x,
          Math.sin(a) * s * 0.65 + 1.3,
          Math.sin(a) * s + direction.z,
        ),
        { gravity: 3, spin: Math.random() * 9 - 4 },
      );
    }
    this.slash(p, direction, heavy ? 1.55 : 1, "#fff3c5");
    if (heavy) this.groundWash(position, "#bb8d4b", 1.8, 0.45);
  }
  slash(position, direction, scale = 1, color = "#eee3b9") {
    const mesh = new THREE.Mesh(
      this.geometry,
      new THREE.MeshBasicMaterial({
        color,
        map: this.strokeMap,
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: false,
        opacity: 0.8,
      }),
    );
    mesh.position.copy(position);
    mesh.rotation.y = Math.atan2(direction.x, direction.z);
    mesh.rotation.z = -0.55;
    mesh.scale.set(scale, 0.1 * scale, 1);
    this.add(mesh, 0.13, new THREE.Vector3(), { grow: 3 });
  }
  groundWash(position, color, size, life = 0.7) {
    const geometry = new THREE.CircleGeometry(1, 18);
    const vertices = geometry.getAttribute("position");
    for (let i = 1; i < vertices.count; i++) {
      const m = 0.88 + Math.sin(i * 7.3) * 0.12;
      vertices.setX(i, vertices.getX(i) * m);
      vertices.setY(i, vertices.getY(i) * m);
    }
    const mesh = new THREE.Mesh(
      geometry,
      new THREE.MeshBasicMaterial({
        color,
        map: this.strokeMap,
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: false,
        opacity: 0.28,
      }),
    );
    mesh.position.copy(position);
    mesh.position.y += 0.025;
    mesh.rotation.set(-Math.PI / 2, 0, Math.random() * 6);
    mesh.scale.setScalar(size * 0.4);
    this.add(mesh, life, new THREE.Vector3(), { grow: 2, owned: true });
  }
  death(position) {
    const p = position.clone().add(new THREE.Vector3(0, 0.85, 0));
    this.groundWash(position, "#343d3c", 1.5, 1.25);
    for (let i = 0; i < 28; i++) {
      const a = (i / 28) * Math.PI * 2,
        r = 0.4 + Math.random() * 1.1;
      this.chip(
        p,
        i % 5 === 0 ? "#e8d49f" : i % 3 === 0 ? "#9ca881" : "#414d48",
        [0.12 + Math.random() * 0.3, 0.06 + Math.random() * 0.12],
        0.8 + Math.random() * 0.7,
        new THREE.Vector3(
          Math.cos(a) * r,
          0.8 + Math.random() * 1.6,
          Math.sin(a) * r,
        ),
        {
          spin: (Math.random() - 0.5) * 6,
          grow: 0.3,
          gravity: -0.1,
          opacity: 0.8,
        },
      );
    }
    for (let i = 0; i < 7; i++)
      this.chip(
        p,
        "#fff3cf",
        [0.1, 0.24],
        1.05 + Math.random() * 0.6,
        new THREE.Vector3(
          (Math.random() - 0.5) * 1.8,
          1 + Math.random() * 1.2,
          (Math.random() - 0.5) * 1.8,
        ),
        { paper: true, spin: (Math.random() - 0.5) * 5, gravity: 0.5 },
      );
    for (let i = 0; i < 8; i++)
      this.chip(
        p,
        "#efb5a6",
        [0.12, 0.055],
        1.4 + Math.random() * 0.5,
        new THREE.Vector3(
          (Math.random() - 0.5) * 2,
          0.7 + Math.random(),
          (Math.random() - 0.5) * 2,
        ),
        { gravity: 0.7, spin: 2 },
      );
  }
  /** Call with two world-space weapon points while its hit window is active. */
  trail(tip, heel, combo = 1) {
    if (!tip || !heel) return;
    if (
      this.trailLast &&
      this.trailLast.combo === combo &&
      this.trailAge < 0.08 &&
      this.trailLast.tip.distanceToSquared(tip) < 16
    ) {
      const last = this.trailLast;
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(
          [
            ...tip.toArray(),
            ...heel.toArray(),
            ...last.tip.toArray(),
            ...last.heel.toArray(),
          ],
          3,
        ),
      );
      geometry.setAttribute(
        "uv",
        new THREE.Float32BufferAttribute([1, 1, 1, 0, 0, 1, 0, 0], 2),
      );
      geometry.setIndex([0, 1, 2, 1, 3, 2]);
      geometry.computeVertexNormals();
      const mesh = new THREE.Mesh(
        geometry,
        new THREE.MeshBasicMaterial({
          color: combo === 3 ? "#9ae9e0" : "#cfefdd",
          map: this.strokeMap,
          side: THREE.DoubleSide,
          transparent: true,
          depthWrite: false,
          opacity: combo === 3 ? 0.7 : 0.46,
        }),
      );
      this.add(mesh, 0.16, new THREE.Vector3(), { owned: true });
    }
    this.trailLast = { tip: tip.clone(), heel: heel.clone(), combo };
    this.trailAge = 0;
  }
  spectralWeapon(position) {
    if (this.spectralAge < 0.075) return;
    this.spectralAge = 0;
    for (let i = 0; i < 2; i++)
      this.chip(
        position,
        i ? "#efffea" : "#94dfd8",
        [0.09, 0.035],
        0.35 + Math.random() * 0.25,
        new THREE.Vector3(
          (Math.random() - 0.5) * 0.6,
          0.35 + Math.random() * 0.3,
          (Math.random() - 0.5) * 0.6,
        ),
        { spin: 0.6, grow: 0.4, opacity: 0.6 },
      );
  }
  foliage(position, forward) {
    const flower = new THREE.Mesh(
      this.geometry,
      new THREE.MeshBasicMaterial({
        color: ["#efb4c0", "#fff0db", "#de9baf"][Math.floor(Math.random() * 3)],
        map: this.flowerMap,
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: false,
        opacity: 0.8,
      }),
    );
    flower.position.copy(position);
    flower.position.x += (Math.random() - 0.5) * 0.45;
    flower.position.z += (Math.random() - 0.5) * 0.45;
    flower.position.y = 0.035;
    flower.rotation.set(-Math.PI / 2, 0, Math.random() * Math.PI * 2);
    const size = 0.26 + Math.random() * 0.22;
    flower.scale.set(size, size, 1);
    this.add(flower, 3.2, new THREE.Vector3(), { grow: 0.1 });
    const sprig = new THREE.Mesh(
      this.geometry,
      new THREE.MeshBasicMaterial({
        color: "#779a57",
        map: this.leafMap,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false,
        opacity: 0.9,
      }),
    );
    sprig.position.copy(flower.position);
    sprig.position.y = 0.13;
    sprig.scale.set(0.23, 0.32, 1);
    sprig.rotation.y = Math.random() * Math.PI;
    this.add(sprig, 2.5, new THREE.Vector3(), { wind: 0.07 });
    const bloom = flower.clone();
    bloom.material = flower.material.clone();
    bloom.position.y = 0.25;
    bloom.scale.multiplyScalar(0.68);
    bloom.rotation.x = -Math.PI * 0.28;
    this.add(bloom, 2.6, new THREE.Vector3(), { wind: 0.07, grow: 0.08 });
    this.chip(
      position.clone().add(new THREE.Vector3(0, 0.25, 0)),
      "#f4b8c6",
      [0.12, 0.065],
      1.4,
      forward
        .clone()
        .multiplyScalar(-0.65)
        .add(
          new THREE.Vector3(
            (Math.random() - 0.5) * 0.7,
            0.45,
            (Math.random() - 0.5) * 0.7,
          ),
        ),
      { spin: 1.2, gravity: 0.2, wind: 0.3 },
    );
    for (let i = 0; i < 2; i++) {
      const leaf = new THREE.Mesh(
        this.geometry,
        new THREE.MeshBasicMaterial({
          color: i ? "#d9c56a" : "#88af69",
          map: this.leafMap,
          side: THREE.DoubleSide,
          transparent: true,
          depthWrite: false,
          opacity: 0.8,
        }),
      );
      leaf.position.copy(position);
      leaf.position.y = 0.18 + i * 0.13;
      leaf.scale.set(0.19, 0.1, 1);
      leaf.rotation.set(
        Math.random() * 3,
        Math.random() * 3,
        Math.random() * 6,
      );
      this.add(
        leaf,
        1.1 + Math.random() * 0.5,
        forward
          .clone()
          .multiplyScalar(-0.3)
          .add(
            new THREE.Vector3(
              (Math.random() - 0.5) * 0.5,
              0.35,
              (Math.random() - 0.5) * 0.5,
            ),
          ),
        { spin: 0.6 + Math.random() * 1.1, gravity: 0.25, wind: 0.25 },
      );
    }
  }
  chargeAura(position, ratio, heavy = false) {
    const p = position.clone();
    p.y += 0.9;
    for (let i = 0; i < 3; i++) {
      const a = Math.random() * Math.PI * 2,
        r = 0.55;
      this.chip(
        p
          .clone()
          .add(
            new THREE.Vector3(
              Math.cos(a) * r,
              Math.random() * 0.3,
              Math.sin(a) * r,
            ),
          ),
        heavy ? "#eabc67" : "#9cdac4",
        [0.08, 0.025],
        0.35,
        new THREE.Vector3(-Math.cos(a) * 0.9, 0.15, -Math.sin(a) * 0.9),
        { opacity: 0.3 + ratio * 0.5, spin: 2 },
      );
    }
  }
  barkWave(position, heading) {
    for (let i = 0; i < 3; i++) {
      const geometry = new THREE.RingGeometry(
        0.45,
        0.55,
        40,
        1,
        0.2,
        Math.PI * 0.85,
      );
      const mesh = new THREE.Mesh(
        geometry,
        new THREE.MeshBasicMaterial({
          color: i % 2 ? "#f8e6ae" : "#a9d8ba",
          transparent: true,
          opacity: 0.5,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      mesh.position.copy(position);
      mesh.position.y = 0.1 + i * 0.12;
      mesh.quaternion.setFromAxisAngle(
        new THREE.Vector3(1, 0, 0),
        -Math.PI / 2,
      );
      mesh.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), heading);
      this.add(mesh, 0.5 + i * 0.09, new THREE.Vector3(), {
        grow: 4.5,
        owned: true,
      });
    }
  }
  stunStars(position) {
    const p = position.clone();
    p.y += 2;
    for (let i = 0; i < 6; i++) {
      const a = (i * Math.PI) / 3;
      this.chip(
        p,
        "#f1d275",
        [0.12, 0.12],
        1.45,
        new THREE.Vector3(Math.cos(a) * 0.25, 0.08, Math.sin(a) * 0.25),
        { spin: 1.8, opacity: 0.8 },
      );
    }
  }
  slam(position) {
    this.groundWash(position, "#423c32", 3.3, 0.65);
    this.groundWash(position, "#f0c46b", 2.5, 0.45);
    for (let i = 0; i < 3; i++) {
      const geometry = new THREE.RingGeometry(0.65, 0.73, 48);
      const mesh = new THREE.Mesh(
        geometry,
        new THREE.MeshBasicMaterial({
          color: i ? "#e9c777" : "#fff4cf",
          transparent: true,
          opacity: 0.7,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      mesh.position.copy(position);
      mesh.position.y += 0.05 + i * 0.025;
      mesh.rotation.x = -Math.PI / 2;
      this.add(mesh, 0.42 + i * 0.08, new THREE.Vector3(), {
        grow: 4.3,
        owned: true,
      });
    }
    this.burst(position, 28, "#bdb098");
    this.landingBloom(position);
  }
  landingBloom(position) {
    this.dust(position, { count: 9 });
    for (let i = 0; i < 8; i++) {
      const a = (i * Math.PI) / 4,
        p = position
          .clone()
          .add(new THREE.Vector3(Math.cos(a) * 0.5, 0.08, Math.sin(a) * 0.5));
      this.chip(
        p,
        "#eebaa2",
        [0.18, 0.08],
        0.7,
        new THREE.Vector3(Math.cos(a) * 1.8, 0.45, Math.sin(a) * 1.8),
        { gravity: 0.9, spin: 2 },
      );
    }
  }
  remove(index) {
    const p = this.items[index];
    if (!p) return;
    this.scene.remove(p.mesh);
    p.mesh.material.dispose();
    if (p.owned) p.mesh.geometry.dispose();
    this.items.splice(index, 1);
  }
  clear() {
    while (this.items.length) this.remove(this.items.length - 1);
    this.trailLast = null;
  }
  update(dt) {
    this.trailAge += dt;
    this.spectralAge += dt;
    if (this.trailAge > 0.1) this.trailLast = null;
    for (let i = this.items.length - 1; i >= 0; i--) {
      const p = this.items[i];
      p.life -= dt;
      if (p.life <= 0) {
        this.remove(i);
        continue;
      }
      p.velocity.y -= dt * p.gravity;
      p.mesh.position.addScaledVector(p.velocity, dt);
      if (p.wind) {
        p.mesh.position.x += Math.sin(p.life * 3 + p.phase) * p.wind * dt;
        p.mesh.rotation.y += Math.cos(p.life * 2 + p.phase) * p.wind * dt;
      }
      p.mesh.rotation.z += dt * p.spin;
      p.mesh.rotation.x += dt * p.spin * 0.23;
      if (p.grow) p.mesh.scale.multiplyScalar(Math.max(0.01, 1 + dt * p.grow));
      p.mesh.material.opacity =
        p.opacity * Math.pow(Math.max(0, p.life / p.total), 0.8);
    }
  }
  dispose() {
    this.clear();
    this.geometry.dispose();
    this.strokeMap.dispose();
    this.paperMap.dispose();
    this.leafMap.dispose();
    this.flowerMap.dispose();
  }
}
