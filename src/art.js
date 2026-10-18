import * as THREE from "three";
import {pigment,brushTexture} from "./environment/pigment.js";

// Surface pigment is baked into tiny local canvas textures. The same seed always
// produces the same painting; no image downloads or postprocess blur is needed.
const ramp = new THREE.DataTexture(new Uint8Array([163,176,189,201,212,223,233,241,248,255]),10,1,THREE.RedFormat);
ramp.minFilter=ramp.magFilter=THREE.LinearFilter;ramp.needsUpdate=true;
export const ink=pigment(new THREE.MeshBasicMaterial({color:'#46443f',side:THREE.BackSide,transparent:true,opacity:.82,depthWrite:false}),'ink');
export function seededRandom(seed = 19) {
  return () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
}
export const paintedTexture=brushTexture;
export function paint(color,kind='wash'){return pigment(new THREE.MeshToonMaterial({color,gradientMap:ramp,map:brushTexture(kind)}),kind);}
export function outline(mesh,width=.026) {
  const shell=new THREE.Mesh(mesh.geometry,ink);shell.scale.setScalar(1+width);shell.userData.outline=true;shell.castShadow=false;shell.receiveShadow=false;mesh.add(shell);return mesh;
}
export function paperTexture() { const texture=paintedTexture("wash").clone();texture.needsUpdate=true;return texture; }
export function stroke(parent,points,color="#b32626",radius=.025) {
  const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
  const m=new THREE.Mesh(new THREE.TubeGeometry(curve,Math.max(8,points.length*5),radius,5,false),paint(color));parent.add(m);return m;
}
