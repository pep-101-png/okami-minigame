import * as THREE from "three";
import {paint} from "./art.js";
export function createDivineSpear(headCarrier) {
  const spear = new THREE.Group();
  headCarrier.add(spear);
  const shaftMat = paint("#674731"),
    inkMat = paint("#282822"),
    bladeMat = paint("#eeedcf"),
    goldMat = paint("#c99c4d");
  const add = (g, m, p, rot) => {
    const o = new THREE.Mesh(g, m);
    o.position.set(...p);
    if (rot) o.rotation.set(...rot);
    o.castShadow = true;
    spear.add(o);
    return o;
  };
  // Handle traverses the jaw; the shaft runs beside the cheek rather than through the nose.
  add(
    new THREE.CylinderGeometry(0.027, 0.027, 2.5, 8),
    shaftMat,
    [0.3, 0, 0.28],
    [Math.PI / 2, 0, 0],
  );
  add(
    new THREE.CylinderGeometry(0.043, 0.043, 0.65, 8),
    inkMat,
    [0, 0, 0],
    [0, 0, Math.PI / 2],
  );
  // Leaf-shaped silver blade with an open crescent heel and spectral inner edge.
  const bladeShape = new THREE.Shape();
  bladeShape.moveTo(0, 0);
  bladeShape.bezierCurveTo(-0.19, 0.18, -0.2, 0.37, 0, 0.67);
  bladeShape.bezierCurveTo(0.18, 0.37, 0.14, 0.14, 0, 0);
  const bladeGeo = new THREE.ExtrudeGeometry(bladeShape, {
    depth: 0.035,
    bevelEnabled: true,
    bevelSize: 0.012,
    bevelThickness: 0.01,
    bevelSegments: 1,
    steps: 1,
  });
  const blade = add(bladeGeo, bladeMat, [0.3, 0, 1.5], [Math.PI / 2, 0, 0]);
  const ghost = add(
    bladeGeo,
    new THREE.MeshBasicMaterial({
      color: "#a6f4e6",
      transparent: true,
      opacity: 0.24,
      depthWrite: false,
      side: THREE.DoubleSide,
    }),
    [0.3, 0, 1.5],
    [Math.PI / 2, 0, 0],
  );
  ghost.scale.set(1.18, 1.04, 1.25);
  for (const z of [-0.8, -0.52, 0.1, 0.5, 1.26, 1.48]) {
    add(new THREE.TorusGeometry(0.037, 0.012, 5, 12), goldMat, [0.3, 0, z]);
  }
  for (let i = 0; i < 11; i++) {
    const binding = add(
      new THREE.TorusGeometry(0.031, 0.008, 4, 10),
      bladeMat,
      [0.3, 0, -0.38 + i * 0.035],
    );
    binding.rotation.y = 0.25;
  }
  const crescent = add(
    new THREE.TorusGeometry(0.15, 0.025, 5, 20, Math.PI * 1.2),
    goldMat,
    [0.3, 0, 1.4],
    [0, 0, 0.3],
  );
  const tassels = [];
  for (let i = 0; i < 3; i++) {
    const tassel = add(
      new THREE.PlaneGeometry(0.04, 0.4 + i * 0.09, 1, 8),
      paint(i === 1 ? "#eee2b5" : "#b93b36"),
      [0.37 + i * 0.025, -0.16, 1.38],
      [0.1, 0.3, -0.25 + i * 0.15],
    );
    tassel.material.side = THREE.DoubleSide;
    tassels.push(tassel);
  }
  const ribbon = add(
    new THREE.PlaneGeometry(0.075, 0.38),
    paint("#c2352d"),
    [0.38, -0.11, 1.49],
    [0.1, 0.3, -0.35],
  );
  ribbon.material.side = THREE.DoubleSide;

return {spear,ribbon,tassels,ghost};
}
