from pathlib import Path
import sys,json,io,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/village-complete');sys.path[:0]=['/workspace/work/full-asset-inspection','/workspace/work/reference-repairs'];from scan import decrypt,container;from meta import meta
src=Path('/workspace/work/playtest-repair/source-native/data_pc/etc/core.dat');data=decrypt(src.read_bytes());c=container(data)[4];eff=data[c[3]:c[4]];c=container(eff)[0];tbl=eff[c[3]:c[4]];records=[]
choose={'taiyou00':'OriginalSun','moon_gekko':'OriginalMoon','inazuma_00':'OriginalLightning','kaninari4p_2':'OriginalThunderSheet','biri_00':'OriginalElectricity','kanji_kami':'OriginalGodSeal','white_ring':'OriginalWhiteRing'}
images=[]
for index,typ,name,start,end in container(tbl):
 if name not in choose:continue
 raw=tbl[start:end];im=Image.open(io.BytesIO(raw)).convert('RGBA');p=D/'Effects'/(choose[name]+'.png');im.save(p);meta(p);records.append(dict(resource='Okami/Effects/'+choose[name],source='data_pc/etc/core.dat/coreEff/coretex/'+name,index=index,sha256=hashlib.sha256(raw).hexdigest(),size=im.size));images.append((name,im))
god=Image.open(D/'Effects/OriginalGodSeal.png').convert('RGBA');tw,th=god.width//4,god.height//4;seal=god.crop((2*tw,3*th,3*tw,4*th));p=D/'Effects/OriginalSaveSeal.png';seal.save(p);meta(p);records.append(dict(resource='Okami/Effects/OriginalSaveSeal',source='data_pc/etc/core.dat/coreEff/coretex/kanji_kami',cropColumn=2,cropRow=3,operation='Intact original celestial glyph crop, no repainting'))
out=Image.new('RGB',(1400,((len(images)+3)//4)*380),'#807764');draw=ImageDraw.Draw(out)
for i,(n,im) in enumerate(images):
 im.thumbnail((345,345));x=i%4*350;y=i//4*380;out.paste(im,(x,y+30),im);draw.text((x+3,y+3),n,fill='white')
out.save(W/'core-paint.jpg');(R/'tools/village-complete/core-provenance.json').write_text(json.dumps(records,indent=2)+'\n')
print('Recovered',len(records),'identified original core effect paintings')
