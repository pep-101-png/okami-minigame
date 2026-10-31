"""Offline regression checks. No Unity editor, compiler, or audible review is implied."""
from pathlib import Path
import sys,json,re,subprocess,hashlib,struct,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';RES=A/'OkamiRemaster/Original/Resources/Okami';BASE='045e48e7f07054b81876c58fe5975cb4616c3139'
sys.path[:0]=[str(ROOT/'tools/repair'),str(ROOT/'tools/original-remake'),str(ROOT/'tools/playtest-followup')]
from scene_data import World,ref
from pose_audit import bank
from native import Scene,vec

def run():
 w=World();s=w.scene;report={};old=lambda p:subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT)
 for p in [A/'Sunward/Scripts/SaveStore.cs',A/'Sunward/Scripts/ProgressionData.cs',A/'Sunward/Scripts/WolfMotor.cs',A/'Sunward/Data/Valley.json',ROOT/'Sunward-Unity/ProjectSettings/EditorBuildSettings.asset',ROOT/'Sunward-Unity/Packages/manifest.json',*(A/'Sunward/Generated').glob('Spirit-*.asset')]:assert p.read_bytes()==old(p),p
 report['saveProgressionPlayerMotorWorldDataEnemyDefinitionsAndBuildScenesUnchanged']=True
 before=Scene(s.path,text=old(s.path).decode());assert all(s.blocks[i]==b for i,b in before.blocks.items() if before.kind(i) in [64,65,135,136,143,154]);report['existingColliderBlocksUnchanged']=sum(before.kind(i) in [64,65,135,136,143,154] for i in before.blocks)
 guids={}
 for p in A.rglob('*.meta'):
  m=re.search(r'^guid: (\w+)',p.read_text(),re.M)
  if m:guids[m[1]]=p.with_suffix('')
 external=set(re.findall(r'guid: ([0-9a-f]{32})',old(s.path).decode()))-guids.keys()
 for p in [s.path,*(A/'OkamiRemaster/Original').rglob('*.mat'),*(A/'Sunward/Generated').glob('NPC-*.prefab'),*(A/'Sunward/Generated').glob('Enemy-*.prefab')]:
  for g in re.findall(r'guid: ([0-9a-f]{32})',p.read_text()):assert g.startswith('0000000000000000') or g in guids or g in external,(p,g)
 for source in [s,*w.prefabs.values()]:
  for i,b in source.blocks.items():
   if source.kind(i)==1 and 'stripped' not in b and source.refs(i):assert source.kind(source.refs(i)[0]) in [4,224],i
 report['savedReferencesAndTransformOrderingChecked']=True
 resources={};models=0
 for p in A.rglob('Resources/**/Model.json'):
  d=json.loads(p.read_text());models+=1
  if (p.parent/'Poses.bytes').exists():
   clips=bank(p.parent/'Poses.bytes');resources[p.parent]=clips
   for name,(x,duration,loop) in clips.items():assert np.isfinite(x).all() and duration>0 and abs(np.linalg.norm(x[:,:,3:7],axis=2)-1).max()<1e-4,(p,name)
  for part in d['parts']:
   v=np.asarray(part['positions']).reshape(-1,3);ix=np.asarray(part['indices']);assert np.isfinite(v).all() and (not len(ix) or 0<=ix.min()<=ix.max()<len(v))
   tex=next(t for t in d['textures'] if t['index']==part['texture']);assert tex.get('vertexOnly') or (p.parent/tex['path']).exists()
 report.update(modelsChecked=models,finiteNormalizedMotionBanksChecked=len(resources))
 actors=0
 for source in [s,*w.prefabs.values()]:
  for i,b in source.blocks.items():
   if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b:continue
   package=re.search(r'  resource: Okami/(\S+)',b)[1];clips=resources[RES/package]
   for field in ['idle','walk','run','windup','strike','recover','death']:assert re.search(r'  '+field+r': (\S+)',b)[1] in clips
   actors+=1
 report['savedActorBindingsChecked']=actors
 wheel=resources[RES/'vt6a']['vt6a_001'][0];assert np.ptp(wheel[:,3,1])<1e-7;assert np.ptp(wheel[:,3,3])>.99 and np.ptp(wheel[:,3,6])>1.9
 assert json.loads((RES/'vt6a/Model.json').read_text())['visibleGroups']==[1]
 report['completeWheelFullTurnWithoutVerticalBobbing']=True
 player=A/'OkamiRemaster/Player/Resources/NativePlayer';bindings=json.loads((player/'Bindings.json').read_text())['bindings'];assert all(b['clip'] in resources[player/'pl00'] for b in bindings)
 assert {b['clip'] for b in bindings if b['state'].startswith('Swim_')}=={'pl00_013'};report['swimBindingChangedTo013']=True;report['swimOriginalActionNameConfirmed']=False
 for ins,x in [(2027807467,-7),(1439298636,7)]:
  src=w.prefabs[ins];root=next(i for i in src.blocks if src.kind(i)==4 and ref(src.blocks[i],'m_Father')[0]==0);p=w.matrix(ins,root)[:3,3];assert np.allclose(p[[0,2]],[x,1.1]);assert any('  hasStation: 1\n' in b and abs(vec(b,'station')[0]-x)<.01 for b in s.blocks.values())
  actor=next(b for b in src.blocks.values() if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' in b);assert '_003\n' in actor and 'venue_' not in actor
 report['merchantStationsCentredAndNativeSeated']=2
 floors=[r for r in w.renderers() if 'food house floor' in r['name']]
 for r in floors:
  v=np.asarray(w.mesh(r['meshGUID'],r['meshID'])['vertices']);y=(v@r['matrix'][:3,:3].T+r['matrix'][:3,3])[:,1];assert np.allclose(y,.4)
 report['pubFloorAndEntryMatched']=True
 for b in s.blocks.values():
  if 'Assembly-CSharp::Sunward.Remaster.NativeVenueActor\n' in b and '  role: training' not in b:assert '  seatedMotion: ' in b and '  handMotion: ' in b
 home=next(b for b in s.blocks.values() if 'Assembly-CSharp::Sunward.HomeCutaway\n' in b);assert '  contents:\n' in home
 assert 'HomeCutaway.Inside' in (A/'Sunward/Scripts/HomeWeaponRack.cs').read_text()
 assert 'hasStation' in (A/'Sunward/Scripts/VillageResident.cs').read_text()
 assert 'chargeStep=Mathf.Min(dt,chargeRemaining)' in (A/'Sunward/Scripts/EnemyBrain.cs').read_text()
 for role,name in [('wisp','em00_131'),('reed','em00_132'),('boss','em65_021')]:
  b=(A/'Sunward/Generated'/('Enemy-'+role+'.prefab')).read_text();assert all('  '+f+': '+name+'\n' in b for f in ['windup','strike','recover'])
 report.update(homeFurnitureVisibilityGuarded=True,enemyAttackBindingsChanged=3,chargeTravelWindowPreserved=True)
 audio=json.loads((ROOT/'tools/playtest-followup/audio-audit.json').read_text())
 for r in audio:assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['outputSHA256'] and r['output']['clippedFraction']==0
 cues=json.loads((RES/'NativeAudio.json').read_text())['cues'];assert next(b['resource'] for b in cues if b['cue']=='battle').endswith('/town-1')
 sound=(A/'Sunward/Scripts/ValleyAudio.cs').read_text();assert 'wind.Stop();river.Stop();' in sound and 'Loop(wind' not in sound and 'if(cue!="battle")return;' in sound and 'id=="step"?.045f' in sound
 report.update(originalAudioFilesStillHashVerified=len(audio),globalUnidentifiedAmbienceDisabled=True,townAndPubMusicPendingIdentification=True)
 sys.path.insert(0,'/workspace/work/csharp-syntax');import tree_sitter,tree_sitter_c_sharp
 parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_c_sharp.language()));files=list(A.rglob('*.cs'));errors=[str(p) for p in files if parser.parse(p.read_bytes()).root_node.has_error];assert not errors,errors
 report.update(CSharpSyntaxFiles=len(files),CSharpSyntaxErrors=errors,UnityCompilationVerified=False,UnityPlaybackVerified=False,audibleBalanceVerified=False)
 # Check every supplied source of active clip names for precise channel usage.
 rows=[json.loads(l) for l in Path('/workspace/work/full-asset-inspection/inventory.jsonl').read_text().splitlines()];names={name for clips in resources.values() for name in clips};affected=[]
 for row in rows:
  if row['type']!='MOT' or row['name'] not in names:continue
  data=(Path('/workspace/work/full-asset-inspection')/row['cache']).read_bytes();count=data[6];props=[struct.unpack_from('<bBHI',data,8+k*8)[1] for k in range(count-1)]
  if any(48<=p<=56 for p in props):affected.append({'package':row['package'],'motion':row['name']})
 report['activePreciseChannelSourceMatches']=affected
 Path(__file__).with_name('verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
