import * as THREE from "three";
const damp = (a, b, dt, rate = 14) => THREE.MathUtils.damp(a, b, rate, dt);
export function animateWolf(w, { dt, time, speed, air, attack, dash }) {
  const stride = time * (8 + speed * 1.7),
    weight = Math.min(1, speed / 5),
    spring = Math.sin(stride * 2) * 0.045 * weight;
  w.body.position.y = damp(w.body.position.y, air ? 0.08 : spring, dt);
  w.body.rotation.x = damp(
    w.body.rotation.x,
    air ? -0.12 : dash ? -0.18 : Math.sin(stride * 2) * 0.025 * weight,
    dt,
  );
  w.body.rotation.z = damp(
    w.body.rotation.z,
    Math.sin(stride) * 0.025 * weight,
    dt,
  );
  w.head.rotation.x = damp(
    w.head.rotation.x,
    air ? 0.12 : Math.sin(stride * 2 + 0.7) * 0.025 * weight,
    dt,
  );
  w.tail.rotation.z = Math.sin(time * 3) * 0.16;
  w.tail.rotation.x = -weight * 0.25;
  w.legs.forEach((leg, i) => {
    const phase = stride + (i === 0 || i === 3 ? 0 : Math.PI);
    leg.rotation.x = damp(
      leg.rotation.x,
      air ? (i % 2 ? -0.65 : 0.65) : Math.sin(phase) * 0.75 * weight,
      dt,
    );
    leg.userData.knee.rotation.x = damp(
      leg.userData.knee.rotation.x,
      air ? 0.65 : Math.max(0, -Math.sin(phase)) * 0.9 * weight,
      dt,
    );
  });
  if (attack > 0) {
    const thrust = Math.sin(attack * Math.PI);
    w.head.position.z = -0.68 - thrust * 0.26;
    w.spear.position.z = -0.51 - thrust * 0.22;
    w.body.position.z = -thrust * 0.12;
    w.head.rotation.y = Math.sin(attack * Math.PI * 2) * 0.06;
  } else {
    w.head.position.z = damp(w.head.position.z, -0.68, dt);
    w.spear.position.z = damp(w.spear.position.z, -0.51, dt);
    w.body.position.z = damp(w.body.position.z, 0, dt);
    w.head.rotation.y = damp(w.head.rotation.y, 0, dt);
  }
}
