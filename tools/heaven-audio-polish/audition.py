"""Original-only listening comparison, outside Assets; never bind by a guessed number."""
from pathlib import Path
import sys,json,struct,hashlib,subprocess,shutil,html,zipfile
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/heaven-audio-polish/audition');W.mkdir(parents=True,exist_ok=True);S=Path('/workspace/work/playtest-repair/source-native/data_pc')
sys.path[:0]=['/workspace/work/full-asset-inspection','/workspace/sunward-remaster/tools/playtest-followup'];from scan import decrypt,inspect_sound;from repair_audio import render

def extract(bank,index):
 p=S/('bgm/bgm00.afs2' if bank=='bgm00' else 'se/'+bank+'.afs2')
 if bank=='ev/evbc':p=Path('/workspace/work/native-power-update/se/ev/evbc.afs2')
 if p.exists():
  b=p.read_bytes();b=decrypt(b) if b[:4]!=b'AFS2' else b;n=struct.unpack_from('<I',b,8)[0]
  if index<n:
   off=16+n*b[6];alignment=struct.unpack_from('<H',b,12)[0];offsets=[int.from_bytes(b[off+i*b[5]:off+(i+1)*b[5]],'little') for i in range(n+1)];start=(offsets[index]+alignment-1)//alignment*alignment;return b[start:offsets[index+1]],str(p)
 p=S/'se'/(bank+'.ses');b=decrypt(p.read_bytes());e=inspect_sound(b)['ADX'][index];return b[e['offset']:e['offset']+e['bytes']],str(p)

selections=[('Shiranui room','core/core',16,'palacemusic',True),('Menu opening','core/core',35,'menu-open',False),('Ammy swing A','pl/pl00',14,'ammy-swing',False),('Ammy swing B','pl/pl00',15,'ammy-swing',False),('Ammy swing C','pl/pl00',16,'ammy-swing',False),('Pond sitting','pl/pl00',27,'pond-sit',False),('Festival race','bgm00',27,'festivalrace',True),('Third-form power-up','ev/evbc',5,'full-power',False)]
bind=json.loads((D/'NativeAudio.json').read_text())['cues'];old=json.loads((R/'tools/full-power-update/audio-provenance.json').read_text())['selections'];records=[]
for i,(label,bank,index,cue,music) in enumerate(selections):
 stem=f'{i+1:02d}';current=next(x for x in old if x['cue']==cue and x['subsong']==index);currentpath=next(p for p in (D/'SelectedAudio').glob(Path(current['resource']).name+'.*') if p.suffix in ['.wav','.ogg']);a=W/(stem+'-installed.mp3');subprocess.run(['ffmpeg','-v','error','-y','-i',str(currentpath),'-t','18','-c:a','libmp3lame','-q:a','3',str(a)],check=True)
 raw,source=extract(bank,index);target=W/(stem+'-alternative'+('.ogg' if music else '.wav'));info=render(raw,target,cue,music);b=W/(stem+'-alternative.mp3');subprocess.run(['ffmpeg','-v','error','-y','-i',str(target),'-t','18','-c:a','libmp3lame','-q:a','3',str(b)],check=True);records.append(dict(label=label,installed=a.name,alternative=b.name,alternativeSource=source,zeroBasedIndex=index,sourceSHA256=hashlib.sha256(raw).hexdigest(),duration=info['seconds'],note='A different original entry for listening, NOT an identified replacement; not assigned in game'));print(label,info['seconds'])
for label,name in [('Existing bark mix','player-shiranui-layered-bark'),('Lightning layer on Thunder Edge bark','thunder-strike')]:
 target=W/(name+'.mp3');subprocess.run(['ffmpeg','-v','error','-y','-i',str(D/'NativeAudio'/(name+'.wav')),'-c:a','libmp3lame','-q:a','3',str(target)],check=True);records.append(dict(label=label,installed=target.name,note='Exact currently installed original recording; isolated from its other game layers'))
body='''<!doctype html><meta charset="utf-8"><title>Sunward original audio comparison</title><style>body{background:#eee7d5;color:#241c16;font:18px system-ui;max-width:850px;margin:40px auto;padding:20px}section{border-top:1px solid #a58f72;padding:20px 0}audio{display:block;width:100%;margin:10px 0}small{color:#69533f}</style><h1>Choose by ear</h1><p>These previews use the exact original game recordings. The alternatives test the neighbouring archive entry; they are not confirmed replacements and have not been assigned in the game. Music previews last up to 18 seconds.</p><p>Tell me the section number and whether you prefer Installed or Alternative. If neither fits, say neither. The final two sections isolate the bark and its lightning layer.</p>'''
for i,r in enumerate(records):
 body+=f'<section><h2>{i+1}. {html.escape(r["label"])}</h2><b>Installed</b><audio controls preload="none" src="{r["installed"]}"></audio>'
 if 'alternative' in r:body+=f'<b>Alternative</b><audio controls preload="none" src="{r["alternative"]}"></audio><small>Original {html.escape(Path(r["alternativeSource"]).name)}, raw index {r["zeroBasedIndex"]}; identity unconfirmed.</small>'
 body+='</section>'
(W/'Open-Audio-Comparison.html').write_text(body);(W/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
with zipfile.ZipFile(W.parent/'Sunward-Original-Audio-Comparison.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in W.iterdir():
  if p.suffix in ['.mp3','.html','.json']:z.write(p,p.name)
