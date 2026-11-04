"""Paint a diagnostic from actual C# InkText page/glyph rectangles, not a Unity screenshot."""
from pathlib import Path
import json,argparse
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('layout',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/UI';glyphs={x['code']:x for x in json.loads((D/'MessageGlyphs.json').read_text())['glyphs']};atlas=Image.open(D/'MessageGlyphs.png').convert('RGBA');bubble=Image.open(D/'DialogueBubble.png').convert('RGBA');counts={}
for row in json.loads(a.layout.read_text()):
 sw,sh=row['screenWidth'],row['screenHeight'];w=min(1360,sw*.96);h=min(460,sh*.56);x=(sw-w)*.5;y=sh-h-25;out=Image.new('RGBA',(sw,sh),(90,112,103,255));out.alpha_composite(bubble.resize((round(w),round(h)),Image.Resampling.LANCZOS),(round(x),round(y)));chars=[c for c in row['text'] if c not in ' \n\r'];assert len(chars)==len(row['rects'])
 for c,r in zip(chars,row['rects']):
  g=glyphs.get(ord(c),glyphs[ord('?')]);im=atlas.crop((g['x'],g['y'],g['x']+g['width'],g['y']+g['height']));im=im.resize((max(1,round(r['width'])),max(1,round(r['height']))),Image.Resampling.LANCZOS);tint=Image.new('RGBA',im.size,(23,15,9,255));tint.putalpha(im.getchannel('A'));out.alpha_composite(tint,(round(row['bodyX']+r['x']),round(row['bodyY']+r['y'])))
 counts[sw]=counts.get(sw,0)+1;out.convert('RGB').save(a.out/f'dialogue-{sw}-page-{counts[sw]}.png')
print('Rendered',sum(counts.values()),'native dialogue page geometry diagnostics; not Unity screenshots')
