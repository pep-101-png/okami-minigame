"""Hand authored Japanese villagers on the retained 13-bone resident rig.
Scene pass is explicit: apply(scene); it never writes the scene by itself.
"""
from pathlib import Path
import sys,re,math,struct,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native
from native import Mesh,ASSETS,guid,fmt,vec
OUT=ASSETS/'Generated/LivingVillagers'
INK=(.045,.035,.035); SKIN=(.81,.62,.47); HAIR=(.06,.045,.045); IVORY=(.88,.84,.72)
ROLES=['Gardener','Merchant','Elder','Samurai','ShrineMaiden','Geisha','Chef']
COLORS={'Gardener':(.27,.39,.25),'Merchant':(.22,.31,.43),'Elder':(.34,.39,.34),'Samurai':(.15,.23,.28),'ShrineMaiden':(.86,.83,.73),'Geisha':(.44,.16,.26),'Chef':(.84,.82,.73)}

def resident(role,variant=0):
 m=Mesh(); female=role in ('Geisha','ShrineMaiden');stocky=role in ('Chef','Merchant'); w=.225 if stocky else .19 if female else .205
 skin=np.array(SKIN)*(1-.045*(variant%3));robe=np.array(COLORS[role])*(.96+.025*(variant%4));obi=(.71,.40,.15) if role=='Geisha' else (.67,.15,.12) if role=='ShrineMaiden' else (.22,.15,.11)
 # One continuous trouser tube per leg. Blended weights are applied at the true
 # knee y=.40; the old calf geometry extended above the knee into the thigh.
 for side in (-1,1):
  leg=3 if side<0 else 6
  m.box((side*.14,.044,.025),(.163,.055,.275),(.25,.16,.085),leg+2,.018)
  m.ellipsoid((side*.14,.094,.052),(.071,.046,.11),IVORY,leg+2,n=16,rows=5)
  rings=[(side*.14,y,0,rx,rz) for y,rx,rz in [(.12,.061,.065),(.22,.072,.070),(.35,.083,.08),(.40,.085,.081),(.47,.09,.086),(.63,.105,.102),(.76,.108,.107)]]
  m.loft(rings,robe*.85,leg,n=20,flute=.03)
  # Tabi split and sandal thong, visible at street camera distances.
  m.tube([(side*.14,.138,.02),(side*.14,.133,.12)],[.005,.004],INK,leg+2,n=5)
 m.loft([(0,.70,0,w*1.13,.145),(0,.84,0,w*1.12,.15),(0,.98,0,w,.14),(0,1.16,0,w*1.12,.145),(0,1.38,-.008,w*1.19,.12)],robe,1,n=28,flute=.02)
 m.loft([(0,.88,0,w*1.13,.156),(0,1.00,0,w*1.10,.15)],obi,0,n=28)
 for yy in (.885,.997):m.loft([(0,yy,0,w*1.14,.159),(0,yy+.008,0,w*1.14,.159)],INK,0,n=28)
 for a,b in [((-.12,1.38,.108),(.09,1.05,.152)),((.12,1.38,.108),(-.05,1.20,.157))]:
  m.tube([a,b],[.021,.020],IVORY,1,n=8)
  m.tube([(a[0]+.013,a[1],a[2]+.002),(b[0]+.013,b[1],b[2]+.002)],[.0035,.003],INK,1,n=5)
 # Anatomical facial planes: tapered jaw, cheekbones, brow and rounded crown.
 # Eyelids sit on the face, rather than floating eyeballs or thick black bars.
 m.loft([(0,1.36,-.008,.058,.054),(0,1.51,-.004,.061,.058)],skin,2,n=24)
 hw=.130 if stocky else .112 if female else .121
 profile=[(1.48,.040,.040,.018),(1.51,.071,.062,.020),(1.55,hw*.82,.080,.013),
          (1.60,hw*.98,.099,.003),(1.66,hw,.104,-.006),(1.72,hw*.94,.100,-.012),
          (1.77,hw*.78,.082,-.018),(1.80,hw*.45,.048,-.02),(1.81,.008,.008,-.02)]
 m.loft([(0,y,z,rx,rz) for y,rx,rz,z in profile],skin,2,n=36)
 for side in (-1,1):
  m.ellipsoid((side*(hw-.002),1.625,-.012),(.016,.027,.018),skin*.94,2,n=14,rows=8)
  # Painted almond lids and pupils contained within a thin warm-white sclera.
  x=side*.048;y=1.651;z=.096
  pts=[(x-side*.026,y,z-.002),(x,y+.006,z+.005),(x+side*.026,y+.001,z-.003),(x,y-.005,z+.005)]
  m.face(pts if side<0 else pts[::-1],(.63,.56,.46),2)
  m.ellipsoid((x, y+.001,z+.007),(.007,.005,.0025),(.105,.070,.055),2,n=10,rows=4)
  m.tube([(x-side*.026,y+.001,z),(x,y+.008,z+.006),(x+side*.026,y+.002,z-.002)],[.0018,.0024,.0015],HAIR,2,n=5)
  m.tube([(side*.025,1.680,.093),(side*.048,1.686,.096),(side*.076,1.679,.085)],[.0025,.0031,.0018],HAIR,2,n=5)
  m.ellipsoid((side*.073,1.600,.084),(.023,.014,.002),skin*np.array([1.01,.94,.93]),2,n=12,rows=5)
 # Nose bridge and alar planes instead of a protruding spherical button.
 for side in (-1,1):
  m.face([(0,1.663,.102),(side*.014,1.610,.108),(side*.010,1.598,.126),(0,1.601,.134)],skin*(.92 if side<0 else 1.02),2)
  m.face([(0,1.601,.134),(side*.010,1.598,.126),(side*.015,1.593,.111),(0,1.591,.114)],skin*.90,2)
 m.tube([(-.021,1.556,.092),(0,1.553,.101),(.021,1.556,.092)],[.0018,.0023,.0018],(.45,.24,.20),2,n=5)
 m.loft([(0,1.70,-.027,hw*1.03,.096),(0,1.78,-.03,hw*.92,.079),(0,1.83,-.03,.049,.04)],HAIR,2,n=32)
 # Scalloped hairline and side locks leave the face visible.
 for side in (-1,1):m.tube([(side*.102,1.76,.025),(side*.12,1.69,.004),(side*.12,1.60,-.015)],[.026,.023,.013],HAIR,2,n=9)
 for side in (-1,1):
  arm=9 if side<0 else 11
  m.tube([(side*.23,1.375,0),(side*.32,1.29,0),(side*.42,1.18,0)],[.092,.102,.088],robe,arm,n=20,groove=.02)
  m.tube([(side*.42,1.18,0),(side*.48,1.07,.022),(side*.51,.98,.04)],[.088,.073,.055],robe,arm+1,n=20)
  m.ellipsoid((side*.515,.953,.052),(.035,.051,.027),skin,arm+1,n=16,rows=8)
  m.tube([(side*.484,.976,.071),(side*.475,.946,.083)],[.014,.010],skin,arm+1,n=8)
  for finger in range(4):
   x=side*(.491+finger*.015);m.tube([(x,.941,.060),(x,.902+(abs(finger-1.5)*.005),.069)],[.009,.0065],skin,arm+1,n=7)
  m.tube([(side*.47,.99,-.018),(side*.51,.99,.09)],[.007,.007],INK,arm+1,n=6)
  if female:m.loft([(side*.34,.95,-.025,.10,.125),(side*.32,1.25,-.01,.105,.11)],robe,arm,n=20)
 for side in (-1,1):
  for j in range(3):
   x=side*(.10+j*.035)
   m.tube([(x,.72,.145),(x*.93,.80,.157),(x*.9,.87,.159)],[.002,.004,.002],robe*.68,0,n=5)
 m.loft([(0,1.36,-.015,.087,.071),(0,1.43,-.008,.076,.064)],robe,1,n=24)
 # Long garments end high enough for the planted feet to remain readable.
 if female or role=='Elder':
  skirt=(.65,.14,.12) if role=='ShrineMaiden' else robe
  m.loft([(0,.25,0,.27,.18),(0,.41,0,.266,.18),(0,.63,0,.25,.17),(0,.87,0,w*1.13,.15)],skirt,0,n=32,flute=.035)
  m.loft([(0,.25,0,.272,.182),(0,.26,0,.272,.182)],INK,0,n=32)
  # Discrete geometric sash/embroidery motifs convey costume identity.
  for j in range(6):
   x=.16*math.sin(j*.8);y=.34+j*.065
   for k in range(5):
    a=k*math.tau/5;m.ellipsoid((x+.012*math.cos(a),y+.012*math.sin(a),.183),(.009,.009,.003),(.9,.68,.44),0,n=6,rows=3)
 if role=='Geisha':
  m.ellipsoid((0,1.81,-.08),(.14,.09,.08),HAIR,2,n=24,rows=10)
  m.box((0,.94,-.20),(.28,.17,.12),obi,0,.025)
  for j in range(2):m.tube([(-.16,1.83+j*.025,-.02),(.17,1.85+j*.025,-.05)],[.006,.006],(.85,.57,.19),2,n=6)
 elif role=='ShrineMaiden':
  m.loft([(0,1.10,-.13,.09,.027),(0,1.56,-.105,.085,.045),(0,1.73,-.10,.10,.06)],HAIR,2,n=20)
  m.box((0,1.57,-.15),(.19,.055,.035),(.73,.12,.10),2,.01)
 elif role=='Chef':
  m.loft([(0,1.77,-.01,.14,.112),(0,1.91,-.01,.155,.12),(0,1.96,-.01,.12,.09)],IVORY,2,n=24,flute=.025)
  m.box((0,.86,.16),(.31,.51,.021),IVORY,0,.005)
  for yy in (.75,.90):m.tube([(-.12,yy,.177),(.12,yy,.177)],[.003,.003],(.34,.28,.19),0,n=5)
 elif role=='Samurai':
  for j in range(5):
   m.loft([(0,1.02+j*.062,0,.235,.155),(0,1.067+j*.062,0,.235,.155)],(.11,.18,.21),1,n=28)
   m.tube([(-.17,1.046+j*.062,.14),(.17,1.046+j*.062,.14)],[.0045,.0045],(.68,.20,.12),1,n=6)
  for side in (-1,1):
   for j in range(3):m.box((side*.285,1.40-j*.047,0),(.16,.043,.26),(.13,.20,.23),9 if side<0 else 11,.01)
  m.loft([(0,1.77,-.02,.17,.14),(0,1.88,-.02,.12,.10),(0,1.95,-.02,.035,.035)],(.10,.15,.18),2,n=24)
  for side in (-1,1):m.tube([(side*.03,1.89,.11),(side*.09,1.98,.10),(side*.13,2.0,.08)],[.012,.009,.003],(.78,.52,.16),2,n=8)
  m.tube([(-.24,.95,-.04),(-.42,.60,-.07),(-.54,.30,-.09)],[.023,.02,.012],INK,0,n=10)
  m.tube([(-.24,.95,-.04),(-.17,1.09,-.02)],[.023,.018],(.50,.24,.12),0,n=10)
 elif role in ('Elder','Gardener'):
  m.loft([(0,1.77,-.01,.255,.235),(0,1.81,-.01,.25,.23),(0,1.94,-.01,.045,.045)],(.60,.45,.24),2,n=32,flute=.015)
  # Ink ribs on conical woven hats.
  for a in np.linspace(0,math.tau,12,endpoint=False):m.tube([(math.cos(a)*.25,1.81,math.sin(a)*.23-.01),(math.cos(a)*.045,1.94,math.sin(a)*.045-.01)],[.0028,.0018],(.25,.17,.09),2,n=5)
  if role=='Elder':m.loft([(0,1.48,.065,.01,.012),(0,1.58,.085,.065,.027)],(.69,.67,.58),2,n=20)
  else:
   m.loft([(0,.92,-.23,.16,.10),(0,1.26,-.23,.20,.13)],(.49,.31,.13),1,n=24,flute=.04)
   for y in np.linspace(.95,1.25,7):m.tube([(-.16,y,-.34),(.16,y,-.34)],[.005,.005],(.72,.50,.23),1,n=5)
 elif role=='Merchant':
  m.loft([(0,1.77,-.02,.13,.105),(0,1.91,-.04,.105,.085),(0,1.96,-.045,.025,.025)],(.15,.20,.26),2,n=24)
  m.box((.18,.85,.13),(.15,.18,.10),(.47,.26,.11),0,.025)
 # Slightly fuller faces improve street-distance readability without replacing rigs.
 for i,((x,y,z),bone) in enumerate(zip(m.v,m.bones)):
  if bone==2:m.v[i]=(x*1.10,1.48+(y-1.48)*1.035,z*1.045)
 return m

