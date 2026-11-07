"""Compare the actual imported instrument against its decoded original archive."""
from pathlib import Path
import json,pickle,hashlib,subprocess,sys,numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/eighth-wonder');P=Path('/workspace/work/wp-inspection');j=json.loads((D/'wp28/Model.json').read_text());original=pickle.loads((P/'models.pkl').read_bytes())['wp28'];n=0
def check(b,s):
 global n;n+=1;assert b,s
before=json.loads(subprocess.check_output(['git','show','HEAD:'+str((D/'wp28/Model.json').relative_to(R))],cwd=R));check(j['parts']==before['parts'] and j['bones']==before['bones'],'Original vertex/pigment/skin streams modified')
check(j['visibleGroups']==[1,2,3,4],'Metal, hilt side or ink outline missing')
for part,source in zip(j['parts'],original['parts']):
 check(np.allclose(np.array(part['positions']).reshape(-1,3),source['p']*[-.075,.075,.075],atol=1e-6),'Original geometry changed')
 uv=source['uv'].copy();uv[:,1]=1-uv[:,1];check(np.array_equal(np.array(part['uv']).reshape(-1,2),uv),'Original atlas coordinates changed')
 check(part['texture']==source['texture'],'Wrong original texture reference')
 image=D/'wp28'/('Texture-'+str(part['texture'])+'.png');check(np.array_equal(np.asarray(Image.open(image).convert('RGBA')),np.asarray(Image.open(source['texturePNG']).convert('RGBA'))),'Recovered original paint differs')
 meta=Path(str(image)+'.meta').read_text();check('wrapU: 0' in meta and 'wrapV: 0' in meta,'Native repeating UVs are clamped')
records=json.loads((P/'inventory.json').read_text());clips={}
for suffix in ['520','521','522','523','524','525']:
 entries=[e for e in records if e['type']=='MOT' and e['name']=='pl00_'+suffix and e['package'] in ['wp25','wp28']];check(len(entries)==2 and len({e['sha256'] for e in entries})==1,'Eighth Wonder player attack differs from imported glaive attack');clips[suffix]=entries[0]['sha256']
for name in ['Poses.bytes','Texture-0.png','Texture-1.png']:
 p=D/'wp28'/name;raw=subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(R))],cwd=R);check(('oid sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()).encode() in raw if raw.startswith(b'version https://git-lfs') else raw==p.read_bytes(),'Original motion/paint rewritten')
sys.path.insert(0,'/workspace/work/csharp-syntax');import tree_sitter,tree_sitter_c_sharp
parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_c_sharp.language()))
for p in (R/'Sunward-Unity/Assets').rglob('*.cs'):check(not parser.parse(p.read_bytes()).root_node.has_error,'C# syntax '+str(p))
report=dict(originalComparisons=n,sourceModel=j['sourceSHA256'],normalVisibleGroups=j['visibleGroups'],excludedGroup0='White effect overlay; not the painted metal blade',playerAttackSourceHashes=clips,originalPaintAndMotionBytesUnchanged=True,unityPlayed=False)
(W/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Original model/atlas/attack sources inspected; source paint and motion bytes preserved. Unity playback unverified.')
