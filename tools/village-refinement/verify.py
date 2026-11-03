"""Portable native-content contracts. No Unity play or audio listening claim."""
from pathlib import Path
import json,hashlib,sys,re,numpy as np
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';RES=A/'OkamiRemaster/Original/Resources/Okami';sys.path.insert(0,str(ROOT/'tools/real-door-street-repairs'));import scene_data as d
from verify import bank
# Importing the established source-bank parser also runs its existing contracts.
checks=0
def check(v,why):
 global checks
 checks+=1;assert v,why
voices=json.loads(Path(__file__).with_name('voice-provenance.json').read_text());check(len(voices)==56,'Expected eight complete seven-syllable voice families')
for v in voices:
 check(v['sourceBundle']==v['character']+'v','General action SND substituted for voice family');check(v['conversion']['seconds']<.8,'Long action noise in dialogue family');check(v['conversion']['output']['clippedFraction']==0,'Clipped dialogue derivative')
 p=RES/'NativeAudio'/(v['character']+'-voice-'+str(v['sourceClip'])+'.wav');check(hashlib.sha256(p.read_bytes()).hexdigest()==v['outputSHA256'],'Voice derivative changed without provenance')
manifest=json.loads((RES/'NativeAudio.json').read_text())['cues'];check([v['resource'] for v in manifest if v['cue']=='bark']==['Okami/NativeAudio/player-pl00-41-bark'],'Bark differs from user-selected PL00-41')
for p in ['hm00','hm01','hm05','hm09','hm0f','hm29','hm44','hm68']:check(sum(v['cue']=='voice-'+p for v in manifest)==7,'Missing native voice family '+p)
font=json.loads((RES/'UI/MessageGlyphs.json').read_text());glyphs={g['code']:g for g in font['glyphs']}
for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,?!+:-':
 check(ord(c) in glyphs,'Original glyph mapping missing '+c);g=glyphs[ord(c)];check(0<=g['x']<g['x']+g['width']<=font['width'] and 0<=g['y']<g['y']+g['height']<=font['height'],'Glyph rectangle outside original atlas')
for n in ['DialogueBubble','MessageGlyphs','TitlePainting','TitleLogo','MenuPaper','HintInk']:check((RES/'UI'/(n+'.png')).exists(),'Missing original UI art '+n)
for n in ['an05','an22','an25']:
 m=json.loads((RES/n/'Model.json').read_text());poses=bank(RES/n/'Poses.bytes');check(poses['an18_011'][0].shape[1]==len(m['bones'])+1,'Puppy motion is on a different skeleton')
poses=bank(RES/'spa-hm16/Poses.bytes');check(np.ptp(poses['hm05_001'][0][:,6:12,3:7],axis=0).max()>.03,'Spa guest still uses a static idle layer')
m=json.loads((RES/'farm-canopy/Model.json').read_text());check(len(m['parts'])==1,'Detached laundry posts leaked into farm canopy');v=np.array(m['parts'][0]['positions']).reshape(-1,3);check(abs(v[:,1].min())<.001 and np.linalg.norm((v.min(0)+v.max(0))[[0,2]])<.001,'Native canopy still carries an off-map source origin')
m=json.loads((RES/'farm-earth/Model.json').read_text());source=json.loads((RES/'vt28/Model.json').read_text());check(m['parts']==source['parts'],'Earth mound geometry fabricated rather than converted from original mesh')
w=d.World();scene=w.scene
for i,b in scene.blocks.items():
 if scene.kind(i)==1 and 'Farm-soil-bed-' in scene.name(i):check('m_IsActive: 0' in b,'Old flat rectangular crop boards remain visible')
for n in ['VillagePresentation','InkText','SpaRest','BrushPatterns','CherryBomb']:
 p=A/'OkamiRemaster/Original/Scripts'/(n+'.cs');check(p.exists() and Path(str(p)+'.meta').exists(),'Missing runtime script/meta '+n)
print('PASS',checks,'voice-family/glyph/native-skin/motion/farm-source contracts; not Unity play or listening')