def skin_weights(mesh,path):
 s=path.read_text();buf=bytearray.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',s)[1]);n=len(mesh.v)
 for i,((x,y,z),bone) in enumerate(zip(mesh.v,mesh.bones)):
  pairs=[(bone,1.)]
  if bone in (3,6):
   knee=np.clip((y-.32)/.16,0,1);pairs=[(bone,float(knee)),(bone+1,float(1-knee))]
   if y<.18:
    a=float(np.clip((y-.12)/.06,0,1));pairs=[(bone+1,a),(bone+2,1-a)]
  elif bone==0 and .24<y<.80:
   # Cloth hem follows a restrained amount of leg swing, not a rigid bell.
   leg=3 if x<0 else 6;a=float(np.clip((.80-y)/.55,0,1))*.40
   pairs=[(0,1-a),(leg,a)]
  elif bone==1 and y<1.20:
   a=float(np.clip((y-.88)/.30,0,1));pairs=[(0,1-a),(1,a)]
  # Smooth elbow skin at the actual elbow location, not separate sleeve rings.
  elif bone in (9,11):
   a=float(np.clip((1.26-y)/.08,0,1));pairs=[(bone,1-a),(bone+1,a)]
  pairs=[p for p in pairs if p[1]>.00001]
  total=sum(v for _,v in pairs);pairs=[(b,v/total) for b,v in pairs]
  weights=[v for _,v in pairs]+[0.]*(4-len(pairs));bones=[b for b,_ in pairs]+[0]*(4-len(pairs))
  struct.pack_into('<4f4I',buf,i*80+48,*weights,*bones)
 s=re.sub(r'(?m)^    _typelessdata: .*','    _typelessdata: '+buf.hex(),s)
 # Widen per-bone culling bounds for blended vertices and stance/gestures.
 s=re.sub(r'  m_BonesAABB:.*?(?=  m_VariableBoneCountWeights:)', '  m_BonesAABB:\n'+''.join('  - m_Min: {x: -2, y: -2, z: -2}\n    m_Max: {x: 2, y: 2, z: 2}\n' for _ in range(13)),s,flags=re.S)
 path.write_text(s)

