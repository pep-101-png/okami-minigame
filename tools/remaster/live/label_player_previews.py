"""Permanently label diagnostic renders; never present them as Unity captures."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).with_name('previews');meta=root/'native-preview-metadata.json';records=json.loads(meta.read_text())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for record in records:
    path=root/('native-'+record['label']+'.png');image=Image.open(path).convert('RGB');out=Image.new('RGB',(image.width,image.height+74),'#f4eddf');out.paste(image,(0,74));draw=ImageDraw.Draw(out)
    draw.text((16,9),'BLENDER POSE CHECK — NOT UNITY / NOT A RUNNING GAME SCREENSHOT',fill='#312920',font=font)
    draw.text((16,40),record['label']+' · original '+record['source']+' · sampled port poses at 5%, 38%, 75%',fill='#312920',font=font)
    target=path.with_suffix('.jpg');out.save(target,quality=92);record['preview']=target.name;record['sha256']=hashlib.sha256(target.read_bytes()).hexdigest();record['labelled']=True
    source=Path(__file__).resolve().parents[3]/'Sunward-Unity/Assets/OkamiRemaster/Player/Resources/NativePlayer'/record['source'].split('_')[0]
    record['poseBankSHA256']=hashlib.sha256((source/'Poses.bytes').read_bytes()).hexdigest();record['modelSHA256']=hashlib.sha256((source/'Model.json').read_bytes()).hexdigest()
meta.write_text(json.dumps(records,indent=2)+'\n')
print('Labelled',len(records),'Blender-only native pose checks')
