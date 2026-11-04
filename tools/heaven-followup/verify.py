"""Source/geometry verification for the requested realm and boar repairs, not a Unity run."""
from pathlib import Path
import sys,json,re,math,numpy as np,subprocess,hashlib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';checks=0

def check(ok,why):
 global checks;checks+=1;assert ok,why
# The existing audit reconstructs actual source triangles, including the new dais.
sys.path.insert(0,str(R/'tools/celestial-garden-polish'));import verify as geometry
layout=geometry.layout;dais=next(i for i in layout if i['resource']=='Okami/celestial-grounded' and i['kind']=='ground')
check(not any(i['resource']=='Okami/celestial-bridge' for i in layout),'Unsupported bridge platform remains under the keeper')
check(dais['position']==dict(x=0,y=-.18,z=0) and dais['size']['x']==110 and dais['size']['z']==108,'Keeper dais is not sunk into its supporting terrain')
for x in [-3,-1,0,1,3]:
 for z in [16,17,18,20,22,24]:check(geometry.height(x,z) is not None,'Keeper or approach lacks real original mesh support')
sea=next(i for i in layout if i['kind']=='cloudsea');check(sea['position']['y']<-4 and sea['size']['x']>=450 and sea['size']['z']>=450,'Cloud underlay is too small or sits above the garden')
shader=(A/'OkamiRemaster/Original/Shaders/OriginalCelestialGround.shader').read_text();code=re.sub(r'//.*','',shader)
check('clip(' not in code and 'half4(c,1)' in code,'Stage vertex fade still cuts holes in solid ground');check('Cull [_Cull]' in code,'Original stone ink shells are rendered inside out')
m=json.loads((D/'celestial-meadow/Model.json').read_text());check(any(min(p['colors'][3::4])==0 for p in m['parts']),'Source fade-out root cause no longer reproduced')
check('_GroundPaint' in code and '_CloudPaint' in code and 'i.world.xz' in code,'Heaven still stretches a bland texture over the entire island')
h=(A/'OkamiRemaster/Original/Scripts/HeavenlyGarden.cs').read_text();check('SetFloat("_Cull",twoSided?0:2)' in h,'Native stone face culling not retained');check('keeperConversation=false;keeperCooldown=.4f;return;' in h,'Keeper can immediately reopen dialogue on the finishing E press')
dressing=(A/'OkamiRemaster/Original/Scripts/NativeInteriorDressing.cs').read_text();check('heaven?!game.Heaven.OwnsRenderer(renderer)' in dressing and 'priorVisibility[renderer] || hidden' in dressing and 'renderer.transform.IsChildOf(game.Player.transform)' in h and 'renderer.transform.IsChildOf(garden.transform)' in h,'Shared visibility controller does not isolate heaven or preserve player effects')
for n,count in [('Okami/vt67',4),('Okami/vt4a',2),('Okami/vt22',5)]:check(sum(i['resource']==n for i in layout)==count,'Missing original ceremonial decorations '+n)
animals=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json').read_text())['actors'];radii=json.loads(Path(__file__).with_name('animal-radii.json').read_text());check(len(animals)==13,'Existing animal population changed')
farm=(A/'OkamiRemaster/Original/Scripts/VillageFarm.cs').read_text();check('Pen("Boar paddock",15.5f,23,27.8f,36.5f,2.1f)' in farm,'No actual fenced boar paddock')
for a in animals:
 if a['asset'] not in ['boar','piglet']:continue
 radius=radii[a['asset']]+.08
 for p in a['path']:check(15.5+radius<p['x']<23-radius and 27.8+radius<p['y']<36.5-radius,'Original full body walks beyond its paddock')
for path in ['OkamiRemaster/Original/Resources/Okami/NativeAudio.json','OkamiRemaster/Original/Resources/Okami/NativeAudio/player-shiranui-layered-bark.wav','Sunward/Scripts/ValleyAudio.cs']:
 p=A/path;old=subprocess.check_output(['git','show','1ad16ca:'+str(p.relative_to(R))],cwd=R)
 if old.startswith(b'version https://git-lfs'):
  expected=re.search(rb'oid sha256:(\w+)',old)[1].decode();check(hashlib.sha256(p.read_bytes()).hexdigest()==expected,'Approved bark changed')
 else:check(p.read_bytes()==old,'Approved audio or mix changed')
changed=subprocess.check_output(['git','diff','1ad16ca','--name-only','--','Sunward-Unity/Assets'],cwd=R).decode();check('WeaponPortraits' not in changed,'Approved shop art changed')
print('PASS',checks,'heaven support/opacity/source-art/isolation and full-body paddock contracts; no Unity rendering or physics approval')
