"""Regression for removing the unintended trailer feature and its CS1955 path."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[2]/'Sunward-Unity/Assets'
for file in root.rglob('*.cs'):
 text=file.read_text()
 assert not re.search(r'\.wasPressedThisFrame\s*\(',text),'Button property called as a method: '+str(file)
ui=(root/'Sunward/Scripts/ScrollUI.cs').read_text()
assert 'TrailerPlayback' not in ui and 'TRAILER PREVIEW' not in ui
assert 'class TrailerPlayback' not in (root/'Sunward/Automation/TrailerPlayback.cs').read_text()
assert 'MenuItem' not in (root/'Editor/SunwardTrailerMenu.cs').read_text()
assert 'PreviewOnly' not in (root/'Sunward/Scripts/SaveStore.cs').read_text()
print('PASS unintended trailer menu/runtime/input path removed; gameplay save behavior restored; no button-property calls remain.')
