"""Decode the user's numbered original-bank selections, using player subsong order."""
from pathlib import Path
import json,sys,struct,hashlib,re
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/native-power-update');SRC=Path('/workspace/work/playtest-repair/source-native/data_pc')
sys.path[:0]=['/workspace/work/full-asset-inspection','/workspace/sunward-remaster/tools/playtest-followup','/workspace/work/reference-repairs'];from scan import decrypt,inspect_sound;from repair_audio import render;from meta import meta
out=D/'SelectedAudio';out.mkdir(exist_ok=True);meta(out);records=[];new=[]
def stream(bank,number):
 index=number-1;p=SRC/'se'/(bank+'.afs2')
 if bank=='bgm00':p=SRC/'bgm/bgm00.afs2'
 if bank=='ev/evbc':p=W/'se/ev/evbc.afs2'
 if p.exists():
  b=p.read_bytes();b=decrypt(b) if b[:4]!=b'AFS2' else b;n=struct.unpack_from('<I',b,8)[0]
  if index<n:
   off=16+n*b[6];alignment=struct.unpack_from('<H',b,12)[0];ofs=[int.from_bytes(b[off+i*b[5]:off+(i+1)*b[5]],'little') for i in range(n+1)];start=(ofs[index]+alignment-1)//alignment*alignment;raw=b[start:ofs[index+1]];return raw,str(p),index
 p=SRC/'se'/(bank+'.ses');b=decrypt(p.read_bytes());e=inspect_sound(b)['ADX'][index];return b[e['offset']:e['offset']+e['bytes']],str(p),index
selections=[('core/core',16,'palacemusic',True),('core/core',35,'menu-open',False),('pl/pl00',14,'ammy-swing',False),('pl/pl00',15,'ammy-swing',False),('pl/pl00',16,'ammy-swing',False),('pl/pl00',27,'pond-sit',False),('bgm00',27,'festivalrace',True),('ev/evbc',5,'full-power',False)]
for bank,number,cue,loop in selections:
 raw,source,index=stream(bank,number);name=bank.replace('/','-')+'-subsong-'+str(number);target=out/(name+('.ogg' if loop else '.wav'));info=render(raw,target,cue,loop);metaText=(D/'NativeAudio/player-shiranui-layered-bark.wav.meta').read_text();guid=hashlib.sha256(('OriginalOnly/'+str(target.relative_to(A))).encode()).hexdigest()[:32];metaText=re.sub(r'^guid: \w+','guid: '+guid,metaText,flags=re.M);Path(str(target)+'.meta').write_text(metaText);resource='Okami/SelectedAudio/'+name;new.append(dict(cue=cue,resource=resource));records.append(dict(cue=cue,userLabel=bank+' #'+str(number),source=source,subsong=number,arrayIndex=index,sourceSHA256=hashlib.sha256(raw).hexdigest(),outputSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),resource=resource,decoding=info));print(cue,'subsong',number,'duration',info['seconds'])
p=D/'NativeAudio.json';j=json.loads(p.read_text());selected={e['cue'] for e in new};j['cues']=[e for e in j['cues'] if e['cue'] not in selected];j['cues']+=new;p.write_text(json.dumps(j,indent=2)+'\n');(R/'tools/full-power-update/audio-provenance.json').write_text(json.dumps(dict(numbering='Standard player subsong numbering: #1 is first entry. Original bank/table order is preserved. User could not confirm numbering by audition.',selections=records),indent=2)+'\n')
