"""Correct audio metadata without changing original recordings or Unity GUIDs."""
from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';sample=(A/'OkamiRemaster/Original/Resources/Okami/NativeAudio/player-shiranui-layered-bark.wav.meta').read_text();ledger=R/'tools/village-complete/audio-import-repairs.json';rows=json.loads(ledger.read_text()) if ledger.exists() else []
for p in A.rglob('*'):
 if p.suffix.lower() not in ['.wav','.ogg','.mp3','.aif','.aiff']:continue
 meta=Path(str(p)+'.meta')
 if not meta.exists():continue
 text=meta.read_text()
 if 'AudioImporter:' in text:continue
 guid=re.search(r'^guid: ([0-9a-f]{32})$',text,re.M)[1];meta.write_text(re.sub(r'^guid: [0-9a-f]{32}$','guid: '+guid,sample,flags=re.M));name=str(p.relative_to(R));rows.append(name) if name not in rows else None
(R/'tools/village-complete/audio-import-repairs.json').write_text(json.dumps(rows,indent=2)+'\n');print('Corrected',len(rows),'audio importers, preserving every GUID and waveform')
