from pathlib import Path
import sys,json,numpy as np,struct
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
from PIL import Image,ImageDraw
W=Path('/workspace/work/imp-kite-cannon');C=Path('/workspace/work/imp-rework');nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(480,400)
sets=[('em01',['180','188','189','184','18a','18b','182']),('em02',['151','152','154','155','156','160','161','163','164','165','166','167','168','16e','170'])]
for pkg,suffixes in sets:
 n=nr.Native(r,'Okami/'+pkg,.8,[0,.18,0]);n.bank=nr.pose_bank(C/(pkg+'-all.bytes'));n.groups={1,2,3,6} if pkg=='em02' else {1,2,3};n.visible=True;r.actors=[n]
 for start in range(0,len(suffixes),7):
  listing=suffixes[start:start+7];sheet=Image.new('RGB',(480*6,400*len(listing)),'white');d=ImageDraw.Draw(sheet)
  for row,suffix in enumerate(listing):
   clip='em00_'+suffix
   for col,phase in enumerate([0,.18,.36,.54,.72,.999]):
    n.update(clip,n.bank[clip][1]*phase,loop=False);r.begin(np.array([3,2.7,4]),[0,1.1,0],0,0,'village',43);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,row*400));d.text((col*480+5,row*400+5),f'{clip} {phase}',fill='black')
  sheet.resize((1800,int(sheet.height*1800/sheet.width))).save(W/f'{pkg}-{start}.jpg')
 n.visible=False
S=Path('/workspace/work/full-asset-inspection');rows=[json.loads(x) for x in (S/'inventory.jsonl').read_text().splitlines()]
for pkg,ss in [('em00',['082','083','087']),('em03',['051','052','058']),('em04',['190','191','193','194']),('em02',['152','155','156','160','161','164','165','166','167','168'])]:
 for suffix in ss:
  name='em00_'+suffix;m=next((x for x in rows if x['package']==pkg and x['name']==name and x['type']=='MOT'),None);q=next((x for x in rows if x['package']==pkg and x['name']==name+'_0' and x['type']=='SEQ'),None)
  if q:
   b=(S/q['cache']).read_bytes();channels=[]
   for i in [1,2]:
    off,num=struct.unpack_from('<HH',b,i*4);channels.append([struct.unpack_from('<HH',b,off+j*4) for j in range(num)])
   print(pkg,name,m.get('frames') if m else None,channels)
