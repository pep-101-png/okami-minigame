import * as THREE from "three";
/** Sparse painted silk ribbons: tip-only flutter, not a replacement for the body mesh. */
export function createWolfFur(body) {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createLinearGradient(0, 0, 0, 256);
  gradient.addColorStop(0, "rgba(255,252,231,.95)");
  gradient.addColorStop(0.5, "rgba(255,251,226,.7)");
  gradient.addColorStop(1, "rgba(255,250,224,0)");
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.moveTo(5, 0);
  ctx.lineTo(59, 0);
  ctx.quadraticCurveTo(40, 140, 32, 256);
  ctx.quadraticCurveTo(23, 140, 5, 0);
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,245,.65)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 6; i++) {
    ctx.beginPath();
    ctx.moveTo(12 + i * 7, 0);
    ctx.quadraticCurveTo(25 + i, 160, 32, 240);
    ctx.stroke();
  }
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  const uniforms = { time: { value: 0 }, flow: { value: 0 } };
  const material = new THREE.MeshBasicMaterial({
    map,
    color: "#fffbe3",
    transparent: true,
    opacity: 0.72,
    side: THREE.DoubleSide,
    depthWrite: false,
    alphaTest: 0.015,
  });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uFurTime = uniforms.time;
    shader.uniforms.uFurFlow = uniforms.flow;
    shader.vertexShader =
      "uniform float uFurTime; uniform float uFurFlow;\n" + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace(
      "#include <begin_vertex>",
      `#include <begin_vertex>
 float tip = (1.-uv.y) * (1.-uv.y);
 transformed.x += sin(uFurTime*2.8 + uv.y*4.5 + position.z*7.) * .018 * tip * (1.+uFurFlow);
 transformed.y += cos(uFurTime*2.2 + uv.y*4.) * .012 * tip * (1.+uFurFlow);`,
    );
  };
  const ribbons = [];
  const anchors = [
    ["b_Neck_04", [-12.5, 61, 28], 0.35, -0.2],
    ["b_Neck_04", [12.5, 61, 28], 0.35, 0.2],
    ["b_Spine02_03", [-12.5, 57, 14], 0.42, -0.1],
    ["b_Spine02_03", [12.5, 57, 14], 0.42, 0.1],
    ["b_Tail02_013", [-3, 46, -58], 0.46, -0.12],
    ["b_Tail02_013", [3, 46, -58], 0.5, 0.12],
  ];
  for (const [boneName, anchor, length, spread] of anchors) {
    const bone = body.getObjectByName(boneName);
    if (!bone) continue;
    const carrier = new THREE.Group();
    bone.add(carrier);
    carrier.position.copy(
      new THREE.Vector3(...anchor)
        .applyMatrix4(body.matrixWorld)
        .applyMatrix4(bone.matrixWorld.clone().invert()),
    );
    const boneWorld = new THREE.Quaternion();
    bone.getWorldQuaternion(boneWorld);
    carrier.quaternion.copy(boneWorld.invert());
    carrier.scale.setScalar(1 / 0.023);
    const positions = [],
      uv = [],
      index = [];
    for (let i = 0; i <= 10; i++) {
      const t = i / 10,
        width = 0.026 * Math.pow(1 - t, 0.6);
      const x = spread * t * 0.25,
        y = Math.sin(t * Math.PI) * 0.045 - t * 0.075,
        z = t * length;
      positions.push(x - width, y, z, x + width, y, z);
      uv.push(0, 1 - t, 1, 1 - t);
      if (i < 10) {
        const a = i * 2;
        index.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    geometry.setIndex(index);
    const ribbon = new THREE.Mesh(geometry, material);
    ribbon.name = "Wolf silk fur";
    ribbon.frustumCulled = false;
    carrier.add(ribbon);
    ribbons.push(ribbon);
  }
  return {
    ribbons,
    update(time, speed) {
      uniforms.time.value = time;
      uniforms.flow.value = Math.min(1, speed / 6.8);
    },
    dispose() {
      map.dispose();
      material.dispose();
      ribbons.forEach((r) => r.geometry.dispose());
    },
  };
}
