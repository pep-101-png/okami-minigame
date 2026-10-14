import { drawWolf } from "./wolf-art.js";
import {
  drawPaintedWolf,
  drawPaintedEnemy,
  drawPaintedBackdrop,
  drawPaintedProp,
  drawPaintedLedge,
} from "./painted-art.js";
import { clamp, damp, lerp, seeded } from "./math.js";
const INK = "#3b3d34";
function path(c, d, fill, stroke = INK, width = 2) {
  const p = new Path2D(d);
  c.fillStyle = fill;
  if (fill) c.fill(p);
  if (stroke) {
    c.strokeStyle = stroke;
    c.lineWidth = width;
    c.lineJoin = "round";
    c.lineCap = "round";
    c.stroke(p);
  }
}
function ellipse(c, x, y, rx, ry, col, stroke = null) {
  c.beginPath();
  c.ellipse(x, y, rx, ry, 0, 0, 7);
  c.fillStyle = col;
  c.fill();
  if (stroke) {
    c.strokeStyle = stroke;
    c.stroke();
  }
}
function wash(c, x, y, rx, ry, col) {
  c.save();
  c.globalAlpha = 0.13;
  for (let i = 0; i < 4; i++)
    ellipse(c, x + i * 3, y - i * 2, rx + i * 9, ry + i * 4, col);
  c.restore();
}
export class Renderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d", { alpha: false });
    this.camera = { x: 0, y: 0, zoom: 1 };
    this.paper = document.createElement("canvas");
    this.paper.width = 512;
    this.paper.height = 512;
    const c = this.paper.getContext("2d"),
      rng = seeded(8981),
      img = c.createImageData(512, 512);
    for (let i = 0; i < img.data.length; i += 4) {
      const v = rng() * 255;
      img.data[i] = v;
      img.data[i + 1] = v;
      img.data[i + 2] = v;
      img.data[i + 3] = 22;
    }
    c.putImageData(img, 0, 0);
    this.resize();
    window.addEventListener("resize", () => this.resize());
  }
  resize() {
    const d = Math.min(devicePixelRatio, 2);
    this.canvas.width = Math.floor(innerWidth * d);
    this.canvas.height = Math.floor(innerHeight * d);
  }
  updateCamera(g, dt) {
    if (g.brush.active) return;
    const p = g.player,
      boss = g.world.bossAwake && !g.world.bossDefeated;
    const zoom = boss ? 0.9 : Math.abs(p.vx) > 350 ? 0.94 : 1;
    let target = clamp(
      p.x - 420 + p.facing * Math.min(Math.abs(p.vx) * 0.28, 115),
      0,
      6700 - 1280 / zoom,
    );
    if (boss) target = clamp(target, 4660, 5020);
    this.camera.x = damp(this.camera.x, target, 4, dt);
    this.camera.y = damp(this.camera.y, clamp(p.y - 540, -190, 60), 3.2, dt);
    this.camera.zoom = damp(this.camera.zoom, zoom, 2, dt);
    g.camera = { ...this.camera };
  }
  screenToWorld(p) {
    return {
      x: p.x / this.camera.zoom + this.camera.x,
      y: p.y / this.camera.zoom + this.camera.y,
    };
  }
  worldToScreen(p) {
    return {
      x: (p.x - this.camera.x) * this.camera.zoom,
      y: (p.y - this.camera.y) * this.camera.zoom,
    };
  }
  draw(g) {
    const c = this.ctx,
      sx = this.canvas.width / 1280,
      sy = this.canvas.height / 720;
    c.setTransform(sx, 0, 0, sy, 0, 0);
    c.clearRect(0, 0, 1280, 720);
    const curse = g.player.x > 3200 && g.player.x < 4900 && !g.world.restored;
    this.background(c, g, curse);
    c.save();
    c.scale(this.camera.zoom, this.camera.zoom);
    c.translate(-this.camera.x, -this.camera.y);
    this.world(c, g);
    for (const item of g.world.pickups)
      if (!item.got && Math.abs(item.x - g.player.x) < 1600)
        this.pickup(c, item, g.time);
    for (const e of g.world.enemies)
      if (Math.abs(e.x - g.player.x) < 1600) this.enemy(c, e, g);
    for (const b of g.world.bombs) {
      c.save();
      c.translate(b.x, b.y);
      ellipse(c, 0, 0, 20, 23, "#263d42", INK);
      path(c, "M 4 -19 Q 20 -39 26 -21", null, "#b84238", 3);
      ellipse(c, 24, -27, 7, 7, "#e6ad52");
      c.restore();
    }
    const p = g.player;
    c.save();
    if (p.hurt > 0 && Math.floor(p.hurt * 16) % 2) c.globalAlpha = 0.55;
    ellipse(c, p.x, p.y + 5, 55, 6, "#29382c25");
    if (!drawPaintedWolf(c, p, g.time)) drawWolf(c, p, g.time);
    c.restore();
    this.weapon(c, p, g.time);
    for (const pr of g.world.projectiles) {
      c.save();
      c.translate(pr.x, pr.y);
      c.rotate(Math.atan2(pr.vy, pr.vx));
      path(
        c,
        pr.kind === "wave"
          ? "M -28 13 Q -4 -32 25 8 L 10 5 Q -4 -12 -28 13 Z"
          : "M -15 -4 L 16 0 L -15 5 L -8 0 Z",
        "#a95968",
        "#583c4c",
        1.3,
      );
      c.restore();
    }
    this.particles(c, g);
    this.foreground(c, g);
    for (let i = 0; i < 14; i++) {
      let x =
          this.camera.x +
          ((((i * 147 - g.time * (12 + (i % 3) * 5)) % 1400) + 1400) % 1400),
        y = 180 + ((i * 49 + g.time * (7 + (i % 4))) % 400);
      c.save();
      c.translate(x, y);
      c.rotate(Math.sin(g.time + i));
      ellipse(c, 0, 0, 4, 1.5, "#dca69699");
      c.restore();
    }
    c.restore();
    c.save();
    c.globalAlpha = 0.21;
    c.globalCompositeOperation = "multiply";
    c.fillStyle = c.createPattern(this.paper, "repeat");
    c.fillRect(0, 0, 1280, 720);
    c.restore();
    const vignette = c.createRadialGradient(640, 300, 240, 640, 300, 830);
    vignette.addColorStop(0, "#b8844100");
    vignette.addColorStop(1, "#83634125");
    c.fillStyle = vignette;
    c.fillRect(0, 0, 1280, 720);
    if (g.brush.active) this.brush(c, g);
  }
  background(c, g, curse) {
    if (drawPaintedBackdrop(c, this.camera, g.time, curse)) return;
    const cx = this.camera.x;
    const sky = c.createLinearGradient(0, 0, 0, 720);
    sky.addColorStop(0, curse ? "#c2bdc0" : "#e6dbc1");
    sky.addColorStop(0.65, curse ? "#d1c9c9" : "#f8ecd0");
    sky.addColorStop(1, "#d7d3b0");
    c.fillStyle = sky;
    c.fillRect(0, 0, 1280, 720);
    wash(c, 930 - cx * 0.025, 133, 240, 80, curse ? "#8d839b" : "#ceb08a");
    ellipse(c, 980 - cx * 0.03, 145, 58, 58, curse ? "#b78e89" : "#d3745b");
    ellipse(c, 980 - cx * 0.03, 145, 49, 49, curse ? "#bca3a0" : "#de9176");
    const layers = [
      { rate: 0.08, y: 350, color: "#b5b7a0", h: 260 },
      { rate: 0.15, y: 410, color: "#9ea998", h: 240 },
      { rate: 0.25, y: 476, color: curse ? "#8b8c98" : "#85978a", h: 190 },
    ];
    for (let n = 0; n < layers.length; n++) {
      const l = layers[n];
      c.save();
      c.translate((-cx * l.rate) % 1800, 0);
      for (let i = -1; i < 3; i++) {
        const x = i * 1700;
        path(
          c,
          `M ${x} 620 L ${x} ${l.y} Q ${x + 80} ${l.y - 65} ${x + 180} ${l.y - 30} L ${x + 400} ${l.y - l.h} Q ${x + 420} ${l.y - l.h - 25} ${x + 451} ${l.y - l.h + 5} L ${x + 650} ${l.y - 55} Q ${x + 800} ${l.y - 150} ${x + 960} ${l.y - 60} L ${x + 1150} ${l.y - l.h * 0.8} L ${x + 1350} ${l.y - 5} Q ${x + 1490} ${l.y - 40} ${x + 1700} ${l.y + 20} L ${x + 1700} 700 Z`,
          l.color,
          null,
        );
        if (n === 0)
          path(
            c,
            `M ${x + 360} ${l.y - l.h + 50} L ${x + 400} ${l.y - l.h} L ${x + 451} ${l.y - l.h + 5} L ${x + 512} ${l.y - l.h + 65} L ${x + 455} ${l.y - l.h + 50} L ${x + 421} ${l.y - l.h + 25} Z`,
            "#eee6d2",
            null,
          );
      }
      c.restore();
    }
    c.save();
    c.translate(-cx * 0.38, 0);
    for (let i = 0; i < 24; i++) {
      const x = i * 370 + 90;
      if (x - cx * 0.38 < -180 || x - cx * 0.38 > 1500) continue;
      this.pine(c, x, 510, 1 + (i % 3) * 0.3, "#526e6040");
    }
    this.pagoda(c, 1350, 455, 0.65);
    this.pagoda(c, 2850, 450, 0.7);
    this.pagoda(c, 3800, 480, 0.55);
    c.restore();
    c.save();
    c.globalAlpha = 0.35;
    for (let i = 0; i < 4; i++) {
      let x = (((i * 370 - g.time * 8 - cx * 0.02) % 1500) + 1500) % 1500;
      path(
        c,
        `M ${x} ${230 + i * 24} q 14 -8 25 0 q 10 -8 24 0`,
        null,
        "#617062",
        1,
      );
    }
    c.restore();
  }
  pine(c, x, y, s, col = "#456451") {
    c.save();
    c.translate(x, y);
    c.scale(s, s);
    path(c, "M -5 0 L -2 -167 L 4 -173 L 8 0 Z", "#655f49", null);
    for (let i = 0; i < 5; i++) {
      const yy = -145 + i * 25,
        ww = 22 + i * 11;
      path(
        c,
        `M 0 ${yy - 25} Q -12 ${yy - 6} ${-ww} ${yy + 9} Q -5 ${yy + 6} 0 ${yy + 14} Q 15 ${yy + 4} ${ww} ${yy + 9} Q 14 ${yy - 10} 0 ${yy - 25} Z`,
        col,
        null,
      );
    }
    c.restore();
  }
  pagoda(c, x, y, s = 1) {
    if (drawPaintedProp(c, 5, x, y, 260 * s)) return;
    c.save();
    c.translate(x, y);
    c.scale(s, s);
    for (let i = 0; i < 3; i++) {
      let yy = -i * 67,
        w = 105 - i * 22;
      path(
        c,
        `M ${-w + 20} ${yy} L ${-w + 20} ${yy - 60} L ${w - 20} ${yy - 60} L ${w - 20} ${yy} Z`,
        "#a98060",
        "#655e49",
        1,
      );
      for (let k = -2; k <= 2; k++)
        path(
          c,
          `M ${k * 20} ${yy - 3} L ${k * 20} ${yy - 45}`,
          null,
          "#655e49",
          3,
        );
      path(
        c,
        `M ${-w - 12} ${yy - 45} Q ${-w} ${yy - 50} ${-w + 25} ${yy - 76} Q 0 ${yy - 65} ${w - 25} ${yy - 76} Q ${w} ${yy - 50} ${w + 12} ${yy - 45} Q 0 ${yy - 33} ${-w - 12} ${yy - 45} Z`,
        "#66735b",
        "#484d3e",
        2,
      );
    }
    path(c, "M 0 -220 L 0 -250", null, "#494f3e", 3);
    c.restore();
  }
  tree(c, tree, t, corrupt = false) {
    if (
      drawPaintedProp(
        c,
        tree.restored ? 0 : 1,
        tree.x,
        tree.y,
        tree.restored ? 290 : 240,
      )
    )
      return;
    c.save();
    c.translate(tree.x, tree.y);
    const live = tree.restored;
    const sway = Math.sin(t * 0.8 + tree.x) * 3;
    path(
      c,
      `M -18 0 Q 2 -70 -11 -120 Q -32 -170 -55 -192 L -63 -230 L -48 -203 L -29 -180 Q -27 -228 -2 -256 L -7 -224 L -18 -190 Q 4 -155 12 -122 Q 29 -164 59 -186 L 78 -230 L 73 -187 L 100 -193 L 72 -174 Q 30 -145 26 -94 L 15 0 Z`,
      live ? "#796b51" : "#666468",
      INK,
      2.5,
    );
    path(
      c,
      "M -5 -15 Q 12 -85 1 -129 M 10 -92 Q 29 -144 58 -172",
      null,
      "#c5ad8250",
      4,
    );
    const rng = seeded(tree.x);
    if (live) {
      for (let i = 0; i < 24; i++) {
        const x = (rng() - 0.5) * 240 + sway,
          y = -130 - rng() * 140,
          r = 22 + rng() * 30;
        wash(c, x, y, r, r * 0.6, "#d69693");
        path(
          c,
          `M ${x - r} ${y} C ${x - r * 1.3} ${y - r * 0.35} ${x - r * 0.7} ${y - r * 0.65} ${x - r * 0.3} ${y - r * 0.48} C ${x} ${y - r * 0.9} ${x + r * 0.5} ${y - r * 0.7} ${x + r * 0.55} ${y - r * 0.38} C ${x + r * 1.1} ${y - r * 0.4} ${x + r * 1.3} ${y + r * 0.2} ${x + r * 0.6} ${y + r * 0.3} C ${x + r * 0.1} ${y + r * 0.72} ${x - r * 0.55} ${y + r * 0.65} ${x - r * 0.7} ${y + r * 0.3} Q ${x - r * 1.15} ${y + r * 0.25} ${x - r} ${y} Z`,
          ["#e9b3a2", "#e5a49b", "#f0c3ab", "#d89892"][i % 4],
          null,
        );
        c.save();
        c.globalAlpha = 0.55;
        for (let j = 0; j < 14; j++) {
          const bx = x + (rng() - 0.5) * r * 1.6,
            by = y + (rng() - 0.5) * r * 0.8;
          for (let k = 0; k < 4; k++)
            ellipse(
              c,
              bx + Math.cos(k * 1.57) * 2.3,
              by + Math.sin(k * 1.57) * 2,
              2,
              1.5,
              j % 3 ? "#f6d3b7" : "#cd8a87",
            );
        }
        c.restore();
      }
      for (let i = 0; i < 10; i++) {
        let y = ((t * 17 + i * 33) % 230) - 250,
          x = Math.sin(t + i) * 100;
        ellipse(c, x + sway, y, 3, 1.5, "#f3c5b2");
      }
    } else {
      for (let i = 0; i < 7; i++) {
        let x = Math.sin(i * 3) * 54;
        path(
          c,
          `M ${x} ${-80 - i * 16} q -35 -20 -5 -45 q 35 -14 5 -30`,
          null,
          corrupt ? "#745475" : "#62695b",
          2,
        );
      }
      ellipse(c, 0, -142, 15, 15, "#9b5662");
      path(c, "M -8 -142 L 8 -142 M 0 -150 L 0 -134", null, "#edcfa3", 2);
    }
    c.restore();
  }
  world(c, g) {
    const w = g.world,
      left = this.camera.x - 200,
      right = left + 1750;
    const rng = seeded(88);
    // River bed: layered wash and ink ripples; the bank is continuous terrain.
    for (const river of [
      { x: 1680, w: 310, y: 612 },
      { x: 2890, w: 400, y: 600 },
    ]) {
      if (river.x > right || river.x + river.w < left) continue;
      path(
        c,
        `M ${river.x} ${river.y} Q ${river.x + river.w * 0.5} ${river.y + 8} ${river.x + river.w} ${river.y} L ${river.x + river.w} 790 L ${river.x} 790 Z`,
        w.restored ? "#72a79b" : "#8c9e91",
        null,
      );
      for (let i = 0; i < 10; i++) {
        const x = river.x + ((i * 71 + g.time * 14) % river.w);
        path(
          c,
          `M ${x} ${river.y + 8 + (i % 3) * 14} l 35 0`,
          null,
          "#e6ead18a",
          1.3,
        );
      }
    }
    for (const p of w.platforms) {
      if (p.x > right || p.x + p.w < left) continue;
      if (p.h > 100) {
        path(
          c,
          `M ${p.x} ${p.y} Q ${p.x + p.w * 0.25} ${p.y - 7} ${p.x + p.w * 0.5} ${p.y + 2} Q ${p.x + p.w * 0.75} ${p.y - 5} ${p.x + p.w} ${p.y} L ${p.x + p.w} 900 L ${p.x} 900 Z`,
          p.x > 3200 && !w.restored ? "#827d76" : "#b1a381",
          "#4e5140",
          2,
        );
        path(
          c,
          `M ${p.x} ${p.y + 12} Q ${p.x + p.w * 0.5} ${p.y + 17} ${p.x + p.w} ${p.y + 10}`,
          null,
          w.restored ? "#74945b" : "#777f56",
          13,
        );
        for (let i = 0; i < p.w / 90; i++) {
          const x = p.x + i * 90,
            y = p.y + 30 + rng() * 40;
          path(
            c,
            `M ${x} ${y} q 30 -15 56 0 q -16 28 -44 20 Z`,
            "#aaa08550",
            "#6c6c4a22",
            1,
          );
        }
      } else {
        if (drawPaintedLedge(c, p)) continue;
        path(
          c,
          `M ${p.x} ${p.y} L ${p.x + p.w} ${p.y} L ${p.x + p.w - 18} ${p.y + 25} L ${p.x + 20} ${p.y + 36} Z`,
          "#b1a688",
          "#4d5240",
          2,
        );
        path(
          c,
          `M ${p.x + 10} ${p.y - 1} L ${p.x + p.w - 10} ${p.y - 1}`,
          null,
          "#819164",
          6,
        );
        path(
          c,
          `M ${p.x + 40} ${p.y + 32} L ${p.x + 58} ${Math.min(groundLevel(w, p.x), p.y + 210)} L ${p.x + 71} ${Math.min(groundLevel(w, p.x), p.y + 210)} L ${p.x + 68} ${p.y + 28} Z`,
          "#938767",
          "#63634a",
          1,
        );
        for (let i = 1; i < 4; i++)
          path(
            c,
            `M ${p.x + (i * p.w) / 4} ${p.y + 5} l -7 16`,
            null,
            "#767256",
            1,
          );
      }
    }
    // A small waterfall joins the river below the old stone terrace.
    if (left < 2860 && right > 2690) {
      c.save();
      c.globalAlpha = 0.56;
      path(
        c,
        "M 2805 390 Q 2795 470 2810 607 L 2840 607 Q 2826 478 2828 390 Z",
        w.restored ? "#b8e0ce" : "#b2c7bf",
        null,
      );
      for (let j = 0; j < 5; j++) {
        const yy = 400 + ((g.time * 95 + j * 43) % 200);
        path(
          c,
          `M ${2810 + (j % 2) * 8} ${yy} q -2 12 2 24`,
          null,
          "#edf0d0",
          2,
        );
      }
      c.restore();
    }
    // Small riverside hamlet and shrine structures.
    if (left < 720) {
      this.pagoda(c, 390, 575, 0.75);
      this.torii(c, 80, 575, 0.75);
      drawPaintedProp(c, 4, 580, 575, 180);
    }
    if (right > 5000) {
      this.torii(c, 5050, 580, 1.15);
      this.pagoda(c, 6370, 580, 0.95);
    }
    for (const tr of [
      { x: 615, y: 575, restored: true },
      { x: 1280, y: 575, restored: true },
    ])
      if (tr.x > left - 200 && tr.x < right + 200) {
        c.save();
        c.globalAlpha = 0.85;
        this.tree(c, tr, g.time);
        c.restore();
      }
    for (const tr of w.trees)
      if (tr.x > left - 200 && tr.x < right + 200)
        this.tree(c, tr, g.time, !w.restored);
    if (left < g.world.gate.x + 180 && right > w.gate.x - 180) {
      c.save();
      c.translate(w.gate.x, w.gate.y);
      path(
        c,
        "M -25 0 L -25 -210 L -7 -210 L -7 0 M 45 0 L 45 -210 L 62 -210 L 62 0",
        "#6b5c4d",
        INK,
        2,
      );
      path(
        c,
        "M -48 -210 Q 22 -195 85 -210 L 80 -194 L -42 -194 Z",
        "#a85443",
        INK,
        2,
      );
      if (!w.gate.open) {
        path(
          c,
          "M -5 -175 L 42 -175 L 42 0 L -5 0 Z",
          "#566063dd",
          "#403d42",
          2,
        );
        for (let i = 0; i < 3; i++)
          path(
            c,
            `M 6 ${-150 + i * 55} L 32 ${-125 + i * 55} M 30 ${-153 + i * 55} L 7 ${-122 + i * 55}`,
            null,
            "#c08970",
            2,
          );
      }
      c.restore();
    }
    c.save();
    c.translate(w.lantern.x, w.lantern.y);
    path(c, "M -8 0 L -8 -90 L -45 -90", null, "#656444", 3);
    path(
      c,
      "M -46 -85 L -24 -85 L -26 -57 L -44 -57 Z",
      w.lantern.lit ? "#e1b764" : "#b4c1aa",
      INK,
      1,
    );
    path(
      c,
      `M -35 -56 q ${Math.sin(g.time * 2) * 12} 13 -2 25`,
      null,
      "#c15346",
      2,
    );
    c.font = "12px Georgia";
    c.fillStyle = "#516658";
    c.fillText("Wind chime", -67, 18);
    c.restore();
    c.save();
    c.translate(w.basin.x, w.basin.y);
    path(c, "M -38 -10 L 37 -10 L 27 30 L -25 30 Z", "#a6a991", INK, 2);
    ellipse(c, 0, -10, 37, 10, w.basin.filled ? "#6facad" : "#727869", INK);
    if (!w.basin.filled) {
      path(c, "M 0 -48 q -12 16 0 23 q 12 -7 0 -23 Z", "#78a3a2", "#3c666a", 1);
    }
    c.restore();
    c.save();
    c.translate(w.water.x, w.water.y - 8);
    ellipse(c, 0, 0, 32, 8, "#add7c555");
    path(c, "M 0 -36 q -13 19 0 29 q 13 -10 0 -29 Z", "#80c0c0", "#3d6c6d", 1);
    c.restore();
    if (!w.wall.broken) drawPaintedProp(c, 14, w.wall.x, w.wall.y, 125);
    for (let x = 40; x < 6700; x += 280)
      if (x > left && x < right) {
        c.save();
        const cursed = x > 3290 && x < 5000 && !w.restored;
        if (cursed) c.filter = "grayscale(1) brightness(.65)";
        drawPaintedProp(c, 7, x, groundLevel(w, x) + 32, 130, 60);
        if (!cursed)
          drawPaintedProp(c, 12, x + 90, groundLevel(w, x) + 3, 125, 44);
        c.restore();
      }
    // Plants are seeded per location, and visibly recolour after restoration.
    const plantRng = seeded(7);
    for (let x = 90; x < 6600; x += 38) {
      const y = groundLevel(w, x),
        h = 8 + plantRng() * 21,
        v = plantRng();
      if (x < left || x > right) continue;
      const grey = x > 3290 && x < 5000 && !w.restored;
      path(
        c,
        `M ${x} ${y} q -10 ${-h} -15 ${-h + 3} M ${x} ${y} q 5 ${-h - 5} 9 ${-h + 1}`,
        null,
        grey ? "#5e5964" : "#687c4d",
        1.3,
      );
      if (v > 0.54 && !grey) {
        const fy = y - h;
        for (let k = 0; k < 5; k++)
          ellipse(
            c,
            x + Math.cos(k * 1.256) * 4,
            fy + Math.sin(k * 1.256) * 3,
            3,
            2,
            v > 0.8 ? "#d99187" : "#f0d49c",
          );
        ellipse(c, x, fy, 1.7, 1.7, "#a97945");
      }
    }
    if (w.restored) {
      for (let k = 0; k < 5; k++) {
        const x = 3450 + k * 230 + Math.sin(g.time + k) * 25,
          y = 465 + Math.sin(g.time * 1.2 + k * 2) * 30;
        if (x < left || x > right) continue;
        c.save();
        c.translate(x, y);
        const flap = Math.sin(g.time * 7 + k) * 4;
        ellipse(c, -5, -flap, 6, 4, "#e3b989");
        ellipse(c, 5, -flap, 6, 4, "#edd09d");
        path(c, "M 0 -3 L 0 5", null, "#6b6b50", 1);
        c.restore();
      }
      for (let k = 0; k < 2; k++) {
        let x = 3570 + k * 590 + Math.sin(g.time * 0.4 + k) * 24,
          y = groundLevel(w, x) - 6;
        ellipse(c, x, y, 12, 7, "#e5dfc9", INK);
        ellipse(c, x + 10, y - 7, 6, 6, "#ede6d2", INK);
        ellipse(c, x + 8, y - 17, 2, 9, "#e8e1cc", INK);
        ellipse(c, x + 13, y - 16, 2, 8, "#e8e1cc", INK);
        ellipse(c, x + 13, y - 8, 1, 1, "#303b33");
      }
    }
    if (w.restored && w.restoration < 1) {
      c.save();
      c.globalAlpha = (1 - w.restoration) * 0.26;
      ellipse(
        c,
        w.trees[1].x,
        480,
        80 + w.restoration * 2500,
        80 + w.restoration * 1200,
        "#fff5c8",
      );
      c.restore();
    }
  }
  torii(c, x, y, s) {
    if (drawPaintedProp(c, 2, x, y, 270 * s)) return;
    c.save();
    c.translate(x, y);
    c.scale(s, s);
    path(
      c,
      "M -83 0 L -75 -176 L -57 -176 L -61 0 M 62 0 L 57 -176 L 75 -176 L 84 0 Z",
      "#b55844",
      INK,
      2,
    );
    path(
      c,
      "M -110 -185 Q 0 -167 110 -185 L 104 -167 Q 0 -153 -104 -167 Z",
      "#a94737",
      INK,
      2,
    );
    path(c, "M -81 -143 L 81 -143 L 81 -134 L -81 -134 Z", "#bd684c", INK, 2);
    path(c, "M -56 -129 Q 0 -100 57 -129", null, "#bea979", 3);
    for (let i = -1; i <= 1; i++)
      path(c, `M ${i * 28} -118 l 0 15 l 8 6 l -8 5 l 7 6`, null, "#e7dbc0", 3);
    c.restore();
  }
  pickup(c, item, t) {
    c.save();
    c.translate(item.x, item.y + Math.sin(t * 2 + item.x) * 5);
    wash(c, 0, 0, 15, 10, "#e1ba67");
    if (item.kind === "treasure" && drawPaintedProp(c, 15, 0, 12, 45)) {
    } else if (item.kind === "treasure") {
      path(c, "M -17 -9 L 17 -9 L 17 11 L -17 11 Z", "#b8874d", INK, 1.5);
      path(c, "M -17 -9 Q 0 -21 17 -9 Z", "#d0a65b", INK, 1.5);
      path(c, "M -4 -13 L 4 -13 L 4 8 L -4 8 Z", "#e3c67b", INK, 1);
    } else {
      ellipse(c, 0, 0, 7, 7, "#e0b45a", "#82663e");
      path(c, "M -3 0 L 3 0 M 0 -3 L 0 3", null, "#fff1bf", 1);
    }
    c.restore();
  }
  enemy(c, e, g) {
    if (drawPaintedEnemy(c, e)) {
      if (!e.dead) {
        if (e.state === "tell") {
          c.fillStyle = "#d99a44";
          c.font = "bold 26px Georgia";
          c.fillText("!", e.x - 6, e.y - (e.type === "boss" ? 375 : 160));
          c.strokeStyle = "#d8a75a";
          c.lineWidth = 3;
          c.beginPath();
          c.ellipse(
            e.x,
            e.y + 2,
            e.type === "boss" ? 110 : 54,
            7,
            0,
            0,
            Math.PI * 2,
          );
          c.stroke();
        }
        if (e.type === "armour" || e.type === "boss") {
          let yy = e.y - (e.type === "boss" ? 145 : 85);
          c.fillStyle = e.exposed > 0 ? "#e8bb73" : "#9672a1";
          c.beginPath();
          c.arc(e.x, yy, 10, 0, Math.PI * 2);
          c.fill();
          c.strokeStyle = "#f8dfae";
          c.lineWidth = 2;
          c.beginPath();
          c.moveTo(e.x - 6, yy);
          c.lineTo(e.x + 6, yy);
          c.stroke();
        }
        if (e.hp < e.maxHp && e.type !== "boss") {
          c.fillStyle = "#76695c55";
          c.fillRect(e.x - 25, e.y - 175, 50, 3);
          c.fillStyle = "#af5149";
          c.fillRect(e.x - 25, e.y - 175, (50 * e.hp) / e.maxHp, 3);
        }
      }
      return;
    }
    if (e.dead && e.death > 1) return;
    c.save();
    c.translate(e.x, e.y);
    if (e.dead) {
      c.globalAlpha = 1 - e.death;
      c.translate(0, -e.death * 50);
      c.scale(1 - e.death * 0.5, 1 - e.death * 0.5);
    }
    c.scale(e.facing, 1);
    const bob = Math.sin(e.age * 6) * 2,
      wind = e.state === "tell",
      att = e.state === "attack";
    if (e.hurt > 0) c.globalAlpha = 0.55;
    if (e.type === "boss") {
      const pulse = Math.sin(e.age * 2) * 3;
      c.translate(0, pulse);
      wash(c, 0, -100, 115, 95, "#605071");
      path(
        c,
        "M -87 0 Q -105 -60 -72 -94 L -90 -111 L -65 -101 Q -66 -160 -23 -173 Q 28 -186 61 -143 L 93 -161 L 75 -132 Q 112 -100 97 -45 L 70 -12 L 76 0 L 32 0 L 24 -41 L -29 -47 L -43 0 Z",
        e.exposed > 0 ? "#665b71" : "#403f4b",
        INK,
        3,
      );
      path(
        c,
        "M -23 -153 L -46 -193 L -75 -211 L -60 -216 L -82 -248 L -49 -228 L -52 -249 L -27 -216 L -11 -180 M 29 -159 L 57 -205 L 92 -224 L 75 -228 L 99 -255 L 65 -238 L 63 -254 L 47 -222 L 20 -181",
        "#9c9374",
        INK,
        2.5,
      );
      path(
        c,
        "M -37 -138 Q 0 -163 43 -137 L 27 -96 L 3 -78 L -23 -100 Z",
        "#dfd2b1",
        INK,
        3,
      );
      path(
        c,
        "M -27 -125 L -8 -117 L -19 -111 Z M 29 -126 L 11 -117 L 19 -111 Z",
        wind ? "#f3bd54" : "#b64542",
        INK,
        1,
      );
      path(
        c,
        "M -9 -99 L 0 -93 L 10 -101 M 0 -139 L 0 -119",
        null,
        "#9c3a43",
        3,
      );
      ellipse(c, 0, -154, 19, 19, e.exposed > 0 ? "#ddac5e" : "#925b7b", INK);
      path(c, "M -10 -154 L 10 -154 M -7 -161 L 7 -147", null, "#f2dbad", 2);
      if (wind) {
        path(c, "M -95 9 Q 0 -7 100 9", null, "#d6914a", 5);
        ellipse(c, 0, -150, 5, 5, "#ffdc81");
      }
      if (e.phase === 2) {
        path(
          c,
          "M -59 -103 q -25 -42 -13 -74 q 23 31 36 30 M 48 -113 q 21 -35 18 -66 q -30 26 -34 26",
          null,
          "#b96450",
          6,
        );
      }
    } else if (e.type === "moth") {
      c.translate(0, -12);
      const flap = Math.sin(e.age * 9) * 15;
      path(
        c,
        `M -4 0 Q -65 ${-45 - flap} -55 -8 Q -63 21 -5 13 M 5 0 Q 65 ${-45 - flap} 55 -8 Q 65 21 5 13`,
        "#977b8c",
        INK,
        2,
      );
      path(c, "M -8 -13 Q 0 -30 10 -11 L 6 25 L -5 25 Z", "#d7ceb1", INK, 2);
      path(
        c,
        "M -5 -5 L 5 -5 M -35 -5 L -18 6 M 18 6 L 35 -5",
        null,
        wind ? "#ffd476" : "#ad4c4d",
        3,
      );
    } else {
      const brute = e.type === "brute",
        arm = e.type === "armour",
        scale = brute ? 1.5 : 1;
      c.scale(scale, scale);
      c.translate(0, bob);
      const swing = att ? 25 : wind ? -20 : Math.sin(e.age * 4) * 5;
      path(
        c,
        `M -20 -8 L -26 0 L -7 0 L -3 -16 L 12 -15 L 15 0 L 31 0 L 26 -15 L 21 -40 Q 23 -70 0 -72 Q -30 -64 -26 -31 Z`,
        arm ? "#6b7974" : "#707166",
        INK,
        2,
      );
      path(
        c,
        "M -22 -49 L -35 -55 L -23 -70 L -27 -85 L -7 -73 L 11 -74 L 28 -87 L 24 -68 L 36 -58 L 24 -48 L 18 -29 L -12 -26 Z",
        "#e1d3ac",
        INK,
        2,
      );
      path(
        c,
        "M -17 -58 L -4 -53 L -14 -49 Z M 9 -54 L 23 -59 L 18 -49 Z",
        wind ? "#ffd275" : "#b24d48",
        INK,
        1,
      );
      path(c, "M -8 -39 L 2 -34 L 13 -41 M 0 -69 L 0 -54", null, "#b24743", 2);
      if (e.type === "archer") {
        path(
          c,
          "M -44 -62 Q 0 -103 43 -63 Q 0 -55 -44 -62 Z",
          "#bfa474",
          INK,
          2,
        );
        path(
          c,
          "M 31 -46 Q 59 -25 33 -8 M 34 -43 L 35 -12",
          null,
          "#a28352",
          3,
        );
      } else {
        c.save();
        c.translate(24, -35);
        c.rotate(swing * 0.035);
        path(
          c,
          brute
            ? "M -8 0 L -10 -62 L 14 -62 L 13 -8 L 5 7 Z"
            : "M -3 0 L -4 -38 L 6 -45 L 9 -34 L 4 3 Z",
          brute ? "#797363" : "#b38e60",
          INK,
          2,
        );
        c.restore();
      }
      if (arm) {
        path(
          c,
          "M -31 -41 L -8 -47 L 11 -38 L 7 -12 L -13 -5 L -34 -20 Z",
          "#96968a",
          INK,
          2,
        );
        ellipse(c, -14, -28, 8, 8, e.exposed > 0 ? "#dac17b" : "#926f87", INK);
        path(c, "M -20 -28 L -8 -28", null, "#efe2b5", 1.5);
      }
    }
    if (wind) {
      c.fillStyle = "#d29544";
      c.font = "bold 24px Georgia";
      c.fillText("!", -6, e.type === "boss" ? -275 : -105);
    }
    c.restore();
    if (!e.dead && e.hp < e.maxHp && e.type !== "boss") {
      c.fillStyle = "#76695c55";
      c.fillRect(e.x - 25, e.y - 100, 50, 3);
      c.fillStyle = "#af5149";
      c.fillRect(e.x - 25, e.y - 100, (50 * e.hp) / e.maxHp, 3);
    }
  }
  weapon(c, p, t) {
    if (!p.attack) return;
    const a = p.attack,
      q = clamp(a.t / a.duration, 0, 1),
      pulse = Math.sin(q * Math.PI),
      dir = p.facing;
    c.save();
    c.translate(p.x, p.y - 115);
    c.scale(dir, 1);
    c.globalAlpha = clamp(pulse * 1.6, 0, 1);
    let angle = (-1.6 + q * 3.8) * (a.combo === 2 ? -1 : 1);
    if (a.kind === "heavy") angle = -2 + q * 4.8;
    if (a.kind === "air") angle = q * 6.28;
    c.rotate(angle);
    const radius = a.weapon === 1 ? 150 : a.kind === "heavy" ? 120 : 90;
    c.strokeStyle = a.kind === "heavy" ? "#ce6f48" : "#eee9d6";
    c.lineWidth = a.kind === "heavy" ? 18 : 12;
    c.beginPath();
    c.arc(0, 0, radius, -0.8, 0.35);
    c.stroke();
    c.strokeStyle = "#b3433988";
    c.lineWidth = 2;
    c.beginPath();
    c.arc(0, 0, radius + 12, -1.0, 0.45);
    c.stroke();
    if (a.weapon === 1) {
      for (let i = 0; i < 9; i++) {
        const x = i * 23,
          y = Math.sin(i * 0.5 + t * 12) * 15;
        ellipse(c, x, y, 6, 6, i % 2 ? "#c4654a" : "#416f63", INK);
      }
    } else if (a.weapon === 2) {
      path(c, "M 10 -6 L 151 -16 L 182 0 L 147 8 L 10 6 Z", "#f2e3ba", INK, 2);
      path(c, "M 50 -4 L 143 -8 L 169 0", null, "#b54238", 3);
    } else {
      ellipse(c, 95, 0, 19, 19, "#b9a368", INK);
      ellipse(c, 95, 0, 13, 13, "#4b7d70", INK);
    }
    c.restore();
  }
  particles(c, g) {
    for (const p of g.particles) {
      c.save();
      c.globalAlpha = clamp(p.life, 0, 1);
      c.translate(p.x, p.y);
      c.rotate(p.angle);
      const colors = {
        petal: "#e5b0a1",
        leaf: "#7f9e63",
        bloom: "#eac1a4",
        hit: "#d28a4e",
        hurt: "#ad4a43",
        dust: "#b7a788",
        gold: "#ddb459",
        water: "#77b8b8",
        shield: "#abaeae",
        wind: "#f4ebd4",
        spirit: "#9ec4ab",
        shock: "#e6c18b",
      };
      const col = colors[p.kind] || "#edddae";
      if (p.kind === "hit" || p.kind === "shock") {
        path(c, `M ${-p.size * 3} 0 L ${p.size * 3} 0`, null, col, 2);
      } else if (
        p.kind === "petal" ||
        p.kind === "bloom" ||
        p.kind === "leaf"
      ) {
        path(
          c,
          `M ${-p.size} 0 Q 0 ${-p.size} ${p.size} 0 Q 0 ${p.size} ${-p.size} 0 Z`,
          col,
          null,
        );
      } else ellipse(c, 0, 0, p.size * 0.5, p.size * 0.5, col);
      c.restore();
    }
  }
  foreground(c, g) {
    const left = this.camera.x - 100,
      right = left + 1550;
    for (let x = 0; x < 6700; x += 300) {
      if (x < left || x > right) continue;
      const y = groundLevel(g.world, x) + 125;
      for (let i = 0; i < 5; i++)
        path(
          c,
          `M ${x + i * 14} ${y} Q ${x + i * 9} ${y - 55} ${x + i * 17 - 25} ${y - 95 - i * 5}`,
          null,
          "#46604755",
          3,
        );
    }
  }
  brush(c, g) {
    c.save();
    c.fillStyle = "#f0e6d2aa";
    c.fillRect(0, 0, 1280, 720);
    c.strokeStyle = "#514c3a";
    c.lineWidth = 2;
    c.strokeRect(18, 18, 1244, 684);
    const draw = (points, color, alpha = 1) => {
      if (points.length < 2) return;
      c.globalAlpha = alpha;
      c.strokeStyle = color;
      c.lineCap = "round";
      c.lineJoin = "round";
      c.lineWidth = 5;
      c.beginPath();
      points.forEach((p, i) => (i ? c.lineTo(p.x, p.y) : c.moveTo(p.x, p.y)));
      c.stroke();
      c.lineWidth = 1.5;
      c.strokeStyle = "#6b6158";
      c.stroke();
    };
    for (const h of g.brush.history)
      draw(h.points, h.success ? "#9b4936" : "#423b37", clamp(2 - h.age, 0, 1));
    draw(g.brush.points, "#282e2b");
    c.globalAlpha = 1;
    const p = g.input.pointer;
    ellipse(c, p.x, p.y, 6, 6, "#2e3937");
    path(
      c,
      `M ${p.x + 3} ${p.y - 3} L ${p.x + 24} ${p.y - 31}`,
      null,
      "#654f39",
      6,
    );
    c.restore();
  }
}
function groundLevel(w, x) {
  return (
    w.platforms.find((p) => p.h > 100 && x >= p.x && x < p.x + p.w)?.y || 620
  );
}
