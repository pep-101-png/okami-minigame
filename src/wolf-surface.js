import * as THREE from "three";
/** Skin anchors track the actual deformed triangle, including blended bone weights. */
export function skinAnchor(skin, point, direction) {
  skin.updateWorldMatrix(true, false);
  skin.skeleton.update();
  const hit = new THREE.Raycaster(point, direction).intersectObject(
    skin,
    false,
  )[0];
  if (!hit?.face) return null;
  const indices = [hit.face.a, hit.face.b, hit.face.c];
  const local = hit.point
    .clone()
    .applyMatrix4(skin.matrixWorld.clone().invert());
  const vertices = indices.map((i) =>
    skin.getVertexPosition(i, new THREE.Vector3()),
  );
  const weights = THREE.Triangle.getBarycoord(
    local,
    ...vertices,
    new THREE.Vector3(),
  );
  return { indices, weights };
}
export function skinPoint(skin, anchor) {
  const points = anchor.indices.map((i) =>
    skin
      .getVertexPosition(i, new THREE.Vector3())
      .applyMatrix4(skin.matrixWorld),
  );
  const point = points[0]
    .clone()
    .multiplyScalar(anchor.weights.x)
    .addScaledVector(points[1], anchor.weights.y)
    .addScaledVector(points[2], anchor.weights.z);
  return {
    point,
    normal: THREE.Triangle.getNormal(...points, new THREE.Vector3()),
  };
}
