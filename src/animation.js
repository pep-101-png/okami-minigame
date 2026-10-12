import * as THREE from "three";
const damp = (a, b, dt, rate = 14) => THREE.MathUtils.damp(a, b, rate, dt);
export function animateWolf(
  w,
  { dt, time, speed, air, attack, dash, combo = 1 },
) {
  w.gait = (w.gait || 0) + dt * (speed > 0.1 ? 5 + speed * 1.9 : 0);
  const stride = w.gait,
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
  w.body.scale.z = damp(
    w.body.scale.z,
    1 + Math.sin(stride) * 0.045 * weight,
    dt,
  );
  if (attack > 0) {
    const wind = Math.min(attack / 0.28, 1),
      release = Math.max(0, Math.min((attack - 0.28) / 0.25, 1)),
      recover = Math.max(0, (attack - 0.65) / 0.35);
    const thrust = Math.sin((release * Math.PI) / 2) * (1 - recover);
    if (combo === 2) {
      const sweep = Math.sin(attack * Math.PI * 2 - 0.9) * 0.85 * (1 - recover);
      w.body.rotation.y = sweep * 0.35;
      w.head.rotation.y = sweep;
      w.head.rotation.z = -sweep * 0.12;
      w.spear.rotation.y = sweep * 0.2;
      w.head.position.z = -0.68;
      w.body.position.z = -thrust * 0.06;
    } else {
      w.head.position.z =
        -0.68 +
        wind * 0.12 * (1 - release) -
        thrust * (combo === 3 ? 0.45 : 0.2);
      w.head.rotation.x = -wind * 0.08 + thrust * 0.14;
      w.spear.position.z = -0.51 - thrust * 0.2;
      w.body.position.z = wind * 0.1 * (1 - release) - thrust * 0.2;
      w.body.rotation.x =
        combo === 3
          ? wind * 0.12 * (1 - release) - thrust * 0.18
          : thrust * -0.04;
      w.head.rotation.y = 0;
      w.body.rotation.y = 0;
    }
  } else {
    w.head.position.z = damp(w.head.position.z, -0.68, dt);
    w.spear.position.z = damp(w.spear.position.z, -0.51, dt);
    w.body.position.z = damp(w.body.position.z, 0, dt);
    w.head.rotation.y = damp(w.head.rotation.y, 0, dt);
    w.body.rotation.y = damp(w.body.rotation.y, 0, dt);
    w.head.rotation.z = damp(w.head.rotation.z, 0, dt);
    w.spear.rotation.y = damp(w.spear.rotation.y, 0, dt);
  }
}
