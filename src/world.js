import * as THREE from "three";
import { mat, part } from "./models.js";
import { paperTexture, stroke, paintedTexture, seededRandom } from "./art.js";
function blossomTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const ctx = c.getContext("2d");
  for (let i = 0; i < 70; i++) {
    const a = i * 2.399,
      r = Math.sqrt(i / 70) * 105,
      x = 128 + Math.cos(a) * r,
      y = 128 + Math.sin(a) * r;
    ctx.fillStyle = i % 3 ? "#eeb6ab" : "#fae1c1";
    ctx.beginPath();
    for (let p = 0; p < 5; p++) {
      const b = (p * Math.PI * 2) / 5;
      ctx.ellipse(
        x + Math.cos(b) * 8,
        y + Math.sin(b) * 8,
        9,
        6,
        b,
        0,
        Math.PI * 2,
      );
    }
    ctx.fill();
    ctx.strokeStyle = "#92565355";
    ctx.lineWidth = 0.7;
    ctx.stroke();
  }
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}
export function createWorld(scene) {
  scene.background = new THREE.Color("#e9dec0");
  scene.fog = new THREE.Fog("#e9dec0", 24, 65);
  scene.add(new THREE.HemisphereLight("#fff7dd", "#647547", 1.55));
  const sun = new THREE.DirectionalLight("#ffe8b6", 1.7);
  sun.position.set(-12, 23, -8);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, {
    left: -42,
    right: 42,
    top: 42,
    bottom: -42,
  });
  sun.shadow.bias = -0.0005;
  sun.shadow.normalBias = 0.035;
  scene.add(sun);
  const ground = mat("#7f9c4e");
  ground.map = paintedTexture("grass").clone();
  ground.map.repeat.set(12, 12);
  part(
    scene,
    new THREE.CylinderGeometry(22, 23, 0.8, 96),
    ground,
    [0, -0.45, 0],
    undefined,
    false,
  );
  const arena = mat("#d9bd7d");
  arena.map = paperTexture();
  arena.map.repeat.set(5, 5);
  part(
    scene,
    new THREE.CircleGeometry(12, 96),
    arena,
    [0, 0.01, 0],
    [-Math.PI / 2, 0, 0],
    false,
  );
  for (let i = 0; i < 3; i++) {
    const ring = part(
      scene,
      new THREE.TorusGeometry(11.5 + i * 0.1, 0.016, 3, 128),
      mat("#8a854d"),
      [0, 0.025, 0],
      [Math.PI / 2, 0, 0],
      false,
    );
  }
  const obstacles = [];
  const red = mat("#bd442b", "wood"),
    wood = mat("#423b30", "wood"),
    stone = mat("#aaa383", "stone");
  const gate = new THREE.Group();
  gate.position.set(0, 0, -14);
  scene.add(gate);
  for (const s of [-1, 1]) {
    obstacles.push({ x: s * 2, z: -14, r: 0.32 });
    part(gate, new THREE.CylinderGeometry(0.19, 0.27, 4.8, 12), red, [
      s * 2,
      2.4,
      0,
    ]);
    part(gate, new THREE.CylinderGeometry(0.28, 0.31, 0.6, 12), wood, [
      s * 2,
      0.3,
      0,
    ]);
  }
  stroke(
    gate,
    [
      [-3.2, 5.05, 0],
      [-2, 4.85, 0],
      [0, 4.82, 0],
      [2, 4.85, 0],
      [3.2, 5.05, 0],
    ],
    "#39342b",
    0.16,
  );
  part(gate, new THREE.BoxGeometry(5.4, 0.22, 0.28), red, [0, 4.5, 0]);
  part(gate, new THREE.BoxGeometry(4.8, 0.18, 0.22), red, [0, 3.65, 0]);
  part(
    gate,
    new THREE.BoxGeometry(0.4, 0.7, 0.25),
    mat("#d4ae5e"),
    [0, 4.02, 0],
  );
  const blossoms = blossomTexture();
  for (const [x, z, scale] of [
    [-10, -8, 1.1],
    [11, -8, 1.2],
    [-14, 5, 1],
    [14, 6, 1],
    [-5, -19, 0.9],
    [8, -20, 1],
  ]) {
    obstacles.push({ x, z, r: 0.55 * scale });
    const tree = new THREE.Group();
    tree.position.set(x, 0, z);
    tree.scale.setScalar(scale);
    scene.add(tree);
    stroke(
      tree,
      [
        [0, 0, 0],
        [0.2, 1.3, 0],
        [-0.1, 2.5, 0.1],
        [0.4, 3.7, 0.2],
      ],
      "#534336",
      0.17,
    );
    for (let j = 0; j < 5; j++) {
      const a = j * 2.4,
        end = [Math.sin(a) * 1.6, 3.4 + j * 0.12, Math.cos(a) * 1.3];
      stroke(
        tree,
        [[0, 2.1, 0], [end[0] * 0.5, 2.9, end[2] * 0.5], end],
        "#534336",
        0.08,
      );
      const foliage = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: blossoms,
          transparent: true,
          depthWrite: false,
        }),
      );
      foliage.position.set(...end);
      foliage.scale.set(3.3, 2.5, 1);
      tree.add(foliage);
    }
  }
  for (const [x, z] of [
    [-6, -11],
    [6, -11],
    [-13, 1],
    [13, 1],
  ]) {
    obstacles.push({ x, z, r: 0.37 });
    part(scene, new THREE.BoxGeometry(0.7, 0.22, 0.7), stone, [x, 0.11, z]);
    part(scene, new THREE.CylinderGeometry(0.16, 0.24, 1.2, 8), stone, [
      x,
      0.8,
      z,
    ]);
    part(scene, new THREE.BoxGeometry(0.6, 0.6, 0.6), mat("#f3d39a"), [
      x,
      1.6,
      z,
    ]);
    part(
      scene,
      new THREE.ConeGeometry(0.6, 0.35, 4),
      wood,
      [x, 2.1, z],
      [0, Math.PI / 4, 0],
    );
  }
  // Flat, layered mountain silhouettes resemble ink washes rather than solid cones.
  for (let layer = 0; layer < 3; layer++)
    for (let i = 0; i < 9; i++) {
      const shape = new THREE.Shape();
      const width = 9 + layer * 4,
        height = 5 + Math.sin(i * 3.7) * 3 + layer * 3;
      shape.moveTo(-width, 0);
      shape.lineTo(-width * 0.35, height * 0.48);
      shape.lineTo(-width * 0.1, height);
      shape.lineTo(width * 0.3, height * 0.6);
      shape.lineTo(width, 0);
      const m = new THREE.Mesh(
        new THREE.ShapeGeometry(shape),
        new THREE.MeshBasicMaterial({
          color: ["#989f83", "#b6b79b", "#d0ccb0"][layer],
          side: THREE.DoubleSide,
        }),
      );
      const a = (i * Math.PI * 2) / 9;
      m.position.set(
        Math.sin(a) * (29 + layer * 9),
        -0.5,
        Math.cos(a) * (29 + layer * 9),
      );
      m.rotation.y = a;
      scene.add(m);
    }
  // Brush grass, flower banks, and scattered painted stepping stones.
  for (let i = 0; i < 100; i++) {
    const a = i * 2.399,
      r = 12.8 + (i % 7) * 0.8,
      x = Math.sin(a) * r,
      z = Math.cos(a) * r;
    stroke(
      scene,
      [
        [x, 0, z],
        [x + 0.12, 0.28, z],
        [x + 0.3, 0.42, z],
      ],
      i % 3 ? "#66734a" : "#b7984d",
      0.018,
    );
    if (i % 4 === 0)
      part(
        scene,
        new THREE.SphereGeometry(0.22, 8, 6),
        mat("#d67f79"),
        [x, 0.12, z],
        undefined,
        false,
      ).scale.set(1, 0.35, 1);
  }
  for (let i = 0; i < 6; i++) {
    const m = part(
      scene,
      new THREE.CylinderGeometry(0.65, 0.7, 0.1, 7),
      stone,
      [Math.sin(i) * 0.3, 0.03, -12 - i * 0.9],
    );
    m.scale.z = 0.65;
  }
  const petals = new THREE.Group();
  scene.add(petals);
  const random = seededRandom(413);
  for (let i = 0; i < 45; i++)
    part(
      petals,
      new THREE.PlaneGeometry(0.13, 0.07),
      new THREE.MeshBasicMaterial({ color: "#d99085", side: THREE.DoubleSide }),
      [
        (random() - 0.5) * 34,
        random() * 7,
        (random() - 0.5) * 34,
      ],
      [random() * 3, 0, random() * 3],
      false,
    );
  return { obstacles, petals };
}
