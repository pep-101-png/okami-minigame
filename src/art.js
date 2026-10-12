import * as THREE from "three";

// Surface pigment is baked into tiny local canvas textures. The same seed always
// produces the same painting; no image downloads or postprocess blur is needed.
const ramp = new THREE.DataTexture(new Uint8Array([142, 194, 234, 255]), 4, 1, THREE.RedFormat);
ramp.minFilter = ramp.magFilter = THREE.NearestFilter;
ramp.needsUpdate = true;
export const ink = new THREE.MeshBasicMaterial({ color: "#27251f", side: THREE.BackSide });
const textureCache = new Map();
export function seededRandom(seed = 19) {
  return () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
}
export function paintedTexture(kind = "wash") {
  if (textureCache.has(kind)) return textureCache.get(kind);
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const ctx = c.getContext("2d"), rand = seededRandom(218 + kind.length * 997);
  ctx.fillStyle = "#fffbed"; ctx.fillRect(0, 0, 256, 256);
  // Uneven pigment pooling, with a darker edge on each translucent wash.
  for (let i = 0; i < 110; i++) {
    const x = rand() * 256, y = rand() * 256, rx = 8 + rand() * 50, ry = 5 + rand() * 30;
    ctx.fillStyle = `rgba(107,84,48,${0.025 + rand() * 0.035})`;
    ctx.strokeStyle = "rgba(113,87,48,.018)"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(x, y, rx, ry, rand() * Math.PI, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  }
  if (kind === "wood") {
    for (let i = 0; i < 8; i++) {
      const y = i * 32 + 1;
      ctx.strokeStyle = "rgba(42,31,19,.36)"; ctx.lineWidth = i % 2 ? 1.4 : 2.3;
      ctx.beginPath(); ctx.moveTo(0, y);
      for (let x = 24; x <= 280; x += 24) ctx.lineTo(x, y + (rand() - .5) * 3);
      ctx.stroke();
      for (let j = 0; j < 5; j++) {
        const start = rand() * 230, yy = y + 4 + rand() * 24;
        ctx.strokeStyle = "rgba(88,65,37,.17)"; ctx.lineWidth = .8;
        ctx.beginPath(); ctx.moveTo(start, yy); ctx.bezierCurveTo(start+8, yy+2, start+20, yy-2, start+35, yy); ctx.stroke();
      }
    }
    for (let i = 0; i < 8; i++) { ctx.strokeStyle = "rgba(46,31,16,.2)"; ctx.beginPath(); ctx.ellipse(rand()*256, rand()*256, 5, 2, 0, 0, Math.PI*2); ctx.stroke(); }
  } else if (kind === "roof") {
    for (let i = 0; i < 420; i++) {
      ctx.fillStyle = `rgba(45,39,23,${.12 + rand() * .2})`;
      ctx.beginPath(); ctx.ellipse(rand()*256, rand()*256, 1 + rand()*3, .6 + rand()*1.5, -.2, 0, Math.PI*2); ctx.fill();
    }
    for (let i = 0; i < 12; i++) { ctx.strokeStyle = "rgba(115,92,52,.15)"; ctx.lineWidth = 2;ctx.beginPath();ctx.moveTo(0,i*23);ctx.lineTo(256,i*23+8);ctx.stroke(); }
  } else if (kind === "stone") {
    for (let i = 0; i < 30; i++) { ctx.strokeStyle="rgba(68,60,41,.13)";ctx.lineWidth=1;const x=rand()*256,y=rand()*256;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+rand()*20,y+rand()*15);ctx.stroke(); }
  } else if (kind === "shoji") {
    for (let i = 0; i < 7; i++) { ctx.strokeStyle="rgba(114,91,57,.08)";ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(i*43,0);ctx.lineTo(i*43,256);ctx.stroke(); }
  } else if (kind === "grass") {
    for (let i = 0; i < 330; i++) {ctx.fillStyle=`rgba(66,84,27,${.015+rand()*.055})`;ctx.beginPath();ctx.ellipse(rand()*256,rand()*256,6+rand()*14,2+rand()*9,rand()*6,0,Math.PI*2);ctx.fill();}
  }
  // Fibers live on surfaces; the screen pass adds only a restrained grain.
  for (let i = 0; i < 6800; i++) { ctx.fillStyle=i%3?"rgba(86,64,37,.045)":"rgba(255,255,255,.19)";ctx.fillRect(rand()*256,rand()*256,1+rand()*2,1); }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4;
  textureCache.set(kind,t);return t;
}
export function paint(color, kind = "wash") { return new THREE.MeshToonMaterial({ color, gradientMap:ramp,map:paintedTexture(kind) }); }
export function outline(mesh,width=.026) {
  const shell=new THREE.Mesh(mesh.geometry,ink);shell.scale.setScalar(1+width);shell.userData.outline=true;shell.castShadow=false;shell.receiveShadow=false;mesh.add(shell);return mesh;
}
export function paperTexture() { const texture=paintedTexture("wash").clone();texture.needsUpdate=true;return texture; }
export function stroke(parent,points,color="#b32626",radius=.025) {
  const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
  const m=new THREE.Mesh(new THREE.TubeGeometry(curve,Math.max(8,points.length*5),radius,5,false),paint(color));parent.add(m);return m;
}
