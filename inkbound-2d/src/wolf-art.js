// Original high-resolution ink silhouettes. Limb endpoints drive two-bone IK;
// no sprite sheet, external models, or 3D assets are used.
import { clamp, lerp } from "./math.js";
const INK = "#302f2b",
  IVORY = "#fff8e8",
  RED = "#b33b38";
function shape(c, d, fill = IVORY, width = 2) {
  c.fillStyle = fill;
  c.strokeStyle = INK;
  c.lineWidth = width;
  c.lineJoin = "round";
  c.lineCap = "round";
  const p = new Path2D(d);
  c.fill(p);
  c.stroke(p);
}
function line(c, d, color = INK, width = 1.5) {
  c.strokeStyle = color;
  c.lineWidth = width;
  c.lineCap = "round";
  c.stroke(new Path2D(d));
}
function leg(c, root, foot, bend, far = false) {
  const dx = foot[0] - root[0],
    dy = foot[1] - root[1],
    len = Math.hypot(dx, dy),
    a = 26,
    b = 29,
    reach = clamp(len, 4, a + b - 1),
    angle = Math.atan2(dy, dx),
    theta = Math.acos(
      clamp((a * a + reach * reach - b * b) / (2 * a * reach), -1, 1),
    ),
    k = [
      root[0] + Math.cos(angle + bend * theta) * a,
      root[1] + Math.sin(angle + bend * theta) * a,
    ];
  const col = far ? "#d7d3c1" : IVORY;
  shape(
    c,
    `M ${root[0] - 7} ${root[1]} Q ${k[0] - 10} ${k[1] - 6} ${k[0] - 4} ${k[1] + 5} L ${foot[0] - 4} ${foot[1] - 5} Q ${foot[0] - 1} ${foot[1] - 2} ${foot[0] + 8} ${foot[1] - 3} Q ${foot[0] + 15} ${foot[1] + 3} ${foot[0] + 7} ${foot[1] + 4} L ${foot[0] - 8} ${foot[1] + 4} Q ${foot[0] - 13} ${foot[1]} ${foot[0] - 9} ${foot[1] - 8} L ${k[0] - 9} ${k[1] + 6} Q ${k[0] - 13} ${k[1] - 6} ${root[0] + 7} ${root[1]} Z`,
    col,
    far ? 1.3 : 1.8,
  );
  if (!far) {
    line(
      c,
      `M ${root[0]} ${root[1] + 6} Q ${k[0] + 4} ${k[1] - 3} ${k[0] - 2} ${k[1] + 9}`,
      RED,
      3,
    );
    line(
      c,
      `M ${foot[0]} ${foot[1]} l 0 3 M ${foot[0] + 5} ${foot[1]} l 0 3`,
      INK,
      1,
    );
  }
}
export function drawWolf(c, p, t) {
  c.save();
  c.translate(p.x, p.y);
  c.scale(p.facing * (1 - Math.sin((p.turn / 0.16) * Math.PI) * 0.08), 1);
  const move = Math.min(1, Math.abs(p.vx) / 250),
    sprint = Math.abs(p.vx) > 340,
    gait = p.stride,
    air = !p.grounded,
    attack = p.attack,
    ap = attack ? clamp(attack.t / attack.duration, 0, 1) : 0;
  let bob = air ? -2 : Math.sin(gait * 2) * 2 * move + Math.sin(t * 2.1) * 0.65,
    rot = 0,
    headAngle = 0;
  if (attack) {
    const pulse = Math.sin(ap * Math.PI);
    if (attack.kind === "heavy") {
      rot = -0.18 * pulse;
      bob -= 7 * pulse;
      headAngle = -0.13 * pulse;
    } else if (attack.kind === "air") {
      rot = Math.PI * 2 * ap;
      bob -= 4;
    } else {
      rot = ([-0.13, 0.18, -0.28][attack.combo - 1] || 0) * pulse;
      bob -= pulse * (attack.combo === 3 ? 12 : 3);
      headAngle = -0.18 * pulse;
    }
  }
  if (p.dodge > 0) {
    rot = -0.1;
    bob += 10;
  }
  if (p.hurt > 0.2) {
    rot = -0.16;
    headAngle = 0.15;
  }
  if (p.dead) {
    rot = -1.45 * clamp(p.deathTime / 0.45, 0, 1);
    bob += 22 * clamp(p.deathTime / 0.45, 0, 1);
  }
  if (p.land > 0) {
    bob += Math.sin((p.land / 0.2) * Math.PI) * 5;
  }
  c.translate(0, bob);
  c.rotate(rot);
  // Painted flame aureole and shoulder mirror.
  c.save();
  c.translate(9, -75);
  c.rotate(Math.sin(t * 2) * 0.04);
  const halo = c.createRadialGradient(0, 0, 4, 0, 0, 55);
  halo.addColorStop(0, "#ffc96a44");
  halo.addColorStop(1, "#ffc96a00");
  c.fillStyle = halo;
  c.beginPath();
  c.arc(0, 0, 55, 0, 7);
  c.fill();
  for (let i = 0; i < 3; i++) {
    let sw = Math.sin(t * 5 + i) * 5;
    shape(
      c,
      `M ${-21 + i * 18} 9 Q ${-40 + i * 18} -17 ${-27 + i * 18 + sw} -38 Q ${-13 + i * 18} -23 ${-4 + i * 18} -51 Q ${6 + i * 18} -20 ${10 + i * 18} 2 Z`,
      i === 1 ? "#d96843" : "#be3c35",
      1.3,
    );
  }
  c.rotate(t * 0.08);
  shape(
    c,
    "M -22 0 Q -24 -20 0 -23 Q 25 -20 23 0 Q 22 22 0 24 Q -23 23 -22 0 Z",
    "#b59b5b",
    2,
  );
  shape(
    c,
    "M -16 0 Q -17 -15 0 -16 Q 17 -15 16 0 Q 17 16 0 17 Q -17 16 -16 0 Z",
    "#3e6f63",
    1,
  );
  line(
    c,
    "M -8 2 Q -12 -9 0 -9 Q 12 -7 7 4 Q 1 12 -4 5 Q -7 0 0 -1",
    "#ead897",
    2,
  );
  c.restore();
  // Tail: one tapering flowing form, with ink-edged layered fur.
  const tail = Math.sin(t * 3 - gait * 0.2) * 5 + move * 7;
  shape(
    c,
    `M -37 -49 Q -71 -48 -82 ${-71 + tail} Q -89 ${-88 + tail} -115 ${-77 + tail} L -105 ${-88 + tail} Q -128 ${-83 + tail} -122 ${-60 + tail} Q -105 ${-45 + tail} -90 ${-49 + tail} L -97 ${-39 + tail} Q -61 -32 -36 -37 Z`,
    IVORY,
    2,
  );
  line(
    c,
    `M -48 -45 Q -72 -41 -88 ${-59 + tail} Q -99 ${-70 + tail} -110 ${-66 + tail}`,
    RED,
    2.4,
  );
  const feet = [];
  for (let i = 0; i < 4; i++) {
    const front = i >= 2,
      far = i % 2 === 0,
      phase =
        gait +
        (sprint
          ? (front ? 0 : 2.4) + (far ? 1 : 0)
          : [Math.PI, 0, 0, Math.PI][i]);
    let fx = (front ? 30 : -35) + Math.cos(phase) * 24 * move,
      fy = -Math.max(0, Math.sin(phase)) * 20 * move;
    if (air) {
      const up = clamp(-p.vy / 620, -1, 1);
      fx = (front ? 35 : -35) + (front ? 1 : -1) * (5 + Math.max(0, up) * 8);
      fy = -10 - Math.max(0, up) * 9 + (front ? -up * 3 : up * 3);
    }
    if (p.dodge > 0) {
      fx += front ? 18 : -10;
      fy = -5;
    }
    if (attack && attack.combo === 3) {
      fx += front ? 12 : -12;
      fy -= Math.sin(ap * Math.PI) * 8;
    }
    if (p.dead) fy = -18;
    feet.push([fx, fy]);
  }
  leg(c, [-27, -42], feet[0], -1, true);
  leg(c, [25, -48], feet[2], 1, true);
  // Continuous torso with deep chest, tucked flank, and pointed ruff.
  shape(
    c,
    "M -44 -45 Q -50 -63 -27 -65 Q -9 -62 17 -67 Q 28 -78 37 -79 Q 49 -73 48 -53 L 55 -42 L 45 -46 L 47 -33 L 38 -38 L 36 -25 Q 24 -23 15 -39 Q 0 -48 -17 -38 Q -31 -25 -42 -37 Z",
    IVORY,
    2.2,
  );
  shape(
    c,
    "M 23 -63 Q 27 -84 47 -94 L 55 -89 L 49 -77 L 60 -71 L 46 -72 L 53 -61 L 39 -64 L 46 -50 L 35 -56 L 38 -42 Q 20 -45 23 -63 Z",
    IVORY,
    1.7,
  );
  // Subtle ink-wash shadow follows the tucked flank, never obscuring the silhouette.
  c.save();
  c.globalAlpha = 0.34;
  shape(
    c,
    "M -39 -40 Q -18 -35 -12 -43 Q 8 -46 20 -33 Q 27 -21 36 -27 L 37 -39 Q 17 -48 -2 -46 Q -26 -48 -39 -40 Z",
    "#8e9886",
    0,
  );
  c.restore();
  leg(c, [-29, -44], feet[1], -1);
  leg(c, [27, -49], feet[3], 1);
  // Layered ruff is part of the silhouette; fine ink hatching gives it direction.
  line(
    c,
    "M 35 -74 Q 29 -63 32 -54 M 40 -73 L 39 -63 M -38 -54 Q -43 -46 -38 -40",
    "#87907e",
    0.8,
  );
  shape(
    c,
    "M 12 -64 Q -5 -61 -19 -61 Q -28 -65 -35 -58 Q -24 -61 -17 -57 Q 0 -55 12 -64 Z",
    RED,
    0,
  );
  // Shoulder spiral and long flowing red flank strokes.
  line(
    c,
    "M 31 -57 C 16 -69 10 -49 24 -48 C 35 -47 37 -60 25 -61 C 17 -62 18 -54 24 -55",
    RED,
    2.7,
  );
  line(
    c,
    "M 13 -59 Q -5 -53 -25 -58 Q -37 -59 -37 -49 Q -34 -43 -29 -46",
    RED,
    2.6,
  );
  line(c, "M 9 -53 Q -12 -47 -22 -49 Q -29 -52 -32 -49", RED, 1.6);
  line(c, "M 32 -45 Q 43 -52 44 -63", RED, 2);
  // Noble wedge head, long muzzle, expressive visible eye, and alert ears.
  c.save();
  c.translate(43, -77);
  c.rotate(headAngle + (air ? -0.06 : Math.sin(t * 2) * 0.016));
  shape(
    c,
    "M -5 -6 L -5 -27 Q -1 -31 5 -13 Q 12 -20 22 -13 L 27 -5 Q 35 -3 48 1 Q 51 7 44 9 L 29 10 Q 26 17 18 16 L 6 17 L 11 10 L 0 14 L 2 5 Q -8 4 -5 -6 Z",
    IVORY,
    2,
  );
  shape(c, "M 12 -13 L 17 -34 Q 23 -34 26 -12 L 20 -8 Z", IVORY, 1.7);
  shape(c, "M 18 -15 L 19 -27 L 23 -15 Z", "#b1a58c", 0.7);
  shape(c, "M 43 2 Q 48 0 51 4 Q 52 8 45 9 Z", INK, 1);
  line(c, "M 31 10 L 43 9", INK, 1);
  line(c, "M 13 -8 Q 17 -13 23 -8", INK, 2);
  shape(c, "M 15 -7 Q 19 -11 24 -7 Q 20 -3 15 -7 Z", "#d4a23c", 0.8);
  line(c, "M 20 -8 L 20 -5", INK, 1.5);
  line(c, "M 13 -14 Q 7 -9 12 -3 L 7 2 Q 10 6 17 3", RED, 2.3);
  line(c, "M 28 -8 Q 33 -5 37 -4", RED, 2);
  line(c, "M -1 1 L -6 6 M 4 5 L 0 10", "#9a9d8d", 0.8);
  c.restore();
  // Thin trailing divine ribbons have a broad root and a soft curling taper.
  c.save();
  c.globalAlpha = 0.7;
  for (let i = 0; i < 3; i++) {
    const y = -66 - i * 10,
      w = Math.sin(t * 3.5 - i * 0.7) * 8;
    line(
      c,
      `M ${17 - i * 5} ${y} Q ${-20 - i * 16} ${y - 17 + w} ${-60 - i * 20} ${y + 3 + w} Q ${-94 - i * 13} ${y + 22 + w} ${-112 - i * 12} ${y + 7}`,
      i === 1 ? "#df8a63" : "#fff9df",
      i === 1 ? 1.3 : 2.2,
    );
  }
  c.restore();
  if (p.brush) {
    c.strokeStyle = "#ba433b";
    c.lineWidth = 1;
    c.beginPath();
    c.ellipse(0, -40, 70, 58, t * 0.3, 0, Math.PI * 2);
    c.stroke();
  }
  c.restore();
}
