import * as THREE from "three";
/** Layered, ink-edged mane tufts with fixed roots and delayed tip motion. */
export function createWolfFur(body) {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff9e8";
  ctx.fillRect(0, 0, 128, 512);
  const wash = ctx.createLinearGradient(0, 0, 128, 0);
  wash.addColorStop(0, "#777b72");
  wash.addColorStop(0.08, "#f1efdf");
  wash.addColorStop(0.46, "#fffbea");
  wash.addColorStop(0.92, "#f0ecdd");
  wash.addColorStop(1, "#72786b");
  ctx.fillStyle = wash;
  ctx.fillRect(0, 0, 128, 512);
  ctx.strokeStyle = "#3e4235";
  ctx.lineWidth = 3;
  for (const x of [3, 125]) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 512);
    ctx.stroke();
  }
  let seed = 907;
  for (let i = 0; i < 1900; i++) {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    const x = seed % 128;
    const y = (seed >>> 8) % 512;
    ctx.fillStyle = i % 2 ? "#8d8e6b18" : "#ffffff30";
    ctx.fillRect(x, y, 1, 2);
  }
  ctx.strokeStyle = "#b7332c";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(87, 0);
  ctx.bezierCurveTo(120, 150, 35, 340, 64, 510);
  ctx.stroke();
  ctx.strokeStyle = "#7d827047";
  ctx.lineWidth = 1;
  for (let i = 0; i < 14; i++) {
    ctx.beginPath();
    ctx.moveTo(i * 9, 0);
    ctx.bezierCurveTo(25 + i * 5, 160, 50 + i * 2, 340, 64, 512);
    ctx.stroke();
  }
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.MeshBasicMaterial({
    map,
    color: "#fffbea",
    side: THREE.DoubleSide,
  });
  const ribbons = [],
    strands = [];
  const anchors = [];
  // A broad crown and layered cheek/neck mane, followed by shoulder, ankle and tail streamers.
  for (const sign of [-1, 1]) {
    for (let i = 0; i < 6; i++)
      anchors.push([
        "b_Neck_04",
        [sign * (8 + i * 1.5), 67 - i * 2.4, 37 - i * 3],
        0.56 + i * 0.085,
        0.12 + i * 0.012,
        sign * (0.18 + i * 0.055),
        0.04 - i * 0.06,
      ]);
    for (let i = 0; i < 4; i++)
      anchors.push([
        "b_Spine02_03",
        [sign * (11 + i * 0.8), 55 - i * 2, 14 - i * 5],
        0.76 + i * 0.12,
        0.14,
        sign * (0.28 + i * 0.045),
        -0.26 - i * 0.065,
      ]);
    anchors.push([
      sign < 0 ? "b_RightForeArm_07" : "b_LeftForeArm_010",
      [sign * 7, 22, 21],
      0.29,
      0.055,
      sign * 0.13,
      -0.04,
    ]);
    for (let i = 0; i < 3; i++)
      anchors.push([
        "b_Tail02_013",
        [sign * (2 + i), 43 - i * 2, -57 - i * 6],
        0.6 + i * 0.12,
        0.09,
        sign * 0.18,
        0.01 + i * 0.01,
      ]);
  }
  anchors.push(["b_Neck_04", [0, 71, 34], 0.8, 0.11, 0, 0.02]);
  body.updateMatrixWorld(true);
  for (const [boneName, anchor, length, width, spread, lift] of anchors) {
    const bone = body.getObjectByName(boneName);
    if (!bone) continue;
    const carrier = new THREE.Group();
    bone.add(carrier);
    carrier.position.copy(
      new THREE.Vector3(...anchor)
        .applyMatrix4(body.matrixWorld)
        .applyMatrix4(bone.matrixWorld.clone().invert()),
    );
    const rotation = new THREE.Quaternion();
    bone.getWorldQuaternion(rotation);
    carrier.quaternion.copy(rotation.invert());
    carrier.rotateZ(Math.sign(anchor[0]) * Math.PI * 0.32);
    carrier.scale.setScalar(1 / 0.023);
    const positions = [],
      uv = [],
      indices = [],
      segments = 18,
      phase = strands.length * 1.91;
    for (let i = 0; i <= segments; i++) {
      const t = i / segments,
        w = width * Math.pow(1 - t, 0.75) * (1 + 0.12 * Math.sin(t * 24));
      const x = spread * t + Math.sin(t * Math.PI) * spread * 0.25;
      const y = lift * t + Math.sin(t * Math.PI) * 0.065;
      positions.push(
        x - w,
        y,
        t * length,
        x + w,
        y + 0.016 * Math.sin(t * Math.PI),
        t * length,
      );
      uv.push(0, 1 - t, 1, 1 - t);
      if (i < segments) {
        const a = i * 2;
        indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const ribbon = new THREE.Mesh(geometry, material);
    ribbon.name = "Layered celestial mane";
    ribbon.frustumCulled = false;
    carrier.add(ribbon);
    ribbons.push(ribbon);
    strands.push({ geometry, base: positions, phase, length });
  }
  let flow = 0;
  return {
    ribbons,
    update(time, speed) {
      flow = THREE.MathUtils.lerp(flow, Math.min(1, speed / 6.8), 0.12);
      for (const strand of strands) {
        const p = strand.geometry.attributes.position;
        for (let i = 0; i < p.count; i++) {
          const t = Math.floor(i / 2) / 18,
            tip = t * t;
          const wave = Math.sin(
            time * (2.1 + flow * 2.5) - t * 4.2 + strand.phase,
          );
          p.setXYZ(
            i,
            strand.base[i * 3] + wave * 0.07 * tip * (0.35 + flow),
            strand.base[i * 3 + 1] +
              Math.sin(time * 2.8 - t * 5 + strand.phase) * 0.055 * tip +
              flow * 0.07 * tip,
            strand.base[i * 3 + 2],
          );
        }
        p.needsUpdate = true;
        strand.geometry.computeVertexNormals();
      }
    },
    dispose() {
      map.dispose();
      material.dispose();
      ribbons.forEach((r) => r.geometry.dispose());
    },
  };
}
