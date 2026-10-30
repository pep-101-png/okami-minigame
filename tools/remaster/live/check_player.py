#!/usr/bin/env python3
"""Check the installed native data and protected gameplay. Does not run Unity."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'Sunward-Unity/Assets';RES=A/'OkamiRemaster/Player/Resources/NativePlayer'
sys.path.insert(0,str(ROOT/'tools/village'));from native import Scene
sys.path.insert(0,str(Path(__file__).parent));import export_player as export
def read_bank(path):
    d=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',d);assert magic==b'OPB1' and version==1;off=16;out={}
    for i in range(count):
        n=struct.unpack_from('<I',d,off)[0];off+=4;name=d[off:off+n].decode();off+=n
        frames,duration,loop=struct.unpack_from('<IfI',d,off);off+=12
        samples=np.frombuffer(d,'<f4',frames*bones*10,off).reshape(frames,bones,10);off+=samples.nbytes
        assert name not in out and np.isfinite(samples).all() and duration>0
        assert np.max(abs(np.linalg.norm(samples[:,:,3:7],axis=2)-1))<1e-5
        assert np.max(abs(samples[:,0,:3]))==0,'Native travel would double motor movement'
        out[name]=(samples,duration,bool(loop))
    assert off==len(d);return out
def matrices(model,pose):
    out=[];bind=np.zeros((len(pose),3))
    for i,record in enumerate(pose):
        p=record[:3];x,y,z,w=record[3:7];s=record[7:]
        m=np.eye(4);m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(s);m[:3,3]=p
        if i:
            parent=model['bones'][i-1]['parent']+1;m=out[parent]@m;bind[i]=bind[parent]+np.asarray(model['bones'][i-1]['position'])
        out.append(m)
    return np.asarray(out),bind
def skin(model,pose):
    mats,bind=matrices(model,pose);out=[]
    for part in model['parts']:
        v=np.asarray(part['positions']).reshape(-1,3);indices=np.asarray(part['boneIndices']).reshape(-1,3)+1;weights=np.asarray(part['weights']).reshape(-1,3);weights/=weights.sum(axis=1,keepdims=True);result=np.zeros_like(v)
        for j in range(3):result+=weights[:,j,None]*(np.einsum('nij,nj->ni',mats[indices[:,j],:3,:3],v-bind[indices[:,j]])+mats[indices[:,j],:3,3])
        out.append(result)
    return out
proof=json.loads(Path(__file__).with_name('player-install.json').read_text());manifest=json.loads(Path(__file__).with_name('player-export.json').read_text());banks={n:read_bank(RES/n/'Poses.bytes') for n in ['pl00','wp24','wp34']}
for record in manifest['motions']:
    samples,duration,loop=banks[record['model']][record['name']]
    assert hashlib.sha256(samples.tobytes()).hexdigest()==record['poseSHA256']
    assert samples.shape[0]==record['samples'] and abs(duration-record['duration'])<1e-5 and loop==record['loop']
bindings=json.loads((RES/'Bindings.json').read_text())['bindings'];names=set(b['state'] for b in bindings)
controller=(A/'Sunward/Generated/Amaterasu-SourceClips.controller').read_text();states=set(re.findall(r'm_Name: (\S+)\n',controller))-{'Amaterasu-SourceClips'}
assert not states-names,states-names
for b in bindings:
    assert b['clip'] in banks['pl00'] and (not b['intro'] or b['intro'] in banks['pl00'])
scene=Scene(A/'Sunward/Scenes/Windflower.unity');cid=proof['nativeAmaterasuComponent']
assert scene.owner(cid)==1873811283 and f'addedObject: {{fileID: {cid}}}' in scene.blocks[1873811279]
prefab=Scene(A/'Sunward/Generated/Sundial.prefab');pid=proof['nativeSolarComponent'];baseline=Scene(prefab.path,text=subprocess.check_output(['git','show','00fd8695363df01de80b012d68feb20c9961e8a9:Sunward-Unity/Assets/Sunward/Generated/Sundial.prefab'],cwd=ROOT,text=True))
for i,old in baseline.blocks.items():
    current=prefab.blocks[i]
    if i==1316439225924063651:current=current.replace(f'  - component: {{fileID: {pid}}}\n','')
    assert current==old,('Changed protected Sundial field',i)
assert set(prefab.blocks)-set(baseline.blocks)=={pid}
# Exact gameplay methods are protected independently of the new visual socket setup.
combat=(A/'Sunward/Scripts/WolfCombat.cs').read_text();oldcombat=subprocess.check_output(['git','show','00fd8695363df01de80b012d68feb20c9961e8a9:Sunward-Unity/Assets/Sunward/Scripts/WolfCombat.cs'],cwd=ROOT,text=True)
assert combat[combat.index('        public void Equip()'):]==oldcombat[oldcombat.index('        public void Equip()'):]
models={n:json.loads((RES/n/'Model.json').read_text()) for n in banks}
# Native +Z is the face, so the model must face the motor's +Z. Ear bones
# parent to skull 7; dorsal mount is bone 30, rather than the tail chain.
bind,_=matrices(models['pl00'],banks['pl00']['pl00_000'][0][0]);assert bind[8,2,3]>0 and bind[31,1,3]>.5
validation=dict(**proof,controllerStatesCovered=len(states),exportedMotionPayloads=len(manifest['motions']),poseBanksHashVerified=True,rootTravelRemoved=True,SundialOriginalBlocksPreserved=True,combatGameplayMethodsBytePreserved=True,sourceBasis='Reflect X; preserve native +Z facing',UnityCompilation=False,UnityPlay=False)
# Optional independent reference: the earlier archive inspector uses separate
# Euler matrices and a separate MOT decoder. Compare actual skinned vertices.
reference=Path('/workspace/work/wp-inspection/motion_math.py')
if reference.exists():
    import importlib.util,pickle
    spec=importlib.util.spec_from_file_location('native_reference',reference);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    lookup=json.loads((export.SOURCE/'motion-source-index.json').read_text())['motions'];worst=0.;compared=0
    for name in ['pl00_000','pl00_010','pl00_011','pl00_012','pl00_021','pl00_019','pl00_501','pl00_520']:
        source=next(x for x in lookup if x['aliases'][0]['name']==name);alias=source['aliases'][0];ref.R=Path('/workspace/work')/(alias['archive']+'-inspection');inventory=json.loads((ref.R/'inventory.json').read_text());entry=next(e for e in inventory if e['sha256']==source['sha256']);clip=ref.parse(entry);data=banks['pl00'][name][0]
        for index in [0,len(data)//2,len(data)-1]:
            frame=index/2;expected=ref.skin(clip,frame);root=ref.pose(clip,frame)[0,:3,3];actual=skin(models['pl00'],data[index])
            assert len(expected)==len(actual)
            for (part,v),ported in zip(expected,actual):
                total=part['weights'][:,4:7].sum(axis=1)/255
                target=(v/total[:,None]-root)*[-.075,.075,.075];error=float(np.max(abs(target-ported)));worst=max(worst,error);compared+=len(v)
    assert worst<.0001,('Independent skin comparison failed (metres)',worst)
    validation['independentReferenceSkinVerticesCompared']=compared;validation['independentReferenceWorstMetres']=worst
Path(__file__).with_name('player-validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation,indent=2))
