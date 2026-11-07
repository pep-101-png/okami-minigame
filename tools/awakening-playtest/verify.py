"""Current source/asset, audio-boundary and placement checks, not Unity."""
from pathlib import Path
import subprocess,json,sys,hashlib,re,numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/awakening-playtest');n=0
BASE='50c46d1322d3fe53ab418e2bd9184d741abe8afd'
def check(b,s):
 global n;n+=1;assert b,s
def same(p):
 raw=subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(R))],cwd=R);data=p.read_bytes();check(('oid sha256:'+hashlib.sha256(data).hexdigest()).encode() in raw if raw.startswith(b'version https://git-lfs') else raw==data,'Approved asset changed: '+str(p))
for folder in ['NativeAudio','WeaponPortraits','es3a','es4a','es4b','es4a-flow','es4b-flow','wp20','wp25','wp29','thunder-awakened']:
 for p in (D/folder).iterdir():
  if p.is_file() and not p.name.endswith('.meta'):same(p)
same(A/'OkamiRemaster/Original/Scripts/SpectralTendrils.cs');same(A/'OkamiRemaster/Original/Shaders/OriginalFlowingRibbon.shader')
old=json.loads(subprocess.check_output(['git','show',BASE+':'+str((D/'NativeAudio.json').relative_to(R))],cwd=R))['cues'];now=json.loads((D/'NativeAudio.json').read_text())['cues'];check(all(x in now for x in old if x['cue'] not in ['gardenmusic','palacemusic']),'An unrelated sound binding changed')
for cue in now:
 files=[p for p in (D.parent/cue['resource']).parent.glob(Path(cue['resource']).name+'.*') if p.suffix in ['.wav','.ogg']];check(len(files)==1,'Missing or ambiguous audio '+cue['resource']);check('AudioImporter:' in Path(str(files[0])+'.meta').read_text(),'Wrong audio importer')
cues={x['cue']:x['resource'] for x in now};check(len({cues[c] for c in ['housemusic','gardenmusic','palacemusic','trial-victory','boss-victory']})==5,'Flute track is reused')
for rec in json.loads((R/'tools/awakening-playtest/audio-provenance.json').read_text()):
 file=next(p for p in (D.parent/rec['resource']).parent.glob(Path(rec['resource']).name+'.*') if p.suffix in ['.wav','.ogg']);check(hashlib.sha256(file.read_bytes()).hexdigest()==rec['outputSHA256'],'Audio provenance mismatch')
 if rec['cue'] in ['palacemusic','gardenmusic']:
  data=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(file),'-ac','2','-ar','32000','-f','f32le','-']),'<f4').reshape(-1,2);check(np.max(abs(data))<.8,'Music clip clips');step=data[0]-data[-1];expected=((data[1]-data[0])+(data[-1]-data[-2]))*.5;check(np.max(abs(step-expected))<.01,'Encoded loop has a discontinuous slope')
seen={}
for p in A.rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',p.read_text(),re.M)
 if m:check(m[1] not in seen,'Duplicate GUID '+str(p));seen[m[1]]=p
sys.path.insert(0,'/workspace/work/csharp-syntax');import tree_sitter,tree_sitter_c_sharp
parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_c_sharp.language()))
for p in A.rglob('*.cs'):check(not parser.parse(p.read_bytes()).root_node.has_error,'C# syntax '+str(p));check(Path(str(p)+'.meta').exists(),'Missing source metadata')
# The moved 1.2m pedestal is clear of the existing table/stand and futon.
sys.path.insert(0,str(R/'tools/spirit-charge-home/trailer'));from scene_data import World
world=World();lo=np.array([-39.1,-249.87,-18.0]);hi=np.array([-37.9,-249.32,-16.8])
for r in world.renderers():
 if r['lo'] is None or not any(k in r['name'] for k in ['home wooden weapon stand','sleep interaction futon']):continue
 check(not np.all((hi>=r['lo']) & (lo<=r['hi'])),'Moved pedestal overlaps existing furnishing')
report=dict(sourceChecks=n,base=BASE,originalModelsPaintAudioAndApprovedTendrilsPreserved=True,unityImportShaderCompilationAndPlaybackVerified=False,latestUnityFeedbackSource='aefd595771e933a3313ecb4170251764c94ab1e3',latestClips='All fourteen: frames_captured_coverage_incomplete; stale source cannot approve this patch')
(W/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Source assets, native audio boundaries and home placement verified; current Unity playback unavailable.')
