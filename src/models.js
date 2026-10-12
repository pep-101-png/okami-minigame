import * as THREE from "three";
import { paint, outline, stroke } from "./art.js";
export const mat = paint;
export function part(
  parent,
  geo,
  material,
  pos = [0, 0, 0],
  rot = [0, 0, 0],
  lined = true,
) {
  const m = new THREE.Mesh(geo, material);
  m.position.set(...pos);
  m.rotation.set(...rot);
  m.castShadow = true;
  m.receiveShadow = true;
  parent.add(m);
  if (lined) outline(m);
  return m;
}
function ellipsoid(parent, material, pos, scale) {
  const m = part(parent, new THREE.SphereGeometry(1, 8, 6), material, pos);
  m.scale.set(...scale);
  return m;
}
export function wolf() {
  const root = new THREE.Group(),
    body = new THREE.Group();
  root.add(body);
  const white = mat("#fff6dd"),
    red = mat("#cf312c"),
    black = mat("#252723"),
    gold = mat("#daa949");
  ellipsoid(body, white, [0, 1.17, 0.08], [0.21, 0.23, 0.72]);
  ellipsoid(body, white, [0, 1.2, -0.45], [0.27, 0.38, 0.34]);
  ellipsoid(body, white, [0, 1.12, 0.65], [0.22, 0.28, 0.3]);
  const head = new THREE.Group();
  head.position.set(0, 1.55, -0.68);
  body.add(head);
  ellipsoid(head, white, [0, 0, -0.08], [0.23, 0.25, 0.3]);
  ellipsoid(head, white, [0, -0.12, -0.43], [0.13, 0.115, 0.36]);
  ellipsoid(head, black, [0, -0.06, -0.7], [0.12, 0.085, 0.09]);
  for (const s of [-1, 1]) {
    const ear = part(
      head,
      new THREE.ConeGeometry(0.15, 0.47, 3),
      white,
      [s * 0.2, 0.34, 0.01],
      [0.1, 0, s * -0.17],
    );
    ear.scale.z = 0.65;
    part(
      head,
      new THREE.ConeGeometry(0.085, 0.27, 3),
      red,
      [s * 0.2, 0.35, -0.045],
      [0.1, 0, s * -0.17],
    );
    ellipsoid(head, black, [s * 0.25, 0.015, -0.27], [0.035, 0.045, 0.085]);
    stroke(
      head,
      [
        [s * 0.26, 0.09, -0.28],
        [s * 0.28, 0.13, -0.13],
        [s * 0.27, 0.08, 0.01],
      ],
      "#282520",
      0.025,
    );
    stroke(
      head,
      [
        [s * 0.2, -0.04, -0.37],
        [s * 0.3, -0.1, -0.15],
        [s * 0.26, -0.2, -0.04],
      ],
      "#cf312c",
      0.035,
    );
    for (let i = 0; i < 2; i++) {
      const tuft = part(
        body,
        new THREE.ConeGeometry(0.09, 0.35, 4),
        white,
        [s * (0.22 + i * 0.015), 1.48 - i * 0.16, -0.44 + i * 0.15],
        [0.75, 0, s * 0.55],
      );
      tuft.scale.z = 0.55;
    }
    stroke(
      body,
      [
        [s * 0.31, 1.27, -0.4],
        [s * 0.38, 1.05, -0.3],
        [s * 0.34, 0.92, -0.08],
        [s * 0.33, 1.17, 0.03],
      ],
      "#cf312c",
      0.037,
    );
  }
  stroke(
    head,
    [
      [0, 0.28, -0.18],
      [0, 0.22, -0.35],
      [0, 0.11, -0.4],
    ],
    "#cf312c",
    0.04,
  );
  const legs = [];
  for (const x of [-0.23, 0.23])
    for (const z of [-0.48, 0.62]) {
      const front = z < 0,
        leg = new THREE.Group();
      leg.position.set(x, 0.97, z);
      body.add(leg);
      ellipsoid(leg, white, [0, -0.18, 0], [0.12, 0.3, 0.14]);
      const knee = new THREE.Group();
      knee.position.set(0, -0.4, 0);
      leg.add(knee);
      part(
        knee,
        new THREE.CylinderGeometry(0.075, 0.055, 0.39, 10),
        white,
        [0, -0.17, 0.03],
        [front ? -0.06 : 0.25, 0, 0],
      );
      ellipsoid(knee, white, [0, -0.36, -0.07], [0.115, 0.08, 0.19]);
      part(
        knee,
        new THREE.CylinderGeometry(0.079, 0.079, 0.09, 10),
        red,
        [0, -0.23, 0.03],
      );
      leg.userData.knee = knee;
      legs.push(leg);
    }
  const tail = new THREE.Group();
  tail.position.set(0, 1.22, 0.8);
  body.add(tail);
  stroke(
    tail,
    [
      [0, 0, 0],
      [0, 0.2, 0.25],
      [0, 0.48, 0.38],
      [0, 0.7, 0.25],
      [0, 0.76, 0.04],
    ],
    "#fff6dd",
    0.13,
  );
  stroke(
    tail,
    [
      [0.01, 0.43, 0.38],
      [0.01, 0.67, 0.27],
      [0.01, 0.71, 0.12],
    ],
    "#cf312c",
    0.04,
  );
  const spear = new THREE.Group();
  head.add(spear);
  spear.position.set(0, -0.22, -0.51);
  part(
    spear,
    new THREE.CylinderGeometry(0.035, 0.035, 2.7, 10),
    mat("#624326"),
    [0.37, 0, -0.42],
    [Math.PI / 2, 0, 0],
  );
  part(
    spear,
    new THREE.CylinderGeometry(0.048, 0.048, 0.76, 10),
    black,
    [0, 0, 0.03],
    [0, 0, Math.PI / 2],
  );
  const blade = part(
    spear,
    new THREE.ConeGeometry(0.15, 0.66, 4),
    mat("#e8e3bc"),
    [0.37, 0, -2.05],
    [-Math.PI / 2, 0, Math.PI / 4],
  );
  blade.scale.z = 0.25;
  part(
    spear,
    new THREE.TorusGeometry(0.1, 0.025, 6, 16),
    gold,
    [0.37, 0, -1.7],
  );
  const ribbon = stroke(
    spear,
    [
      [0.38, 0, -1.65],
      [0.5, -0.15, -1.45],
      [0.63, -0.2, -1.3],
    ],
    "#cf312c",
    0.035,
  );
  return { root, body, head, legs, tail, spear, ribbon };
}
export function demon() {
  const root = new THREE.Group(),
    m = mat("#39564d"),
    red = mat("#c73727");
  ellipsoid(root, m, [0, 0.85, 0], [0.44, 0.65, 0.35]);
  const face = ellipsoid(
    root,
    mat("#e5d6aa"),
    [0, 1.25, -0.31],
    [0.37, 0.43, 0.14],
  );
  for (const s of [-1, 1]) {
    part(
      root,
      new THREE.ConeGeometry(0.1, 0.57, 7),
      red,
      [s * 0.24, 1.72, -0.05],
      [0, 0, s * -0.4],
    );
    stroke(
      root,
      [
        [s * 0.1, 1.32, -0.45],
        [s * 0.23, 1.35, -0.44],
      ],
      "#2c2926",
      0.035,
    );
    ellipsoid(root, m, [s * 0.4, 0.75, 0], [0.12, 0.4, 0.13]);
    ellipsoid(root, m, [s * 0.23, 0.24, 0], [0.12, 0.25, 0.15]);
  }
  stroke(
    root,
    [
      [-0.15, 1.08, -0.45],
      [0, 1.04, -0.46],
      [0.15, 1.08, -0.45],
    ],
    "#c73727",
    0.03,
  );
  return root;
}
