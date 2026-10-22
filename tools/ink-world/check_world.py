"""Check the saved Unity scene/assets and preservation boundaries, without Unity.

This does not certify Unity shader compilation, gameplay rendering or frame time.
"""
from pathlib import Path
import sys,re,json,struct,subprocess,collections,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
from native import ASSETS,Scene,vec,guid
from check_village import unresolved

OUT=ASSETS/'Generated/InkWorld'
BASE='ce07e12'


def mesh(path):
    s=path.read_text()
    count=int(re.search(r'm_VertexCount: (\d+)',s)[1])
    data=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',s)[1])
    stride=len(data)//count
    assert stride in (24,48), (path,stride)
    assert len(data)==count*stride==int(re.search(r'm_DataSize: (\d+)',s)[1])
    channels=re.findall(r'- stream: (\d+)\n      offset: (\d+)\n      format: (\d+)\n      dimension: (\d+)',s)
    assert len(channels)==14 and int(channels[0][3])==int(channels[1][3])==3
    assert int(channels[3][3])==(0 if stride==24 else 4)
    assert int(channels[4][3])==(0 if stride==24 else 2)
    v=np.array([struct.unpack_from('<3f',data,i*stride) for i in range(count)])
    normal=np.array([struct.unpack_from('<3f',data,i*stride+12) for i in range(count)])
    assert np.isfinite(v).all() and np.isfinite(normal).all(),path
    assert max(abs(np.linalg.norm(normal,axis=1)-1))<.001,path
    center=vec(s,'m_Center');extent=vec(s,'m_Extent')
    assert np.all(abs(v-center)<=extent+.001),('bounds',path)
    dtype='<u4' if 'm_IndexFormat: 1' in s else '<u2'
    ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',s)[1]),dtype=dtype)
    assert len(ix)==int(re.search(r'indexCount: (\d+)',s)[1]) and len(ix)%3==0
    assert min(ix)>=0 and max(ix)<count,path
    return len(ix)//3


def source(path):
    return subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True)


def normalize(text):return '\n'.join(s.rstrip() for s in text.splitlines())


