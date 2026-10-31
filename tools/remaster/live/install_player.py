#!/usr/bin/env python3
"""Install native visual adapters into the existing gameplay scene/prefab only."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'Sunward-Unity/Assets'
sys.path.insert(0,str(ROOT/'tools/village'));from native import Scene
OUT=A/'OkamiRemaster/Player';RES=OUT/'Resources/NativePlayer'

def guid(path):
    path=Path(path);meta=Path(str(path)+'.meta')
    if meta.exists():return re.search(r'^guid: (\w+)',meta.read_text(),re.M)[1]
    value=hashlib.sha256(('NativePlayer/'+str(path.relative_to(A))).encode()).hexdigest()[:32]
    if path.is_dir():kind='folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n'
    elif path.suffix=='.cs':kind='MonoImporter:\n  externalObjects: {}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n'
    elif path.suffix=='.mat':kind='NativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 2100000\n'
    elif path.suffix=='.png':
        template=(ROOT/'tools/remaster/reference/NativeSources/pl00/Texture-0.png.meta').read_text();meta.write_text(re.sub(r'^guid: \w+','guid: '+value,template,flags=re.M));return value
    else:kind='TextScriptImporter:\n  externalObjects: {}\n'
    meta.write_text('fileFormatVersion: 2\nguid: '+value+'\n'+kind+'  userData:\n  assetBundleName:\n  assetBundleVariant:\n');return value

bindings=[]
def bind(states,clip,loop=False,intro=None,mirror=False,reason='Pose inspected; action binding is a Sunward adaptation, not an original action-name table'):
    for state in states.split(','):
        bindings.append(dict(state=state,clip='pl00_'+clip,loop=loop,intro='pl00_'+intro if intro else '',mirror=mirror,evidence=reason))
bind('Idle_Natural','000',True)
bind('Walk_Natural,Walk_Turn_L,Walk_Turn_R','010',True,reason='Original cyclic walk; motor turns the character, same original gait for turn variants')
bind('Jog_Natural,Jog_Turn_L,Jog_Turn_R','011',True)
bind('Sprint_Fluid,Sprint_Turn_L,Sprint_Turn_R','012',True)
bind('Sleep_Down,Sleep_Down_Legacy','005',intro='003')
bind('Sleep_Loop,Sleep_Loop_Legacy','004',True)
bind('Sleep_Up,Sleep_Up_Legacy','006')
bind('Jump_Standing','021',intro='020')
bind('Jump_Jog,Jump_Walk','025',intro='024')
bind('Jump_Sprint','029',intro='027')
bind('Jump_Double','031')
bind('Air_Fall','022')
bind('Land_Soft,Land_Heavy','02d')
bind('Dodge_Forward,Dodge_Jog,Dodge_Sprint,Dodge_Walk','017')
bind('Dodge_Back','018')
bind('Dodge_Right','019')
bind('Dodge_Left','019',mirror=True,reason='Original side roll mirrored in bone transforms; no negative renderer scale')
bind('Bark','04e')
bind('Disc1','500');bind('Disc2','501');bind('Disc3','502');bind('DiscHeavy','503');bind('DiscCharged','504')
bind('ChargeLight,ChargeHeavy','511',True)
bind('AirStrike','505');bind('AirStrike_Glaive','525')
bind('Thrust','520');bind('Sweep','521');bind('Finish','522');bind('HeavyArc','523');bind('HeavyReturn','524')
bind('ChargedThrust','523');bind('ChargedHeavy','524')
assert len({b['state'] for b in bindings})==len(bindings)
(RES/'Bindings.json').write_text(json.dumps(dict(bindings=bindings),indent=2)+'\n')
material=(A/'OkamiRemaster/Village/Resources/Farm/AnimalPaint.mat').read_text().replace('Original Farm Animal Paint','Original Amaterasu and Solar Flare paint')
(RES/'Surface.mat').write_text(material)
for file in [OUT,*sorted(OUT.rglob('*'))]:
    if not file.name.endswith('.meta'):guid(file)

def component(id,gameobject,script,classname):
    return f'''MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {gameobject}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: Assembly-CSharp::Sunward.Remaster.{classname}
'''
scene=Scene(A/'Sunward/Scenes/Windflower.unity');cid=8100000000000010001
already_installed=cid in scene.blocks
scene.blocks[cid]=f'--- !u!114 &{cid}\n'+component(cid,1873811283,guid(OUT/'NativeAmaterasu.cs'),'NativeAmaterasu')
instance=scene.blocks[1873811279];needle='  m_SourcePrefab:'
record=f'''    - targetCorrespondingSourceObject: {{fileID: 1713185874664353117, guid: 52f64adb2bcfddb45acb71e708bf1fe9, type: 3}}
      insertIndex: -1
      addedObject: {{fileID: {cid}}}
'''
assert instance.count(needle)==1
if not already_installed:scene.blocks[1873811279]=instance.replace(needle,record+needle)
scene.save()

prefab=Scene(A/'Sunward/Generated/Sundial.prefab');pid=8100000000000010002;go=1316439225924063651
if pid not in prefab.blocks:
    text=prefab.blocks[go];text=text.replace('  m_Layer:',f'  - component: {{fileID: {pid}}}\n  m_Layer:',1);prefab.blocks[go]=text
prefab.blocks[pid]=f'--- !u!114 &{pid}\n'+component(pid,go,guid(OUT/'NativeSolarFlare.cs'),'NativeSolarFlare')
prefab.path.write_text(prefab.header+''.join(prefab.blocks.values()))
proof=dict(nativeAmaterasuComponent=cid,nativeSolarComponent=pid,stateBindings=len(bindings),distinctAmmySourceMotions=len({b['clip'] for b in bindings}|{b['intro'] for b in bindings if b['intro']}),modifiedScene='Assets/Sunward/Scenes/Windflower.unity',modifiedPrefab='Assets/Sunward/Generated/Sundial.prefab',UnityVerified=False,completeSolarEffects=False)
Path(__file__).with_name('player-install.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

if __name__=='__main__':pass
