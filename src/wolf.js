import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { clone } from "three/addons/utils/SkeletonUtils.js";
import { paint } from "./art.js";
import { wolfPaint } from "./wolf-paint.js";
import { createWolfFur } from "./wolf-fur.js";
let asset, coat;
export async function loadWolf() {
  asset ??= await new GLTFLoader().loadAsync(
    `${import.meta.env.BASE_URL}models/sunward-wolf.glb`,
  );
  if (!coat) {
    asset.scene.traverse((o) => {
      if (o.isMesh && o.material.map && !coat) coat = wolfPaint(o.material.map);
    });
  }
  return asset;
}
export function wolf() {
  if (!asset) throw new Error("Wolf must load before starting.");
  const root = new THREE.Group(),
    body = clone(asset.scene);
  body.scale.setScalar(0.023);
  body.rotation.y = Math.PI;
  root.add(body);
  body.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
      const m = paint("#fffaf0");
      m.map = coat;
      m.side = THREE.FrontSide;
      o.material = m;
    }
  });
  body.updateMatrixWorld(true);
  const head = body.getObjectByName("b_Head_05"),
    headCarrier = new THREE.Group();
  head.add(headCarrier);
  // Convert a model-space grip at the muzzle into the artist rig's local head coordinates.
  const headPoint = new THREE.Vector3(0, 56.2, 60);
  const gripLocal = headPoint
    .clone()
    .applyMatrix4(body.matrixWorld)
    .applyMatrix4(head.matrixWorld.clone().invert());
  headCarrier.position.copy(gripLocal);
  const worldRigRotation = new THREE.Quaternion();
  head.getWorldQuaternion(worldRigRotation);
  const desired = new THREE.Quaternion().setFromAxisAngle(
    new THREE.Vector3(0, 1, 0),
    Math.PI,
  );
  headCarrier.quaternion.copy(worldRigRotation.invert().multiply(desired));
  headCarrier.scale.setScalar(1 / 0.023);
  function headDetail(position, geometry, color, scale = [1, 1, 1]) {
    const detail = new THREE.Mesh(geometry, paint(color));
    detail.position.copy(
      new THREE.Vector3(...position)
        .applyMatrix4(body.matrixWorld)
        .applyMatrix4(head.matrixWorld.clone().invert()),
    );
    detail.scale.set(...scale);
    head.add(detail);
    return detail;
  }
  const eyes = [],
    eyeAnchors = [];
  const sourceSkin = (() => {
    let m;
    body.traverse((o) => {
      if (o.isSkinnedMesh && !m) m = o;
    });
    return m;
  })();
  sourceSkin.skeleton.update();
  for (const sign of [-1, 1]) {
    const origin = new THREE.Vector3(sign * 45, 63.2, 56.0).applyMatrix4(
        body.matrixWorld,
      ),
      direction = new THREE.Vector3(-sign, 0, 0).transformDirection(
        body.matrixWorld,
      );
    const hits = new THREE.Raycaster(origin, direction).intersectObject(
      sourceSkin,
      false,
    );
    const point =
      hits[0]?.point.clone() ||
      new THREE.Vector3(sign * 10, 63.2, 56.0).applyMatrix4(body.matrixWorld);
    const outward =
      hits[0]?.face?.normal
        .clone()
        .applyMatrix3(
          new THREE.Matrix3().getNormalMatrix(sourceSkin.matrixWorld),
        )
        .normalize() ||
      new THREE.Vector3(sign, 0, 0).transformDirection(body.matrixWorld);
    const surfacePoint = point.clone();
    point.addScaledVector(outward, 0.02);
    const eye = new THREE.Group();
    eye.name = sign < 0 ? "Wolf eye left" : "Wolf eye right";
    head.add(eye);
    eye.position.copy(point.applyMatrix4(head.matrixWorld.clone().invert()));
    const headRotation = new THREE.Quaternion();
    head.getWorldQuaternion(headRotation);
    const look = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      outward,
    );
    eye.quaternion.copy(headRotation.invert().multiply(look));
    const shape = new THREE.Shape();
    shape.moveTo(-2.4, 0);
    shape.quadraticCurveTo(-0.7, 1.35, 2.4, 0.05);
    shape.quadraticCurveTo(0.8, -1, -2.4, 0);
    const lid = new THREE.Mesh(
      new THREE.ShapeGeometry(shape),
      new THREE.MeshBasicMaterial({ color: "#231e19", side: THREE.DoubleSide }),
    );
    eye.add(lid);
    const iris = new THREE.Mesh(
      new THREE.CircleGeometry(0.9, 20),
      new THREE.MeshBasicMaterial({ color: "#c89843" }),
    );
    iris.scale.set(0.8, 1, 1);
    iris.position.set(0.25, 0, 0.12);
    eye.add(iris);
    const pupil = new THREE.Mesh(
      new THREE.CircleGeometry(0.49, 16),
      new THREE.MeshBasicMaterial({ color: "#151917" }),
    );
    pupil.scale.x = 0.62;
    pupil.position.set(0.26, 0, 0.2);
    eye.add(pupil);
    const glint = new THREE.Mesh(
      new THREE.CircleGeometry(0.22, 12),
      new THREE.MeshBasicMaterial({ color: "#fffbe7" }),
    );
    glint.position.set(0.04, 0.32, 0.25);
    eye.add(glint);
    eyes.push(eye);
    if (hits[0]?.face) {
      const face = hits[0].face,
        a = sourceSkin.getVertexPosition(face.a, new THREE.Vector3()),
        b = sourceSkin.getVertexPosition(face.b, new THREE.Vector3()),
        c = sourceSkin.getVertexPosition(face.c, new THREE.Vector3()),
        local = surfacePoint
          .clone()
          .applyMatrix4(sourceSkin.matrixWorld.clone().invert());
      const weights = THREE.Triangle.getBarycoord(
        local,
        a,
        b,
        c,
        new THREE.Vector3(),
      );
      eyeAnchors.push({ eye, indices: [face.a, face.b, face.c], weights });
    }
  }
  const fur = createWolfFur(body);
  const skins = [];
  body.traverse((o) => {
    if (o.isSkinnedMesh) skins.push(o);
  });
  for (const original of skins) {
    const inkMaterial = new THREE.MeshToonMaterial({
      color: "#30342c",
      side: THREE.BackSide,
    });
    inkMaterial.onBeforeCompile = (shader) => {
      shader.vertexShader = shader.vertexShader.replace(
        "#include <skinning_vertex>",
        "#include <skinning_vertex>\n transformed += normalize(objectNormal) * .55;",
      );
    };
    const shell = new THREE.SkinnedMesh(original.geometry, inkMaterial);
    shell.bind(original.skeleton, original.bindMatrix);
    shell.position.copy(original.position);
    shell.quaternion.copy(original.quaternion);
    shell.scale.copy(original.scale);
    shell.frustumCulled = false;
    original.parent.add(shell);
  }
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
  const blade = add(
    new THREE.ConeGeometry(0.135, 0.55, 4),
    bladeMat,
    [0.3, 0, 1.805],
    [Math.PI / 2, 0, Math.PI / 4],
  );
  blade.scale.z = 0.22;
  add(new THREE.TorusGeometry(0.095, 0.025, 6, 12), goldMat, [0.3, 0, 1.51]);
  const ribbon = add(
    new THREE.PlaneGeometry(0.075, 0.38),
    paint("#c2352d"),
    [0.38, -0.11, 1.49],
    [0.1, 0.3, -0.35],
  );
  ribbon.material.side = THREE.DoubleSide;
  const mixer = new THREE.AnimationMixer(body),
    actions = {};
  for (const clip of asset.animations) {
    const upperCharge = ["ChargeLight", "ChargeHeavy"].includes(clip.name);
    const playClip = upperCharge
      ? new THREE.AnimationClip(
          clip.name,
          clip.duration,
          clip.tracks.filter(
            (t) => !/UpperArm|ForeArm|Hand|Leg|Foot|Hip/.test(t.name),
          ),
        )
      : clip;
    const action = mixer.clipAction(playClip);
    actions[clip.name] = action;
    if (!["Idle", "Walk", "Run"].includes(clip.name)) {
      action.setLoop(THREE.LoopOnce, 1);
      action.clampWhenFinished = true;
    }
  }
  const chargeStride = mixer.clipAction(
    new THREE.AnimationClip(
      "ChargeStride",
      actions.Walk.getClip().duration,
      actions.Walk.getClip().tracks.filter((t) =>
        /UpperArm|ForeArm|Hand|Leg|Foot|Hip/.test(t.name),
      ),
    ),
  );
  let strideWeight = 0;
  chargeStride.play().setEffectiveWeight(0);
  const result = {
    root,
    body,
    head,
    spear,
    ribbon,
    mixer,
    actions,
    state: null,
    legs: [],
    tail: body.getObjectByName("b_Tail01_012"),
    previousAir: false,
    eyes,
    fur,
    footfalls: [],
    landing: 0,
    lastAttackPhase: 0,
  };
  result.weaponEndpoints = () => {
    root.updateMatrixWorld(true);
    return {
      tip: spear.localToWorld(new THREE.Vector3(0.3, 0, 2.08)),
      heel: spear.localToWorld(new THREE.Vector3(0.3, 0, -0.9)),
    };
  };
  function transition(nextState, fade = 0.14) {
    const next = actions[nextState],
      previous = actions[result.state];
    if (!next) return;
    next.reset().setEffectiveWeight(1).setEffectiveTimeScale(1).play();
    if (previous && previous !== next) previous.crossFadeTo(next, fade, false);
    result.state = nextState;
  }
  result.updateDetails = () => {
    root.updateMatrixWorld(true);
    sourceSkin.skeleton.update();
    for (const anchor of eyeAnchors) {
      const points = anchor.indices.map((i) =>
        sourceSkin
          .getVertexPosition(i, new THREE.Vector3())
          .applyMatrix4(sourceSkin.matrixWorld),
      );
      const normal = THREE.Triangle.getNormal(...points, new THREE.Vector3());
      const p = points[0]
        .clone()
        .multiplyScalar(anchor.weights.x)
        .addScaledVector(points[1], anchor.weights.y)
        .addScaledVector(points[2], anchor.weights.z)
        .addScaledVector(normal, 0.02);
      anchor.eye.position.copy(
        p.applyMatrix4(head.matrixWorld.clone().invert()),
      );
      const headRotation = new THREE.Quaternion();
      head.getWorldQuaternion(headRotation);
      anchor.eye.quaternion.copy(
        headRotation
          .invert()
          .multiply(
            new THREE.Quaternion().setFromUnitVectors(
              new THREE.Vector3(0, 0, 1),
              normal,
            ),
          ),
      );
    }
  };
  result.animate = ({
    dt,
    speed,
    air,
    attack,
    dash,
    combo = 1,
    turnDelta = 0,
    verticalVelocity = 0,
    attackClip = null,
    charge = null,
    voice = null,
    landing = 0,
  }) => {
    if (result.previousAir && !air) result.landing = 0.26;
    result.previousAir = air;
    result.landing = Math.max(0, result.landing - dt);
    const state =
      attack > 0
        ? attackClip || ["", "Thrust", "Sweep", "Finish"][combo]
        : dash
          ? "Dodge"
          : air
            ? verticalVelocity >= -0.25
              ? "JumpRise"
              : "JumpFall"
            : charge
              ? charge.kind === "heavy"
                ? "ChargeHeavy"
                : "ChargeLight"
              : voice && speed < 0.6
                ? voice.clip
                : result.landing > 0
                  ? "Land"
                  : speed > 6.2
                    ? "Run"
                    : speed > 0.18
                      ? "Walk"
                      : "Idle";
    const restartAttack =
      attack > 0 &&
      state === result.state &&
      attack + 0.1 < result.lastAttackPhase;
    if (state !== result.state || restartAttack)
      transition(state, attack > 0 ? 0.08 : state === "Land" ? 0.07 : 0.16);
    const action = actions[state];
    if (state === "Walk")
      action.setEffectiveTimeScale(
        THREE.MathUtils.clamp(speed / 2.45, 0.45, 2.4),
      );
    else if (state === "Run")
      action.setEffectiveTimeScale(
        THREE.MathUtils.clamp(speed / 3.1, 0.8, 2.4),
      );
    strideWeight = THREE.MathUtils.damp(
      strideWeight,
      charge && speed > 0.18 && !air && attack <= 0 ? 1 : 0,
      14,
      dt,
    );
    chargeStride
      .setEffectiveWeight(strideWeight)
      .setEffectiveTimeScale(THREE.MathUtils.clamp(speed / 2.45, 0.25, 1.5));
    const before = action.time / action.getClip().duration;
    mixer.update(dt);
    const after = action.time / action.getClip().duration;
    result.footfalls = [];
    if ((state === "Walk" || state === "Run") && speed > 0.3 && !air) {
      const contacts = state === "Walk" ? [0.17, 0.67] : [0.53, 0.95];
      for (let i = 0; i < contacts.length; i++) {
        const phase = contacts[i];
        if (
          (after >= before && phase > before && phase <= after) ||
          (after < before && (phase > before || phase <= after))
        ) {
          root.updateMatrixWorld(true);
          const foot = body.getObjectByName(
            i ? "b_RightHand_08" : "b_LeftHand_011",
          );
          const p = foot.getWorldPosition(new THREE.Vector3());
          p.y = root.position.y + 0.015;
          result.footfalls.push(p);
        }
      }
    }
    if (attack > 0) {
      action.time = attack * action.getClip().duration;
      mixer.update(0);
    }
    if (air && attack <= 0 && !dash) {
      const phase =
        state === "JumpRise"
          ? THREE.MathUtils.clamp(1 - verticalVelocity / 7.7, 0.05, 0.95)
          : THREE.MathUtils.clamp(-verticalVelocity / 7.7, 0.05, 0.95);
      action.time = phase * action.getClip().duration;
      mixer.update(0);
    }
    if (charge && attack <= 0 && !air) {
      action.time =
        Math.min(0.95, 0.2 + charge.ratio * 0.75) * action.getClip().duration;
      mixer.update(0);
    }
    if (voice && state === voice.clip) {
      action.time = voice.phase * action.getClip().duration;
      mixer.update(0);
    }
    const blink = Math.pow(Math.max(0, Math.cos(mixer.time * 1.05 + 1.2)), 70);
    for (const eye of eyes)
      eye.scale.y = Math.max(0.08, 1 - blink * (charge ? 0.65 : 0.91));
    fur.update(mixer.time, speed);
    result.updateDetails();
    result.lastAttackPhase = attack;
    // Modest secondary leaning follows steering, not the animation's foot contacts.
    body.rotation.z = THREE.MathUtils.damp(
      body.rotation.z,
      THREE.MathUtils.clamp(turnDelta * 0.18, -0.09, 0.09),
      10,
      dt,
    );
    ribbon.rotation.z = -0.35 + Math.sin(mixer.time * 10) * 0.13;
  };
  return result;
}
