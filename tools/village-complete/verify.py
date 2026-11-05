"""Source, native provenance and placement checks; never Unity play-test evidence."""
from pathlib import Path
import json,sys,re,subprocess,numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';BASE='e17c75d275d0fb2fa2f4dd09cb99dd8af57c54a6';W=Path('/workspace/work/village-complete');checks=0
sys.path.insert(0,'/workspace/sunward-remaster/tools/repair');import scene_data as sd
sd.A=A;w=sd.World();s=w.scene

def check(ok,message):
 global checks
 checks+=1
 assert ok,message

def old(path):return subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(R))],cwd=R)
def same_native(path):
 data=old(path)
 if data.startswith(b'version https://git-lfs'):check(('oid sha256:'+__import__('hashlib').sha256(path.read_bytes()).hexdigest()).encode() in data,'Approved LFS asset changed: '+str(path))
 else:check(path.read_bytes()==data,'Approved asset changed: '+str(path))
# Every actual sound resource is importable as AudioClip; original recordings untouched.
for entry in json.loads((D/'NativeAudio.json').read_text())['cues']:
 candidates=[p for p in (A/'OkamiRemaster/Original/Resources'/entry['resource']).parent.glob(Path(entry['resource']).name+'.*') if p.suffix in ['.wav','.ogg']]
 check(len(candidates)==1,'Audio resource missing/ambiguous '+entry['resource']);check('AudioImporter:' in Path(str(candidates[0])+'.meta').read_text(),'Audio clip imported as text '+str(candidates[0]));check(not candidates[0].read_bytes().startswith(b'version https://git-lfs'),'Unresolved LFS audio')
same_native(D/'NativeAudio/player-shiranui-layered-bark.wav')
for p in (D/'WeaponPortraits').glob('*.png'):same_native(p)
# Every recovered core painting, model and runtime source has metadata; GUIDs remain unique.
guids={}
for p in A.rglob('*.meta'):
 text=p.read_text();m=re.search(r'^guid: ([a-f0-9]{32})$',text,re.M)
 if not m:continue
 check(m[1] not in guids,'Duplicate GUID '+str(p));guids[m[1]]=p
for p in [*(D/'Effects').glob('Original*.png'),*(D/'et90').glob('*'),*(A/'OkamiRemaster/Original/Scripts').glob('*.cs')]:
 if p.name.endswith('.meta') or p.is_dir():continue
 check(Path(str(p)+'.meta').exists(),'Missing metadata '+str(p))
# Actual resolved world transforms, not local-space coordinates mistaken for world-space.
rows=[r for r in w.renderers() if 'village house 7 ·' in r['name']];check(len(rows)==3,'Rotated shell incomplete')
for row in rows:check(np.linalg.norm(((row['lo']+row['hi'])/2)[[0,2]]-[14,29])<2,'Rotated house moved away from its plot')
check(not any('village house 6 ·' in r['name'] for r in w.renderers()),'Removed house still rendered')
for c in s.refs(1808887473):
 if s.kind(c)==65:check('m_Enabled: 0' in s.blocks[c],'Orphan riverbank wall remains active')
q=sd.vec(s.blocks[s.transform(1166610200)],'m_LocalPosition');check(np.linalg.norm(q[[0,2]]-[-19.11,23])<.02,'Relocated house collision did not follow its shell')
# Preserve terrain triangles, UVs and native pigment. Only existing vertex heights/normals change.
row=next(r for r in w.renderers() if r['go']==8000000000000011394);mesh=w.mesh(row['meshGUID'],row['meshID']);raw=old(mesh['path']).decode();source=bytes.fromhex(re.search('_typelessdata: ([a-f0-9]+)',raw)[1]);current=bytes.fromhex(re.search('_typelessdata: ([a-f0-9]+)',mesh['raw'])[1]);count=len(mesh['vertices']);stride=mesh['stride'];before=np.frombuffer(source,np.uint8).reshape(count,stride);after=np.frombuffer(current,np.uint8).reshape(count,stride)
check(re.search('m_IndexBuffer: ([a-f0-9]+)',raw)[1]==re.search('m_IndexBuffer: ([a-f0-9]+)',mesh['raw'])[1],'Terrain topology changed')
check(np.array_equal(before[:,24:],after[:,24:]),'Native terrain pigment/UVs changed');check(np.array_equal(before[:,:4],after[:,:4]) and np.array_equal(before[:,8:12],after[:,8:12]),'Terrain horizontal vertex coordinates changed');check(np.isfinite(mesh['vertices']).all(),'Nonfinite terrain vertex')
check('clip(-1)' not in (A/'OkamiRemaster/Windflower/Shaders/ContinuousGround.shader').read_text(),'Shader still removes a rectangular bank')
# Original save model, with the effect curtain hidden after bounds normalization.
j=json.loads((D/'et90/Model.json').read_text());check(len(j['parts'])==5 and j['sourceSHA256'],'Original save-mirror assembly incomplete')
check((D/'Effects/OriginalSaveSeal.png').exists(),'Original celestial save seal missing')
# Own-rig sleep loops: preserve every existing source clip and add only the recovered alias.
sys.path.insert(0,'/workspace/sunward-remaster/tools/playtest-followup');from pose_audit import bank
for name in ['hm00','hm05','hm68','hm0f']:
 p=D/name/'Poses.bytes';temp=W/(name+'-before.bytes');temp.write_bytes(old(p));a=bank(temp);b=bank(p);check(set(b)==set(a)|{'village_sleep'},'Existing pose names lost')
 for label,clip in a.items():check(np.array_equal(clip[0],b[label][0]) and clip[1:]==b[label][1:],'Existing native pose changed '+name+'/'+label)
check('→' in (A/'OkamiRemaster/Original/Scripts/MemoryMirrorMenu.cs').read_text(),'Native selected-row arrow missing')
report=dict(checks=checks,sourceChecksPassed=True,unityPlayed=False,audioAwaitingListening=['gong replacement','thunder strike replacement','house flute music','separate quiet palace music'],readyForPackage=True)
(W/'source-review.json').write_text(json.dumps(report,indent=2));print('PASS',checks,'native preservation/import/source-placement contracts. Assets packaging requested; original audio identification pending; Unity runtime unverified.')
