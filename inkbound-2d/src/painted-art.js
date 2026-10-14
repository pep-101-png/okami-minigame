// Local painted animation atlases. Logical combat/physics stay independent of art.
import { clamp } from "./math.js";
const atlases = {};
export async function loadPaintedArt(wolfOnly = false) {
  await Promise.all(
    (wolfOnly
      ? ["wolf-motion", "wolf-actions"]
      : [
          "wolf-motion",
          "wolf-actions",
          "spirits",
          "spirits-walk",
          "landscape",
          "props",
        ]
    ).map(async (name) => {
      const img = new Image();
      img.src = `/art/${name}.png`;
      try {
        await img.decode();
        atlases[name] = {
          image: img,
          w: img.naturalWidth / 4,
          h: img.naturalHeight / 4,
        };
        if (name !== "landscape") prepareFrames(atlases[name]);
      } catch {
        throw new Error("Painted artwork could not load. Reload the game.");
      }
    }),
  );
}
function cell(c, name, index, x, y, width, anchor = 0.985) {
  const a = atlases[name];
  if (!a) return false;
  const height = (width * a.h) / a.w;
  const f = a.frames?.[index];
  if (f) {
    const scale = width / a.w;
    const baseline =
      index === 15 && name === "wolf-actions" ? f.bottom : anchor * a.h;
    c.drawImage(
      f.canvas,
      x + (f.left - a.w / 2) * scale,
      y + (f.top - baseline) * scale,
      f.canvas.width * scale,
      f.canvas.height * scale,
    );
  } else
    c.drawImage(
      a.image,
      (index % 4) * a.w,
      Math.floor(index / 4) * a.h,
      a.w,
      a.h,
      x - width / 2,
      y - height * anchor,
      width,
      height,
    );
  return true;
}
export function drawPaintedWolf(c, p, time) {
  const motion = atlases["wolf-motion"];
  if (!motion) return false;
  let sheet = "wolf-motion",
    frame = 0;
  const speed = Math.abs(p.vx),
    a = p.attack;
  if (p.dead) {
    sheet = "wolf-actions";
    frame = 15;
  } else if (p.hurt > 0.75) {
    sheet = "wolf-actions";
    frame = 14;
  } else if (a) {
    sheet = "wolf-actions";
    let u = clamp(a.t / a.duration, 0, 0.999);
    if (a.kind === "heavy") frame = 8 + Math.floor(u * 4);
    else if (a.kind === "air") frame = 12 + (u > 0.38 ? 1 : 0);
    else if (a.combo === 1) frame = u < 0.35 ? 4 : 5;
    else if (a.combo === 2) frame = 6;
    else frame = u < 0.25 ? 4 : u < 0.8 ? 7 : 11;
  } else if (!p.grounded) frame = p.vy < -200 ? 12 : p.vy < 80 ? 13 : 14;
  else if (p.land > 0) frame = 15;
  else if (speed > 175) {
    frame = 4 + (Math.floor((p.stride / (Math.PI * 2)) * 8) % 8);
  } else if (speed > 25 && atlases["wolf-actions"]) {
    sheet = "wolf-actions";
    frame = Math.floor((p.stride / (Math.PI * 2)) * 8) % 4;
  } else frame = Math.floor(time * 3) % 4;
  c.save();
  c.translate(p.x, p.y);
  c.scale(p.facing, 1);
  let tilt = 0,
    bob = 0;
  if (a) {
    const u = clamp(a.t / a.duration, 0, 1);
    tilt =
      (a.kind === "heavy"
        ? -0.045
        : a.kind === "air"
          ? 0.12
          : a.combo === 2
            ? 0.05
            : -0.03) * Math.sin(u * Math.PI);
    bob = -Math.sin(u * Math.PI) * (a.combo === 3 ? 8 : 2);
  }
  if (p.dodge > 0) {
    c.globalAlpha *= 0.75;
    tilt = -0.08;
    bob = 4;
  }
  if (p.brush) {
    c.shadowColor = "#e6ab50";
    c.shadowBlur = 14;
  }
  c.translate(0, bob);
  c.rotate(tilt);
  if (!cell(c, sheet, frame, 0, 0, 240)) cell(c, "wolf-motion", 0, 0, 0, 240);
  c.restore();
  return true;
}
export function drawPaintedEnemy(c, e) {
  if (!atlases.spirits) return false;
  if (e.dead && e.death > 1) return true;
  let base = { imp: 0, armour: 0, brute: 0, moth: 4, archer: 8, boss: 12 }[
    e.type
  ];
  let stage =
    e.state === "tell"
      ? 1
      : e.state === "attack"
        ? 2
        : e.hurt > 0 || e.dead
          ? 3
          : 0;
  c.save();
  c.translate(e.x, e.y);
  c.scale(e.facing, 1);
  if (e.dead) {
    c.globalAlpha = 1 - e.death;
    c.translate(0, -e.death * 50);
  }
  if (e.hurt > 0) c.globalAlpha *= 0.55;
  const size =
    e.type === "boss"
      ? 390
      : e.type === "brute"
        ? 210
        : e.type === "moth"
          ? 165
          : 155;
  if (e.type === "armour") {
    c.shadowColor = e.exposed > 0 ? "#eabb73" : "#87879d";
    c.shadowBlur = e.exposed > 0 ? 12 : 4;
  }
  let sheet = "spirits",
    index = base + stage;
  if (
    !e.dead &&
    e.hurt <= 0 &&
    ((e.state === "patrol" && e.type !== "boss") ||
      (e.type === "boss" && e.state === "attack" && e.pattern === 0)) &&
    e.type !== "moth" &&
    atlases["spirits-walk"]
  ) {
    sheet = "spirits-walk";
    index =
      { imp: 0, armour: 0, archer: 4, brute: 8, boss: 12 }[e.type] +
      (Math.floor(e.age * (e.type === "boss" ? 9 : 6)) % 4);
  }
  if (e.type === "moth" && !e.dead && ["patrol", "recover"].includes(e.state))
    index = 4 + (Math.sin(e.age * 9) > 0 ? 1 : 0);
  const atlas = atlases[sheet],
    f = atlas.frames[index];
  cell(
    c,
    sheet,
    index,
    0,
    e.type === "moth" ? 55 : 0,
    size,
    e.type === "moth" ? 0.5 : f?.bottom / atlas.h || 0.96,
  );

  c.restore();
  return true;
}
export function artStatus() {
  return Object.fromEntries(
    Object.entries(atlases).map(([name, a]) => [
      name,
      {
        width: a.image.naturalWidth,
        height: a.image.naturalHeight,
        frames: name === "landscape" ? 1 : a.frames.length,
        missing: name === "landscape" ? 0 : a.frames.filter((f) => !f).length,
      },
    ]),
  );
}
export function drawPaintedBackdrop(c, camera, time, curse) {
  const a = atlases.landscape;
  if (!a) return false;
  c.save();
  if (curse) c.filter = "grayscale(.86) sepia(.18) brightness(.72)";
  const h = 766,
    w = (h * a.image.naturalWidth) / a.image.naturalHeight,
    shift = -(camera.x * 0.075) % w;
  for (let i = -1; i < 2; i++) c.drawImage(a.image, shift + i * w, -65, w, h);
  c.restore();
  const mist = c.createLinearGradient(0, 350, 0, 720);
  mist.addColorStop(0, "#f6ead800");
  mist.addColorStop(1, curse ? "#7b737577" : "#fff1c533");
  c.fillStyle = mist;
  c.fillRect(0, 0, 1280, 720);
  return true;
}

