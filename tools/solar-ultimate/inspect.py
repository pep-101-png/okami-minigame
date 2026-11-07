from pathlib import Path
import sys,json,numpy as np,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/solar-ultimate');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(480,360);folder=W/'es3a';folder.mkdir(exist_ok=True)
for p in (nr.D/'es3a').iterdir():
 if p.suffix in ['.json','.png']:shutil.copyfile(p,folder/p.name)
shutil.copyfile(nr.A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes',folder/'Poses.bytes');body=nr.Native(r,str(folder));body.visible=True;r.actors=[body]
sheet=Image.new('RGB',(1920,1080));draw=ImageDraw.Draw(sheet)
for row,clip in enumerate(['pl00_02b','pl00_02c','pl00_017']):
 for col,phase in enumerate([0,.25,.5,.75]):
  t=body.bank[clip][1]*phase;body.update(clip,t,nr.matrix(scale=1.2),False);r.begin(np.array([4,2.8,5]),[0,1,0],0,0,'village',45);r.geometry();im=Image.frombytes('RGB',(480,360),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);p=(col*480,row*360);sheet.paste(im,p);draw.text((p[0]+6,p[1]+6),clip+' '+str(phase),fill='black')
sheet.save(W/'curl-inspection.jpg')
rows=json.load(open('/workspace/work/playtest-repair/extra-inventory.json'));names=['bafooon','sand_01','rcok_gray','kemuri_01','fire_02','circleLight','hanabi_00','kami_fubuki01'];sheet=Image.new('RGB',(1024,512),'#444');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(names):
 row=next(x for x in rows if x['name']==name);im=Image.open(row['cache']).convert('RGBA');im.thumbnail((250,225));p=(i%4*256,i//4*256);sheet.paste(im,p,im);draw.text((p[0],p[1]+230),name,fill='white')
sheet.save(W/'paint-inspection.jpg')
