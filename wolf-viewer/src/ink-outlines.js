import * as THREE from 'three';

/** Keep the body outline behind its skin; groom contours have their own pass. */
export function createInkOutlines(mesh) {
  function shell(geometry, order, depthWrite) {
    const material = new THREE.MeshBasicMaterial({color:'#62584b',side:THREE.BackSide,depthWrite});
    material.onBeforeCompile = shader => {
      shader.vertexShader = shader.vertexShader.replace('#include <skinning_vertex>', '#include <skinning_vertex>\n transformed += normalize(objectNormal) * .013;');
    };
    const ink = new THREE.SkinnedMesh(geometry, material);
    ink.bind(mesh.skeleton, mesh.bindMatrix);
    ink.position.copy(mesh.position); ink.quaternion.copy(mesh.quaternion); ink.scale.copy(mesh.scale);
    ink.frustumCulled = false; ink.renderOrder = order;
    ink.morphTargetInfluences = mesh.morphTargetInfluences;
    return ink;
  }
  const source = mesh.geometry, detail = source.getAttribute('_fur_detail');
  if (!detail) return [shell(source, 0, true)];
  const contours = new THREE.BufferGeometry(), indices = [];
  for (const [name, attribute] of Object.entries(source.attributes)) contours.setAttribute(name, attribute);
  for (let i = 0; i < source.index.count; i += 3) {
    const a=source.index.getX(i),b=source.index.getX(i+1),c=source.index.getX(i+2);
    if (detail.getX(a)>.5 && detail.getX(b)>.5 && detail.getX(c)>.5) indices.push(a,b,c);
  }
  contours.setIndex(indices);
  contours.morphAttributes = source.morphAttributes;
  contours.morphTargetsRelative = source.morphTargetsRelative;
  return [shell(source, -1, false), shell(contours, 1, false)];
}
