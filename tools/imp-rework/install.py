"""Install inspected original imp meshes, native motion and SEQ-to-SES audio bindings."""
from pathlib import Path
import json,struct,hashlib,sys,re
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';S=Path('/workspace/work/full-asset-inspection');W=Path('/workspace/work/imp-rework')
sys.path.insert(0,str(S));from scan import inspect_sound
sys.path.insert(0,'/workspace/sunward-remaster/tools/playtest-followup');from repair_audio import render
rows=[json.loads(x) for x in (S/'inventory.jsonl').read_text().splitlines()];out=D/'ImpAudio';out.mkdir(exist_ok=True)
ledger=[];bindings=[];exported={}
def guid(p):
 meta=Path(str(p)+'.meta')
 if meta.exists():return
 key=hashlib.sha256(('OriginalOnly/'+str(p.relative_to(A))).encode()).hexdigest()[:32]
 if p.suffix=='.wav':s=(D/'NativeAudio/enemy0-0.wav.meta').read_text();s=re.sub('guid: [0-9a-f]+','guid: '+key,s,count=1)
 else:s='fileFormatVersion: 2\nguid: '+key+'\n'+('folderAsset: yes\nDefaultImporter:\n' if p.is_dir() else 'TextScriptImporter:\n')+'  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n'
 meta.write_text(s)
def sound(pkg,id):
 assert id>>8==1
 idx=id&255;owner=pkg;b=(W/(pkg+'.ses')).read_bytes();base=struct.unpack_from('<I',b,16)[0];count=struct.unpack_from('<I',b,base)[0]
 if idx>=count or struct.unpack_from('<I',b,base+32+idx*48+12)[0]==0x80000000:
  owner='eb00';b=(W/'eb00.ses').read_bytes();base=struct.unpack_from('<I',b,16)[0];count=struct.unpack_from('<I',b,base)[0]
 if idx>=count:raise ValueError((pkg,id))
 cue=struct.unpack_from('<24H',b,base+32+idx*48);assert cue[7]!=0x8000
 sample=cue[20];table=struct.unpack_from('<I',b,24)[0];n,off=struct.unpack_from('<II',b,table);assert sample<n
 stream=struct.unpack_from('<H',b,table+off+sample*32+2)[0];clips=inspect_sound(b)['ADX'];assert stream<len(clips)
 key=f'imp-{owner}-{idx}';resource='Okami/ImpAudio/'+key
 if key not in exported:
  c=clips[stream];raw=b[c['offset']:c['offset']+c['bytes']];target=out/(key+'.wav');dec=render(raw,target,key);guid(target);bindings.append(dict(cue=key,resource=resource));ledger.append(dict(cue=key,bank=owner,sourceBankSHA256=hashlib.sha256((W/'eb00-source.ses').read_bytes() if owner=='eb00' else (Path('/workspace/work/playtest-repair/source-native/data_pc/se/em')/(owner+'.ses')).read_bytes()).hexdigest(),sequenceSoundID=hex(id),cueIndex=idx,sampleIndex=sample,streamIndex=stream,sourceStreamSHA256=hashlib.sha256(raw).hexdigest(),outputSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),decoding=dec,assignment='Native SEQ sound ID -> matching SES cue -> sample record -> ADX stream; no guessed neighbouring stream'))
  exported[key]=True
 return key,round(cue[8]/127,5)
def events(pkg,clip,duration):
 row=next((x for x in rows if x['package']==pkg and x['type']=='SEQ' and x['name']==clip+'_0'),None);result=[]
 if row:
  b=(S/row['cache']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];off,n=struct.unpack_from('<HH',b,8)
  for i in range(n):
   frame,id=struct.unpack_from('<HH',b,off+i*4);t=(frame&0x7fff)/30
   if t>duration:continue
   if id>>8!=1:raise ValueError((pkg,clip,id))
   cue,gain=sound(pkg,id);result.append(dict(time=t,cue=cue,gain=gain))
 return result
