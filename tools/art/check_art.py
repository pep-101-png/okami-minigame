"""Focused offline checks; does not substitute for Unity import/render validation."""
from pathlib import Path
import collections, re, struct, math
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'Sunward-Unity/Assets/Sunward'

def check():
    for p in (ASSETS/'Textures/SurfaceDetail').glob('*.png'):
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:
            assert im.size==(1024,1024), str(p)
        meta=p.with_suffix(p.suffix+'.meta').read_text()
        assert ('sRGBTexture: 0' if p.stem.endswith(('Normal','Mask')) else 'sRGBTexture: 1') in meta,str(p)
        if p.stem.endswith('Normal'):
            assert 'textureType: 1' in meta, str(p)
    for relative in ['EnvironmentReview/Mesh-1.asset','Renovation/Detail-73.asset']:
        s=(ASSETS/'Generated'/relative).read_text()
        n=int(re.search(r'm_VertexCount: (\d+)',s)[1])
        raw=bytes.fromhex(re.search(r'_typelessdata: (\w+)',s)[1])
        assert len(raw)==n*48
        rows=list(struct.iter_unpack('<12f',raw))
        assert all(math.isfinite(v) for row in rows for v in row)
        assert all(abs(sum(v*v for v in row[3:6])-1)<1e-5 for row in rows)
        idx=struct.unpack('<'+'H'*(len(bytes.fromhex(re.search(r'm_IndexBuffer: (\w+)',s)[1]))//2),bytes.fromhex(re.search(r'm_IndexBuffer: (\w+)',s)[1]))
        assert len(idx)==int(re.search(r'indexCount: (\d+)',s)[1]) and max(idx)<n
        edges=collections.Counter()
        for a,b,c in zip(idx[0::3],idx[1::3],idx[2::3]):
            assert len({a,b,c})==3
            for edge in [(a,b),(b,c),(c,a)]:edges[tuple(sorted(edge))]+=1
        assert all(count==2 for count in edges.values()),'Open/non-manifold cap'
        assert min(row[1] for row in rows)>=1.49999 and max(row[1] for row in rows)<=2.03001
        assert max(abs(row[0]) for row in rows)<=.51001 and max(abs(row[2]) for row in rows)<=.51001
        print(f'{relative}: {n} vertices, {len(idx)//3} closed triangles; valid normals and mounting bounds')
    guid=re.search(r'guid: (\w+)',(ASSETS/'Shaders/PaintedSky.shader.meta').read_text())[1]
    assert guid in (ASSETS/'Generated/PaintedSky.mat').read_text()
    sky_guid=re.search(r'guid: (\w+)',(ASSETS/'Generated/PaintedSky.mat.meta').read_text())[1]
    assert sky_guid in (ASSETS/'Scenes/Windflower.unity').read_text()
    # Source leaf textures remain mipmapped RGBA cutouts on the existing GUIDs.
    for name in ['map-1.png','map-3.png']:
        with Image.open(ASSETS/'Textures'/name) as im:
            assert im.mode=='RGBA' and im.getextrema()[3][0]==0
    print('PASS: texture files/colour spaces, cutout alpha, native mesh topology, and active sky binding.')
    print('NOT TESTED: Unity shader compilation, actual scene rendering, frame time, or movement.')
if __name__=='__main__':check()
