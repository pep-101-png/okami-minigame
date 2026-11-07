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
  c=clips[stream];raw=b[c['offset']:c['offset']+c['bytes']];target=out/(key+'.wav');dec=render(raw,target,key);guid(target);bindings.append(dict(cue=key,resource=resource));ledger.append(dict(cue=key,bank=owner,sourceBankSHA256=hashlib.sha256((W/'eb00-source.ses').read_bytes() if owner=='eb00' else (Path('/workspace/work/playtest-repair/source-native/data_pc/se/em')/(owner+'.ses')).read_bytes()).hexdigest(),sequenceSoundID=hex(id),cueIndex=idx,sampleIndex=sample,streamIndex=stream,sourceStreamSHA256=hashlib.sha256(raw).hexdigest(),outputSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),decoding=dec,pitchCentsRange=[struct.unpack('<h',struct.pack('<H',cue[j]))[0] for j in (12,13)],playbackPitch=2**((struct.unpack('<h',struct.pack('<H',cue[12]))[0]+struct.unpack('<h',struct.pack('<H',cue[13]))[0])/2400),assignment='Native SEQ sound ID -> matching SES cue -> sample record -> ADX stream; no guessed neighbouring stream'))
  exported[key]=True
 return key,round(cue[8]/127,5),2**((struct.unpack('<h',struct.pack('<H',cue[12]))[0]+struct.unpack('<h',struct.pack('<H',cue[13]))[0])/2400)
def events(pkg,clip,duration):
 row=next((x for x in rows if x['package']==pkg and x['type']=='SEQ' and x['name']==clip+'_0'),None);result=[]
 if row:
  b=(S/row['cache']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];off,n=struct.unpack_from('<HH',b,8)
  for i in range(n):
   frame,id=struct.unpack_from('<HH',b,off+i*4);t=(frame&0x7fff)/30
   if t>duration:continue
   if id>>8!=1:raise ValueError((pkg,clip,id))
   cue,gain,pitch=sound(pkg,id);result.append(dict(time=t,cue=cue,gain=gain,pitch=pitch))
 return result
# Original body masks from the first repair remain unchanged.
def action(id,clip,w,e,c,rate=1.35,kind='melee',windup=None,recover=None,aim=None):
 return dict(id=id,kind=kind,strike=clip,windup=windup or clip,recover=recover or clip,aim=aim,separate=windup is not None,windupEnd=w,strikeEnd=e,contact=c,rate=rate)
sets=[
 ('wisp','em00',[action('lute-leap','em00_082',.34,.68,.53),action('lute-strum','em00_083',.24,.83,44/113,1.5)]),
 ('reed','em01',[action('kite-sweep','em00_184',.30,.70,.55,1),action('kite-right','em00_18a',.28,.72,.5,1),action('kite-left','em00_18b',.28,.72,.5,1)]),
 ('ranged','em02',[action('cannon','em00_152',0,1,8/44,1.3,'cannon','em00_150','em00_154','em00_151'),action('kick-left','em00_155',.30,.7,37/69,1.3),action('kick-right','em00_156',.30,.7,37/69,1.3)]),
 ('heavy','em03',[action('flute-slam','em00_052',.34,.68,46/96),action('flute-thrust','em00_051',.25,.68,.42,1.1)]),
 ('elite','em04',[action('drum-kick','em00_194',.26,.65,35/90,1.5),action('drum-turn','em00_191',.45,.86,71/90,1.4)])]
profiles=[]
for role,pkg,actions in sets:
 old=json.loads((D/'ImpMotions.json').read_text())['profiles'];profile=next(p for p in old if p['resource']=='Okami/'+pkg)
 idle='em00_180' if role=='reed' else 'em00_000';walk='em00_188' if role=='reed' else 'em00_010';reaction='em00_188' if role=='reed' else 'em00_020';death='em00_182' if role=='reed' else 'em00_032'
 selected={idle,walk,reaction,death}
 for a in actions:selected.update(c for c in [a['strike'],a['windup'],a['recover'],a['aim']] if c)
 raw=(W/f'{pkg}-all.bytes').read_bytes();magic,ver,bones,count=struct.unpack_from('<4sIII',raw);offset=16;records=[]
 for i in range(count):
  start=offset;n=struct.unpack_from('<I',raw,offset)[0];offset+=4;name=raw[offset:offset+n].decode();offset+=n;samples=struct.unpack_from('<I',raw,offset)[0];offset+=12+samples*bones*40
  if name in selected:records.append(raw[start:offset])
 assert len(records)==len(selected);(D/pkg/'Poses.bytes').write_bytes(struct.pack('<4sIII',magic,ver,bones,len(records))+b''.join(records))
 roots={m['name']:m for m in json.loads((W/f'{pkg}-roots.json').read_text())};motions=[]
 for name in sorted(selected):
  m=roots[name];m['sounds']=events(pkg,name,m['duration']);motions.append(m)
 profile.update(actions=actions,reaction=reaction,defeat=death,motions=motions)
 if role=='ranged':
  fire,fg,fp=sound(pkg,0x1cf);impact,ig,ip=sound(pkg,0x1cb)
  profile['cannon']=dict(muzzle=[.78,-.05,.74],speed=9.5,gravity=2.8,radius=.24,splash=2.4,fireCue=fire,impactCue=impact,firePitch=fp,impactPitch=ip)
 profiles.append(profile)
 path=R/f'Sunward-Unity/Assets/Sunward/Generated/Enemy-{role}.prefab';text=path.read_text()
 for key,val in [('idle',idle),('walk',walk),('run',walk),('death',death)]:text=re.sub('^  '+key+': .*','  '+key+': '+val,text,flags=re.M)
 path.write_text(text)
# Whole original paintings: do not incorrectly crop single flames into 2x2 tiles.
extra=json.loads(Path('/workspace/work/playtest-repair/extra-inventory.json').read_text());from PIL import Image
art=[]
for name,source in [('CannonCore','fire_00'),('CannonFire','fire_15'),('CannonSmoke','smoke_00')]:
 row=next(r for r in extra if r['type']=='DDS' and r['name']==source);data=Path(row['cache']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];target=D/'Effects'/(name+'.png');Image.open(row['cache']).save(target)
 meta=Path(str(target)+'.meta');template=(D/'Effects/Flame.png.meta').read_text();key=hashlib.sha256(('OriginalOnly/'+str(target.relative_to(A))).encode()).hexdigest()[:32];meta.write_text(re.sub('guid: [0-9a-f]+','guid: '+key,template,count=1));art.append(dict(resource='Okami/Effects/'+name,original=source,sourceSHA256=row['sha256']))
(D/'ImpMotions.json').write_text(json.dumps(dict(profiles=profiles),separators=(',',':')))
bank=json.loads((D/'NativeAudio.json').read_text());bank['cues']=[c for c in bank['cues'] if not c['cue'].startswith('imp-')]+bindings;(D/'NativeAudio.json').write_text(json.dumps(bank,indent=2)+'\n')
# Retain already delivered recordings even when no longer bound, so cumulative
# Assets delivery never needs a deletion manifest.
(R/'tools/imp-kite-cannon/provenance.json').write_text(json.dumps(dict(audio=ledger,paint=art),indent=2)+'\n')
print('Installed kite-safe stances/reaction/defeat,',sum(len(p['actions']) for p in profiles),'native actions and original cannon paintings/sound cues')