// Find opaque connected sprite silhouettes across nominal tile boundaries.
// This keeps full antlers/flames while excluding neighbouring actors and flecks.
function prepareFrames(atlas) {
  const W = atlas.image.naturalWidth,
    H = atlas.image.naturalHeight,
    canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(atlas.image, 0, 0);
  const pixels = ctx.getImageData(0, 0, W, H),
    labels = new Int32Array(W * H),
    queue = new Int32Array(W * H),
    components = [];
  let id = 0;
  for (let start = 0; start < labels.length; start++) {
    if (labels[start] || pixels.data[start * 4 + 3] < 90) continue;
    id++;
    let head = 0,
      tail = 1;
    queue[0] = start;
    labels[start] = id;
    let left = W,
      right = 0,
      top = H,
      bottom = 0;
    while (head < tail) {
      const p = queue[head++],
        x = p % W,
        y = Math.floor(p / W);
      left = Math.min(left, x);
      right = Math.max(right, x);
      top = Math.min(top, y);
      bottom = Math.max(bottom, y);
      for (const n of [
        x ? p - 1 : -1,
        x < W - 1 ? p + 1 : -1,
        y ? p - W : -1,
        y < H - 1 ? p + W : -1,
      ])
        if (n >= 0 && !labels[n] && pixels.data[n * 4 + 3] >= 90) {
          labels[n] = id;
          queue[tail++] = n;
        }
    }
    if (tail > atlas.w * atlas.h * 0.035)
      components.push({ id, left, right, top, bottom, area: tail });
  }
  const used = new Set();
  atlas.frames = [];
  for (let i = 0; i < 16; i++) {
    const x = ((i % 4) + 0.5) * atlas.w,
      y = (Math.floor(i / 4) + 0.58) * atlas.h;
    const choices = components
      .filter(
        (k) =>
          !used.has(k.id) &&
          Math.abs((k.left + k.right) / 2 - x) < atlas.w * 0.7 &&
          Math.abs((k.top + k.bottom) / 2 - y) < atlas.h * 0.75,
      )
      .sort(
        (a, b) =>
          Math.hypot((a.left + a.right) / 2 - x, (a.top + a.bottom) / 2 - y) -
          Math.hypot((b.left + b.right) / 2 - x, (b.top + b.bottom) / 2 - y),
      );
    const k = choices[0];
    if (!k) {
      atlas.frames.push(null);
      continue;
    }
    used.add(k.id);
    const out = document.createElement("canvas");
    out.width = k.right - k.left + 5;
    out.height = k.bottom - k.top + 5;
    const outctx = out.getContext("2d"),
      data = outctx.createImageData(out.width, out.height);
    for (let yy = 0; yy < out.height; yy++)
      for (let xx = 0; xx < out.width; xx++) {
        const px = k.left + xx - 2,
          py = k.top + yy - 2;
        if (px < 0 || py < 0 || px >= W || py >= H) continue;
        const source = py * W + px;
        let belongs = labels[source] === k.id;
        if (!belongs && pixels.data[source * 4 + 3] > 0) {
          for (const n of [source - 1, source + 1, source - W, source + W])
            if (labels[n] === k.id) belongs = true;
        }
        if (belongs) {
          const dest = (yy * out.width + xx) * 4;
          for (let channel = 0; channel < 4; channel++)
            data.data[dest + channel] = pixels.data[source * 4 + channel];
        }
      }
    outctx.putImageData(data, 0, 0);
    atlas.frames.push({
      canvas: out,
      left: k.left - 2 - (i % 4) * atlas.w,
      top: k.top - 2 - Math.floor(i / 4) * atlas.h,
      bottom: k.bottom - Math.floor(i / 4) * atlas.h,
    });
  }
}

export function drawPaintedProp(c, index, x, y, width, height = null) {
  const f = atlases.props?.frames[index];
  if (!f) return false;
  const h = height || (width * f.canvas.height) / f.canvas.width;
  c.drawImage(f.canvas, x - width / 2, y - h, width, h);
  return true;
}
export function drawPaintedLedge(c, p) {
  if (!atlases.props) return false;
  drawPaintedProp(c, 9, p.x + p.w / 2, p.y + 45, p.w, 45);
  const depth = Math.max(45, 610 - p.y);
  c.save();
  c.globalAlpha = 0.72;
  drawPaintedProp(c, 7, p.x + p.w * 0.45, p.y + depth, p.w * 0.52, depth - 16);
  c.restore();
  return true;
}
