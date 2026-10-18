import * as THREE from "three";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
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
export { wolf } from "./expansion/amaterasu.js";
// Hand shaped rings keep the sentinel's silhouette coherent rather than a stack
// of primitive spheres. These assets are intentionally original and local.
function sculpt(rings, sides = 8) {
  const vertices = [], indices = [];
  for (const [y, width, depth, z = 0] of rings) {
    for (let i = 0; i < sides; i++) {
      const a = (i / sides) * Math.PI * 2;
      vertices.push(Math.cos(a) * width, y, Math.sin(a) * depth + z);
    }
  }
  for (let j = 0; j < rings.length - 1; j++) for (let i = 0; i < sides; i++) {
    const a = j * sides + i, b = j * sides + (i + 1) % sides;
    indices.push(a, b, a + sides, b, b + sides, a + sides);
  }
  for (let i = 1; i < sides - 1; i++) {
    indices.push(0, i + 1, i);
    const o = (rings.length - 1) * sides;
    indices.push(o, o + i, o + i + 1);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}
function joint(parent, position) {
  const group = new THREE.Group();
  group.position.set(...position);
  parent.add(group);
  return group;
}
function limb(parent, length, top, bottom, material) {
  return part(parent, sculpt([[0, top, top * 0.78], [-length * 0.65, bottom * 1.2, bottom], [-length, bottom, bottom * 0.8]]), material);
}
function ribbon(parent, material, points, width = 0.12) {
  const vertices = [], indices = [];
  points.forEach(([x, y, z], i) => vertices.push(x - width * (1 - i / (points.length * 1.1)), y, z, x + width * (1 - i / (points.length * 1.1)), y - .03, z));
  for (let i = 0; i < points.length - 1; i++) indices.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return part(parent, geometry, material, [0, 0, 0], [0, 0, 0], false);
}
export function batchFixedParts(root) {
  const groups=[];
  root.traverse(object=>{if(object.isGroup)groups.push(object);});
  for(const group of groups) {
    const batches=new Map(), originals=[];
    const collect=(mesh,matrix)=>{
      const material=mesh.material;
      const key=[material.type,material.color?.getHexString(),material.map?.uuid,material.side,material.transparent,material.opacity].join("|");
      if(!batches.has(key))batches.set(key,{material,geometries:[]});
      let geometry=mesh.geometry.index?mesh.geometry.toNonIndexed():mesh.geometry.clone();
      if(!geometry.getAttribute("uv"))geometry.setAttribute("uv",new THREE.Float32BufferAttribute(new Float32Array(geometry.getAttribute("position").count*2),2));
      geometry.applyMatrix4(matrix);
      batches.get(key).geometries.push(geometry);
    };
    for(const mesh of [...group.children]) {
      if(!mesh.isMesh||mesh.userData.dynamic)continue;
      mesh.updateMatrix();collect(mesh,mesh.matrix);originals.push(mesh);
      for(const shell of mesh.children)if(shell.isMesh&&shell.userData.outline) {
        shell.updateMatrix();collect(shell,new THREE.Matrix4().multiplyMatrices(mesh.matrix,shell.matrix));
      }
    }
    // A single part already draws efficiently; leave its outline hierarchy.
    if(originals.length<2) {
      for(const {geometries} of batches.values())for(const geometry of geometries)geometry.dispose();
      continue;
    }
    for(const {material,geometries} of batches.values()) {
      const geometry=mergeGeometries(geometries,false);
      const mesh=new THREE.Mesh(geometry,material);
      mesh.castShadow=material.side!==THREE.BackSide;mesh.receiveShadow=mesh.castShadow;
      group.add(mesh);
      for(const source of geometries)source.dispose();
    }
    for(const mesh of originals){group.remove(mesh);mesh.geometry.dispose();}
  }
}
export function demon() {
  const root = new THREE.Group();
  root.name = "Reed Sentinel";
  const visual = joint(root, [0, 0, 0]);
  const green = mat("#697c51"), bark = mat("#726142"), mask = mat("#ecdfb5"), red = mat("#bd4936"), dark = mat("#302d2b"), cloak = mat("#59604e");
  cloak.side = THREE.DoubleSide;
  const pelvis = joint(visual, [0, .85, .06]);
  const torso = joint(pelvis, [0, 0, 0]);
  part(torso, sculpt([[-.12, .22, .18], [.08, .25, .2], [.34, .38, .23, -.04], [.55, .32, .19, -.09], [.63, .13, .12, -.1]]), green);
  // A tied sash and uneven mantle define a hunched torso and waist.
  part(pelvis, sculpt([[-.06, .26, .22], [.04, .265, .225], [.1, .23, .2]]), red);
  const mantle = joint(torso, [0, .44, .16]);
  for (let i = -2; i <= 2; i++) ribbon(mantle, cloak, [[i * .125, .12, 0], [i * .14, -.16, .09], [i * .15, -.49 - (i % 2 ? .1 : 0), .16]], .09);
  // Mask has an angular forehead, pronounced cheek planes and a narrow chin.
  const head = joint(torso, [0, .68, -.19]);
  const faceShape = new THREE.Shape();
  faceShape.moveTo(-.24, .2); faceShape.lineTo(-.3, .03); faceShape.lineTo(-.21, -.22); faceShape.lineTo(0, -.35); faceShape.lineTo(.21, -.22); faceShape.lineTo(.3, .03); faceShape.lineTo(.24, .2); faceShape.lineTo(0, .3); faceShape.closePath();
  const face = part(head, new THREE.ExtrudeGeometry(faceShape, {depth:.12, bevelEnabled:true, bevelThickness:.03, bevelSize:.035, bevelSegments:1, steps:1}), mask, [0, 0, -.16]);
  face.rotation.y = Math.PI;
  part(head,new THREE.ConeGeometry(.055,.16,4),mask,[0,-.035,-.353],[-Math.PI/2,0,Math.PI/4]);
  const eyes = [];
  for (const side of [-1, 1]) {
    stroke(head, [[side * .065,.045,-.336],[side * .14,.092,-.338],[side * .23,.10,-.32]], "#302d2b", .024);
    const eye = part(head, new THREE.BoxGeometry(.095,.023,.013), new THREE.MeshBasicMaterial({color:"#e8aa52"}), [side * .14,.035,-.347], [0,0,side * .12], false);
    eye.userData.dynamic=true;
    eyes.push(eye);
    stroke(head, [[side * .205,-.095,-.333],[side * .13,-.17,-.335],[side * .045,-.185,-.338]], "#9c3d31", .018);
    const antler = joint(head, [side * .2, .2, 0]);
    stroke(antler, [[0,0,0],[side * .05,.17,.02],[side * .09,.34,.04],[side * .18,.47,.03]], "#443c31", .035);
    stroke(antler, [[side * .075,.28,.025],[side * .19,.29,-.02],[side * .22,.35,-.055]], "#443c31", .025);
    ribbon(antler, red, [[side * .09,.25,-.01],[side * .12,.03,-.03],[side * .2,-.14,-.02]], .033);
  }
  stroke(head, [[-.095,-.23,-.335],[0,-.255,-.338],[.095,-.23,-.335]], "#302d2b", .018);
  const arms = [], legs = [];
  for (const side of [-1, 1]) {
    const shoulder = joint(torso, [side * .32, .44, -.015]);
    shoulder.rotation.z = side * .16;
    limb(shoulder,.43,.125,.075,green);
    const elbow = joint(shoulder, [0,-.43,0]);
    limb(elbow,.42,.083,.045,bark);
    const hand = joint(elbow, [0,-.42,0]);
    part(hand, sculpt([[.03,.07,.055],[-.12,.067,.035],[-.2,.018,.025]]), bark);
    for (const finger of [-1, 1]) part(hand, new THREE.ConeGeometry(.023,.11,4), mask, [finger * .04,-.19,-.025], [Math.PI-.2,0,finger * .1]);
    arms.push({shoulder, elbow, hand, side});
    const hip = joint(pelvis, [side * .19, -.09, .015]);
    limb(hip,.38,.12,.068,green);
    const knee = joint(hip, [0,-.38,0]);
    limb(knee,.33,.071,.038,bark);
    const foot = joint(knee, [0,-.33,0]);
    part(foot, sculpt([[-.005,.058,.1,-.045],[-.065,.063,.15,-.08],[-.09,.055,.12,-.08]]), dark);
    legs.push({hip,knee,foot,side});
  }
  const club = joint(arms[1].hand, [.015,-.075,-.03]);
  club.rotation.set(-.3,0,-.35);
  part(club,new THREE.CylinderGeometry(.04,.045,.64,7),bark,[0,.18,0]);
  part(club,sculpt([[.34,.075,.065],[.46,.11,.09],[.77,.095,.08],[.85,.045,.055]]),dark);
  part(club,new THREE.CylinderGeometry(.117,.117,.055,7),red,[0,.52,0]);
  const talisman = joint(torso, [0,.3,-.255]);
  ribbon(talisman,mask, [[0,.03,0],[0,-.14,-.01],[0,-.29,.02]], .055);
  stroke(talisman, [[-.025,-.055,-.01],[.024,-.087,-.017],[-.02,-.125,-.016]], "#bd4936", .013);
  batchFixedParts(root);
  root.userData.rig = {visual,pelvis,torso,head,mantle,arms,legs,eyes,club,talisman};
  return root;
}
