import * as THREE from "three";
// A local hand-drawn atlas overlays the source UV layout with ivory washes and brush marks.
// The artist source palette supplies the tiny eye/nose masks; its original orange is replaced.
export function wolfPaint(source) {
  const c = document.createElement("canvas");
  c.width = c.height = 1024;
  const ctx = c.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(source.image, 0, 0, 1024, 1024);
  const image = ctx.getImageData(0, 0, 1024, 1024);
  let seed = 4147;
  const rand = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  for (let i = 0; i < image.data.length; i += 4) {
    const r = image.data[i],
      g = image.data[i + 1],
      b = image.data[i + 2];
    if (r > 125 || r > g * 1.4) {
      const grain = (rand() - 0.5) * 10,
        shade = 5 * Math.sin((i / 4 / 1024) * 0.025);
      image.data[i] = Math.max(0, 248 + grain);
      image.data[i + 1] = Math.max(0, 241 + grain + shade);
      image.data[i + 2] = Math.max(0, 220 + grain + shade);
    } else {
      image.data[i] = 35;
      image.data[i + 1] = 32;
      image.data[i + 2] = 29;
    }
  }
  ctx.putImageData(image, 0, 0);
  function brush(points, width = 19) {
    ctx.strokeStyle = "#be322c";
    ctx.lineWidth = width;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(...points[0]);
    for (let i = 1; i < points.length; i++) ctx.lineTo(...points[i]);
    ctx.stroke();
    ctx.strokeStyle = "#aa2825";
    ctx.lineWidth = width * 0.18;
    ctx.stroke();
  }
  brush(
    [
      [455, 387],
      [437, 423],
      [440, 481],
      [388, 523],
      [359, 478],
    ],
    14,
  );
  brush(
    [
      [211, 708],
      [239, 752],
      [236, 807],
      [288, 849],
      [320, 795],
    ],
    14,
  );
  brush(
    [
      [556, 416],
      [531, 443],
      [559, 466],
      [584, 459],
    ],
    12,
  );
  brush(
    [
      [86, 726],
      [112, 753],
      [86, 775],
      [59, 767],
    ],
    12,
  );
  // Brush cuffs in each leg's UV island and a tail accent.
  for (const [x, y] of [
    [83, 156],
    [199, 160],
    [431, 153],
    [554, 155],
    [792, 468],
    [926, 465],
  ])
    brush(
      [
        [x - 20, y],
        [x, y + 10],
        [x + 25, y - 2],
      ],
      13,
    );
  brush(
    [
      [799, 667],
      [825, 700],
      [853, 707],
      [876, 682],
    ],
    14,
  );
  // Very light pigment blooms, generated with the same seed every load.
  ctx.globalCompositeOperation = "source-atop";
  for (let i = 0; i < 160; i++) {
    ctx.fillStyle = "rgba(151,116,72,.016)";
    ctx.beginPath();
    ctx.ellipse(
      rand() * 1024,
      rand() * 1024,
      25 + rand() * 50,
      8 + rand() * 20,
      rand() * Math.PI,
      0,
      Math.PI * 2,
    );
    ctx.fill();
  }
  const texture = new THREE.CanvasTexture(c);
  texture.flipY = source.flipY;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.magFilter = THREE.LinearFilter;
  return texture;
}
