import * as THREE from "three";
import { createWorld } from "./world.js";
import { part, mat } from "./models.js";
import { stroke, paperTexture } from "./art.js";
function roof(parent, w, d, y, color) {
  const positions = [],
    indices = [];
  for (let side = 0; side < 2; side++) {
    const sign = side ? 1 : -1;
    const base = positions.length / 3;
    for (let i = 0; i < 5; i++) {
      const t = i / 4;
      for (const z of [-d / 2, d / 2])
        positions.push(
          (sign * t * w) / 2,
          y + 1.4 * (1 - t) + 0.28 * t * t * t,
          z,
        );
    }
    for (let i = 0; i < 4; i++) {
      let a = base + i * 2;
      indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  const m = mat(color);
  m.side = THREE.DoubleSide;
  part(parent, g, m, undefined, undefined, false);
  for (const z of [-d / 2, d / 2])
    stroke(
      parent,
      [
        [-w / 2, y + 0.28, z],
        [-w * 0.25, y + 0.7, z],
        [0, y + 1.4, z],
        [w * 0.25, y + 0.7, z],
        [w / 2, y + 0.28, z],
      ],
      "#322b24",
      0.06,
    );
  for (let i = -3; i <= 3; i++)
    stroke(
      parent,
      [
        [(i * w) / 8, y + 1.4 * (1 - Math.abs(i) / 4) + 0.06, -d / 2],
        [(i * w) / 8, y + 1.4 * (1 - Math.abs(i) / 4) + 0.06, d / 2],
      ],
      "#6b4936",
      0.025,
    );
}
function house(scene, x, z, w = 5, d = 4, color = "#b57642", turn = 0) {
  const h = new THREE.Group();
  h.position.set(x, 0, z);
  h.rotation.y = turn;
  scene.add(h);
  part(h, new THREE.BoxGeometry(w, 3, d), mat("#e1c69c"), [0, 1.5, 0]);
  for (const sx of [-1, 1])
    for (const sz of [-1, 1])
      part(h, new THREE.BoxGeometry(0.18, 3.2, 0.18), mat("#563b29"), [
        (sx * w) / 2,
        1.6,
        (sz * d) / 2,
      ]);
  part(h, new THREE.BoxGeometry(1, 2, 0.13), mat("#533c2c"), [
    0,
    1,
    d / 2 + 0.1,
  ]);
  for (const sx of [-1, 1]) {
    part(h, new THREE.BoxGeometry(1.15, 1.2, 0.12), mat("#f4dea5"), [
      sx * w * 0.3,
      1.65,
      d / 2 + 0.1,
    ]);
    for (let i = -1; i <= 1; i++)
      part(h, new THREE.BoxGeometry(0.045, 1.2, 0.15), mat("#493b2c"), [
        sx * w * 0.3 + i * 0.3,
        1.65,
        d / 2 + 0.18,
      ]);
    part(h, new THREE.BoxGeometry(1.2, 0.06, 0.15), mat("#493b2c"), [
      sx * w * 0.3,
      1.65,
      d / 2 + 0.18,
    ]);
  }
  for (let i = 0; i < 9; i++)
    part(
      h,
      new THREE.BoxGeometry(w, 0.028, 0.03),
      mat("#91704c"),
      [0, 0.2 + i * 0.31, d / 2 + 0.03],
      undefined,
      false,
    );
  roof(h, w + 1.3, d + 1.3, 3, color);
  return h;
}
function label(text) {
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 96;
  const ctx = c.getContext("2d");
  ctx.font = "32px Georgia";
  ctx.fillStyle = "#f3e6c6";
  ctx.fillRect(10, 10, 492, 76);
  ctx.strokeStyle = "#63513b";
  ctx.strokeRect(10, 10, 492, 76);
  ctx.fillStyle = "#4d3428";
  ctx.textAlign = "center";
  ctx.fillText(text, 256, 60);
  const s = new THREE.Sprite(
    new THREE.SpriteMaterial({
      map: new THREE.CanvasTexture(c),
      depthTest: true,
    }),
  );
  s.scale.set(3.2, 0.6, 1);
  return s;
}
function npc(scene, x, z, name, color, lines, route = null) {
  const root = new THREE.Group();
  root.position.set(x, 0, z);
  scene.add(root);
  part(root, new THREE.ConeGeometry(0.4, 1.35, 6), mat(color), [0, 0.8, 0]);
  part(
    root,
    new THREE.SphereGeometry(0.22, 8, 6),
    mat("#edd2a3"),
    [0, 1.65, 0],
  );
  part(
    root,
    new THREE.SphereGeometry(0.24, 8, 6),
    mat("#302c27"),
    [0, 1.8, 0.03],
  ).scale.y = 0.55;
  for (const s of [-1, 1]) {
    part(
      root,
      new THREE.CylinderGeometry(0.09, 0.12, 0.8, 6),
      mat(color),
      [s * 0.36, 1.02, 0],
      [0, 0, s * 0.22],
    );
    part(root, new THREE.BoxGeometry(0.15, 0.16, 0.3), mat("#473729"), [
      s * 0.16,
      0.1,
      -0.04,
    ]);
  }
  part(
    root,
    new THREE.CylinderGeometry(0.26, 0.26, 0.12, 6),
    mat("#e6ca87"),
    [0, 0.9, 0],
  );
  const tag = label(name);
  tag.position.y = 2.35;
  root.add(tag);
  return {
    root,
    name,
    lines,
    route,
    index: 0,
    home: new THREE.Vector3(x, 0, z),
  };
}
export function createTown(scene) {
  const world = createWorld(scene);
  for (const child of [...scene.children]) {
    if (child.geometry?.type === "ShapeGeometry") {
      scene.remove(child);
      continue;
    }
    if (!child.isLight) child.position.x += 26;
  }
  for (const o of world.obstacles) o.x += 26;
  scene.background = new THREE.Color("#7dbcd1");
  scene.fog = new THREE.Fog("#c9d9c4", 45, 110);
  const terrain = mat("#879b57");
  terrain.map = paperTexture();
  terrain.map.repeat.set(18, 18);
  part(
    scene,
    new THREE.PlaneGeometry(90, 72),
    terrain,
    [8, -0.02, 0],
    [-Math.PI / 2, 0, 0],
    false,
  );
  const road = mat("#cfb079");
  part(
    scene,
    new THREE.PlaneGeometry(8, 52),
    road,
    [0, 0.03, 0],
    [-Math.PI / 2, 0, 0],
    false,
  );
  part(
    scene,
    new THREE.PlaneGeometry(45, 5),
    road,
    [13, 0.035, 0],
    [-Math.PI / 2, 0, 0],
    false,
  );
  world.bounds = { minX: -20, maxX: 44, minZ: -27, maxZ: 27 };
  world.boxes = [];
  const homes = [
    [-8, 15, 5, 4, "#b57b44"],
    [8, 15, 5, 4, "#9a623d"],
    [-9, 6, 6, 4, "#a16c43"],
    [9, 6, 5, 4, "#bd8549"],
    [-9, -5, 5, 5, "#a4633e"],
    [9, -9, 6, 4, "#799064"],
    [-8, -18, 6, 5, "#a96f43"],
    [8, -20, 5, 5, "#b67b44"],
  ];
  for (const [x, z, w, d, col] of homes) {
    house(scene, x, z, w, d, col);
    world.boxes.push({ x, z, halfX: w / 2 + 0.15, halfZ: d / 2 + 0.15 });
  }
  for (let i = 0; i < 12; i++) {
    const shape = new THREE.Shape();
    const x = -35 + i * 9;
    shape.moveTo(-10, 0);
    shape.lineTo(-5, 7);
    shape.lineTo(0, 12 + (i % 3) * 4);
    shape.lineTo(5, 8);
    shape.lineTo(12, 0);
    const mountain = new THREE.Mesh(
      new THREE.ShapeGeometry(shape),
      new THREE.MeshBasicMaterial({
        color: i % 2 ? "#779788" : "#a5b5a0",
        side: THREE.DoubleSide,
      }),
    );
    mountain.position.set(x, 0, -43 - (i % 2) * 9);
    scene.add(mountain);
  }
  // Shrine, market stalls and watermill form landmarks along the main street.
  house(scene, 0, -25, 8, 4, "#a63d2d");
  world.boxes.push({ x: 0, z: -25, halfX: 4.2, halfZ: 2.2 });
  for (const x of [-4.5, 4.5]) {
    const stall = new THREE.Group();
    stall.position.set(x, 0, 0);
    scene.add(stall);
    part(
      stall,
      new THREE.BoxGeometry(2.3, 0.8, 1.1),
      mat("#9d6b42"),
      [0, 0.4, 0],
    );
    for (const sx of [-1, 1])
      part(
        stall,
        new THREE.CylinderGeometry(0.045, 0.045, 2.2, 6),
        mat("#513e2d"),
        [sx * 1.1, 1.1, 0],
      );
    part(
      stall,
      new THREE.BoxGeometry(2.7, 0.12, 1.5),
      mat(x < 0 ? "#d08360" : "#7d9c84"),
      [0, 2.2, 0],
      [0.12, 0, 0],
    );
    for (let i = 0; i < 5; i++)
      part(stall, new THREE.SphereGeometry(0.13, 6, 4), mat("#c75d38"), [
        -0.8 + i * 0.4,
        0.9,
        0,
      ]);
    world.boxes.push({ x, z: 0, halfX: 1.2, halfZ: 0.65 });
  }
  const wheel = new THREE.Group();
  wheel.position.set(-13, 1.8, -5);
  wheel.rotation.y = Math.PI / 2;
  scene.add(wheel);
  part(wheel, new THREE.TorusGeometry(1.5, 0.12, 6, 16), mat("#5e422d"));
  for (let i = 0; i < 8; i++)
    part(
      wheel,
      new THREE.BoxGeometry(0.1, 3, 0.12),
      mat("#765232"),
      undefined,
      [0, 0, (i * Math.PI) / 4],
    );
  const sign = label("EAST → SPIRIT GROVE");
  sign.position.set(12, 2, 0);
  scene.add(sign);
  part(
    scene,
    new THREE.CylinderGeometry(0.06, 0.06, 2.2, 6),
    mat("#59432d"),
    [12, 1, 0],
  );
  for (let i = 0; i < 65; i++) {
    const x = Math.sin(i * 2.4) * 19,
      z = Math.cos(i * 2.4) * 25;
    if (Math.abs(x) < 5) continue;
    stroke(
      scene,
      [
        [x, 0, z],
        [x + 0.1, 0.3, z],
        [x + 0.2, 0.35, z],
      ],
      "#536d3c",
      0.022,
    );
  }
  world.npcs = [
    npc(scene, -2, 10, "Hana · gardener", "#a4778d", [
      "Welcome to Windflower Village, little guardian.",
      "The shadow spirits gather in the grove to the east. Follow the sign.",
    ]),
    npc(scene, 3, -2, "Taro · merchant", "#6d9488", [
      "My stall is open, but the grove has frightened away the travelers.",
      "Try a quick thrust, a sweeping second strike, then a lunging finish.",
    ]),
    npc(scene, -3, -17, "Elder Sora", "#aa914e", [
      "Our shrine watches over this valley.",
      "Restore the five spirits in the eastern grove, then return to wander in peace.",
    ]),
    npc(
      scene,
      2,
      19,
      "Yui · traveler",
      "#bd705f",
      [
        "Such a fine white wolf!",
        "Hold Shift to run. K dodges. The village is safe; the grove is not.",
      ],
      [new THREE.Vector3(2, 0, 19), new THREE.Vector3(-2, 0, 5)],
    ),
  ];
  world.wheel = wheel;
  world.update = (dt, time) => {
    wheel.rotation.z += dt * 0.35;
    for (const n of world.npcs) {
      if (n.route) {
        const target = n.route[n.index];
        const delta = target.clone().sub(n.root.position);
        if (delta.length() < 0.3) n.index = (n.index + 1) % n.route.length;
        else {
          n.root.position.addScaledVector(delta.normalize(), dt * 0.7);
          n.root.rotation.y = Math.atan2(-delta.x, -delta.z);
        }
      }
      n.root.children[0].rotation.z = Math.sin(time * 2 + n.home.x) * 0.018;
    }
  };
  return world;
}