def generate():
 OUT.mkdir(exist_ok=True);native.OUT=OUT
 meta=Path(str(OUT)+'.meta')
 if not meta.exists():meta.write_text('fileFormatVersion: 2\nguid: '+hashlib.md5(str(OUT.relative_to(ROOT)).encode()).hexdigest()+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
 mat=native.material('Village-painted-cloth')
 p=OUT/'Village-painted-cloth.mat';s=p.read_text();s=s.replace('- _Pigment: 0.22','- _Pigment: 0.12');p.write_text(s)
 template=(ASSETS/'Generated/Renovation/Resident-0-0.asset').read_text();models={}
 for i,role in enumerate(ROLES):
  mesh=resident(role,i);g=mesh.save('Living-'+role,True,template);skin_weights(mesh,OUT/('Living-'+role+'.asset'));models[role]=g
 return models,mat

def apply(scene,places=None):
 models,mat=generate();count=0;roles={}
 old={guid(ASSETS/'Generated/VillageFinish'/('Resident-'+role+'.asset')):role for role in ROLES}
 for i,b in list(scene.blocks.items()):
  if scene.kind(i)!=137 or '  m_Enabled: 1\n' not in b or scene.name(scene.owner(i)).startswith('Living villager ink'):continue
  g=re.search(r'm_Mesh: \{fileID: 4300000, guid: (\w+)',b)
  if not g:continue
  role=old.get(g[1]) or next((r for r,gg in models.items() if gg==g[1]),None)
  if not role:continue
  scene.set(i,'m_Mesh',f'{{fileID: 4300000, guid: {models[role]}, type: 2}}')
  scene.blocks[i]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mat}, type: 2}}\n',scene.blocks[i],flags=re.S)
  roles[i]=role;count+=1
 # Existing thirteen skins retain all skeletons and named quest objects.
 assert count>=13,count
 return {'retainedResidentRigs':count,'costumeRoles':list(models),'models':models,'material':mat}

