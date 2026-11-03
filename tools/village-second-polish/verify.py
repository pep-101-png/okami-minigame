"""Focused source/asset contracts. Not Unity physics, rendering or audio approval."""
from pathlib import Path
import json,re,wave,numpy as np,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';S=A/'OkamiRemaster/Original/Scripts';checks=0

def check(v,why):
 global checks;checks+=1;assert v,why

def text(p):return p.read_text()
audio=text(A/'Sunward/Scripts/ValleyAudio.cs');check('id=="bark"?.75f' in audio,'Selected bark gain not raised')
clip=D/'NativeAudio/player-pl00-41-bark.wav';old=subprocess.check_output(['git','show','b451c8b:'+str(clip.relative_to(R))],cwd=R)
if not old.startswith(b'version https://git-lfs'):check(old==clip.read_bytes(),'Selected bark was altered')
with wave.open(str(clip)) as f:
 check(f.getsampwidth()==2,'Unexpected bark encoding');v=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(float)/32768;check(abs(v).max()*.75*.6<1,'New bark gain clips the original waveform')
festival=text(S/'FestivalChallenges.cs');check('kind==1?50:90' in festival,'Race time was extended again')
ui=text(A/'Sunward/Scripts/ScrollUI.cs');check('START SPIRIT RUN · 50 seconds' in ui and '95 seconds' not in ui,'Race display disagrees with timing')
check('InkText.MeasureHeight' in ui and 'panel.width-108' in ui,'Menu layout ignores native glyph widths or scroll edges');ink=text(S/'InkText.cs');check('GUI.BeginGroup(area)' in ink and 'GUI.EndGroup()' in ink,'Lettering is not clipped')
check('Bar(260,' in ui and '272, 142' in ui,'Status bar exceeds available scroll space')
sys.path.insert(0,str(R/'tools/interior-village-repairs'));from verify import blocks
scene=blocks(text(A/'Sunward/Scenes/Windflower.unity'));ledger=json.loads(Path(__file__).with_name('home-collision.json').read_text())
for cid in ledger['retired']:check('m_Enabled: 0' in scene[cid],'Old invisible house obstacle remains enabled')
b=scene[ledger['collider']];check(b.startswith('--- !u!64 ') and 'm_Enabled: 1' in b and ledger['meshGUID'] in b,'House collision does not match visible exterior mesh');check(str(ledger['collider']) in scene[ledger['house']],'Exact house collider is detached')
farm=text(S/'VillageFarm.cs');check('Okami/farm-canopy' not in farm and 'Okami/farm-pitched-roof' in farm and 'Okami/farm-post' in farm,'Washing platform is still used as a roof')
roof=json.loads((D/'farm-pitched-roof/Model.json').read_text());check(roof['sourceName']=='r107/__LY32__3F_Yane' and roof['sourceParts']==[1],'Roof is not recovered original roof geometry')
post=json.loads((D/'farm-post/Model.json').read_text());check(post['sourceComponent']==411 and 'without the washing platforms' in post['derivation'],'Roof supports contain unrelated boards')
spa=json.loads((D/'spa-hm16/Model.json').read_text());check(len(spa['omittedHeldProps'])==8,'Spa held props were restored');check('seatedArmMotion="hm05_027"' in farm and 'seatedArmPause=.8f' in farm,'Spa gesture does not run with native motion and resting interval')
for resource in ['farm-pitched-roof','farm-post','spa-hm16']:
 folder=D/resource;m=json.loads((folder/'Model.json').read_text())
 for p in m['parts']:
  v=np.array(p['positions']).reshape(-1,3);check(np.isfinite(v).all() and max(p['indices'])<len(v),'Invalid native mesh '+resource)
 for t in m['textures']:check(t.get('vertexOnly') or (folder/t['path']).exists(),'Unresolved original painting '+resource)
 for p in folder.iterdir():
  if p.suffix!='.meta':check(Path(str(p)+'.meta').exists(),'Missing Unity metadata '+str(p))
from PIL import Image
for i in range(0x20,0x25):
 p=D/'WeaponPortraits'/f'wp{i:02x}.png';im=Image.open(p).convert('RGBA');check(im.size==(1024,1024) and len(set(im.getdata()))>50,'Empty reflector catalogue image');check(p.stat().st_size>20000,'Reflector portrait still an edge/effect sliver')
water=text(S/'HeavenlyGarden.cs');check('WaterfallLip=36' in water and 'p.z>WaterfallLip-.75f' in water,'Portal remains beyond village boundary');check('-37.445568f' in water and '_FlowDirection' in water,'Waterfall still uses guessed reverse direction')
valley=json.loads((A/'Sunward/Data/Valley.json').read_text());check(36-.75<valley['world']['bounds']['maxZ']+1.5,'Portal unreachable')
align=json.loads(Path(__file__).with_name('waterfall-alignment.json').read_text());check(abs(align['flowAfterRotationXZ'][0])<1e-5 and align['flowAfterRotationXZ'][1]>1,'Waterfall falls inland')
for shader in ['ContinuousGround','RecoveredRiver']:check('world.z>36' in text(A/f'OkamiRemaster/Windflower/Shaders/{shader}.shader'),'River floor extends past new waterfall lip')
check('collapseDelay=won?3f:-1' in text(S/'LowerArena.cs'),'Final wave has no pause before collapse')
enemy=text(A/'Sunward/Scripts/EnemyBrain.cs');check(enemy.count('GroundBoss();')==3 and 'LowerArena.Height(p,out var floor)' in enemy,'Boss scale/movement is not grounded on actual floor')
for p in [A/'Sunward/Automation/TrailerPlayback.cs',A/'Editor/SunwardTrailerMenu.cs']:check('class ' not in text(p),'In-game trailer code was restored')
check('TRAILER' not in ui,'In-game trailer menu was restored')
print('PASS',checks,'second play-test source/resource contracts; no Unity playback, audio listening or physics approval')
