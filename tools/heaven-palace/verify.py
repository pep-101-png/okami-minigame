"""Geometry/source audits for the user's heaven and Thunder Edge repair list; not Unity playback."""
from pathlib import Path
import sys,json,hashlib,subprocess,re
import numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';P=A/'OkamiRemaster/Original/Scripts';W=Path('/workspace/work/heaven-palace');checks=0
sys.path[:0]=[str(R/'tools/heaven-qol'),'/workspace/sunward-remaster/tools/playtest-followup',str(R/'tools/spirit-charge-home/trailer')];import geometry as g;from pose_audit import bank;from asset_geometry import rotation

def check(v,msg):
 global checks
 checks+=1;assert v,msg
l=json.loads((D/'CelestialGarden.json').read_text())
for pool in l['ponds']:
 x,z=pool['position']['x'],pool['position']['z'];check(abs(pool['position']['y']-g.height(x,z)-.45)<1e-5,'Pond is still deeper than a shallow sitting pool');check(pool['depth']==.45,'Old deep-water metadata remains')
s=(A/'Sunward/Scripts/WolfMotor.cs').read_text();check('heavenDepth>.65f' not in s and '!Sunward.Remaster.HeavenlyGarden.Inside(transform.position)' in s,'Heaven still triggers swimming')
s=(P/'HeavenlyGarden.Features.cs').read_text();check('river-waterfall' not in s and '"vt2a"' not in s,'Detached waterfall / pointed rocks remain');check('World("heaven-bird"' not in s,'Repeating bird voice remains');check('World("heaven-gong-strike"' in s and 'World("heaven-gong"' in s,'Gong magic or new resonant strike missing');check('"vt9a"' not in s and '"dr0d"' in s,'Go board still used as tea table');check('side*.55f,.615f,0' in s and 'side<0?90:270' in s,'Two correctly oriented tea settings missing');check('seat+Vector3.up*.25f' in s and 'new Vector3(.9f,.27f,.9f)' in s,'Tea seating clearance wrong');check('BeginCinematic(false)' in s and 'Quaternion.Euler(-90,t*23,0)' in s,'Chest camera or vertical reward orientation still broken');check('new Vector3(.7f,.16f,2.2f)' in s,'Reward blade is flattened/stretched on the wrong axis');check('chest.SetActive(found)' in s,'Opened chest disappears after reward')
# The reveal stands Ammy in the centre cell's open east passage, clear of maze walls.
check('treasurePoint+Vector3.right*1.8f' in s,'Chest staging points Ammy into a maze wall')
spot=l['treasure']
for dx in np.linspace(.28,2.74,25):
 p=np.array([spot['x']+dx,spot['z']]);dist=[]
 for wall in l['mazeWalls']:
  a=np.array([wall['a']['x'],wall['a']['z']]);b=np.array([wall['b']['x'],wall['b']['z']]);lo=np.minimum(a,b)-.325;hi=np.maximum(a,b)+.325;dist.append(np.linalg.norm(np.maximum(np.maximum(lo-p,p-hi),0)))
 check(min(dist)>.34,'Revealing chest puts the wolf body into a maze wall')
# Audit seated skin support (exact cut-surface check in heaven-dialogue) and Ammy head clearance.
def matrices(model,pose):
 out=[]
 for i,r in enumerate(pose):
  m=np.eye(4);m[:3,:3]=rotation(r[3:7])@np.diag(r[7:]);m[:3,3]=r[:3];parent=model['bones'][i-1]['parent']+1 if i else -1;out.append(m if parent<0 else out[parent]@m)
 return out
from asset_geometry import skin
m=json.loads((D/'heaven-tea-hm50/Model.json').read_text());pose=bank(D/'heaven-tea-hm50/Poses.bytes')['hm05_003'][0][0];pelvis=matrices(m,pose)[1][1,3]*.82+.25
seatBottom=float(np.concatenate(skin(m,pose))[:,1].min()*.82+.25);check(.24<=seatBottom<=.255,'Seated guest support height is wrong; see exact surface audit')
folder=A/'OkamiRemaster/Player/Resources/NativePlayer/pl00';m=json.loads((folder/'Model.json').read_text());poses=bank(folder/'Poses.bytes')['pl00_009'][0];heads=[matrices(m,p)[8][1,3] for p in poses];check(min(heads)>.45+.35,'Seated Ammy head submerged')
m=json.loads((D/'wp29/Model.json').read_text());check(m['visibleGroups']==[1,2,3,4],'Native side pieces still excluded');bolt=json.loads((D/'thunder-lightning/Model.json').read_text());source=next(p for p in m['parts'] if p['name']=='Native-0-0');check(bolt['parts']==[source],'Lightning geometry was invented or substituted');check(json.loads((D/'thunder-awakened/Model.json').read_text())['visibleGroups']==[1,4],'Reveal has overlapping guard variants')
bind=json.loads((A/'OkamiRemaster/Player/Resources/NativePlayer/Bindings.json').read_text())['bindings'];check(next(x for x in bind if x['state']=='NativeCharge_glaive')['clip']=='pl00_523','Glaive still uses rosary charge clip')
s=(P/'HeavenlyGarden.Palace.cs').read_text();check('pl00_004' in s and 'palace-shiranui' in s,'Recovered sleeping Shiranui missing');check('level 15' in s and '30 total upgrade ranks' in s and 'future encounter' in s,'Quest requirements changed or future guardian falsely unlocked');check('PalaceInteractions' in (P/'HeavenlyGarden.cs').read_text(),'Palace not connected to play');check('new Vector3(1.6f,7,.28f)' in s,'Shiranui seal can be jumped over')
# Existing approved audio and portraits remain byte-identical; add native cues without replacing them.
base='4bb8a7409797ff8408d0284d989a526c061bf657';old=json.loads(subprocess.check_output(['git','show',base+':Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/NativeAudio.json'],cwd=R));now=json.loads((D/'NativeAudio.json').read_text());check(now['cues'][:len(old['cues'])]==old['cues'],'Existing sounds overwritten')
for name in ['Original/Resources/Okami/WeaponPortraits','Original/Resources/Okami/NativeAudio/player-shiranui-layered-bark.wav']:
 check((A/'OkamiRemaster'/name).exists(),'Preserved asset missing');diff=subprocess.check_output(['git','diff',base,'--name-only','--','Sunward-Unity/Assets/OkamiRemaster/'+name],cwd=R);check(not diff.strip(),'Approved portraits or bark audio changed')
result=dict(checks=checks,pondDepthMetres=.45,teaPelvisHeight=float(pelvis),stumpHeight=.27,seatedHeadAboveWater=float(min(heads)-.45),scope='Native geometry/source contracts, not Unity physics or visual playback');W.mkdir(exist_ok=True);(W/'audit.json').write_text(json.dumps(result,indent=2));print('PASS',checks,'native heaven/palace/tea/chest/Thunder Edge contracts',result)
