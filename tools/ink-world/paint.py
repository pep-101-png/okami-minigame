"""Original seamless brush paintings for Sunward's existing environment.

No downloaded artwork or runtime texture generation. Re-run with Python, numpy,
Pillow; every colour map is paired with linear RGB relief for Surface Pigment.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'Sunward-Unity/Assets/Sunward'
OUT = ASSETS / 'Textures/InkWorld'
N = 512
TAU = math.tau
Y, X = np.mgrid[:N, :N] / N
RNG = np.random.default_rng(22261022)


def field(seed, scales=(1, 2, 4, 8, 16), decay=.55):
    """Periodic, directionless pigment wash. All coordinates close at the seam."""
    rng = np.random.default_rng(seed)
    result = np.zeros((N, N))
    for octave, scale in enumerate(scales):
        for _ in range(5):
            kx, ky = rng.integers(-scale, scale + 1, 2)
            if kx == ky == 0:
                kx = scale
            result += np.sin(TAU * (X * kx + Y * ky) + rng.uniform(0, TAU)) * decay**octave
    return result / max(1e-5, np.std(result))


def base(rgb, seed, strength=7):
    f = field(seed)
    arr = np.clip(np.array(rgb)[None, None, :] + f[..., None] * strength, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGB')


def line(img, points, color, width=1):
    draw = ImageDraw.Draw(img)
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            draw.line([(round(x + ox), round(y + oy)) for x, y in points], fill=color, width=max(1, round(width)), joint='curve')


def polygon(img, points, color):
    draw = ImageDraw.Draw(img)
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            draw.polygon([(round(x + ox), round(y + oy)) for x, y in points], fill=color)


def brush(img, points, rgb, width, seed=0, dry=.25):
    """Uneven-edged stroke with narrow dry bristle gaps, never a perfect line."""
    rng = np.random.default_rng(seed)
    points = np.array(points, float)
    # Broad transparent wash sits below the narrower broken dry brush marks.
    layer = Image.new('RGBA', (N, N))
    line(layer, points, (*rgb, 115), width)
    img.paste(Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB'))
    strands = max(3, int(width / 2))
    for j in range(strands):
        if rng.random() < dry:
            continue
        offset = (j / max(1, strands - 1) - .5) * width
        strand = points.copy()
        strand[:, 0] += offset + rng.uniform(-.8, .8, len(points))
        strand[:, 1] += rng.uniform(-1.0, 1.0, len(points))
        short_start = int(rng.integers(0, max(1, len(points) // 6)))
        short_end = len(points) - int(rng.integers(0, max(1, len(points) // 6)))
        shade = tuple(int(np.clip(c + rng.uniform(-4, 4), 0, 255)) for c in rgb)
        line(img, strand[short_start:short_end], shade, max(1, width / strands * .65))


def plaster():
    img = base((224, 202, 154), 101, 6)
    for j in range(65):
        px, py = RNG.uniform(-40, N, 2)
        width, length = RNG.uniform(12, 48), RNG.uniform(20, 105)
        points = [(px + math.sin(t * .7 + j) * 3, py + length * t / 12) for t in range(13)]
        brush(img, points, (230, 210, 170) if j % 3 else (181, 155, 112), width, j, .5)
    # Hand-drawn fading cracks and exposed ochre brush edges, not a square tile.
    for j in range(16):
        x, y = RNG.uniform(0, N, 2)
        p = [(x, y)]
        for k in range(int(RNG.integers(3, 8))):
            x += RNG.uniform(-9, 9); y += RNG.uniform(4, 11); p.append((x, y))
        line(img, p, (159, 130, 85), 1)
        line(img, [(x + 1, y + 1) for x, y in p], (242, 222, 184), 1)
    return img, 'Warm plaster, dry ochre washes and narrow faded hairline cracks', .75


def timber():
    img = base((168, 117, 66), 202, 8)
    knots = [(.26, .29, .060, .13), (.73, .74, .04, .09)]
    # Rings flow around elliptical knots. The edge wraps through periodic displacement.
    for j in range(55):
        bx = j * N / 55
        pts = []
        for py in np.linspace(-20, N + 20, 105):
            yy = py / N
            xx = bx + 4 * math.sin(TAU * yy * 2 + j * .71) + 2 * math.sin(TAU * yy * 6 + j)
            for kx, ky, rx, ry in knots:
                dx = ((bx / N - kx + .5) % 1) - .5
                dy = ((yy - ky + .5) % 1) - .5
                xx += np.sign(dx) * 25 * math.exp(-(dx / .09)**2 - (dy / .18)**2)
            pts.append((xx, py))
        ink = (69, 46, 27) if j % 4 == 0 else (116, 73, 37)
        line(img, pts, ink, 2 if j % 4 == 0 else 1)
        if j % 3 == 0:
            line(img, [(x + 2.7, y) for x, y in pts], (199, 151, 91), 2)
    for cx, cy, rx, ry in knots:
        for ring in range(7):
            radius = .16 + ring * .14
            pts = []
            for a in np.linspace(0, TAU, 100):
                rr = radius * (1 + .05 * math.sin(a * 5 + ring))
                pts.append(((cx + math.cos(a) * rx * rr) * N, (cy + math.sin(a) * ry * rr) * N))
            line(img, pts, (71 + ring * 4, 43 + ring * 4, 22 + ring * 3), max(1, 3 - ring / 3))
    # Sparse ink rubbed scratches expose the paler wood under the surface.
    for j in range(35):
        x, y = RNG.uniform(0, N, 2)
        line(img, [(x, y), (x + RNG.uniform(-2, 2), y + RNG.uniform(7, 32))], (213, 163, 96), 1)
    return img, 'Japanese timber grain with flowing knots, dry brush fissures and exposed fibres', .6


def roof(indigo=False):
    img = base((104, 126, 131) if indigo else (190,116,61), 303, 5)
    # Eight columns by four tile courses; raised lips read from gameplay distance.
    for row in range(4):
        for col in range(8):
            x = col * 64 + (row % 2) * 32; y = row * 128
            t = RNG.uniform(-5, 5)
            polygon(img, [(x, y + 8), (x + 54, y + 3), (x + 62, y + 112), (x + 53, y + 125), (x + 4, y + 122)], tuple(int(c+t) for c in ((109,131,133) if indigo else (191,115,61))))
            # Glazed broad highlight broken into brush dashes, not a uniform gradient.
            for stripe in range(4):
                sx = x + 10 + stripe * 4
                line(img, [(sx, y + 16), (sx - 3, y + 61), (sx + 2, y + 100)], (148-stripe*6, 162-stripe*5, 155-stripe*4) if indigo else (232-stripe*7,163-stripe*7,92-stripe*5), 3)
            line(img, [(x + 57, y + 6), (x + 61, y + 58), (x + 62, y + 111), (x + 55, y + 123)], (35, 52, 57) if indigo else (67,40,25), 3)
            line(img, [(x + 2, y + 120), (x + 19, y + 124), (x + 40, y + 126), (x + 55, y + 121)], (25, 42, 48) if indigo else (49,31,23), 4)
            line(img, [(x + 7, y + 115), (x + 31, y + 119), (x + 51, y + 115)], (166, 176, 158) if indigo else (235,173,105), 2)
    return img, ('Indigo' if indigo else 'Burnt orange')+' glazed ceramic tiles, four staggered courses, expressive dark lips and chalky highlights', 1.2


def cliff():
    img = base((188, 158, 104), 404, 7)
    # Ochre sheer faces, long dipping strata and split mineral seams. Deliberately
    # avoid regular stone-block courses: these are natural cliffs, not masonry.
    for row in range(7):
        yy=row*N/7
        pts=[]
        for px in np.linspace(-30,N+30,75):
            u=px/N
            py=yy+8*math.sin(u*TAU*2+row*.7)+3*math.sin(u*TAU*5+row*1.1)
            pts.append((px,py))
        for j in range(6):
            offset=j*3
            line(img,[(x,y+offset) for x,y in pts],(165+j*2,126+j*3,77+j*2),2)
        line(img,[(x,y+18) for x,y in pts],(220,184,115),3)
        # Sparse discontinuous dark stroke, rather than a continuous black grid.
        for chunk in range(3):
            a=(row*13+chunk*21)%56
            line(img,pts[a:a+12],(103,91,62),2)
    for seam in range(15):
        x,y=RNG.uniform(0,N,2);length=RNG.uniform(60,180)
        pts=[(x,y)]
        for k in range(8):
            x+=RNG.uniform(-9,9);y+=length/8
            pts.append((x,y))
        line(img,[(px+3,py) for px,py in pts],(221,180,111),3)
        line(img,pts,(95,83,57),2)
        branch=pts[4]
        line(img,[branch,(branch[0]+17,branch[1]+10),(branch[0]+24,branch[1]+35)],(122,102,65),1)
    for j in range(85):
        px,py=RNG.uniform(0,N,2)
        # Long dry bristle traces read as weathered vertical planes.
        brush(img,[(px,py),(px+2,py+12),(px-3,py+RNG.uniform(20,52))],(204,170,108) if j%2 else (164,135,86),RNG.uniform(2,7),1700+j,.65)
    return img, 'Golden ochre sheer cliff planes, dipping mineral strata, split crevices and weathered bristles', .24


def path():
    img = base((197, 159, 94), 505, 7)
    for j in range(85):
        px, py = RNG.uniform(0, N, 2)
        brush(img, [(px, py), (px+12, py-8), (px+35, py-15)], (219, 185, 115) if j%3 else (160, 125, 71), RNG.uniform(5, 15), 900+j, .6)
    for j in range(44):
        x, y = RNG.uniform(0, N, 2); rx, ry = RNG.uniform(3, 10, 2)
        pts=[(x + math.cos(a)*rx, y+math.sin(a)*ry) for a in np.linspace(0, TAU, 7)]
        polygon(img, pts, (166, 145, 104));line(img, pts[1:4], (116, 102, 77), 1);line(img, pts[4:], (226, 199, 143), 1)
    return img, 'Golden ochre footpath with directional dry washes and small handpainted pebbles', .35


def meadow():
    img = base((130, 155, 79), 606, 7)
    for j in range(110):
        x,y=RNG.uniform(0,N,2)
        rgb=(169, 177, 91) if j%3 else (91, 123, 65)
        brush(img, [(x-8,y+8),(x+5,y),(x+25,y-12)],rgb,RNG.uniform(10,26),1200+j,.62)
    # Curved, broken tapered blades and soil flecks offer visible painterly strokes.
    for j in range(290):
        x,y=RNG.uniform(0,N,2);l=RNG.uniform(5,18)
        rgb=(62,103,57) if j%4 else (190,185,101)
        line(img,[(x,y),(x+1,y-l*.5),(x+RNG.uniform(1,5),y-l)],rgb,2)
    return img, 'Sage meadow wash with ochre patches, hooked grass strokes and deep green bristles', .4


ARTISTS = {'Plaster':plaster, 'Timber':timber, 'Roof':roof, 'RoofIndigo':lambda:roof(True), 'Cliff':cliff, 'Path':path, 'Meadow':meadow}


def write(name, image, description, tiling):
    # Wrapped marks close geometrically; glazed tile/slab washes also need a
    # short colour blend where the independently painted first/last slabs meet.
    arr=np.asarray(image).astype(float).copy()
    if name in ('Roof','RoofIndigo','Cliff'):
        for axis in (0,1):
            for k in range(12):
                alpha=.5*(1-k/12)**2
                if axis==0:
                    a,b=arr[k].copy(),arr[-1-k].copy()
                    arr[k]=a*(1-alpha)+b*alpha;arr[-1-k]=b*(1-alpha)+a*alpha
                else:
                    a,b=arr[:,k].copy(),arr[:,-1-k].copy()
                    arr[:,k]=a*(1-alpha)+b*alpha;arr[:,-1-k]=b*(1-alpha)+a*alpha
        image=Image.fromarray(np.uint8(np.clip(arr,0,255)),'RGB')
    rgb=np.asarray(image).astype(float)
    # Low-amplitude relief, derived from authored strokes rather than unrelated noise.
    gray = np.asarray(image.convert('L').filter(ImageFilter.GaussianBlur(.7))).astype(float)
    dx=(np.roll(gray,-1,1)-np.roll(gray,1,1))*.045
    dy=(np.roll(gray,-1,0)-np.roll(gray,1,0))*.045
    normal=np.stack([-dx,-dy,np.ones_like(dx)],-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    normal_image=Image.fromarray(np.uint8(np.clip(normal*.5+.5,0,1)*255),'RGB')
    guids={}
    for suffix,im in [('',image),('-normal',normal_image)]:
        p=OUT/(name+suffix+'.png');im.save(p,optimize=True)
        meta=(ASSETS/'Textures/VillageFinish/Bark.png.meta').read_text()
        g=hashlib.md5(str(p.relative_to(ROOT)).encode()).hexdigest()
        meta=re.sub(r'guid: \w+','guid: '+g,meta,count=1)
        if suffix:meta=meta.replace('sRGBTexture: 1','sRGBTexture: 0')
        meta=meta.replace('maxTextureSize: 2048','maxTextureSize: 512')
        Path(str(p)+'.meta').write_text(meta)
        guids['normal' if suffix else 'color']=g
    # Seam evidence: compare outer texels to nearest ordinary adjacent pixels.
    a=np.asarray(image).astype(float)
    edge=float(np.mean(np.abs(a[:,0]-a[:,-1]))+np.mean(np.abs(a[0]-a[-1]))) / 2
    inner=float(np.mean(np.abs(a[:,1:]-a[:,:-1]))+np.mean(np.abs(a[1:]-a[:-1]))) / 2
    return {'description':description,'size':[N,N],'worldTiling':tiling,'guids':guids,'edgeDifference':round(edge,2),'ordinaryDifference':round(inner,2),'averageAlbedoRGB':[round(float(v),3) for v in np.mean(a,axis=(0,1))/255],'storageBytes':sum((OUT/(name+suffix+'.png')).stat().st_size for suffix in ('','-normal'))}


def main():
    global RNG
    RNG=np.random.default_rng(22261022)
    OUT.mkdir(parents=True,exist_ok=True)
    foldermeta=Path(str(OUT)+'.meta')
    foldermeta.write_text('fileFormatVersion: 2\nguid: '+hashlib.md5(str(OUT.relative_to(ROOT)).encode()).hexdigest()+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
    manifest={}; tiles=[]
    for name,fn in ARTISTS.items():
        image,description,tiling=fn();manifest[name]=write(name,image,description,tiling);tiles.append((name,Image.open(OUT/(name+'.png')).convert('RGB')))
    manifest_path=OUT/'painting-manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    Path(str(manifest_path)+'.meta').write_text('fileFormatVersion: 2\nguid: '+hashlib.md5(str(manifest_path.relative_to(ROOT)).encode()).hexdigest()+'\nTextScriptImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
    # Side-by-side tile pairs make seams visible, with honest non-game labelling.
    preview=Image.new('RGB',(1260,1380),(239,227,201));d=ImageDraw.Draw(preview)
    d.text((20,12),'SUNWARD ORIGINAL BRUSH PAINTINGS - TEXTURE CONTACT SHEET, NOT UNITY RENDER',fill=(36,32,22))
    for j,(name,image) in enumerate(tiles):
        ox=20+(j%3)*415;oy=44+(j//3)*440
        d.text((ox,oy),name+' / original albedo + repeated tile pair',fill=(36,32,22))
        preview.paste(image.resize((390,300)),(ox,oy+24))
        small=image.resize((190,95));preview.paste(small,(ox,oy+329));preview.paste(small,(ox+190,oy+329))
    target=Path('/workspace/work/ink-world');target.mkdir(parents=True,exist_ok=True)
    preview.save(target/'paintings-contact.jpg',quality=92)
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
