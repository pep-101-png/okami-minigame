"""Validate the saved living-village integration without claiming Unity runtime tests.

Run after applying all authoring passes. Checks actual serialized references,
mesh streams, preserved bridge rails, animations and sync files against 7046ef0.
"""
from pathlib import Path
import json,re,struct,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'Sunward-Unity'
ASSETS=PROJECT/'Assets'
BASE='7046ef08b6c394d05a1536f6c4dac28b766214df'
sys.path.insert(0,str(ROOT/'tools/village'))
from native import Scene,vec
from check_village import unresolved


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def baseline(path):
    return git('show',BASE+':'+str(path.relative_to(ROOT))).decode()


def clean(text):
    return '\n'.join(line.rstrip() for line in text.splitlines())


def changed_files():
    tracked=git('diff','--name-only','-z',BASE).decode().split('\0')
    new=git('ls-files','--others','--exclude-standard','-z').decode().split('\0')
    return sorted({ROOT/p for p in tracked+new if p})


def mesh(path):
    text=path.read_text()
    match=re.search(r'm_VertexCount: (\d+)',text)
    if not match:return 0
    count=int(match[1]); assert count>0,(path,'empty mesh')
    raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',text)[1])
    size=int(re.search(r'm_DataSize: (\d+)',text)[1])
    assert len(raw)==size and len(raw)%count==0,(path,'vertex byte count')
    stride=len(raw)//count
    assert stride in (24,32,48,80),(path,'unknown vertex stride',stride)
    v=np.array([struct.unpack_from('<3f',raw,i*stride) for i in range(count)])
    normals=np.array([struct.unpack_from('<3f',raw,i*stride+12) for i in range(count)])
    assert np.isfinite(v).all() and np.isfinite(normals).all(),(path,'nonfinite vertices')
    assert np.max(abs(np.linalg.norm(normals,axis=1)-1))<.003,(path,'nonunit normals')
    assert np.all(abs(v-vec(text,'m_Center'))<=vec(text,'m_Extent')+.002),(path,'bounds')
    data=bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',text)[1])
    ix=np.frombuffer(data,dtype='<u4' if 'm_IndexFormat: 1' in text else '<u2')
    assert len(ix)>0 and len(ix)%3==0 and np.max(ix)<count,(path,'indices')
    assert len(ix)==int(re.search(r'indexCount: (\d+)',text)[1]),(path,'index count')
    if stride==80:
        weights=np.array([struct.unpack_from('<4f',raw,i*stride+48) for i in range(count)])
        assert np.isfinite(weights).all() and np.min(weights)>=0 and np.max(abs(weights.sum(axis=1)-1))<.001,(path,'skin weights')
        bones=np.array([struct.unpack_from('<4I',raw,i*stride+64) for i in range(count)])
        bind_count=len(re.findall(r'^  - e00:',text,re.M))
        assert bind_count and np.max(bones[weights>0])<bind_count,(path,'skin bone indices')
    return len(ix)//3


def critical_bindings(scene):
    expected = {
        'DayNightCycle': (1, ('game','sun')),
        'VillageRest': (2, ('game','cycle')),
        'VillageInterior': (2, ('player','valley')),
        'ResidentPerformance': (5, ('gait',)),
    }
    result = {}
    for name, (minimum, fields) in expected.items():
        scripts = [(i,b) for i,b in scene.blocks.items() if scene.kind(i)==114 and
                   'Sunward.'+name+'\n' in b and '  m_Enabled: 1\n' in b]
        assert len(scripts)>=minimum, ('Missing authored runtime system',name,len(scripts),minimum)
        for i,b in scripts:
            for field in fields:
                value = re.search(r'^  '+field+r': \{fileID: (-?\d+)\}',b,re.M)
                assert value and int(value[1]) in scene.blocks, ('Missing runtime binding',name,i,field)
        result[name]=len(scripts)
    return result


def main():
    scene_path=ASSETS/'Sunward/Scenes/Windflower.unity'
    scene=Scene(scene_path);before=Scene(scene_path,baseline(scene_path))
    assert not(unresolved(scene)-unresolved(before)),'New dangling local scene reference'
    metas={}
    for path in ASSETS.rglob('*.meta'):
        m=re.search(r'^guid: ([0-9a-f]{32})',path.read_text(),re.M)
        if m:
            assert m[1] not in metas,('Duplicate asset GUID',path,metas.get(m[1]))
            metas[m[1]]=path
    old_guids=set(re.findall(r'guid: ([0-9a-f]{32})',baseline(scene_path)))
    changed=changed_files(); mesh_count=triangles=0
    for path in changed:
        if not path.is_file() or ASSETS not in path.parents:continue
        if path.suffix!='.meta':assert Path(str(path)+'.meta').exists(),('Missing meta',path)
        if path.suffix in ('.asset','.mat','.prefab','.unity'):
            text=path.read_text()
            for g in re.findall(r'guid: ([0-9a-f]{32})',text):
                assert g in metas or g in old_guids or g.startswith('0000000000000000'),('Missing asset',path,g)
            if path.suffix=='.asset' and 'm_VertexCount:' in text:
                triangles+=mesh(path);mesh_count+=1
    # Retain exact red rails, gold medallions and their ink shells. Decks are separate.
    rails=[]
    for go in before.blocks:
        if before.kind(go)!=1 or 'Ink world · vermilion bridge at' not in before.name(go):continue
        rails.append(go)
        assert go in scene.blocks,('Removed red bridge rail',go)
        for block in [go]+before.refs(go):
            assert clean(scene.blocks[block])==clean(before.blocks[block]),('Changed red bridge rail',go,block)
    assert len(rails)==8,('Bridge preservation coverage',len(rails))
    for path in (ASSETS/'Sunward/Generated/InkWorld').glob('*Bridge*'):
        assert git('show',BASE+':'+str(path.relative_to(ROOT)))==path.read_bytes(),('Changed bridge rail asset',path)
    for path in changed:
        rel=str(path.relative_to(ROOT))
        assert not rel.startswith(('tools/windows-sync/','tools/git-sync/','tools/sunward-sync/','tools/sync/')),("Changed sync",rel)
        assert not (rel.startswith('Sunward-Unity/Assets/Sunward/Generated/Animations/') and path.suffix=='.anim'),('Changed existing clip',rel)
    runtime=critical_bindings(scene)
    report=dict(runtimeBindings=runtime,scope='Serialized assets and references only; not Unity API compilation, render or gameplay',
                sceneObjects=sum(scene.kind(i)==1 for i in scene.blocks),
                preservedBridgeParts=len(rails),checkedChangedMeshes=mesh_count,sharedLibraryTriangles=triangles,
                localReferences='passed',assetGuidReferences='passed',existingClips='preserved',syncing='untouched')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
