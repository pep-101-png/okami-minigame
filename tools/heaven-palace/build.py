from pathlib import Path
import sys,json,shutil,copy,struct,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami'
sys.path[:0]=['/workspace/work/reference-repairs','/workspace/work/heaven-complete','/workspace/work/full-asset-inspection','/workspace/sunward-remaster/tools/playtest-followup'];import assets;from meta import meta;from components import components
# Rebuild the real original terrain with only 18 cm water depth.
p=ROOT/'tools/heaven-complete/build_assets.py';s=p.read_text().replace('depth=.85','depth=.18').replace('0.85m basins','0.18m shallow basins');p.write_text(s)
subprocess.run([sys.executable,str(p)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
def save(name,m,source):
 dest=D/name;dest.mkdir(exist_ok=True);(dest/'Model.json').write_text(json.dumps(m,separators=(',',':')))
 for t in m['textures']:
  if not t.get('vertexOnly'):shutil.copyfile(D/source/t['path'],dest/t['path'])
 for p in [dest,*dest.iterdir()]:
  if p.suffix!='.meta':meta(p)
# Complete native Thunder Edge crossguard variants are retained for the weapon driver.
m=json.load(open(D/'wp29/Model.json'));m['visibleGroups']=[1,2,3,4];(D/'wp29/Model.json').write_text(json.dumps(m,separators=(',',':')))
q=copy.deepcopy(m);q['visibleGroups']=[1,4];q['derivation']='Original WP29 with its genuine extended side pieces selected.';save('thunder-awakened',q,'wp29')
q=copy.deepcopy(m);q.pop('visibleGroups',None);q['parts']=[p for p in q['parts'] if p['name']=='Native-0-0'];q['derivation']='Original WP29 angular lightning geometry, selected intact for native thunder flashes.';save('thunder-lightning',q,'wp29')
# Actual cut stump without the two tall pole components.
m=json.load(open(D/'vt74/Model.json'));p=m['parts'][0];v=np.array(p['positions']).reshape(-1,3);keep=set(components(p)[0]);p['indices']=[int(i) for t in np.array(p['indices']).reshape(-1,3) if all(int(i) in keep for i in t) for i in t];used=sorted(set(p['indices']));mapping={i:j for j,i in enumerate(used)}
for key,dim in [('positions',3),('uv',2),('colors',4),('boneIndices',3),('weights',3)]:p[key]=np.array(p[key]).reshape(-1,dim)[used].ravel().tolist()
p['indices']=[mapping[i] for i in p['indices']];m['derivation']='Original broad cut stump; the two tall pole components omitted so the seat has a real flat top.';save('heaven-tea-seat',m,'vt74')
# A finished original timber tabletop and original timber legs replace the Go board.
if not(D/'dr0d/Model.json').exists():assets.export('dr0d',D/'dr0d')
for p in [D/'dr0d',*(D/'dr0d').iterdir()]:
 if p.suffix!='.meta':meta(p)
# Original Shiranui skin with only the recovered original sleeping motion.
m=json.load(open(D/'pl0d/Model.json'));save('palace-shiranui',m,'pl0d')
from pose_audit import bank
b=bank(ROOT/'Sunward-Unity/Assets/OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes');a,d,l=b['pl00_004'];dest=D/'palace-shiranui/Poses.bytes'
with dest.open('wb') as f:
 f.write(struct.pack('<4sIII',b'OPB1',1,a.shape[1],1));n=b'pl00_004';f.write(struct.pack('<I',len(n))+n+struct.pack('<IfI',len(a),d,1)+a.astype('<f4').tobytes())
meta(dest)
# Original recordings only: low resonant metallic core strike and Thunder Edge's own bank.
from scan import decrypt,inspect_sound
from repair_audio import render
rows=[]
for path,index,name,cue in [(Path('/workspace/work/playtest-repair/source-native/data_pc/se/core/core.ses'),13,'heaven-gong-strike','heaven-gong-strike'),(Path('/workspace/work/playtest-repair/source-native/data_pc/se/wp/wp29.ses'),1,'thunder-strike','thunder-strike'),(Path('/workspace/work/playtest-repair/source-native/data_pc/se/wp/wp29.ses'),3,'thunder-burst','thunder-burst')]:
 clear=decrypt(path.read_bytes());es=inspect_sound(clear)['ADX'];e=es[index];raw=clear[e['offset']:e['offset']+e['bytes']];dest=D/'NativeAudio'/(name+'.wav');info=render(raw,dest,cue);meta(dest);rows.append(dict(cue=cue,resource='Okami/NativeAudio/'+name,source=str(path),stream=index,conversion=info))
x=json.load(open(D/'NativeAudio.json'));x['cues']=[c for c in x['cues'] if c['cue'] not in [r['cue'] for r in rows]]+[dict(cue=r['cue'],resource=r['resource']) for r in rows];(D/'NativeAudio.json').write_text(json.dumps(x,indent=2)+'\n')
(ROOT/'tools/heaven-palace/audio-provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Built shallow ponds, original timber/seat, full Thunder Edge parts, native lightning, sleeping Shiranui and native sound derivatives')
