export const WIDTH = 6700;
// Continuous riverbank with embedded ledges, a stone bridge, and shrine terraces.
export const platforms = [
  { x: 0, y: 575, w: 1680, h: 350 },
  { x: 1680, y: 620, w: 310, h: 350 },
  { x: 1990, y: 575, w: 900, h: 350 },
  { x: 2890, y: 610, w: 400, h: 350 },
  { x: 3290, y: 560, w: 1710, h: 350 },
  { x: 5000, y: 580, w: 1700, h: 350 },
  { x: 670, y: 452, w: 240, h: 24 },
  { x: 1030, y: 368, w: 235, h: 26 },
  { x: 1370, y: 462, w: 195, h: 24 },
  { x: 1900, y: 470, w: 190, h: 30 },
  { x: 2280, y: 420, w: 200, h: 30 },
  { x: 2650, y: 360, w: 230, h: 32 },
  { x: 2970, y: 455, w: 150, h: 28 },
  { x: 3480, y: 438, w: 180, h: 26 },
  { x: 3930, y: 375, w: 250, h: 28 },
  { x: 4470, y: 448, w: 230, h: 26 },
  { x: 5680, y: 450, w: 230, h: 30 },
  { x: 6030, y: 360, w: 240, h: 30 },
];
export const makeEnemy = (type, x, y) => ({
  type,
  x,
  y,
  vx: 0,
  vy: 0,
  home: x,
  facing: -1,
  hp: { imp: 3, moth: 2, archer: 3, armour: 5, brute: 8, boss: 40 }[type],
  maxHp: { imp: 3, moth: 2, archer: 3, armour: 5, brute: 8, boss: 40 }[type],
  state: "patrol",
  timer: 0.5,
  age: 0,
  hurt: 0,
  exposed: 0,
  dead: false,
  hitIds: new Set(),
  phase: 1,
});
export function createWorld() {
  return {
    platforms: platforms.map((p) => ({ ...p })),
    enemies: [
      makeEnemy("imp", 870, 575),
      makeEnemy("moth", 1330, 380),
      makeEnemy("archer", 2380, 420),
      makeEnemy("imp", 2680, 575),
      makeEnemy("armour", 3540, 560),
      makeEnemy("imp", 3750, 560),
      makeEnemy("moth", 4110, 390),
      makeEnemy("brute", 4460, 560),
      makeEnemy("boss", 5510, 580),
    ],
    trees: [
      { x: 1900, y: 620, restored: false, name: "River willow" },
      { x: 3910, y: 560, restored: false, name: "Heart of the grove" },
      { x: 5820, y: 580, restored: false, name: "Shrine cherry" },
    ],
    lantern: { x: 1500, y: 460, lit: false },
    gate: { x: 3220, y: 610, open: false },
    wall: { x: 4730, y: 560, broken: false },
    water: { x: 1780, y: 613 },
    basin: { x: 2170, y: 535, filled: false },
    restored: false,
    restoration: 0,
    bossAwake: false,
    bossDefeated: false,
    exit: { x: 6450, y: 580 },
    pickups: [
      ...Array.from({ length: 19 }, (_, i) => ({
        x: 410 + i * 278,
        y: 530,
        kind: "pearl",
        got: false,
      })),
      { x: 1160, y: 333, kind: "treasure", got: false },
      { x: 2750, y: 325, kind: "treasure", got: false },
      { x: 4050, y: 340, kind: "treasure", got: false },
      { x: 6160, y: 325, kind: "treasure", got: false },
    ],
    projectiles: [],
    bombs: [],
    events: [],
    flowers: [],
  };
}
export function groundAt(w, x) {
  return (
    w.platforms.find((p) => p.h > 100 && x >= p.x && x < p.x + p.w)?.y || 620
  );
}
export function collide(w, a, oldY, dt) {
  a.grounded = false;
  for (const p of w.platforms) {
    if (
      a.x + 20 > p.x &&
      a.x - 20 < p.x + p.w &&
      oldY <= p.y + 4 &&
      a.y >= p.y &&
      a.vy >= 0
    ) {
      a.y = p.y;
      a.vy = 0;
      a.grounded = true;
      break;
    }
  }
  if (a.y > 850) {
    a.x = 260;
    a.y = 575;
    a.vy = 0;
    a.hp = Math.max(0, a.hp - 1);
  }
}
