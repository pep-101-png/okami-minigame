"""Authored market, food hall and training shrine. apply(scene) never saves the scene.
No runtime model reconstruction; all meshes/materials are native project assets.
"""
from pathlib import Path
import sys,re,math,json,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
import native
from native import Mesh,ASSETS,guid,fmt,vec
from environment import roof
OUT=ASSETS/'Generated/LivingPlaces'
WOOD=(.46,.27,.12); INK=(.07,.045,.03); PAPER=(.87,.77,.55); RED=(.64,.12,.075); GOLD=(.80,.51,.17)

def save(mesh,name):
 OUT.mkdir(parents=True,exist_ok=True);p=OUT/(name+'.asset');mesh.write(p);return guid(p)
def material(name,template,color=(1,1,1)):
 OUT.mkdir(parents=True,exist_ok=True)
 p=OUT/(name+'.mat');s=(ASSETS/'Generated/InkWorld'/template).read_text();s=re.sub(r'm_Name: .*','m_Name: '+name,s,count=1);s=re.sub(r'- _BaseColor: .*','- _BaseColor: {r: %g, g: %g, b: %g, a: 1}'%color,s);p.write_text(s);return guid(p)
def script_guid(name):return re.search(r'guid: (\w+)',(ASSETS/f'Scripts/{name}.cs.meta').read_text())[1]
def mono(s,go,name,fields):
 id=s.alloc();s.blocks[id]=f'''--- !u!114 &{id}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script_guid(name)}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: Assembly-CSharp::Sunward.{name}
{fields}'''
 s.blocks[go]=s.blocks[go].replace('  m_Component:\n',f'  m_Component:\n  - component: {{fileID: {id}}}\n');return id

def box(s,go,center,size,solid=True):
 old=next(i for i in s.blocks if s.kind(i)==65);id=s.alloc();raw=s.blocks[old]
 raw=re.sub(r'^--- !u!65 &-?\d+',f'--- !u!65 &{id}',raw);raw=re.sub(r'm_GameObject: \{fileID: -?\d+\}',f'm_GameObject: {{fileID: {go}}}',raw)
 raw=re.sub(r'  m_Center: .*','  m_Center: '+fmt(center),raw);raw=re.sub(r'  m_Size: .*','  m_Size: '+fmt(size),raw);raw=re.sub(r'  m_Enabled: .*','  m_Enabled: 1',raw)
 s.blocks[id]=raw;s.blocks[go]=s.blocks[go].replace('  m_Component:\n',f'  m_Component:\n  - component: {{fileID: {id}}}\n');s.set(go,'m_Layer',6)
 if solid:mono(s,go,'VillageWorldSolid','')
 return id

def room_mesh(w,d):
 timber=Mesh();panels=Mesh();floor=Mesh();doorwall=Mesh();h=3.15
 # Floor: staggered individual boards with dark gaps and ink bevels.
 for row,back in enumerate(np.arange(-d/2,d/2,.39)):
  plankdepth=min(.37,d/2-back);z=back+plankdepth/2
  for left in np.arange(-w/2,w/2,1.4):
   end=min(1.37,w/2-left);x=left+end/2
   floor.box((x,.025,z),(end,.075,plankdepth),np.array(WOOD)*(1+.08*math.sin(row*2+x)),bevel=.012)
 for x in [-w/2,w/2]:
  for z in [-d/2,d/2]:timber.box((x,h/2,z),(.22,h,.22),WOOD,bevel=.025)
 for z in [-d/2,d/2]:timber.box((0,h-.14,z),(w+.2,.28,.25),WOOD,bevel=.025)
 for x in [-w/2,w/2]:timber.box((x,h-.14,0),(.25,.28,d+.2),WOOD,bevel=.025)
 # Open south entry, clear 3.2 metres for the wolf's full body sweep.
 for side in [-1,1]:
  width=(w-3.2)/2;x=side*(w/2-width/2)
  doorwall.box((x,1.5,-d/2),(width,2.8,.16),PAPER,bevel=.018)
  timber.box((side*1.6,1.4,-d/2),(.20,2.8,.23),RED,bevel=.018)
 for x in [-w/2,w/2]:panels.box((x,1.52,0),(.16,2.8,d),PAPER,bevel=.02)
 panels.box((0,1.52,d/2),(w,2.8,.16),PAPER,bevel=.02)
 # Recessed raised shoji lattice and plaster lower/upper painted edges.
 for side in [-1,1]:
  for z in np.arange(-d/2+.45,d/2,.48):timber.box((side*(w/2+.1),1.55,z),(.05,1.55,.025),INK,bevel=.003)
  for y in [.70,1.45,2.25]:timber.box((side*(w/2+.11),y,0),(.06,.032,d-.3),WOOD,bevel=.004)
 for x in np.arange(-w/2+.4,w/2,.42):timber.box((x,1.55,d/2+.1),(.024,1.55,.04),INK,bevel=.003)
 for y in [.68,2.28]:timber.box((0,y,d/2+.11),(w,.04,.04),WOOD,bevel=.006)
 for x in np.arange(-w/2+.18,w/2,.42):timber.tube([(x,h-.1,-d/2-.48),(x,h+.08,-d/2+.3)],[.045,.05],WOOD,n=8)
 return timber,panels,floor,doorwall,roof(w,d,3.15)