if __name__=='__main__':print(json.dumps(generate(),indent=2))

def add_component(scene,go,classname,fields):
 component=scene.alloc();script=ASSETS/'Scripts'/(classname+'.cs')
 scene.blocks[component]=f'''--- !u!114 &{component}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {guid(script)}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: Assembly-CSharp::Sunward.{classname}
'''+fields
 scene.blocks[go]=scene.blocks[go].replace('  m_Component:\n','  m_Component:\n  - component: {fileID: '+str(component)+'}\n')
 return component

def clone_actor(scene,source,name,position,yaw,role,models,mat):
 root=scene.transform(source);transforms=set()
 def visit(t):
  transforms.add(t)
  children=re.search(r'  m_Children:(.*?)(?=  m_Father:)',scene.blocks[t],re.S)[1]
  for child in map(int,re.findall(r'fileID: (-?\d+)',children)):visit(child)
 visit(root)
 objects={scene.owner(t) for t in transforms};ids=set()
 for go in objects:ids.add(go);ids.update(scene.refs(go))
 mapping={old:scene.alloc() for old in sorted(ids)}
 for old,new in mapping.items():
  raw=scene.blocks[old]
  raw=re.sub(r'^--- !u!(\d+) &-?\d+',lambda m:f'--- !u!{m[1]} &{new}',raw)
  raw=re.sub(r'fileID: (-?\d+)',lambda m:'fileID: '+str(mapping.get(int(m[1]),int(m[1]))),raw)
  scene.blocks[new]=raw
 go=mapping[source];t=mapping[root]
 scene.set(go,'m_Name',json.dumps(name));scene.set(t,'m_LocalPosition',fmt(position));scene.set(t,'m_LocalRotation','{x: 0, y: %g, z: 0, w: %g}'%(math.sin(yaw*math.pi/360),math.cos(yaw*math.pi/360)))
 # Parent under the same village root, not underneath the source resident.
 parent=int(re.search(r'm_Father: \{fileID: (-?\d+)\}',scene.blocks[t])[1])
 scene.blocks[parent]=scene.blocks[parent].replace('  m_Children:\n',f'  m_Children:\n  - {{fileID: {t}}}\n')
 for old,new in mapping.items():
  if scene.kind(new)==114 and any(x in scene.blocks[new] for x in ('Sunward.MarketWalker','Sunward.VillageResident','Sunward.ResidentPerformance')):scene.disabled(new)
  if scene.kind(new)==137 and '  m_Enabled: 1\n' in scene.blocks[new]:
   scene.set(new,'m_Mesh',f'{{fileID: 4300000, guid: {models[role]}, type: 2}}')
   scene.blocks[new]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mat}, type: 2}}\n',scene.blocks[new],flags=re.S)
 gait=next(i for i in scene.refs(go) if scene.kind(i)==114 and 'Sunward.ResidentLocomotion' in scene.blocks[i])
 return go,gait

