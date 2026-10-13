import * as THREE from "three";
// A local hand-drawn atlas overlays the source UV layout with ivory washes and brush marks.
// The artist source palette supplies the tiny eye/nose masks; its original orange is replaced.
export function wolfPaint(source, geometry) {
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
  // Project curved, tapered calligraphy onto the mesh's own UV triangles.
  // This keeps markings on the flank instead of arbitrary straight atlas bands.
  const mesh = new THREE.Mesh(
    geometry,
    new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }),
  );
  mesh.updateMatrixWorld(true);
  const ray = new THREE.Raycaster();
  function paintedCurve(points, width = 9) {
    const curve = new THREE.CatmullRomCurve3(
      points.map((p) => new THREE.Vector3(...p)),
    );
    for (const side of [-1, 1]) {
      let previous = null;
      for (let i = 0; i <= 180; i++) {
        const t = i / 180,
          p = curve.getPoint(t);
        ray.set(
          new THREE.Vector3(side * 100, p.y, p.z),
          new THREE.Vector3(-side, 0, 0),
        );
        const hit = ray.intersectObject(mesh, false)[0];
        if (!hit?.uv) {
          previous = null;
          continue;
        }
        const uv = new THREE.Vector2(
          hit.uv.x * 1024,
          (source.flipY ? 1 - hit.uv.y : hit.uv.y) * 1024,
        );
        if (previous && uv.distanceTo(previous) < 80) {
          ctx.strokeStyle = "#b92f2b";
          ctx.lineCap = "round";
          ctx.lineWidth =
            width * (0.12 + 0.88 * Math.pow(Math.sin(Math.PI * t), 0.65));
          ctx.beginPath();
          ctx.moveTo(previous.x, previous.y);
          ctx.lineTo(uv.x, uv.y);
          ctx.stroke();
        }
        previous = uv;
      }
    }
  }
  // Long sweeping shoulder/flank strokes and fine trailing flame branches.
  paintedCurve(
    [
      [0, 59, 22],
      [0, 56, 14],
      [0, 51, 1],
      [0, 48, -12],
      [0, 45, -24],
    ],
    12,
  );
  paintedCurve(
    [
      [0, 53, 23],
      [0, 48, 15],
      [0, 43, 1],
      [0, 44, -15],
      [0, 49, -28],
    ],
    7,
  );
  paintedCurve(
    [
      [0, 55, 17],
      [0, 59, 6],
      [0, 56, -8],
      [0, 52, -21],
    ],
    5,
  );
  paintedCurve(
    [
      [0, 44, 14],
      [0, 40, 3],
      [0, 41, -10],
    ],
    4,
  );
  // Open spirals flow into the other strokes; no solid rings around the limbs.
  for (const [cy, cz, r] of [
    [49, -17, 6],
    [52, 15, 4],
  ]) {
    const pts = [];
    for (let i = 0; i < 26; i++) {
      const t = i / 25,
        a = t * Math.PI * 3.9,
        rr = r * (1 - t);
      pts.push([0, cy + Math.sin(a) * rr, cz + Math.cos(a) * rr]);
    }
    paintedCurve(pts, 6);
  }
  for (const z of [21, -31]) {
    paintedCurve(
      [
        [0, 31, z - 2],
        [0, 25, z + 2],
        [0, 20, z + 1],
        [0, 17, z - 3],
      ],
      6,
    );
    paintedCurve(
      [
        [0, 27, z],
        [0, 24, z - 3],
        [0, 22, z],
        [0, 24, z + 2],
      ],
      4,
    );
  }
  paintedCurve(
    [
      [0, 58, 61],
      [0, 64, 54],
      [0, 66, 44],
    ],
    6,
  );
  mesh.material.dispose();
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
