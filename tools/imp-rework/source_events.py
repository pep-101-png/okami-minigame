from pathlib import Path
import json,struct,sys,hashlib
S=Path('/workspace/work/full-asset-inspection');W=Path('/workspace/work/imp-rework');rows=[json.loads(x) for x in (S/'inventory.jsonl').read_text().splitlines()]
for pkg,clips in [('em00',['em00_082','em00_020','em00_032','em00_03a']),('em01',['em00_181']),('em02',['em00_150','em00_152','em00_154']),('em03',['em00_052']),('em04',['em00_194'])]:
 for c in clips:
  row=next((r for r in rows if r['package']==pkg and r['type']=='SEQ' and r['name']==c+'_0'),None)
  if not row:continue
  b=(S/row['cache']).read_bytes();channels=[]
  for i in range(4):
   off,n=struct.unpack_from('<HH',b,i*4);channels.append([struct.unpack_from('<HH',b,off+j*4) for j in range(n)])
  print(pkg,c,channels)
