"""Offline preservation, dependency and original-data checks; NOT Unity tests."""
from pathlib import Path
import collections,hashlib,json,re,struct,subprocess,sys
import numpy as np
from export_assets import ROOT,A,OUT,RES,guid
sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref
sys.path.insert(0,str(ROOT/'tools/village'));from native import Scene
BASE='ee9af00b74c8157bfc93a150068b31e23d3c331f'
def source(path):return subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT)
def bank(path):
    raw=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',raw);assert magic==b'OPB1' and version==1;off=16;clips={}
    for _ in range(count):
        n=struct.unpack_from('<I',raw,off)[0];off+=4;name=raw[off:off+n].decode();off+=n;frames,duration,loop=struct.unpack_from('<IfI',raw,off);off+=12;data=np.frombuffer(raw,'<f4',frames*bones*10,off).reshape(frames,bones,10);off+=data.nbytes
        assert frames>=2 and duration>0 and np.isfinite(data).all();assert np.max(abs(np.linalg.norm(data[:,:,3:7],axis=2)-1))<1e-4;clips[name]=dict(frames=frames,duration=duration)
    assert off==len(raw);return bones,clips
def run():
    w=World();scene=w.scene;previous=Scene(scene.path,text=source(scene.path).decode());report={};problems=[]
    for i,b in previous.blocks.items():
        if previous.kind(i) in [64,65,135,136,143,154]:assert scene.blocks[i]==b,('Collider changed',i)
    for path in [A/'Sunward/Data/Valley.json',A/'Sunward/Scripts/SaveStore.cs',A/'Sunward/Scripts/ProgressionData.cs',A/'Sunward/Scripts/WolfMotor.cs',A/'Sunward/Scripts/VillageResident.cs',ROOT/'Sunward-Unity/ProjectSettings/EditorBuildSettings.asset',ROOT/'Sunward-Unity/Packages/manifest.json']:
        assert path.read_bytes()==source(path),('Gameplay/layout baseline changed',path)
    report['unchangedColliderBlocks']=sum(previous.kind(i) in [64,65,135,136,143,154] for i in previous.blocks)
    report['saveProgressionPlayerMotorNPCNavigationWorldDataAndBuildScenePreserved']=True
    for path in list((A/'Sunward/Generated').glob('Spirit-*.asset'))+[A/'Sunward/Generated/spear.asset',A/'Sunward/Generated/sundial.asset']:
        strip=lambda s:re.sub(r'^  title: .*\n','',s,flags=re.M)
        assert strip(path.read_text())==strip(source(path).decode()),('Mechanic definition changed',path)
    report['enemyAndWeaponMechanicsPreserved']=True
    guids={}
    for meta in A.rglob('*.meta'):
        m=re.search(r'^guid: (\w+)',meta.read_text(),re.M)
        if m:guids[m[1]]=meta.with_suffix('')
    baseline_external=set(re.findall(r'guid: ([0-9a-f]{32})',source(scene.path).decode()));external=set()
    for path in [scene.path,*OUT.rglob('*.mat'),*(A/'Sunward/Generated').glob('NPC-*.prefab'),*(A/'Sunward/Generated').glob('Enemy-*.prefab'),A/'Sunward/Generated/Spear.prefab']:
        for g in re.findall(r'guid: ([0-9a-f]{32})',path.read_text()):
            if not g.startswith('0000000000000000') and g not in guids:
                assert g in baseline_external,('New missing GUID',path,g);external.add(g)
    report['preservedExternalPackageGuidsNotLocallyImported']=sorted(external)
    visible=list(w.renderers());bad=[]
    for r in visible:
        if r['kind']!=23:continue
        for g in r['materials']:
            if not str(w.assets.get(g,'')).startswith(str(OUT)):bad.append(dict(name=r['name'],material=str(w.assets.get(g))))
    assert not bad,bad[:10]
    report['visibleSavedMeshRenderers']=sum(r['kind']==23 for r in visible);report['visibleLegacyArtBindings']=bad
    for i in scene.blocks:
        if scene.kind(i) in [96,120,199]:assert '  m_Enabled: 0\n' in scene.blocks[i]
    model_index=json.loads(Path(__file__).with_name('original-assets.json').read_text())['models'];models={e['package']:e for e in model_index};vertices=triangles=0
    for entry in model_index:
        path=RES/entry['package']/'Model.json'
        if path.exists():
            model=json.loads(path.read_text());nb=len(model['bones'])
            for p in model['parts']:
                pos=np.asarray(p['positions']).reshape(-1,3);ix=np.asarray(p['indices']);assert np.isfinite(pos).all() and (len(ix)==0 or ix.max()<len(pos));weights=np.asarray(p['weights']).reshape(-1,3);bones=np.asarray(p['boneIndices']).reshape(-1,3);assert (abs(weights.sum(1)-1)<.01).all() and bones.min()>=-1 and bones.max()<nb
                vertices+=len(pos);triangles+=len(ix)//3
                t=next(e for e in model['textures'] if e['index']==p['texture'])
                assert t.get('vertexOnly') or (RES/entry['package']/t['path']).is_file()
            if (RES/entry['package']/'Poses.bytes').exists():assert bank(RES/entry['package']/'Poses.bytes')[0]==nb+1
    report['convertedOriginalModels']=len(model_index);report['nativeVertexStreamsChecked']=vertices;report['nativeTrianglesChecked']=triangles
    install=json.loads(Path(__file__).with_name('world-install.json').read_text());report['nativeScenePlacements']=len(install['nativePlacements']);report['villageHouseRootsReused']=len(install['houses']);assert len(install['houses'])==14
    report['humanActors']=len(install['humanActors']);report['enemyRoles']=len(install['enemyVisuals']);assert report['humanActors']==13 and report['enemyRoles']==6
    for actor in install['humanActors']+install['enemyVisuals']+[install['secondWeapon'],install['waterwheel']]:
        _,clips=bank(RES/actor['package']/'Poses.bytes')
        for name in actor['bindings'].values():assert name in clips,(actor['package'],name)
    report['actorMotionBindingsResolve']=True
    # The three existing quest IDs/interaction points retain functioning visuals.
    report['originalQuestFlowerRenderers']=sum(scene.kind(i)==1 and scene.name(i).startswith('OriginalQuestFlower-') for i in scene.blocks);assert report['originalQuestFlowerRenderers']>=3
    assert 'else if (r.name.StartsWith("QuestFlower-" + id))\n                        r.enabled = false;' in (A/'Sunward/Scripts/GameFlow.cs').read_text()
    for p in OUT.rglob('*.meta'):assert p.with_suffix('').exists(),('Orphan metadata',p)
    # Native converted inputs remain ordinary payloads in the install, not LFS pointers.
    for p in OUT.rglob('*'):
        if p.is_file():assert not p.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'),('Unhydrated new original asset',p)
    for p in [OUT/'Shaders/OriginalPaint.shader']:
        for include in re.findall(r'#include "([^"]+)"',p.read_text()):assert (p.parent/include).exists(),('Missing shader include',include)
    report['UnityCompilationVerified']=False;report['UnityPlaybackVerified']=False;report['completeOriginalEffects']=False;report['missingAuthenticSoundBanks']=True;report['UIFontsOriginal']=False;report['scope']='Offline data/preservation/reference verification only. No Unity editor is installed here.'
    Path(__file__).with_name('verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':run()
