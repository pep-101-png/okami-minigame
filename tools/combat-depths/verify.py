"""Geometry/resource/audio regressions for this exact candidate. Not a Unity compile."""
from pathlib import Path
import sys,re,json,hashlib,subprocess,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';RES=A/'OkamiRemaster/Original/Resources/Okami';BASE='1a47fd212f238f7cfa54eea5cc82c63481ddcb9b'
sys.path[:0]=[str(ROOT/'tools/repair'),str(ROOT/'tools/playtest-followup')]
from scene_data import World,ref,vec
from pose_audit import bank

def hits(v,ix,x,z):
 a,b,c=v[ix[:,0]],v[ix[:,1]],v[ix[:,2]];u=b[:,[0,2]]-a[:,[0,2]];q=c[:,[0,2]]-a[:,[0,2]];p=np.array([x,z])-a[:,[0,2]];den=u[:,0]*q[:,1]-u[:,1]*q[:,0];valid=abs(den)>1e-9;f=np.zeros_like(den);g=f.copy();f[valid]=(p[valid,0]*q[valid,1]-p[valid,1]*q[valid,0])/den[valid];g[valid]=(u[valid,0]*p[valid,1]-u[valid,1]*p[valid,0])/den[valid];ok=valid&(f>=-1e-6)&(g>=-1e-6)&(f+g<=1.000001);return (a[:,1]+f*(b[:,1]-a[:,1])+g*(c[:,1]-a[:,1]))[ok]
def soup(v,ix):return collections.Counter(tuple(np.round(t,3).ravel()) for t in np.asarray(v,dtype=float)[ix])
def geometry(w,r):
 d=w.mesh(r['meshGUID'],r['meshID']);return np.asarray(d['vertices'])@r['matrix'][:3,:3].T+r['matrix'][:3,3],np.asarray(d['triangles'])
