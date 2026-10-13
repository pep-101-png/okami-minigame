export const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const damp = (a, b, k, dt) => lerp(a, b, 1 - Math.exp(-k * dt));
export const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
export function pointSegment(p, a, b) {
  const dx = b.x - a.x,
    dy = b.y - a.y,
    l = dx * dx + dy * dy,
    t = l ? clamp(((p.x - a.x) * dx + (p.y - a.y) * dy) / l, 0, 1) : 0;
  return Math.hypot(p.x - a.x - dx * t, p.y - a.y - dy * t);
}
export function seeded(seed) {
  return () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
}