specs=[('wisp','em00','em00_082',.34,.68,.53,1.35),('reed','em01','em00_184',.30,.70,.55,1.0),('ranged','em02','em00_152',0,1,8/44,1.3),('heavy','em03','em00_052',.34,.68,46/96,1.35),('elite','em04','em00_194',.26,.65,35/90,1.5)]
profiles=[]
for role,pkg,attack,wind,finish,contact,rate in specs:
 folder=D/pkg;model=json.loads((folder/'Model.json').read_text());model['visibleGroups']=[1,2,3,6] if pkg=='em02' else [1,2,3];(folder/'Model.json').write_text(json.dumps(model,separators=(',',':')))
 selected=['em00_000','em00_010','em00_020','em00_032',attack]+(['em00_150','em00_154'] if role=='ranged' else [])
 raw=(W/f'{pkg}-all.bytes').read_bytes();magic,ver,bones,count=struct.unpack_from('<4sIII',raw);offset=16;records=[]
 for i in range(count):
  a=offset;length=struct.unpack_from('<I',raw,offset)[0];offset+=4;name=raw[offset:offset+length].decode();offset+=length;samples=struct.unpack_from('<I',raw,offset)[0];offset+=12+samples*bones*40
  if name in selected:records.append(raw[a:offset])
 assert len(records)==len(selected);(folder/'Poses.bytes').write_bytes(struct.pack('<4sIII',magic,ver,bones,len(records))+b''.join(records))
 roots={m['name']:m for m in json.loads((W/f'{pkg}-roots.json').read_text())};motions=[]
 for name in selected:
  m=roots[name];m['sounds']=events(pkg,name,m['duration']);motions.append(m)
 profile=dict(resource='Okami/'+pkg,attack=attack,windup='em00_150' if role=='ranged' else attack,recover='em00_154' if role=='ranged' else attack,separate=role=='ranged',windupEnd=wind,strikeEnd=finish,contact=contact,rate=rate,walkDistance=abs(roots['em00_010']['rootXZ'][-1]-roots['em00_010']['rootXZ'][1]),motions=motions);profiles.append(profile)
 text=(R/f'Sunward-Unity/Assets/Sunward/Generated/Enemy-{role}.prefab').read_text();text=text.replace('  strike: em00_181','  strike: em00_184').replace('  windup: em00_181','  windup: em00_184').replace('  recover: em00_181','  recover: em00_184')
 text=text.replace('  run: em00_012','  run: em00_010').replace('  death: em00_040','  death: em00_032')
 # Lowest animated foot over a full walk cycle plus a small soil clearance.
 scales={'wisp':.8612828629880562,'reed':.5126863411293356,'ranged':.8223172658957211,'heavy':.6523764948162111,'elite':.8097522785162592};feet={'wisp':.1806,'reed':.1806,'ranged':.2156,'heavy':.1789,'elite':.1898};y=feet[role]*scales[role]+.012
 text=re.sub(r'(  modelOffset: \{x: [^,]+, y: )[^,]+',lambda m:m[1]+str(round(y,6)),text)
 (R/f'Sunward-Unity/Assets/Sunward/Generated/Enemy-{role}.prefab').write_text(text)
for stale in out.glob('*.wav'):
 if stale.stem not in exported:stale.unlink();Path(str(stale)+'.meta').unlink(missing_ok=True)
(D/'ImpMotions.json').write_text(json.dumps(dict(profiles=profiles),separators=(',',':')));guid(D/'ImpMotions.json');guid(out)
bank=json.loads((D/'NativeAudio.json').read_text());bank['cues']=[c for c in bank['cues'] if not c['cue'].startswith('imp-')]+bindings;(D/'NativeAudio.json').write_text(json.dumps(bank,indent=2)+'\n')
(R/'tools/imp-rework/audio-provenance.json').write_text(json.dumps(ledger,indent=2)+'\n');print('Installed full articulated bodies, native vertical leaps, timelines and',len(bindings),'SEQ-resolved sound cues')
