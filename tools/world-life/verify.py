"""Offline source/geometry regression checks. Does not claim Unity compilation."""
from pathlib import Path
import sys,json,re,subprocess,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/repair'),str(ROOT/'tools/playtest-followup'),'/workspace/work/csharp-syntax']
from scene_data import World,ref,vec
from pose_audit import bank
from tree_sitter import Language,Parser
import tree_sitter_c_sharp
A=ROOT/'Sunward-Unity/Assets';S=A/'Sunward/Scripts';O=A/'OkamiRemaster/Original';plan=json.loads(Path(__file__).with_name('world-changes.json').read_text());w=World();s=w.scene;s.set(json.loads((ROOT/'tools/dungeon-dojo/world-changes.json').read_text())['chamber'],'m_IsActive',1)
parser=Parser(Language(tree_sitter_c_sharp.language()));scripts=list(A.rglob('*.cs'));bad=[str(p) for p in scripts if parser.parse(p.read_bytes()).root_node.has_error];assert not bad,bad
base=subprocess.check_output(['git','show',plan['base']+':Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'],cwd=ROOT,text=True);scene=(A/'Sunward/Scenes/Windflower.unity').read_text();newguids=set(re.findall('guid: ([a-f0-9]{32})',scene))-set(re.findall('guid: ([a-f0-9]{32})',base));missing=newguids-set(w.assets);assert not missing,missing
for go,b in s.blocks.items():
 if s.kind(go)==1 and 'stripped' not in b:
  components=re.findall(r'  - component: \{fileID: (\d+)\}',b)
  if components:assert s.kind(int(components[0]))==4,go
