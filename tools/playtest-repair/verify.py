"""Offline checks of the actual repair candidate, never a Unity compile claim."""
from pathlib import Path
import collections,hashlib,json,re,struct,subprocess,sys,wave,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';OUT=A/'OkamiRemaster/Original';RES=OUT/'Resources/Okami';BASE='72336e1aa558d1344c1b52b93bac882b3dd31eb4'
sys.path.insert(0,str(ROOT/'tools/original-remake'))
spec=importlib.util.spec_from_file_location('previous_native_verifier',ROOT/'tools/original-remake/verify.py');previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref
from native import Scene
from PIL import Image

def original(path):return subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT)
def run():
    report={};w=World();s=w.scene;before=Scene(s.path,text=original(s.path).decode());plan=json.loads(Path(__file__).with_name('scene-repairs.json').read_text())
    # Preserve unaffected collision and all save-format/source interfaces.
    disabled=set(plan['retiredSolidRoomColliders']);unchanged=0
    for id,b in before.blocks.items():
        if before.kind(id) not in [64,65,135,136,143,154]:continue
        if id in disabled:
            assert s.blocks[id]==b.replace('  m_Enabled: 1\n','  m_Enabled: 0\n'),id
        else:assert s.blocks[id]==b,('Unexpected collider edit',id);unchanged+=1
    for p in [A/'Sunward/Scripts/SaveStore.cs',A/'Sunward/Scripts/VillageResident.cs',ROOT/'Sunward-Unity/ProjectSettings/EditorBuildSettings.asset',ROOT/'Sunward-Unity/Packages/manifest.json']:
        assert p.read_bytes()==original(p),('Unrelated source changed',p)
    current=json.loads((A/'Sunward/Data/Valley.json').read_text());old=json.loads(original(A/'Sunward/Data/Valley.json'));assert current['world']['terrain']==old['world']['terrain'];assert current['world']['bounds']==old['world']['bounds']
    boxes=collections.Counter()
    for i,(a,b) in enumerate(zip(old['world']['boxes'],current['world']['boxes'])):
        if a!=b:assert {k for k in a if a[k]!=b[k]}<={'x','z'};boxes['moved']+=1
    assert boxes['moved']==4
    report.update(unchangedExistingColliderBlocks=unchanged,retiredSolidRoomColliders=len(disabled),newStaticColliderBlocks=sum(s.kind(i) in [64,65] and i not in before.blocks for i in s.blocks),terrainBoundsSavingNPCNavigationAndBuildScenePreserved=True,houseNavigationBoxesMoved=boxes['moved'])
    for p in (A/'Sunward/Generated').glob('Spirit-*.asset'):assert p.read_bytes()==original(p)
    for p in [A/'Sunward/Generated/spear.asset',A/'Sunward/Generated/sundial.asset']:assert p.read_bytes()==original(p)
    # New rendering references must resolve to real original-derived payloads.
    guids={};duplicates=[]
    for meta in A.rglob('*.meta'):
        m=re.search(r'^guid: (\w+)',meta.read_text(),re.M)
        if not m:continue
        if m[1] in guids and str(meta).startswith(str(OUT)):duplicates.append(str(meta))
        guids[m[1]]=meta.with_suffix('')
    assert not duplicates,duplicates
    external=set(re.findall(r'guid: ([0-9a-f]{32})',original(s.path).decode()))-guids.keys()
    for path in [s.path,*OUT.rglob('*.mat'),*(A/'Sunward/Generated').glob('NPC-*.prefab'),*(A/'Sunward/Generated').glob('Enemy-*.prefab')]:
        for g in re.findall(r'guid: ([0-9a-f]{32})',path.read_text()):assert g.startswith('0000000000000000') or g in guids or g in external,('Unresolved GUID',path,g)
    for p in OUT.rglob('*.meta'):assert p.with_suffix('').exists(),('Orphan metadata',p)
    for r in w.renderers():
        if r['kind']!=23:continue
        for g in r['materials']:assert str(w.assets.get(g,'')).startswith(str(OUT)),('Non-original visible saved artwork',r['name'],w.assets.get(g))
    model_count=0;bank_count=0
    for path in RES.rglob('Model.json'):
        d=json.loads(path.read_text());n=len(d['bones']);groups=d.get('visibleGroups');available=set(int(p['name'].split('-')[1]) for p in d['parts'])
        assert not groups or set(groups)<=available,(path,groups,available)
        for p in d['parts']:
            v=np.asarray(p['positions']).reshape(-1,3);ix=np.asarray(p['indices']);weights=np.asarray(p['weights']).reshape(-1,3);bones=np.asarray(p['boneIndices']).reshape(-1,3)
            assert np.isfinite(v).all() and (not len(ix) or 0<=ix.min()<=ix.max()<len(v));assert (abs(weights.sum(1)-1)<.01).all() and bones.min()>=-1 and bones.max()<n
            t=next(t for t in d['textures'] if t['index']==p['texture']);assert t.get('vertexOnly') or (path.parent/t['path']).exists()
        if (path.parent/'Poses.bytes').exists():assert previous.bank(path.parent/'Poses.bytes')[0]==n+1;bank_count+=1
        model_count+=1
    report.update(originalModelResourcesChecked=model_count,finitePoseBanksChecked=bank_count)
    expected={'em00':[0,3],'em01':[0,3],'em02':[0,3],'em03':[0,3],'em04':[0,3],'em11':[0,2],'hm29':[0,1],'vt6a':[0],'hm05':[1,2]}
    for name,mask in expected.items():assert json.loads((RES/name/'Model.json').read_text())['visibleGroups']==mask
    actors=[]
    for instance,source in [(0,s),*w.prefabs.items()]:
        for id,b in source.blocks.items():
            if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b:continue
            resource=re.search(r'  resource: (\S+)',b)[1];path=next(p for p in A.rglob('Resources') if (p/resource/'Poses.bytes').exists())/resource/'Poses.bytes';_,clips=previous.bank(path)
            for field in ['idle','walk','run','windup','strike','recover','death']:assert re.search(r'^  '+field+r': (\S+)',b,re.M)[1] in clips,(resource,field)
            actors.append(resource)
    report.update(savedNativeActorsChecked=len(actors),singleBodyAndWaterwheelMasksChecked=True)
    # Merchant feet are calibrated from the visible body, not the detached prop.
    sys.path.insert(0,str(Path(__file__).parent));from install_repairs import calibration
    for i in [1]:
        p=A/'Sunward/Generated'/('NPC-'+str(i)+'.prefab');scene=Scene(p);b=next(b for b in scene.blocks.values() if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' in b);idle=re.search(r'  idle: (\S+)',b)[1];scale,offset=calibration('hm29',idle,1.8)
        assert abs(float(re.search(r'  modelScale: (\S+)',b)[1])-scale)<1e-6
    # All fifteen native instruments and their own motion banks must be present.
    for i in range(0x20,0x2f):
        name='wp'+format(i,'02x');assert (RES/name/'Model.json').exists();_,clips=previous.bank(RES/name/'Poses.bytes');assert name+'_000' in clips and name+'_001' in clips
    player=A/'OkamiRemaster/Player/Resources/NativePlayer';_,clips=previous.bank(player/'pl00/Poses.bytes');bindings=json.loads((player/'Bindings.json').read_text())['bindings']
    for b in bindings:assert b['clip'] in clips and (not b.get('intro') or b['intro'] in clips),b
    for state in ['Swim_Idle','Swim_Move','Sit','Beads1','Beads2','Beads3','BeadsHeavy','BeadsAir']:assert any(b['state']==state for b in bindings)
    assert len(json.loads((RES/'pl0d/Model.json').read_text())['bones'])+1==previous.bank(player/'pl00/Poses.bytes')[0]
    report.update(nativeWeapons=15,playerMotionBindings=len(bindings),swimmingSeatedRosaryAndShiranuiResourcesResolve=True)
    paper=np.asarray(Image.open(RES/'UI/Paper.png').convert('RGB'),dtype=float)/255
    linear=np.where(paper<=.04045,paper/12.92,((paper+.055)/1.055)**2.4);lum=linear@np.array([.2126,.7152,.0722]);ink=np.array([.075,.055,.035]);ink=np.where(ink<=.04045,ink/12.92,((ink+.055)/1.055)**2.4);contrast=(lum+.05)/(ink@np.array([.2126,.7152,.0722])+.05)
    assert np.percentile(contrast,5)>7,np.percentile(contrast,[0,5,50]);report['paperInkContrast5thPercentile']=round(float(np.percentile(contrast,5)),2)
    audio=json.loads(Path(__file__).with_name('audio-provenance.json').read_text());bindings=json.loads((RES/'NativeAudio.json').read_text())['cues'];assert len(audio)==len(bindings)==42
    for r in audio:
        name=Path(r['resource']).name;file=next(p for p in (RES/'NativeAudio').glob(name+'.*') if p.suffix!='.meta');assert hashlib.sha256(file.read_bytes()).hexdigest()==r['outputSHA256']
        if file.suffix=='.wav':
            with wave.open(str(file)) as wav:raw=wav.readframes(wav.getnframes());assert wav.getnframes()>0 and np.max(abs(np.frombuffer(raw,'<i2').astype(np.int32)))>8,('Silent original cue',file)
        else:
            info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(file)]));assert float(info['format']['duration'])>1
    report['nonGeneratedOriginalAudioBindings']=len(audio)
    for p in OUT.rglob('*'):
        if p.is_file():
            with p.open('rb') as f:assert not f.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'),p
    for p in OUT.rglob('*.shader'):
        for include in re.findall(r'#include "([^"]+)"',p.read_text()):assert include.startswith('Packages/') or (p.parent/include).exists(),(p,include)
    sys.path.insert(0,'/workspace/work/csharp-syntax');import tree_sitter,tree_sitter_c_sharp
    parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_c_sharp.language()));files=list(A.rglob('*.cs'));errors=[str(p.relative_to(ROOT)) for p in files if parser.parse(p.read_bytes()).root_node.has_error];assert not errors,errors
    report.update(CSharpSyntaxFiles=len(files),CSharpSyntaxErrors=errors,UnityCompilationVerified=False,UnityPlaybackVerified=False,UnityShopPurchaseTestsExecuted=False,audioCueTimingAndMusicIdentityApproved=False,fullNativeESTSEQDispatchComplete=False,UIFontsOriginal=False)
    Path(__file__).with_name('verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':run()
