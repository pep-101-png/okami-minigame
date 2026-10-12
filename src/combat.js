// Normalized animation timings. Victims are hit once across a moving active arc.
export const ATTACKS = [
  null,
  {
    name: "I · REED THRUST",
    duration: 0.46,
    hit: 0.4,
    active: [0.35, 0.49],
    link: 0.77,
    cancel: 0.55,
    damage: 1,
    range: 3.3,
    arc: 0.8,
    lunge: 3.2,
    movement: 0.18,
    knockback: 0.6,
    stagger: 0.42,
    hitStop: 0.038,
  },
  {
    name: "II · CRESCENT SWEEP",
    duration: 0.62,
    hit: 0.46,
    active: [0.3, 0.62],
    link: 0.8,
    cancel: 0.64,
    damage: 2,
    range: 3.15,
    arc: 0.32,
    lunge: 1.3,
    movement: 0.14,
    knockback: 0.95,
    stagger: 0.58,
    hitStop: 0.054,
  },
  {
    name: "III · SUNWARD LUNGE",
    duration: 0.86,
    hit: 0.49,
    active: [0.42, 0.59],
    link: 0.89,
    cancel: 0.72,
    damage: 3,
    range: 3.8,
    arc: 0.82,
    lunge: 8.5,
    movement: 0.06,
    knockback: 1.85,
    stagger: 0.85,
    hitStop: 0.078,
  },
];

export const COMBO_GRACE = 0.52;
export const ATTACK_BUFFER = 0.3;

export function attackEnvelope(phase, attack) {
  const a = attack.active[0] - 0.04;
  const b = attack.active[1] + 0.06;
  if (phase <= a || phase >= b) return 0;
  return Math.sin(((phase - a) / (b - a)) * Math.PI);
}

export function sweepAngle(phase) {
  const t = Math.max(0, Math.min(1, (phase - 0.3) / 0.32));
  return -0.98 + t * 1.96;
}