rooms=[(i,b) for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.Remaster.NativeHomeRoom\n' in b];assert len(rooms)==12
for i,b in rooms:
 for key in ['entrance','bed','hearth']:
  p=vec(b,key);root=vec(s.blocks[s.transform(s.owner(i))],'m_LocalPosition');assert abs(p[0]-root[0])<4 and abs(p[2]-root[2])<3 and abs(p[1]+55)<1,(i,key,p)
 ids=[int(k) for k in re.findall(r'fileID: (\d+)',b.split('  contents:\n')[1])];assert len(ids)>=12 and all(k in s.blocks for k in ids)
# Exact collider/render mesh agreement, containment, finite meshes and shaft seams.
shaft=[];dojo=[]
for r in w.renderers():
 if 'textured earth shaft' not in r['name'] and 'training hall · dojo-floor' not in r['name']:continue
 d=w.mesh(r['meshGUID'],r['meshID']);v=np.array(d['vertices'])@r['matrix'][:3,:3].T+r['matrix'][:3,3];faces=np.array(d['triangles']);assert np.isfinite(v).all();assert faces.max()<len(v)
 cid=s.component(r['go'],64);assert ref(s.blocks[cid],'m_Mesh')[1]==r['meshGUID']
 if 'dojo-floor' in r['name']:
  used=v[np.unique(faces)];assert np.all(abs(used[:,0])<=6.40001) and np.all((used[:,2]>=16.59999)&(used[:,2]<=33.60001));dojo.append(r['go'])
 else:
  a,b,c=v[faces[:,0]],v[faces[:,1]],v[faces[:,2]];norm=np.cross(b-a,c-a);rad=(a+b+c)/3-[35,0,0];rad[:,1]=0;dot=(norm*rad).sum(1);assert np.all(dot<1e-8),float(dot.max());shaft.append(v)
assert len(shaft)==6
for depth in [-.35,-1.25,-4,-12,-24]:
 sets=[]
 for v in shaft:
  ring=v[np.isclose(v[:,1],depth,atol=1e-5)]
  if len(ring):sets.append(set(map(tuple,np.round(ring,4))))
 assert len(sets)==2 and sets[0]==sets[1],(depth,len(sets))
# Cover geometry stays the original, complete 652-triangle cut.
previous=json.loads((ROOT/'tools/dungeon-dojo/world-changes.json').read_text());cover=json.loads((ROOT/'tools/combat-depths/world-changes.json').read_text());count=0
for tr in cover['coverFragments']:
 go=s.owner(tr);mesh=ref(s.blocks[s.component(go,33)],'m_Mesh')[1];count+=len(w.mesh(mesh,4300000)['triangles'])
assert count==652
# Original MOTs resolve for every source prefab, including continuous gait flags.
actor_count=0
for p in [A/'Sunward/Scenes/Windflower.unity',*(A/'Sunward/Generated').glob('*.prefab')]:
 raw=p.read_text()
 for block in raw.split('--- !u!'):
  if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in block:continue
  resource=re.search(r'^  resource: (.+)',block,re.M)[1];folder=next((d/resource for d in A.rglob('Resources') if (d/resource/'Poses.bytes').exists()),None);assert folder,resource;clips=bank(folder/'Poses.bytes');model=json.loads((folder/'Model.json').read_text())
  for key in ['idle','walk','run','strike','windup','recover','death','chargeAttack','slamAttack','rangedAttack']:
   found=re.search(r'^  '+key+r': (\S+)',block,re.M)
   if found:assert found[1] in clips,(p,key,found[1])
  if resource.startswith('Okami/em'):
   n=re.search(r'^  run: (\S+)',block,re.M)[1];assert clips[n][2],(resource,n,'non-loop run')
  for name,(poses,duration,loop) in clips.items():assert np.isfinite(poses).all() and len(poses[0])==len(model['bones'])+1 and duration>0
  actor_count+=1
player=A/'OkamiRemaster/Player/Resources/NativePlayer';clips=bank(player/'pl00/Poses.bytes');bindings=json.loads((player/'Bindings.json').read_text())['bindings'];states={b['state']:b for b in bindings}
for key in ['Dig','Eat','Swim_Idle','Swim_Move','Sit']:assert key in states and states[key]['clip'] in clips
assert states['Dig']['clip']=='pl00_092'
# Wiring assertions target previously broken transitions and shared constraints.
game=(S/'GameFlow.cs').read_text();waves=game.split('static readonly string[][] waves =')[1].split('void Awake()')[0];assert '"boss"' not in waves and waves.count('new[]')==3
assert 'if(Health<=0){ReturnHome();return;}' in game and 'if(Health<=0 && panel!="result")return;' in game
assert 'BossTrial=InTrial=true' in game and 'LowerArena.Inside(Player.transform.position)' in game
assert 'VisualStateProgress>=.55f' in (S/'EnemyBrain.cs').read_text() and 'ranged ? "shot" : "melee"' in (S/'EnemyBrain.cs').read_text()
assert 'if(!win)ClearEnemies();' in game and 'Player.Locked=Health<=0' in game
motor=(S/'WolfMotor.cs').read_text();assert 'game.BossTrial?29:17' in motor and 'NativeHomeRoom.Guard(old,guarded)' in motor
combat=(S/'WolfCombat.cs').read_text();assert 'length/FormMultiplier' in combat and 'strike.damage * mul*FormMultiplier' in combat
lower=(O/'Scripts/LowerArena.cs').read_text();assert 'ApplyOpen(false,false)' in lower and 'if(!inUpper && open)ApplyOpen(false,false)' in lower
assert 'p.y>-2' in (O/'Scripts/VillageServices.cs').read_text()
# Original audio stream provenance and metadata, no short result-loop substitution.
audio=json.loads((O/'Resources/Okami/NativeAudio.json').read_text())['cues'];music=[c for c in audio if c['cue']=='housemusic'];assert len(music)==1 and music[0]['resource'].endswith('foodhouse-background-0')
source=json.loads(Path(__file__).with_name('music-source.json').read_text());assert source['seconds']>60
profile=(S/'ProgressionData.cs').read_text();assert 'p.version != 1 && p.version != 2' in profile and 'p.farmVitality>10' in profile
crops=[b for b in s.blocks.values() if 'Assembly-CSharp::Sunward.Remaster.FarmCrop\n' in b];assert len(crops)==18
result=dict(csharpSyntaxFiles=len(scripts),unityCompilation='UNVERIFIED: no editor/compiler',unityPlayback='UNVERIFIED: no PC access',newSceneGUIDs=len(newguids),homes=len(rooms),crops=len(crops),dojoContainedFloors=len(dojo),shaftSections=len(shaft),shaftTriangles=sum(len(v)//6*4 for v in shaft),shaftSeamsWelded=True,unchangedCoverTriangles=count,originalActorsValidated=actor_count,playerBindings=len(bindings),checks=['three normal waves upstairs; boss start restricted to depths','death cannot close to zero-health free roam; defeated enemies cleared','boss/player boundary agree downstairs','form damage, speed and attack cadence double','original Dig/Eat/Swim/Sit bindings resolve','home rooms separated from surface venue checks','original positional animal retries and food-house music binding','backwards-compatible save fields with bounded farm vitality'],limits=['Dedicated original koto finger-playing action unidentified; seated own-bank arm motion is provisional','Food-house BGM stream 0 is provisional, musical title/instrument unverified','No original bathing action positively identified; compatible NPCs use native seated actions','Full EST/SEQ event dispatch remains incomplete','Unity compilation, gameplay, audio balance, paths and VFX need actual playtesting'])
Path(__file__).with_name('verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