def stall(seed):
 wood=Mesh();cloth=Mesh();goods=Mesh();dark=Mesh();width=2.5;col=[(.67,.12,.08),(.20,.31,.42),(.32,.43,.22),(.74,.48,.12)][seed]
 for x in [-1.18,1.18]:
  for z in [-.62,.62]:wood.tube([(x,0,z),(x,2.38,z)],[.065,.055],WOOD,n=10,groove=.09)
 for x in np.arange(-1.1,1.11,.22):wood.box((x,.80,0),(.21,.1,1.3),np.array(WOOD)*(1+.1*math.sin(x*4)),bevel=.012)
 for z in [-.60,.60]:wood.box((0,.56,z),(2.44,.39,.12),WOOD,bevel=.018)
 # Deep segmented awning with scalloped valance; no flat primitive rectangles.
 for j,x in enumerate(np.linspace(-1.30,1.30,17)[:-1]):
  xx=x+2.6/16
  for k,z in enumerate(np.linspace(-.85,.85,9)[:-1]):
   zz=z+1.7/8
   def yy(a,b):return 2.32+.23*math.cos(b/.85*math.pi/2)+.025*math.sin(a*8)
   cloth.face([(x,yy(x,z),z),(x,yy(x,zz),zz),(xx,yy(xx,zz),zz),(xx,yy(xx,z),z)],np.array(col)*(1+.1*math.cos(j*.8)))
  bottom=2.04-.06*math.sin((j+.5)*math.pi/4)
  cloth.box(((x+xx)/2,(2.33+bottom)/2,-.83),(xx-x+.003,2.33-bottom,.045),col,bevel=.004)
  if j%4==0:dark.box((x,2.18,-.862),(.027,.26,.018),GOLD,bevel=.003)
 # Bold geometric wave / sakura stencil bands printed on the cloth.
 for j in range(7):
  points=[(-1.13+j*.35+.10*math.cos(a),2.17+.08*math.sin(a),-.868) for a in np.linspace(0,math.pi*1.6,12)]
  dark.tube(points,[.012]*len(points),PAPER,n=5)
 for j in range(3):
  x=(j-1)*.73;wood.box((x,.9,.08),(.65,.17,.75),WOOD,bevel=.024)
  for k in range(7):
   if seed%2:goods.loft([(x+(k%3-1)*.16,.99+(k//3)*.08,(k//3-1)*.16,.065,.065),(x+(k%3-1)*.16,1.08+(k//3)*.08,(k//3-1)*.16,.06,.06)],(.78,.67,.36),n=10)
   else:goods.ellipsoid((x+(k%3-1)*.16,1.02+(k//3)*.08,(k//3-1)*.15),(.085,.085,.075),[(.70,.12,.07),(.65,.57,.12),(.27,.47,.16)][j],n=10,rows=6)
 return wood,cloth,goods,dark

def dog_bed():
 basket=Mesh();cushion=Mesh();ink=Mesh()
 for y,r in [(.04,1.08),(.12,1.12),(.20,1.12),(.28,1.08)]:
  points=[(math.cos(a)*r,y,math.sin(a)*r*.62) for a in np.linspace(0,math.tau,65)]
  basket.tube(points,[.035]*len(points),WOOD,n=7,groove=.08)
 for a in np.linspace(0,math.tau,40,endpoint=False):basket.tube([(math.cos(a)*1.05,.04,math.sin(a)*.65),(math.cos(a)*1.12,.24,math.sin(a)*.69)],[.015,.015],GOLD,n=6)
 cushion.ellipsoid((0,.10,0),(.99,.13,.59),(.34,.40,.27),n=32,rows=8)
 for x in [-.60,.60]:
  pts=[(x,.19,z) for z in np.linspace(-.40,.40,9)];ink.tube(pts,[.012]*9,PAPER,n=6)
 for part in [basket,cushion,ink]:part.v=[(v[0]*.75,v[1],v[2]*2.4) for v in part.v]
 return basket,cushion,ink

def table():
 m=Mesh()
 for x in [-.65,.65]:
  for z in [-.33,.33]:m.box((x,.23,z),(.10,.46,.10),WOOD,bevel=.015)
 for z in [-.31,0,.31]:m.box((0,.48,z),(1.55,.10,.30),WOOD,bevel=.018)
 for x in [-.45,.45]:
  m.loft([(x,.55,0,.15,.15),(x,.61,0,.17,.17),(x,.65,0,.15,.15)],(.79,.74,.57),n=20)
  m.ellipsoid((x,.65,0),(.12,.025,.12),(.91,.87,.67),n=16,rows=4)
  for z in [-.13,-.10]:m.tube([(x-.17,.56,z),(x+.17,.56,z)],[.008,.008],INK,n=6)
 return m

def dummy():
 wood=Mesh();straw=Mesh();ink=Mesh()
 wood.tube([(0,0,0),(0,1.88,0)],[.11,.085],WOOD,n=20,groove=.10)
 wood.tube([(-.62,1.28,0),(.62,1.28,0)],[.065,.065],WOOD,n=12,groove=.08)
 straw.loft([(0,.70,0,.23,.15),(0,1.38,0,.25,.17)],(.62,.49,.25),n=24,flute=.035)
 straw.loft([(0,1.42,0,.14,.13),(0,1.74,0,.14,.13)],(.67,.53,.31),n=24,flute=.04)
 for y in np.arange(.74,1.39,.12):
  pts=[(math.cos(a)*.255,y,math.sin(a)*.18) for a in np.linspace(0,math.tau,33)];ink.tube(pts,[.014]*33,INK,n=6)
 for a in np.linspace(0,math.tau,20,endpoint=False):straw.tube([(math.cos(a)*.24,.71,math.sin(a)*.16),(math.cos(a)*.25,1.39,math.sin(a)*.17)],[.012,.012],GOLD,n=6)
 for x,z in [(-.55,0),(.55,0),(0,-.40),(0,.40)]:wood.tube([(0,.13,0),(x,.04,z)],[.06,.04],WOOD,n=10)
 return wood,straw,ink


def apply(s):
 if any(s.kind(i)==1 and s.name(i)=='Living places · market bed' for i in s.blocks):return {'alreadyApplied':True}
 native.OUT=OUT;OUT.mkdir(parents=True,exist_ok=True)
 # Self-contained contour helper; only geometry-normal assets are copied.
 spec=importlib.util.spec_from_file_location('places_ink_helpers',ROOT/'tools/ink-world/apply.py');inkmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(inkmod);inkmod.OUT=OUT
 mats={'wood':guid(ASSETS/'Generated/InkWorld/Ink-painted-timber.mat'),'plaster':guid(ASSETS/'Generated/InkWorld/Ink-painted-plaster.mat'),'roof':guid(ASSETS/'Generated/InkWorld/Ink-indigo-roof.mat'),'ink':guid(ASSETS/'Generated/InkWorld/Ink-contour.mat'),'cloth':material('Market-fabric','Ink-painted-plaster.mat'),'goods':material('Market-produce','Ink-painted-plaster.mat'),'straw':material('Training-straw','Ink-painted-timber.mat')}
 lantern_path=OUT/'Evening-glowing-paper.mat';lantern_text=(ASSETS/'Generated/InkWorld/Ink-painted-plaster.mat').read_text();lantern_text=re.sub(r'm_Name: .*','m_Name: Evening-glowing-paper',lantern_text,count=1);lantern_text=re.sub(r'm_Shader: .*','m_Shader: {fileID: 4800000, guid: '+guid(ASSETS/'Shaders/NightLantern.shader')+', type: 3}',lantern_text);lantern_path.write_text(lantern_text);mats['lantern']=guid(lantern_path)
 cache={};new=[];lights=[]
 def add(name,m,mat='wood',p=(0,0,0),yaw=0,parent=0,outline=True):
  g=save(m,name);go=s.add('Living places · '+name,g,mats[mat],p=p,parent=parent);t=s.transform(go)
  if yaw:s.set(t,'m_LocalRotation','{x: 0, y: %g, z: 0, w: %g}'%(math.sin(math.radians(yaw)/2),math.cos(math.radians(yaw)/2)))
  if outline:
   shell=inkmod.shell_mesh(OUT/(name+'.asset'),cache);o=s.add('Living ink · '+name,shell,mats['ink'],parent=t);s.set(s.component(o,23),'m_CastShadows',0)
  new.append(go);return go
 def empty(name,p,parent=0):
  # Reuse a tiny authored marker, hidden visual; no collider.
  m=Mesh();m.box((0,0,0),(.01,.01,.01),INK);go=add(name,m,p=p,outline=False,parent=parent);s.set(s.component(go,23),'m_Enabled',0);return go
 game=next(i for i,b in s.blocks.items() if s.kind(i)==114 and 'Assembly-CSharp::Sunward.GameFlow\n' in b)
 player=next(i for i,b in s.blocks.items() if s.kind(i)==114 and 'Assembly-CSharp::Sunward.WolfMotor\n' in b)
 valley=next(i for i,b in s.blocks.items() if s.kind(i)==114 and 'Assembly-CSharp::Sunward.Valley\n' in b)
 # Replace old enclosed shell visual parts, preserving every other village house.
 rooms=[]
 for index,center,w,d,yaw in [(8,(0,0,26),10.6,7.6,0),(5,(9,0,9),7.4,8.6,90)]:
  legacy=(0,25) if index==8 else (9,9)
  for i in list(s.blocks):
   if s.kind(i)==1 and (s.name(i).startswith('Village house '+str(index)+' ·') or s.name(i).startswith('Ink contour · Village house '+str(index)+' ·')):
    s.set(i,'m_IsActive',0)
  for i in list(s.blocks):
   if s.kind(i)==1 and any(s.name(i).startswith('Ink world · '+part+' '+str(index)) for part in ['roof sun crest','curved entrance fascia','carved eave joinery','high gable wood','high gable paper','hall belfry timber','hall belfry plaster','hall belfry tiles']):s.set(i,'m_IsActive',0)
  for i,b in list(s.blocks.items()):
   if s.kind(i)==65:
    go=s.owner(i);t=s.transform(go)
    if t and abs(vec(s.blocks[t],'m_LocalPosition')[0]-legacy[0])<.02 and abs(vec(s.blocks[t],'m_LocalPosition')[2]-legacy[1])<.02 and s.name(go)=='Building / rail collider':s.set(i,'m_Enabled',0)
  label='Windflower training shrine' if index==8 else 'Street food hall';parts=room_mesh(w,d);group=empty(label,center);gt=s.transform(group)
  s.set(gt,'m_LocalRotation','{x: 0, y: %g, z: 0, w: %g}'%(math.sin(math.radians(yaw)/2),math.cos(math.radians(yaw)/2)))
  objects=[]
  for part,m,mat in zip(['timber','shoji walls','floor','door jamb panels','roof'],parts,['wood','plaster','wood','plaster','roof']):objects.append(add(label+' '+part,m,mat,parent=gt))
  box(s,objects[2],(0,-.04,0),(w,.12,d),False)
  # Deliberate physical walls, no invisible solid box over the doorway.
  for side in [-1,1]:
   for pos,size in [((side*w/2,1.5,0),(.20,3,d)),((side*(w/2+1.6)/2,1.5,-d/2),((w-3.2)/2,3,.20))]:
    wall=empty(label+' wall collision '+str(len(new)),(0,0,0),parent=gt);wt=s.transform(wall);s.set(wt,'m_LocalPosition',fmt(pos));box(s,wall,(0,0,0),size)
  wall=empty(label+' rear collision',(0,0,0),parent=gt);wt=s.transform(wall);s.set(wt,'m_LocalPosition',fmt((0,1.5,d/2)));box(s,wall,(0,0,0),(w,3,.20))
  # Cut away all roof/upper lateral panels and their attached ink renderers when inside.
  renderers=[]
  for o in [objects[1],objects[3],objects[4]]:
   renderers.append(s.component(o,23))
   for child in s.blocks:
    if s.kind(child)==4 and re.search(r'm_Father: \{fileID: '+str(s.transform(o))+r'\}',s.blocks[child]):renderers.append(s.component(s.owner(child),23))
  hs=(w/2,d/2) if yaw==0 else (d/2,w/2)
  mono(s,group,'VillageInterior',f'  player: {{fileID: {player}}}\n  valley: {{fileID: {valley}}}\n  halfSize: {{x: {hs[0]}, y: {hs[1]}}}\n  legacyHouse: {{x: {legacy[0]}, y: {legacy[1]}}}\n  cutaway:\n'+''.join(f'  - {{fileID: {r}}}\n' for r in renderers if r))
  rooms.append(group)
 # Hide only superseded stall hierarchy. Existing merchant interactions remain in GameFlow.
 for i in list(s.blocks):
  if s.kind(i)==1 and s.name(i)=='Market · crafted stalls and arranged goods':s.set(i,'m_IsActive',0)
 for i,b in list(s.blocks.items()):
  if s.kind(i)==65:
   o=s.owner(i);t=s.transform(o);p=vec(s.blocks[t],'m_LocalPosition') if t else np.zeros(3)
   if s.name(o)=='Building / rail collider' and abs(abs(p[0])-4.8)<.02 and abs(p[2])<.02:s.set(i,'m_Enabled',0)
 for k,(x,z,yaw) in enumerate([(-4.3,-3.6,-90),(4.3,-3.6,90),(-4.3,3.2,-90),(4.3,3.2,90)]):
  root=empty('market stall '+str(k),(x,0,z));rt=s.transform(root);s.set(rt,'m_LocalRotation','{x: 0, y: %g, z: 0, w: %g}'%(math.sin(math.radians(yaw)/2),math.cos(math.radians(yaw)/2)))
  for part,m,mat in zip(['cedar frame','dyed wave awning','hand arranged produce','printed brush ornaments'],stall(k),['wood','cloth','goods','cloth']):go=add('stall '+str(k)+' '+part,m,mat,parent=rt)
  box(s,root,(0,.6,0),(2.6,1.2,1.4))
 # Three real straw dummies preserve a clear central walking route.
 for k,(x,z) in enumerate([(-2.7,25.8),(2.7,25.8)]):
  for part,m,mat in zip(['timber','woven straw','binding'],dummy(),['wood','straw','wood']):go=add('training dummy '+str(k)+' '+part,m,mat,p=(x,0,z))
  box(s,go,(0,.8,0),(.7,1.6,.5))
 for k,z in enumerate([7,11]):
  go=add('food hall low table '+str(k),table(),p=(8,0,z));box(s,go,(0,.3,0),(1.5,.6,.8))
 # Raised musician dais on east side with lacquer trim.
 stage=Mesh();stage.box((0,.08,0),(1.7,.16,2.3),WOOD,bevel=.025);stage_go=add('food hall musician dais',stage,p=(11.7,0,10.8));box(s,stage_go,(0,.08,0),(1.7,.16,2.3),False)
 # Lantern strings have actual grounded posts, not floating lengths of rope.
 for row,z in enumerate([-4,4]):
  posts=Mesh();rope=Mesh()
  for x in [-5.5,5.5]:
   posts.tube([(x,0,0),(x,3.65,0)],[.085,.065],WOOD,n=12,groove=.08)
   posts.box((x,.10,0),(.28,.20,.28),INK,bevel=.045)
  pts=[(x,3.25+.40*(x/5.5)**2,0) for x in np.linspace(-5.5,5.5,45)]
  rope.tube(pts,[.018]*len(pts),INK,n=7,groove=.10)
  add('market supported lantern posts '+str(row),posts,p=(0,0,z));add('market sagging lantern rope '+str(row),rope,p=(0,0,z))
 # Four vermilion hanging market strings with lanterns and physically bounded point lights.
 light_source=next(i for i,b in s.blocks.items() if s.kind(i)==108 and '  m_Type: 2\n' in b)
 for i,(x,z,c) in enumerate([(-3,-4,(1,.42,.12)),(3,-4,(.36,.55,1)),(-3,4,(1,.23,.32)),(3,4,(.30,1,.70)),(7,9,(1,.54,.20)),(11,9,(1,.47,.18)),(-2.5,24,(1,.57,.24)),(2.5,24,(1,.57,.24))]):
  m=Mesh();m.loft([(0,-.26,0,.13,.13),(0,-.21,0,.22,.22),(0,.18,0,.22,.22),(0,.25,0,.13,.13)],c,n=18,flute=.035)
  g=add('evening lantern '+str(i),m,'lantern',p=(x,2.5,z));lid=s.alloc();raw=s.blocks[light_source];raw=re.sub(r'^--- !u!108 &-?\d+',f'--- !u!108 &{lid}',raw);raw=re.sub(r'm_GameObject: \{fileID: -?\d+\}',f'm_GameObject: {{fileID: {g}}}',raw);raw=re.sub(r'  m_Color: .*','  m_Color: {r: %g, g: %g, b: %g, a: 1}'%c,raw);raw=re.sub(r'  m_Intensity: .*','  m_Intensity: 2.0',raw);raw=re.sub(r'  m_Range: .*','  m_Range: 5.5',raw);raw=re.sub(r'(  m_Shadows:\n    m_Type:) \d+',r'\g<1> 0',raw);s.blocks[lid]=raw;s.blocks[g]=s.blocks[g].replace('  m_Component:\n',f'  m_Component:\n  - component: {{fileID: {lid}}}\n');lights.append(lid)
  # Actual attached hanging cord and top/bottom lacquer rings.
  cord=Mesh();cord.tube([(0,.25,0),(0,.9,0)],[.012,.012],INK,n=6)
  for y in [-.26,.25]:cord.loft([(0,y-.018,0,.14,.14),(0,y+.018,0,.14,.14)],RED,n=18)
  add('evening lantern cord '+str(i),cord,parent=s.transform(g))
 cycle_obj=empty('day and night rhythm',(0,0,0));sun=next(i for i,b in s.blocks.items() if s.kind(i)==108 and '  m_Type: 1\n' in b)
 existing=[i for i,b in s.blocks.items() if s.kind(i)==108 and '  m_Type: 2\n' in b]
 cycle=mono(s,cycle_obj,'DayNightCycle',f'  game: {{fileID: {game}}}\n  sun: {{fileID: {sun}}}\n  hour: 9\n  dayMinutes: 20\n  lanterns:\n'+''.join(f'  - {{fileID: {i}}}\n' for i in existing)+'  lanternPaper: []\n')
 # Remove old stall analytic boxes with a dedicated interior cleanup, no changes to source Valley.json.
 cleanup=mono(s,cycle_obj,'MarketLayout','  valley: {fileID: '+str(valley)+'}\n')
 for name,p,watch in [('market bed',(-2.7,.10,7.0),False),('food hall listening mat',(10,.05,9),True)]:
  objs=[]
  for part,m,mat in zip(['woven wicker','soft cushion','stitching'],dog_bed(),['wood','cloth','cloth']):objs.append(add(name+' '+part,m,mat,p=p,yaw=45 if watch else 0))
  s.set(objs[0],'m_Name','Living places · '+name)
  mono(s,objs[0],'VillageRest',f'  game: {{fileID: {game}}}\n  cycle: {{fileID: {cycle}}}\n  displayName: '+json.dumps('Sit and listen to the musician' if watch else 'Rest until morning or evening')+f'\n  watchOnly: {1 if watch else 0}\n  radius: 1.65\n')
 return {'rooms':len(rooms),'stalls':4,'trainingDummies':2,'restPlaces':2,'nightLanterns':len(lights),'newObjects':len(new),'outlineMeshes':len(cache)}