def main():
    paths=list(OUT.glob('*.asset'));triangles=sum(mesh(p) for p in paths)
    scene=Scene(ASSETS/'Scenes/Windflower.unity')
    before=Scene(ASSETS/'Scenes/Windflower.unity',source(ASSETS/'Scenes/Windflower.unity'))
    assert set(before.blocks)<=set(scene.blocks),'Lost pre-existing scene objects'
    assert not(unresolved(scene)-unresolved(before)),'New dangling local scene references'
    physics=(54,64,65,136,143,153)
    old_physics=[i for i in before.blocks if before.kind(i) in physics]
    for i in before.blocks:
        # All existing physics and every gameplay script serialized field stays
        # exactly as before. New cosmetic wheel components are checked separately.
        if before.kind(i) in physics+(114,):
            assert normalize(before.blocks[i])==normalize(scene.blocks[i]),('Changed existing system',i)
    prefab=Scene(ASSETS/'Generated/TownV3.prefab')
    old_overrides=''.join(b for i,b in before.blocks.items() if before.kind(i)==1001)
    new_overrides=''.join(b for i,b in scene.blocks.items() if scene.kind(i)==1001)
    disabled=[]
    pattern=r'- target: \{fileID: (-?\d+),[^\n]+\}\n      propertyPath: m_IsActive\n      value: 0'
    for target in set(re.findall(pattern,new_overrides))-set(re.findall(pattern,old_overrides)):
        go=int(target);assert prefab.kind(go)==1
        assert all(prefab.kind(i) in (4,23,33) for i in prefab.refs(go)),('Hidden gameplay object',go)
        disabled.append(go)
    metas={}
    for path in (ROOT/'Sunward-Unity/Assets').rglob('*.meta'):
        g=re.search(r'guid: (\w+)',path.read_text())
        if g:metas[g[1]]=path
    known=set(re.findall(r'guid: ([0-9a-f]{32})',source(ASSETS/'Scenes/Windflower.unity')))
    for path in list(OUT.glob('*.mat'))+[ASSETS/'Scenes/Windflower.unity']:
        for g in re.findall(r'guid: ([0-9a-f]{32})',path.read_text()):
            assert g in metas or g in known or g.startswith('0000000000000000'),('Missing asset',path,g)
    # Check shell cost and culling margins against actual saved parent scales.
    outlines=[i for i in scene.blocks if scene.kind(i)==1 and scene.name(i).startswith('Ink contour · ')]
    assert 200<=len(outlines)<350,len(outlines)
    shells={guid(p):p for p in OUT.glob('Contour-*.asset')}
    def world_scale(context,t):
        if not t:return np.ones(3)
        b=context.blocks[t]
        if 'm_LocalScale:' not in b:
            target=int(re.search(r'm_CorrespondingSourceObject: \{fileID: (-?\d+)',b)[1])
            assert target in prefab.blocks,('Unknown stripped transform',t)
            # Current preserved TownV3 root has no transform-scale overrides.
            instance=int(re.search(r'm_PrefabInstance: \{fileID: (-?\d+)',b)[1])
            overrides=scene.blocks[instance]
            for record in re.finditer(r'- target: \{fileID: '+str(target)+r',[^\n]+\}\n      propertyPath: ([^\n]+)',overrides):
                assert 'm_LocalScale' not in record[1],('Unexpected prefab scale override',t)
            return world_scale(prefab,target)
        parent=int(re.search(r'm_Father: \{fileID: (-?\d+)\}',b)[1])
        return abs(vec(b,'m_LocalScale'))*world_scale(context,parent)
    for go in outlines:
        assert 'Home · ' not in scene.name(go),'Home interior inverted hull'
        r=scene.component(go,23);assert '  m_CastShadows: 0\n' in scene.blocks[r]
        assert '  m_ReceiveShadows: 0\n' in scene.blocks[r]
        for field in ['m_LightProbeUsage','m_ReflectionProbeUsage','m_MotionVectors']:
            assert '  '+field+': 0\n' in scene.blocks[r]
        scales=world_scale(scene,scene.transform(go))
        assert min(scales)*.40>=.055,('Shell bounds margin too small',go,scales)
        g=re.search(r'm_Mesh: .*guid: (\w+)',scene.blocks[scene.component(go,33)])[1]
        assert g in shells and len(bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',shells[g].read_text())[1]))%24==0
    wheel_go=next(i for i in scene.blocks if scene.kind(i)==1 and scene.name(i)=='Bucket wheel · X axle')
    wheel_t=scene.transform(wheel_go)
    parts=[i for i in scene.blocks if scene.kind(i)==1 and scene.name(i) in ['Ink world · millwheel wood','Ink world · millwheel iron']]
    assert len(parts)==2
    for part in parts:
        b=scene.blocks[scene.transform(part)]
        assert '  m_Father: {fileID: '+str(wheel_t)+'}' in b
        assert np.allclose(vec(b,'m_LocalScale'),(.76,.76,1))
    assert not any(scene.kind(i)==1 and scene.name(i).startswith('Ink world · millwheel bearing') for i in scene.blocks),'Duplicate standalone mill support'
    def beneath(t,parent):
        while t:
            if t==parent:return True
            m=re.search(r'm_Father: \{fileID: (-?\d+)\}',before.blocks[t]);t=int(m[1]) if m else 0
        return False
    original_wheel_renderers=[i for i in before.blocks if before.kind(i)==23 and before.owner(i) in before.blocks and beneath(before.transform(before.owner(i)),wheel_t)]
    assert original_wheel_renderers and all('  m_Enabled: 0\n' in scene.blocks[i] for i in original_wheel_renderers),'Old wheel duplicates new wheel'
    assert not any('Sunward.WaterwheelMotion' in b for b in scene.blocks.values()),'Unnecessary replacement mill-motion system'
    assert all(scene.kind(i)!=114 for i in set(scene.blocks)-set(before.blocks)),'New gameplay component'
    manifest=json.loads((ASSETS/'Textures/InkWorld/painting-manifest.json').read_text())
    for family,info in manifest.items():
        for suffix in ['','-normal']:
            path=ASSETS/'Textures/InkWorld'/(family+suffix+'.png')
            with Image.open(path) as im:
                assert im.size==(512,512) and im.mode=='RGB'
                if suffix:
                    n=np.asarray(im,dtype=float)/255*2-1
                    assert max(abs(np.linalg.norm(n,axis=-1).ravel()-1))<.02
            text=Path(str(path)+'.meta').read_text()
            assert ('sRGBTexture: 0' if suffix else 'sRGBTexture: 1') in text
            assert 'textureType: 0' in text
    # These are intentionally small ordinary-Git paintings, with a bounded
    # exception; large source assets and full wolf animation still require LFS.
    small=[]
    for folder in ['Art','VillageFinish','InkWorld']:
        for path in (ASSETS/'Textures'/folder).glob('*.png'):
            assert path.stat().st_size<2*1024*1024,path
            small.append(str(path.relative_to(ROOT)))
    attributes=subprocess.check_output(['git','check-attr','filter','--']+small,cwd=ROOT,text=True)
    assert all(line.endswith(': unset') for line in attributes.splitlines()),attributes
    lfs=subprocess.check_output(['git','check-attr','filter','--','Sunward-Unity/Assets/Sunward/Generated/Animations/Idle_Natural.anim'],cwd=ROOT,text=True)
    assert lfs.strip().endswith(': lfs')
    protected=['Sunward-Unity/Assets/Sunward/Generated/Animations','Sunward-Unity/Assets/Sunward/Models',
               'Sunward-Unity/Assets/Sunward/Generated/Amaterasu.prefab','tools/windows-sync',
               'tools/unity-automation','Sunward-Unity/Packages','Sunward-Unity/Assets/Sunward/Scripts/WolfMotor.cs',
               'Sunward-Unity/Assets/Sunward/Scripts/WolfAnimation.cs']
    assert not subprocess.check_output(['git','diff',BASE,'--name-only','--']+protected,cwd=ROOT,text=True).strip(),'Protected system modified'
    print(f'PASS: {len(paths)} ink-world meshes, {triangles:,} shared library triangles; {len(outlines)} bounded outline renderers.')
    print(f'PASS: {len(before.blocks):,} existing scene objects and {len(old_physics)} physics components retained; every original gameplay component unchanged.')
    print(f'PASS: {len(disabled)} superseded prefab visual nodes only, valid asset/reference/buffer/normal/bounds/import contracts.')
    print(f'PASS: {len(small)} small paintings have explicit ordinary-Git rules; full Idle_Natural remains LFS.')
    print('NOT VERIFIED: Unity import/shader compilation/rendering, PC synchronization, movement or GPU frame time.')

if __name__=='__main__':main()
