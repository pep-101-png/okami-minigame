import { distance, pointSegment, clamp } from "./math.js";
import { hitEnemy } from "./enemies.js";
export function recognise(points) {
  if (points.length < 5) return { kind: "none" };
  const minX = Math.min(...points.map((p) => p.x)),
    maxX = Math.max(...points.map((p) => p.x)),
    minY = Math.min(...points.map((p) => p.y)),
    maxY = Math.max(...points.map((p) => p.y)),
    w = maxX - minX,
    h = maxY - minY,
    a = points[0],
    b = points.at(-1),
    span = Math.hypot(w, h),
    center = { x: (minX + maxX) / 2, y: (minY + maxY) / 2 };
  let length = 0;
  for (let i = 1; i < points.length; i++)
    length += distance(points[i - 1], points[i]);
  const closed = distance(a, b) < span * 0.35;
  let turns = 0;
  for (let i = 2; i < points.length; i++) {
    const v0 = {
        x: points[i - 1].x - points[i - 2].x,
        y: points[i - 1].y - points[i - 2].y,
      },
      v1 = {
        x: points[i].x - points[i - 1].x,
        y: points[i].y - points[i - 1].y,
      };
    turns += Math.atan2(v0.x * v1.y - v0.y * v1.x, v0.x * v1.x + v0.y * v1.y);
  }
  if (span < 28) return { kind: "none" };
  // Spiral: a coil ending near its centre. Circle: generous closed oval.
  if (Math.abs(turns) > Math.PI * 2.5 && distance(b, center) < span * 0.45)
    return { kind: "bomb", center, points, w, h };
  if (closed && w > 35 && h > 35 && length > span * 1.7)
    return { kind: "bloom", center, points, w, h };
  if (distance(a, b) / length > 0.88)
    return { kind: "slash", center, a, b, points, w, h };
  if (length > span * 1.25 && w > h * 1.3)
    return { kind: "wind", center, a, b, points, w, h };
  return { kind: "water", center, a, b, points, w, h };
}
export class Brush {
  constructor(g) {
    this.g = g;
    this.active = false;
    this.drawing = false;
    this.points = [];
    this.history = [];
    g.input.onDown = (p, button) => {
      if (this.active && button === 0) {
        this.drawing = true;
        this.points = [{ ...p }];
        g.audio.play("ink");
      }
    };
    g.input.onMove = (p) => {
      if (this.active && this.drawing && distance(p, this.points.at(-1)) > 3) {
        this.points.push({ ...p });
        if (this.points.length % 12 === 0) g.audio.play("ink");
      }
    };
    g.input.onUp = () => {
      if (this.active && this.drawing) {
        this.drawing = false;
        this.cast();
      }
    };
  }
  toggle() {
    if (this.g.state !== "playing") return;
    this.active = !this.active;
    this.g.player.brush = this.active;
    this.points = [];
    this.drawing = false;
    this.g.audio.play("brush");
    this.g.ui();
  }
  world(p) {
    return this.g.renderer.screenToWorld(p);
  }
  cast() {
    const g = this.g,
      w = g.world,
      r = recognise(this.points);
    this.history.push({
      points: this.points.map((p) => ({ ...p })),
      age: 0,
      success: false,
    });
    let cost =
      { slash: 12, bloom: 22, wind: 16, bomb: 28, water: 18 }[r.kind] || 0;
    if (!cost) {
      g.say("Draw a longer stroke. A line cuts; a circle blooms.", 3);
      this.points = [];
      return;
    }
    if (g.player.ink < cost) {
      g.say("Not enough ink. Leave Brush Mode to recharge.", 3);
      this.points = [];
      return;
    }
    let success = false;
    const pts = r.points.map((p) => this.world(p)),
      center = this.world(r.center);
    const nearLine = (point, radius) =>
      pts.some((p, i) => i && pointSegment(point, pts[i - 1], p) < radius);
    // Water uses the actual stroke between the river and the receiving stone basin.
    if (
      (r.kind === "water" || r.kind === "slash" || r.kind === "wind") &&
      distance(pts[0], w.water) < 140 &&
      distance(pts.at(-1), w.basin) < 110
    ) {
      w.basin.filled = true;
      success = true;
      r.kind = "water";
      g.effect(w.basin.x, w.basin.y, "water", 35);
      g.say("The water returns to the mill. Its seal begins to glow.", 4);
    } else if (r.kind === "slash") {
      for (const e of w.enemies)
        if (
          !e.dead &&
          nearLine(
            { x: e.x, y: e.y - (e.type === "boss" ? 90 : 40) },
            e.type === "boss" ? 95 : 48,
          )
        ) {
          if (e.type === "boss" && !w.bossAwake) continue;
          e.exposed = e.type === "boss" ? 4 : 7;
          hitEnemy(e, 1, g.player.facing, g, true);
          success = true;
        }
      if (
        nearLine({ x: w.wall.x, y: w.wall.y - 45 }, 50) &&
        w.wall.broken === false
      ) {
        g.say("This ancient wall needs a bomb spiral or a heavy strike.", 3);
      }
    } else if (r.kind === "bloom") {
      for (let i = 0; i < w.trees.length; i++) {
        const tree = w.trees[i],
          tp = g.renderer.worldToScreen({ x: tree.x, y: tree.y - 190 });
        if (
          !tree.restored &&
          Math.abs(tp.x - r.center.x) < r.w * 0.6 + 25 &&
          Math.abs(tp.y - r.center.y) < r.h * 0.6 + 45
        ) {
          if (
            i === 1 &&
            w.enemies.some((e) => !e.dead && e.x > 3300 && e.x < 4900)
          ) {
            g.say(
              "The grove is still bound. Release its four restless spirits.",
              4,
            );
            continue;
          }
          if (i === 2 && !w.bossDefeated) {
            g.say(
              "The shrine tree is bound to Kurobane. Slash his seal first.",
              3,
            );
            continue;
          }
          tree.restored = true;
          success = true;
          g.effect(tree.x, tree.y - 90, "bloom", 70);
          if (i === 0) {
            g.player.doubleJump = true;
            g.player.unlocked = 2;
            g.say(
              "River willow restored · Double jump & River Beads awakened.",
              5,
            );
          }
          if (i === 1) {
            w.restored = true;
            w.restoration = 0;
            g.player.unlocked = 3;
            g.player.hp = g.player.maxHp;
            g.say("The grove remembers spring · Mountain Fang awakened.", 5);
          }
        }
      }
    } else if (r.kind === "wind") {
      for (const e of w.enemies)
        if (!e.dead && distance(center, { x: e.x, y: e.y - 40 }) < 320) {
          e.x += Math.sign(r.b.x - r.a.x) * 100;
          e.exposed = Math.max(e.exposed, 2);
          success = true;
        }
      for (const p of w.projectiles) {
        p.vx *= -1;
        p.reflected = true;
        success = true;
      }
      if (distance(center, w.lantern) < 200 && !w.lantern.lit) {
        w.lantern.lit = true;
        g.player.pearls += 3;
        success = true;
      }
      g.effect(center.x, center.y, "wind", 25);
      success = true;
    } else if (r.kind === "bomb") {
      w.bombs.push({
        x: center.x,
        y: Math.min(center.y, g.player.y - 20),
        fuse: 1.1,
      });
      success = true;
      g.say("An ink bomb takes shape. Leave Brush Mode to detonate.", 3);
    }
    if (success) {
      g.player.ink -= cost;
      this.history.at(-1).success = true;
      g.audio.play(r.kind === "bloom" ? "bloom" : "collect");
      if (w.trees[0].restored && w.basin.filled) {
        w.gate.open = true;
        g.say(
          "The river gate is open. Follow the path into the cursed grove.",
          4,
        );
      }
    } else
      g.say(
        "No valid target. Circle the tree crown, or cut through a spirit.",
        3,
      );
    this.points = [];
    g.ui();
  }
  update(dt) {
    for (const h of this.history) h.age += dt;
    this.history = this.history.filter((h) => h.age < 2);
  }
}
