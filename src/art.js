import * as THREE from "three";
const ramp = new THREE.DataTexture(
  new Uint8Array([95, 155, 215, 255]),
  4,
  1,
  THREE.RedFormat,
);
ramp.minFilter = ramp.magFilter = THREE.NearestFilter;
ramp.needsUpdate = true;
export const ink = new THREE.MeshBasicMaterial({
  color: "#302b29",
  side: THREE.BackSide,
});
let wash;
function washTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#fff9e8";
  ctx.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 500; i++) {
    ctx.fillStyle = `rgba(76,57,30,${0.01 + Math.random() * 0.035})`;
    ctx.beginPath();
    ctx.ellipse(
      Math.random() * 256,
      Math.random() * 256,
      8 + Math.random() * 30,
      2 + Math.random() * 12,
      Math.random() * 3,
      0,
      Math.PI * 2,
    );
    ctx.fill();
  }
  for (let i = 0; i < 9000; i++) {
    ctx.fillStyle = "rgba(44,30,15,.07)";
    ctx.fillRect(Math.random() * 256, Math.random() * 256, 1, 1);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
export function paint(color) {
  wash ??= washTexture();
  return new THREE.MeshToonMaterial({ color, gradientMap: ramp, map: wash });
}
export function outline(mesh, width = 0.035) {
  const shell = new THREE.Mesh(mesh.geometry, ink);
  shell.scale.setScalar(1 + width);
  shell.userData.outline = true;
  mesh.add(shell);
  return mesh;
}
export function paperTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 512;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#eee4c6";
  ctx.fillRect(0, 0, 512, 512);
  let seed = 19;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  for (let i = 0; i < 24000; i++) {
    ctx.fillStyle = `rgba(95,69,35,${rand() * 0.06})`;
    ctx.fillRect(rand() * 512, rand() * 512, 1 + rand() * 3, 1);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}
export function stroke(parent, points, color = "#b32626", radius = 0.025) {
  const curve = new THREE.CatmullRomCurve3(
    points.map((p) => new THREE.Vector3(...p)),
  );
  const m = new THREE.Mesh(
    new THREE.TubeGeometry(curve, 24, radius, 5, false),
    paint(color),
  );
  parent.add(m);
  return m;
}
