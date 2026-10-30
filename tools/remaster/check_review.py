#!/usr/bin/env python3
"""Run actual Windflower integrity checks and verify retained original source bytes.
These checks do not launch or compile Unity. Research/reference assets are outside Assets.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
subprocess.run([sys.executable,str(ROOT/'tools/remaster/live/check_windflower.py')],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(ROOT/'tools/remaster/live/check_player.py')],cwd=ROOT,check=True)
source=ROOT/'tools/remaster/reference/NativeSources'
index=json.loads((source/'motion-source-index.json').read_text())
for item in index['motions']:
 assert hashlib.sha256((source/item['path']).read_bytes()).hexdigest()==item['sha256']
for item in json.loads((source/'original-component-index.json').read_text()):
 assert hashlib.sha256((source/item['path']).read_bytes()).hexdigest()==item['sha256']
assert len(index['motions'])==165
assert not list((ROOT/'Sunward-Unity/Assets/OkamiRemaster').rglob('VillageDemo.unity'))
print('Actual Windflower checks passed; original 165 motion payloads and Solar Flare source records retained. Unity compilation/play verification remains pending.')
