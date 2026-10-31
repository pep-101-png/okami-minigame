"""Bind each instrument to its own original SES, with explicit provisional event indices."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/playtest-repair'));import export_audio as original
for i in range(0x20,0x2f):
 name='wp'+format(i,'02x');p=original.WORK/('source-native/data_pc/se/wp/'+name+'.ses');raw=p.read_bytes();data=original.decrypt(raw);streams=original.inspect_sound(data)['ADX'];assert streams
 # No guessed core jingle or unrelated glaive bank for the other families.
 for heavy,index in [(False,0),(True,2 if len(streams)>2 else len(streams)-1)]:
  cue='weapon-'+name+('-heavy' if heavy else '');r=streams[index];assert r['seconds']<=3
  original.convert(cue,data[r['offset']:r['offset']+r['bytes']],'data_pc/se/wp/'+name+'.ses',index)
  original.records[-1].update(sourceBankSHA256=hashlib.sha256(raw).hexdigest(),assignment='Own original instrument SES bank. Source waveform, decrypted/attenuated only. Exact original attack-event index dispatch is not reconstructed; audible acceptance pending.')
p=original.RES/'NativeAudio.json';d=json.loads(p.read_text());d['cues']=[c for c in d['cues'] if not c['cue'].startswith('weapon-')]+original.cues;p.write_text(json.dumps(d,indent=2)+'\n');Path(__file__).with_name('weapon-audio-sources.json').write_text(json.dumps(original.records,indent=2)+'\n');print('Own-bank weapon sound bindings',len(original.records))
