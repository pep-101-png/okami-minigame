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
export function paint(color) {
  return new THREE.MeshToonMaterial({ color, gradientMap: ramp });
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
