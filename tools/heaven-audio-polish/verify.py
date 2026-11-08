"""Original asset integrity and C# syntax checks; not Unity validation."""
from pathlib import Path
import json,hashlib,subprocess,sys,struct
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';BASE='fe99c7e921a74c079b0a283a16c4453e8747bcc6';checks=0

def check(b,s):
 global checks
 checks+=1;assert b,s
old=json.loads(subprocess.check_output(['git','show',BASE+':'+str((D/'NativeAudio.json').relative_to(R))],cwd=R));now=json.loads((D/'NativeAudio.json').read_text());unchanged=[x for x in old['cues'] if x['cue']!='palacemusic'];check(all(x in now['cues'] for x in unchanged),'Existing weapon/combat cue replaced')
for n in ['es3a','es4a','es4b']:
 j=json.loads((D/n/'Model.json').read_text());check(j['version']==1 and j['sourceSHA256'],'Missing original asset provenance')
 for part in j['parts']:
  v=len(part['positions'])//3;check(len(part['positions'])==3*v and len(part['weights'])==3*v and len(part['boneIndices'])==3*v and len(part['colors'])==4*v and len(part['uv'])==2*v,'Native streams do not agree');check(max(part['indices'])<v,'Native index out of bounds');check(max(part['boneIndices'])<len(j['bones']),'Native bone out of bounds')
 for t in j['textures']:
  if not t.get('vertexOnly'):check((D/n/t['path']).is_file(),'Missing native paint')
 for p in (D/n).iterdir():
  if p.suffix!='.meta':check(Path(str(p)+'.meta').is_file(),'Missing Unity meta')
a=json.loads((D/'es3a/Model.json').read_text());b=json.loads((D/'pl0d/Model.json').read_text());check(a['bones']==b['bones'],'ES3A does not share PL0D native bind hierarchy');check(struct.unpack_from('<I',(A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes').read_bytes(),8)[0]==len(a['bones'])+1,'Wolf motion bank does not match full-power skeleton')
a=json.loads((D/'es4a/Model.json').read_text());b=json.loads((D/'es4b/Model.json').read_text());check(a['bones']==b['bones'] and a['parts']==b['parts'],'ES4B motion sharing is not on an identical rig');check((D/'es4a/Poses.bytes').read_bytes()==(D/'es4b/Poses.bytes').read_bytes(),'ES4B lost matching original motion')
for name,groups in [('wp20',[0,3]),('wp25',[0,1,3,4]),('wp29',[1,2,3,4]),('thunder-awakened',[1,2,3,4])]:check(json.loads((D/name/'Model.json').read_text())['visibleGroups']==groups,'Recovered weapon sections excluded')
provenance=json.loads((R/'tools/full-power-update/audio-provenance.json').read_text());check(len(provenance['selections'])==8,'Missing selected sound')
for s in provenance['selections']:
 files=[p for p in (A/'OkamiRemaster/Original/Resources'/s['resource']).parent.glob(Path(s['resource']).name+'.*') if p.suffix in ['.wav','.ogg']];check(len(files)==1,'Selected clip missing');p=files[0];check(hashlib.sha256(p.read_bytes()).hexdigest()==s['outputSHA256'],'Selected clip differs from decoded original');check('AudioImporter:' in Path(str(p)+'.meta').read_text(),'Audio imported as text');check(s['subsong']==s['arrayIndex']+1,'Inconsistent sound numbering')
sys.path.insert(0,'/workspace/work/csharp-syntax');import tree_sitter,tree_sitter_c_sharp
parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_c_sharp.language()))
for p in A.rglob('*.cs'):check(not parser.parse(p.read_bytes()).root_node.has_error,'C# syntax error: '+str(p))
check(not subprocess.check_output(['git','diff','--check'],cwd=R),'Whitespace errors');
for name in ['wp25','wp29','thunder-awakened']:
 current=json.loads((D/name/'Model.json').read_text());original=json.loads(subprocess.check_output(['git','show','HEAD:'+str((D/name/'Model.json').relative_to(R))],cwd=R));check(current['parts']==original['parts'] and current['textures']==original['textures'],'Original weapon geometry, UVs or paints were altered')
for p in [*(D/'NativeAudio').glob('*.wav'),*(D/'SelectedAudio').glob('*.wav'),*(D/'SelectedAudio').glob('*.ogg'),*(D/'WeaponPortraits').glob('*.png')]:
 blob=subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(R))],cwd=R);check(('oid sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()).encode() in blob if blob.startswith(b'version https://git-lfs') else blob==p.read_bytes(),'Existing original audio or approved portrait modified: '+str(p))
print('PASS',checks,'original model/audio integrity and all-Assets C# syntax contracts; Unity unverified')