def artistic_props():
 native.OUT=OUT
 violin=Mesh();wood=(.43,.20,.075);iv=(.80,.67,.37)
 # Ribbed waist, twin rounded bouts, f holes, bridge, four strings and scroll.
 violin.loft([(0,-.09,.025,.025,.022),(0,-.06,.025,.075,.028),(0,-.005,.025,.085,.029),(0,.04,.025,.044,.023),(0,.085,.025,.07,.028),(0,.125,.025,.06,.026)],wood,n=24,flute=.02)
 violin.box((0,.19,.025),(.023,.15,.025),INK,bevel=.003)
 violin.ellipsoid((0,.28,.025),(.027,.030,.025),wood,n=12,rows=6)
 violin.box((0,.012,.058),(.055,.015,.012),iv,bevel=.002)
 for x in np.linspace(-.013,.013,4):violin.tube([(x,-.06,.062),(x,.25,.045)],[.0012,.0012],iv,n=4)
 for side in (-1,1):violin.tube([(side*.044,-.036,.055),(side*.037,-.01,.057),(side*.047,.02,.055)],[.0025,.0025,.0025],INK,n=5)
 for i,v in enumerate(violin.v):violin.v[i]=tuple(np.array(v)*1.50)
 bow=Mesh();bow.tube([(-.34,0,0),(.36,0,0)],[.003,.003],(.38,.19,.08),n=6);bow.tube([(-.33,-.024,0),(.35,-.024,0)],[.0018,.0018],IVORY,n=4)
 bokken=Mesh();
 bokken.loft([(0,-.19,0,.025,.023),(0,.03,0,.027,.024)],(.15,.10,.07),n=12)
 for y in np.linspace(-.18,.015,11):bokken.tube([(-.022,y,-.015),(.022,y+.012,.015)],[.006,.006],(.70,.48,.22),n=5)
 bokken.loft([(0,.025,0,.090,.060),(0,.050,0,.090,.060)],(.20,.115,.055),n=18)
 bokken.tube([(0,.05,0),(0,.36,.022),(0,.66,.058),(0,.88,.09)],[.033,.029,.023,.008],(.64,.40,.17),n=14,groove=.03)
 bokken.tube([(-.021,.08,.020),(-.020,.38,.045),(-.014,.66,.080),(0,.87,.098)],[.004,.004,.003,.001],(.23,.13,.055),n=5)

 bowl=Mesh();bowl.loft([(0,0,0,.045,.045),(0,.04,0,.07,.07),(0,.055,0,.075,.075)],(.28,.14,.085),n=24);bowl.loft([(0,.056,0,.066,.066),(0,.057,0,.065,.065)],(.89,.80,.58),n=24)
 cup=Mesh();cup.loft([(0,0,0,.052,.052),(0,.10,0,.067,.067)],(.68,.76,.63),n=20);cup.loft([(0,.10,0,.055,.055),(0,.103,0,.052,.052)],(.19,.26,.12),n=20)
 return {'cup':cup.save('Tea-cup'), 'violin':violin.save('Violin-carved-body'),'bow':bow.save('Violin-horsehair-bow'),'bokken':bokken.save('Practice-bokken'),'bowl':bowl.save('Rice-bowl')}