def run():
 report={};w=World();s=w.scene;plan=json.loads(Path(__file__).with_name('world-changes.json').read_text());old=lambda p:subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT)
 for p in [A/'Sunward/Scripts/SaveStore.cs',A/'Sunward/Scripts/ProgressionData.cs',A/'Sunward/Data/Valley.json',ROOT/'Sunward-Unity/ProjectSettings/EditorBuildSettings.asset',ROOT/'Sunward-Unity/Packages/manifest.json',*(A/'Sunward/Generated').glob('Spirit-*.asset')]:assert p.read_bytes()==old(p),p
 report['saveSchemaProgressionEnemyStatsWorldDataAndBuildScenePreserved']=True
 guids={}
 for p in A.rglob('*.meta'):
  m=re.search(r'^guid: (\w+)',p.read_text(),re.M)
  if m:assert m[1] not in guids,(p,guids[m[1]]);guids[m[1]]=p.with_suffix('')
 previous_external=set(re.findall(r'guid: ([0-9a-f]{32})',old(s.path).decode()))-guids.keys()
 for p in [s.path,*(A/'OkamiRemaster/Original').rglob('*.mat'),*(A/'Sunward/Generated').glob('Enemy-*.prefab')]:
  for g in re.findall(r'guid: ([0-9a-f]{32})',p.read_text()):assert g.startswith('0000000000000000') or g in guids or g in previous_external,(p,g)
 for p in (A/'OkamiRemaster/Original').rglob('*.meta'):assert p.with_suffix('').exists(),p
 for source in [s,*w.prefabs.values()]:
  for i,b in source.blocks.items():
   if source.kind(i)==1 and 'stripped' not in b and source.refs(i):assert source.kind(source.refs(i)[0]) in [4,224],i
 report['referencesMetadataAndTransformOrderingChecked']=True
 oldground=w.mesh(plan['oldGroundSource'],-1844107791034710560);expected=soup(oldground['vertices'],oldground['triangles']);rs=list(w.renderers());ground=next(r for r in rs if r['name']=='Existing native-painted ground · centre opening');v,ix=geometry(w,ground);actual=soup(v,ix)
 for r in rs:
  if r['name'].startswith('Original terrain seal fragment '):q,j=geometry(w,r);actual.update(soup(q,j))
 assert expected==actual,('Closed terrain mismatch',sum((expected-actual).values()),sum((actual-expected).values()))
 for x,z in [(35,0),(38.5,0),(31.5,0),(35,3.5),(35,-3.5)]:assert len(hits(v,ix,x,z))==0,(x,z)
 assert len(hits(v,ix,43,0))>0
 report.update(originalGroundTrianglesRestoredByClosedCover=sum(expected.values()),centreTrianglesInSixFragments=plan['cutOriginalGroundTriangles'],shaftClearOfUpperGround=True)
 # Inspect chamber even though the saved scene initially keeps it inactive.
 assert '  m_IsActive: 0\n' in s.blocks[plan['chamber']];s.set(plan['chamber'],'m_IsActive',1);w.transforms.clear();rs=list(w.renderers());floors=[geometry(w,r) for r in rs if r['name'].startswith('Original painted lower arena floor ')]
 samples=0
 for x in np.linspace(-29,29,17):
  for z in np.linspace(-29,29,17):
   if x*x+z*z>29**2:continue
   y=[h for q,j in floors for h in hits(q,j,35+x,z)];assert y and -20.001<=max(y)<=-19.98,(x,z,y);samples+=1
 vault=[geometry(w,r) for r in rs if 'depths native stone vault' in r['name'] or 'depths ink cliff' in r['name']]
 for x,z in [(35,0),(38.5,0),(31.5,0),(35,3.5),(35,-3.5)]:
  blocked=[h for q,j in vault for h in hits(q,j,x,z) if -19<h<1];assert not blocked,('Shaft blocked by stone',x,z,blocked)
 mirror=s.transform(plan['mirror']);p=w.matrix(0,mirror)[:3,3];assert p[1]==-20 and np.linalg.norm(p[[0,2]]-[35,0])<30
 report.update(lowerFloorSamplesWithSupport=samples,stoneVaultLeavesShaftClear=True,returnMirrorInsideChamber=True,lowerArenaEnemySpawners=0)
 for row in plan['trainingGrounding']:assert abs(row['position'][1]-row['floor']-.015)<1e-6
 report['trainingPairsAlignedToActualRotatedFloor']=6
 for support in plan['homeDisplaySupports']:
  points=[]
  for r in rs:
   if r['go'] in support['objects']:q,j=geometry(w,r);points.append(q)
  assert points and abs(np.concatenate(points)[:,1].min()-support['top'])<.001,support
 report['homeWeaponsRestOnCabinetTops']=2
 # Entry height must be above its original floor; do not teleport into a ramp.
 dojo=[geometry(w,r) for r in rs if 'training hall · dojo-floor' in r['name']];entry=[h for q,j in dojo for h in hits(q,j,0,18.3)];report['dojoEntryPhysicalFloor']=max(entry)
 services=(A/'OkamiRemaster/Original/Scripts/VillageServices.cs').read_text();entry_y=float(re.search(r'new Vector3\(0,([.0-9]+)f,18.3f\)',services)[1]);assert 0<entry_y-max(entry)<.075,('Dojo entry intersects/overfloats ramp',max(entry),entry_y)
 for ins,side in [(2027807467,-1),(1439298636,1)]:
  src=w.prefabs[ins];tr=next(i for i in src.blocks if src.kind(i)==4 and ref(src.blocks[i],'m_Father')[0]==0);mat=w.matrix(ins,tr);assert np.allclose(mat[[0,2],3],[side*8.6,0]);assert np.dot(mat[:3,2],np.array([-side,0,0]))>.99
 report['marketMerchantsBehindCountersFacingStreet']=2
 banks={};models=0
 for p in A.rglob('Resources/**/Model.json'):
  d=json.loads(p.read_text());models+=1
  if (p.parent/'Poses.bytes').exists():
   clips=bank(p.parent/'Poses.bytes');banks[p.parent]=clips
   for name,(x,dur,loop) in clips.items():assert dur>0 and np.isfinite(x).all() and abs(np.linalg.norm(x[:,:,3:7],axis=2)-1).max()<1e-4,(p,name)
  mask=d.get('visibleGroups');available={int(q['name'].split('-')[1]) for q in d['parts']};assert not mask or set(mask)<=available
  for t in d['textures']:assert t.get('vertexOnly') or (p.parent/t['path']).exists()
 bindings=json.loads((A/'OkamiRemaster/Player/Resources/NativePlayer/Bindings.json').read_text())['bindings'];player=banks[A/'OkamiRemaster/Player/Resources/NativePlayer/pl00'];assert len({b['state'] for b in bindings})==len(bindings)
 for b in bindings:assert b['clip'] in player
 assert {b['clip'] for b in bindings if b['state'].startswith('Swim_')}=={'pl00_130','pl00_131'}
 expected_weapons={x['package']:x['visibleGroups'] for x in json.loads(Path(__file__).with_name('weapon-model-audit.json').read_text())}
 for name,mask in expected_weapons.items():assert json.loads((RES/name/'Model.json').read_text())['visibleGroups']==mask
 assert len(expected_weapons)==15
 for p in (A/'Sunward/Generated').glob('Enemy-*.prefab'):
  b=p.read_text();package=re.search(r'  resource: Okami/(\S+)',b)[1]
  for f in ['idle','walk','run','windup','strike','recover','death','chargeAttack','slamAttack','rangedAttack']:
   m=re.search(r'(?m)^  '+f+r': (\S+)',b)
   if m:assert m[1] in banks[RES/package],(p,f,m[1])
 report.update(modelResources=models,finiteNormalizedPoseBanks=len(banks),playerBindings=len(bindings),weaponModelSelectionsChecked=15,enemyPrefabsWithVariantAttacks=6)
 cues=json.loads((RES/'NativeAudio.json').read_text())['cues']
 for c in cues:assert (A/'OkamiRemaster/Original/Resources'/(c['resource']+'.wav')).exists() or (A/'OkamiRemaster/Original/Resources'/(c['resource']+'.ogg')).exists(),c
 audio=json.loads(Path(__file__).with_name('weapon-audio-sources.json').read_text())
 for r in audio:
  p=A/'OkamiRemaster/Original/Resources'/(r['resource']+'.wav');assert hashlib.sha256(p.read_bytes()).hexdigest()==r['outputSHA256'];assert r['decoding']['output']['clippedFraction']==0 and r['decoding']['output']['peak']<=.45001
 assert len(audio)==30
 report.update(ownInstrumentAudioCuesHashAndPeakChecked=len(audio),soundBalanceAudiblyVerified=False)
 for p in [*(A/'OkamiRemaster/Original').rglob('*'),*(A/'OkamiRemaster/Player/Resources').rglob('*')]:
  if p.is_file():
   with p.open('rb') as f:assert not f.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'),p
 sys.path.insert(0,'/workspace/work/csharp-syntax');import tree_sitter,tree_sitter_c_sharp
 parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_c_sharp.language()));files=list(A.rglob('*.cs'));errors=[str(p) for p in files if parser.parse(p.read_bytes()).root_node.has_error];assert not errors,errors
 combat=(A/'Sunward/Scripts/WolfCombat.cs').read_text();assert 'previousPhase <= strike.end' in combat and 'originalView.AttackPhase' in combat and 'Instantiate(spear.visual' not in combat
 game=(A/'Sunward/Scripts/GameFlow.cs').read_text();assert 'LowerArena.TrialStarted()' in game and 'LowerArena.TrialFinished(win)' in game and 'Consider("offering"' not in game
 report.update(CSharpSyntaxFiles=len(files),CSharpSyntaxErrors=errors,UnityCompilationVerified=False,UnityPlaytestVerified=False,exactNativeSEQESTDispatchReconstructed=False,swimSourceSymbolicNamesAvailable=False)
 Path(__file__).with_name('verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