def ground(x,z):
 data=json.loads((ASSETS/'Data/Valley.json').read_text())['world']['terrain'];u=(x-data['minX'])/data['step'];v=(-z-data['minZ'])/data['step'];i=max(0,min(data['nx']-2,int(u)));j=max(0,min(data['nz']-2,int(v)));u-=i;v-=j
 h=data['heights'];w=data['nx'];return (h[j*w+i]*(1-u)+h[j*w+i+1]*u)*(1-v)+(h[(j+1)*w+i]*(1-u)+h[(j+1)*w+i+1]*u)*v

base_apply=apply
def apply(scene,places=None):
 report=base_apply(scene);models=report['models'];mat=report['material'];props=artistic_props();native.OUT=OUT
 # Place performers once; the pass may safely run again for authoring iteration.
 if not any(scene.kind(i)==1 and scene.name(i)=='Dojo student · left' for i in scene.blocks):
  source=next(i for i in scene.blocks if scene.kind(i)==1 and scene.name(i).startswith('Ambient shopper'))
  for n,(name,x,z,yaw,role,activity) in enumerate([
   ('Dojo student · left',-2.7,28.60,0,'Samurai',1),('Dojo student · right',1.7,28.60,0,'Samurai',1),
   ('Food hall · violin performer',14.6,12.1,-90,'Geisha',3),('Food hall · guest one',6.8,7,90,'Chef',2),('Food hall · guest two',6.8,12.5,90,'Merchant',2)]):
   go,gait=clone_actor(scene,source,name,(x,ground(x,z)+(.17 if activity==3 else .07),z),yaw,role,models,mat)
   rig=int(re.search(r'hips: \{fileID: (-?\d+)\}',scene.blocks[gait])[1]);rig=int(re.search(r'm_Father: \{fileID: (-?\d+)\}',scene.blocks[rig])[1]);riggo=scene.owner(rig)
   add_component(scene,riggo,'ResidentPerformance',f'  activity: {activity}\n  gait: {{fileID: {gait}}}\n  variation: {n}\n')
 # The diners enter through the west door and return to their meal. No
 # walking through the old analytic building footprint or through side walls.
 for n,go in enumerate(i for i in list(scene.blocks) if scene.kind(i)==1 and scene.name(i).startswith('Food hall · guest')):
  walker=next(i for i in scene.refs(go) if scene.kind(i)==114 and 'Sunward.MarketWalker' in scene.blocks[i])
  scene.set(walker,'m_Enabled',1)
  z=7 if n==0 else 12.5
  route=[(6,ground(6,9.35)+.07,9.35),(2.5,ground(2.5,9.35),9.35),(2.5,ground(2.5,10.65),10.65),(6,ground(6,10.65)+.07,10.65),(6.8,ground(6.8,z)+.07,z)]
  raw=scene.blocks[walker];raw=re.sub(r'  route:.*?(?=  phase:)', '  route:\n'+''.join('  - '+fmt(p)+'\n' for p in route),raw,flags=re.S)
  raw=re.sub(r'  phase: .*',f'  phase: {n*9+2}',raw)
  for key in ('foodHallRoute','mealWaypoint','initialWaypoint','conversationPartner'):
   raw=re.sub(r'  '+key+r':.*\n','',raw)
  scene.blocks[walker]=raw+'  foodHallRoute: 1\n  mealWaypoint: 4\n  initialWaypoint: 0\n'
 # Attach performances to all original rigs, preserving named quest components.
 existing_gaits=set(int(m[1]) for b in scene.blocks.values() if (m:=re.search(r'  gait: \{fileID: (-?\d+)\}',b)))
 for gait,b in list(scene.blocks.items()):
  if scene.kind(gait)!=114 or 'Sunward.ResidentLocomotion' not in b or gait in existing_gaits:continue
  hip=int(re.search(r'hips: \{fileID: (-?\d+)\}',b)[1]);rig=int(re.search(r'm_Father: \{fileID: (-?\d+)\}',scene.blocks[hip])[1]);riggo=scene.owner(rig)
  add_component(scene,riggo,'ResidentPerformance',f'  activity: 0\n  gait: {{fileID: {gait}}}\n  variation: {len(existing_gaits)}\n');existing_gaits.add(gait)
 # Props attach to actual arm bones and therefore follow the gesture animation.
 for perf,b in list(scene.blocks.items()):
  if scene.kind(perf)!=114 or 'Sunward.ResidentPerformance' not in b or '  m_Enabled: 1\n' not in b:continue
  gait=int(re.search(r'gait: \{fileID: (-?\d+)\}',b)[1]);g=scene.blocks[gait]
  activity=int(re.search(r'activity: (\d+)',b)[1]);hands=list(map(int,re.findall(r'fileID: (-?\d+)',re.search(r'  forearms:(.*?)(?=  game:)',g,re.S)[1])))
  prefix=f'Living performance {perf} '
  if any(scene.kind(i)==1 and scene.name(i).startswith(prefix) for i in scene.blocks):continue
  if activity==1:
   sword=scene.add(prefix+'wooden practice sword',props['bokken'],mat,parent=hands[1],p=(.10,-.24,.052));scene.blocks[perf]+=f'  practiceSword: {{fileID: {scene.transform(sword)}}}\n'
  elif activity==3:
   violin=scene.add(prefix+'carved violin',props['violin'],mat,parent=hands[0],p=(-.04,-.05,.15));bow=scene.add(prefix+'bow',props['bow'],mat,parent=hands[1],p=(.07,.12,.15))
   scene.blocks[perf]+=f'  instrument: {{fileID: {scene.transform(violin)}}}\n  bow: {{fileID: {scene.transform(bow)}}}\n'
  elif activity==2:
   bowl=scene.add(prefix+'rice bowl',props['bowl'],mat,parent=hands[0],p=(-.10,-.24,.052));cup=scene.add(prefix+'tea cup',props['cup'],mat,parent=hands[1],p=(.10,-.24,.052))
   scene.blocks[perf]+=f'  mealBowl: {{fileID: {scene.transform(bowl)}}}\n  teaCup: {{fileID: {scene.transform(cup)}}}\n'
 # Keep shoppers on neat street-side routes with conversation pauses.
 walkers=[i for i,b in scene.blocks.items() if scene.kind(i)==114 and 'Sunward.MarketWalker' in b and '  m_Enabled: 1\n' in b and '  foodHallRoute: 1\n' not in b]
 pockets=[(-2,1.8),(-2.7,2.3),(2,-4.5),(2.7,-4.2),(-2.1,-1.3),(2.1,1.6)]
 roots=[]
 for n,w in enumerate(walkers):
  go=scene.owner(w);t=scene.transform(go);x,z=pockets[n%len(pockets)];p=(x,ground(x,z),z);scene.set(t,'m_LocalPosition',fmt(p));roots.append(t)
  route=[(x,ground(x,z),z),(x,ground(x,z+1.1),z+1.1)]
  raw=scene.blocks[w];raw=re.sub(r'  route:.*?(?=  phase:)', '  route:\n'+''.join('  - '+fmt(p)+'\n' for p in route),raw,flags=re.S);scene.blocks[w]=raw
 for n,w in enumerate(walkers):
  scene.blocks[w]=re.sub(r'  conversationPartner:.*\n','',scene.blocks[w]);scene.blocks[w]+=f'  conversationPartner: {{fileID: {roots[n^1] if n^1<len(roots) else roots[0]}}}\n'
 from resident_audio import generate as generate_audio
 audio=generate_audio()
 for perf,b in list(scene.blocks.items()):
  if scene.kind(perf)!=114 or 'Sunward.ResidentPerformance' not in b:continue
  for field,g in audio.items():
   if field=='sole':continue
   scene.blocks[perf]=re.sub(r'  '+field+r':.*\n','',scene.blocks[perf])
   scene.blocks[perf]+=f'  {field}: {{fileID: 8300000, guid: {g}, type: 3}}\n'
 for gait,b in list(scene.blocks.items()):
  if scene.kind(gait)==114 and 'Sunward.ResidentLocomotion' in b:
   scene.set(gait,'footstep','{fileID: 8300000, guid: '+audio['sole']+', type: 3}')
 # Explicit skinned contours share the exact body mesh, bones and weights.
 contour=OUT/'Villager-ink-contour.mat'
 text=(ASSETS/'Generated/InkWorld/Ink-contour.mat').read_text().replace('m_Name: Ink-contour','m_Name: Villager-ink-contour')
 text=re.sub(r'- _InkPixels: .*','- _InkPixels: 1.8',text)
 text=re.sub(r'- _InkWorldMax: .*','- _InkWorldMax: 0.022',text)
 contour.write_text(text);ink=guid(contour)
 outlines=0
 for skin,b in list(scene.blocks.items()):
  if scene.kind(skin)!=137 or '  m_Enabled: 1\n' not in b or scene.name(scene.owner(skin)).startswith('Living villager ink'):continue
  g=re.search(r'm_Mesh: \{fileID: 4300000, guid: (\w+)',b)
  if not g or g[1] not in models.values():continue
  label='Living villager ink '+str(skin)
  if any(scene.kind(i)==1 and scene.name(i)==label for i in scene.blocks):continue
  oldt=scene.transform(scene.owner(skin));raw=scene.blocks[oldt]
  parent=int(re.search(r'm_Father: \{fileID: (-?\d+)\}',raw)[1])
  go=scene.add(label,g[1],ink,parent=parent,p=vec(raw,'m_LocalPosition'),scale=vec(raw,'m_LocalScale'))
  t=scene.transform(go);scene.set(t,'m_LocalRotation',re.search(r'm_LocalRotation: (.*)',raw)[1])
  for c in list(scene.refs(go)):
   if scene.kind(c) in (23,33):del scene.blocks[c]
  renderer=scene.alloc();new=re.sub(r'^--- !u!137 &-?\d+',f'--- !u!137 &{renderer}',b)
  new=re.sub(r'  m_GameObject: .*',f'  m_GameObject: {{fileID: {go}}}',new)
  new=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {ink}, type: 2}}\n',new,flags=re.S)
  new=new.replace('  m_CastShadows: 1','  m_CastShadows: 0').replace('  m_ReceiveShadows: 1','  m_ReceiveShadows: 0')
  scene.blocks[renderer]=new
  scene.blocks[go]=re.sub(r'  m_Component:\n.*?(?=  m_Layer:)',f'  m_Component:\n  - component: {{fileID: {t}}}\n  - component: {{fileID: {renderer}}}\n',scene.blocks[go],flags=re.S)
  outlines+=1
 report['skinnedInkOutlines']=outlines
 report.update({'trainingStudents':2,'foodHallPerformers':3,'conversationWalkers':len(walkers)})
 return report
