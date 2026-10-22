"""Author articulated ink spirits in the existing stable enemy prefab identities.
No player meshes, damage/reward definitions, scenes or external models replaced.
Call apply(scene) from the combined living-world pass; scene is not changed here.
"""
from pathlib import Path
import sys, re, math, json, struct, collections
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
from native import Mesh, Scene, ASSETS, guid, fmt, vec
OUT=ASSETS/'Generated/LivingCombat'
PALETTES={
 'wisp':((.16,.38,.38),(.86,.93,.73),(.85,.32,.12)),
 'reed':((.25,.36,.19),(.85,.77,.47),(.52,.15,.08)),
 'heavy':((.29,.34,.29),(.69,.66,.48),(.76,.30,.12)),
 'ranged':((.32,.34,.54),(.94,.86,.59),(.75,.15,.14)),
 'elite':((.58,.075,.06),(.93,.74,.42),(.15,.19,.23)),
 'boss':((.19,.22,.22),(.72,.57,.28),(.76,.16,.065))}
INK=(.023,.021,.017)

def save(mesh,name):
 path=OUT/(name+'.asset');mesh.write(path);return guid(path)

def shell(path):
 raw=path.read_text();n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);data=bytearray.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',raw)[1]);stride=len(data)//n
 p=np.array([struct.unpack_from('<3f',data,i*stride) for i in range(n)]);nn=np.array([struct.unpack_from('<3f',data,i*stride+12) for i in range(n)])
 sums=collections.defaultdict(lambda:np.zeros(3));keys=np.round(p*10000).astype(int)
 for k,v in zip(keys,nn):sums[tuple(k)]+=v
 compact=bytearray()
 for point,k,normal in zip(p,keys,nn):
  normal=sums[tuple(k)] if np.linalg.norm(sums[tuple(k)])>1e-7 else normal
  compact.extend(struct.pack('<6f',*point,*(normal/max(np.linalg.norm(normal),1e-7))))
 raw=re.sub(r'(?m)^    _typelessdata: .*','    _typelessdata: '+compact.hex(),raw)
 raw=re.sub(r'(?m)^    m_DataSize: .*','    m_DataSize: '+str(len(compact)),raw)
 channels=''.join(f'    - stream: 0\n      offset: {12 if i==1 else 0}\n      format: 0\n      dimension: {3 if i<2 else 0}\n' for i in range(14))
 raw=re.sub(r'    m_Channels:\n.*?(?=    m_DataSize:)','    m_Channels:\n'+channels,raw,flags=re.S)
 raw=re.sub(r'm_Extent: \{[^}]+\}',lambda m:'m_Extent: '+fmt(vec(m[0],'m_Extent')+.12),raw)
 out=OUT/('Contour-'+path.name);out.write_text(raw);return guid(out)

def armor(mesh,p,size,color,rows=4):
 x,y,z=p;w,h,d=size
 for j in range(rows):
  t=j/(rows-1);mesh.box((x,y+h*(.5-t),z+.015*math.sin(t*math.pi)),(w*(1+.15*t),h/rows*.9,d),np.array(color)*(1-.12*t),bevel=.025)
  for xx in [-.28*w,.28*w]:mesh.ellipsoid((x+xx,y+h*(.5-t),z+d*.55),(.018,.018,.009),(.83,.62,.25),n=8,rows=4)

def mask(kind,face,accent):
 m=Mesh();m.loft([(0,-.12,0,.12,.12),(0,-.04,0,.21,.16),(0,.14,0,.23,.15),(0,.26,0,.16,.12)],face,n=20)
 # Mask cheeks, carved beak/nose and sharp raised sumi eyebrows.
 m.ellipsoid((0,-.02,.155),(.105,.075,.09),np.array(face)*.84,n=16,rows=6)
 for side in [-1,1]:
  m.tube([(side*.03,.13,.153),(side*.11,.16,.157),(side*.18,.11,.13)],[.020,.025,.008],INK,n=7)
  m.ellipsoid((side*.105,.092,.161),(.065,.026,.012),INK,n=12,rows=5)
  m.ellipsoid((side*.104,.093,.173),(.022,.012,.005),(.98,.51,.14),n=8,rows=4)
  m.tube([(side*.03,-.08,.155),(side*.10,-.07,.17),(side*.17,-.015,.14)],[.007,.009,.003],INK,n=6)
  if kind not in ('ranged','wisp'):
   m.tube([(side*.16,.20,0),(side*.25,.33,-.01),(side*.23,.49,.015)],[.065,.043,.002],accent,n=9,groove=.10)
  if kind in ('elite','boss'):
   m.tube([(side*.07,.22,.08),(side*.18,.35,.05),(side*.32,.40,.02)],[.04,.035,.002],(.82,.62,.23),n=9)
 # Lower jaw is shaped around the cheek instead of a cylindrical NPC head.
 m.loft([(0,-.16,.01,.09,.10),(0,-.11,.06,.15,.13),(0,-.055,.06,.17,.13)],np.array(face)*.72,n=14)
 if kind=='ranged':
  for side in [-1,1]:m.face([(0,.19,-.04),(side*.32,.06,.0),(side*.4,.32,-.08),(0,.43,0)],accent)
 if kind=='boss':
  m.box((0,.13,-.07),(.48,.07,.28),accent,bevel=.025)
  m.tube([(-.19,.25,-.08),(0,.34,-.11),(.19,.25,-.08)],[.035,.05,.035],(.81,.63,.24),n=9)
 return m

def parts(kind):
 body,face,accent=PALETTES[kind];wide=1.25 if kind in ('heavy','boss') else 1
 torso=Mesh()
 torso.loft([(0,-.08,0,.16*wide,.14),(0,.05,0,.23*wide,.16),(0,.30,-.025,.32*wide,.18),(0,.45,-.015,.25*wide,.16)],body,n=18,flute=.025)
 armor(torso,(0,.24,.17),(.5*wide,.34,.10),accent)
 torso.box((0,.015,.0),(.48*wide,.08,.33),(.12,.11,.075),bevel=.025)
 # Hanging lamellar skirt follows waist while leaving leg joints unobstructed.
 for side in [-1,1]:armor(torso,(side*.19*wide,-.12,.12),(.19,.27,.08),body,rows=3)
 if kind in ('heavy','boss'):
  for side in [-1,1]:
   torso.ellipsoid((side*.30*wide,.35,-.01),(.18,.15,.22),np.array(face)*.70,n=12,rows=6)
   for k in range(3):torso.tube([(side*.29*wide,.44,-.12+k*.11),(side*.41*wide,.52,-.12+k*.11)],[.045,.002],accent,n=7)
 if kind=='ranged':
  for k in range(5):
   a=k*math.tau/5;torso.tube([(0,.12,-.16),(math.cos(a)*.45,.18+math.sin(a)*.43,-.19)],[.035,.012],face,n=7)
 if kind=='wisp':
  for k in range(3):torso.tube([(0,.02,-.08),(math.sin(k*2)*.22,-.29,-.14),(math.sin(k*2+.4)*.15,-.50,-.2)],[.12,.065,.001],body,n=9)
 result={'torso':(torso,(0,.68,0)),'mask':(mask(kind,face,accent),(0,1.18,.05))}
 for side,label in [(-1,'left'),(1,'right')]:
  arm=Mesh();arm.tube([(0,0,0),(side*.07,-.20,0),(side*.06,-.43,.07)],[.11,.09,.065],body,n=12,groove=.05)
  armor(arm,(side*.03,-.09,.055),(.21,.20,.14),accent,rows=3)
  arm.ellipsoid((side*.06,-.45,.08),(.09,.09,.09),face,n=12,rows=6)
  for finger in range(3):arm.tube([(side*.03+(finger-1)*.04,-.46,.10),(side*.03+(finger-1)*.045,-.54,.17)],[.022,.006],face,n=7)
  if kind=='wisp':
   for k in range(5):
    reach=.33+k*.07;arm.face([(0,-.03,0),(side*reach,-.10+k*.11,-.02),(side*(reach+.12),-.23+k*.09,-.08),(side*.03,-.26,-.04)],np.array(body)*(1+k*.07))
  if kind in ('reed','elite') and side==1:
   arm.tube([(0,-.38,.10),(0,-.56,.10),(0,-.83,.10)],[.023,.025,.015],(.23,.14,.065),n=9)
   arm.face([(-.04,-.66,.10),(-.06,-.87,.10),(.015,-.96,.12),(.055,-.68,.11)],(.76,.72,.49))
   arm.tube([(-.08,-.63,.11),(.08,-.63,.11)],[.018,.018],(.83,.58,.18),n=8)
  result[label+' arm']=(arm,(side*.31*wide,1.05,0))
  leg=Mesh();leg.tube([(0,0,0),(side*.02,-.25,.02),(0,-.46,0)],[.11,.075,.07],body,n=12,groove=.025)
  armor(leg,(0,-.31,.06),(.15,.23,.09),accent,rows=3)
  leg.loft([(0,-.57,.055,.10,.16),(0,-.51,.065,.11,.18),(0,-.46,.02,.065,.09)],INK,n=12)
  for toe in [-1,0,1]:leg.tube([(toe*.055,-.53,.16),(toe*.065,-.545,.23)],[.025,.003],face,n=7)
  result[label+' leg']=(leg,(side*.15,.62,0))
 # Distinct spirit anatomy instead of six recoloured humanoids.
 if kind=='wisp':
  bodymesh=Mesh()
  bodymesh.loft([(0,-.20,0,.025,.025),(0,-.03,0,.11,.10),(0,.21,0,.21,.12),(0,.40,0,.14,.10)],body,n=16,flute=.08)
  for j in range(5):
   x=(j-2)*.075;bodymesh.tube([(x,.32,0),(x*1.5,.49,-.04),(x*1.2,.66,-.08)],[.046,.027,.001],np.array(body)*(1+j*.08),n=8)
  result['torso']=(bodymesh,(0,.68,0))
  for side,label in [(-1,'left'),(1,'right')]:
   wing=Mesh()
   for j in range(7):
    tip=(side*(.38+j*.065),.12+j*.025,-.025*j)
    points=[np.array(p) for p in [(0,0,0),tip,(tip[0]+side*.09,tip[1]-.10,tip[2]-.04),(side*.03,-.16,-.03)]]
    shade=np.array(body)*(1+j*.055);back=[p-np.array([0,0,.014]) for p in points]
    wing.face(points,shade);wing.face(list(reversed(back)),shade*.8)
    for edge in range(4):wing.face([points[edge],back[edge],back[(edge+1)%4],points[(edge+1)%4]],shade*.7)
    wing.tube([(0,0,0),tip],[.016,.002],face,n=6)
   result[label+' arm']=(wing,(side*.14,1.03,0))
   trail=Mesh();trail.tube([(0,0,0),(side*.14,-.21,-.10),(side*.08,-.39,-.17)],[.09,.05,.001],body,n=9)
   result[label+' leg']=(trail,(side*.09,.63,0))
 if kind=='ranged':
  kite=Mesh()
  kite.face([(0,-.20,-.04),(-.53,.22,0),(0,.67,.025),(.53,.22,0)],face)
  kite.face([(0,-.20,-.055),(.53,.22,-.02),(0,.67,.005),(-.53,.22,-.02)],np.array(face)*.7)
  kite.tube([(-.53,.22,.015),(0,.23,.035),(.53,.22,.015)],[.012,.02,.012],INK,n=7)
  kite.tube([(0,-.20,-.025),(0,.68,.045)],[.018,.012],accent,n=7)
  for side in [-1,1]:
   kite.tube([(side*.06,.23,.05),(side*.18,.32,.05),(side*.30,.23,.04),(side*.18,.14,.04),(side*.06,.23,.05)],[.015]*5,accent,n=6)
  result['torso']=(kite,(0,.68,0))
  for side,label in [(-1,'left'),(1,'right')]:
   stream=Mesh();stream.tube([(0,0,0),(side*.13,-.20,-.04),(side*.24,-.41,.06),(side*.12,-.58,.09)],[.045,.034,.026,.002],accent,n=7)
   result[label+' arm']=(stream,(side*.47,.92,0))
   trail=Mesh();trail.tube([(0,0,0),(side*.06,-.23,-.08),(side*.15,-.41,-.02)],[.035,.028,.001],face,n=7)
   result[label+' leg']=(trail,(side*.10,.59,0))
 if kind=='heavy':
  # Bouldered hulk: broad hunched spine, long stone fists and a squat base.
  for label in ['left arm','right arm']:
   m,p=result[label];m.ellipsoid((0,-.38,.06),(.20,.23,.18),np.array(face)*.72,n=12,rows=6)
   for j in range(3):m.tube([(-.14+j*.14,-.32,.20),(-.13+j*.13,-.48,.20)],[.012,.006],INK,n=6)
  back=Mesh();back.ellipsoid((0,.25,-.13),(.45,.34,.25),np.array(body)*.8,n=12,rows=7);torso.merge(back)
 if kind=='boss':
  bell=Mesh();bell.loft([(0,-.14,0,.48,.28),(0,-.07,0,.48,.28),(0,.05,0,.38,.24),(0,.32,0,.27,.21),(0,.49,0,.21,.17)],body,n=24,flute=.04)
  for yy,rx,rz in [(-.12,.49,.29),(-.04,.46,.28),(.27,.30,.23),(.43,.245,.195)]:
   bell.loft([(0,yy-.018,0,rx,rz),(0,yy+.018,0,rx,rz)],(.72,.55,.23),n=24)
  for j in range(9):
   a=j*math.tau/9
   bell.tube([(math.cos(a)*.46,-.05,math.sin(a)*.27),(math.cos(a)*.31,.23,math.sin(a)*.225)],[.009,.009],accent,n=6)
  bell.ellipsoid((0,.13,.24),(.11,.12,.035),(.83,.64,.25),n=14,rows=7)
  result['torso']=(bell,(0,.68,0))
 return result

def apply(scene=None):
 OUT.mkdir(parents=True,exist_ok=True)
 folder=Path(str(OUT)+'.meta')
 if not folder.exists():folder.write_text('fileFormatVersion: 2\nguid: 70de978f5e9045f38b37b5cf0f61cb45\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
 mat=OUT/'Spirit-painted.mat';raw=(ASSETS/'Generated/InkWorld/Ink-painted-plaster.mat').read_text()
 raw=re.sub(r'm_Name: .*','m_Name: Spirit-painted',raw,count=1)
 for key,val in [('_ArtStrength',0),('_VertexTint',1),('_Wind',0),('_NormalStrength',0),('_SurfaceKind',0)]:raw=re.sub(r'(?m)^    - '+key+r': .*',f'    - {key}: {val}',raw)
 mat.write_text(raw);mg=guid(mat);ig=guid(ASSETS/'Generated/InkWorld/Ink-contour.mat')
 report={}
 for kind in PALETTES:
  path=ASSETS/f'Generated/Enemy-{kind}.prefab';s=Scene(path)
  root=next(i for i in s.blocks if s.kind(i)==1 and s.name(i)=='Enemy-'+kind);rt=s.transform(root)
  # Keep original imported geometry for provenance, but only authored joints draw.
  # Re-running removes previous generated children before adding the same IDs.
  generated=[i for i in s.blocks if s.kind(i)==1 and s.name(i).startswith('Spirit ')]
  for i in generated:
   t=s.transform(i);s.blocks[rt]=s.blocks[rt].replace(f'  - {{fileID: {t}}}\n','')
   for c in s.refs(i):s.blocks.pop(c,None)
   s.blocks.pop(i,None)
  for i in list(s.blocks):
   if s.kind(i)==23:s.disabled(i)
  triangles=0
  for name,(m,p) in parts(kind).items():
   meshname='Spirit-'+kind+'-'+name.replace(' ','-');g=save(m,meshname);triangles+=len(m.tri)
   obj=s.add('Spirit '+name,g,mg,parent=rt,p=p)
   t=s.transform(obj);outline=s.add('Spirit '+name+' ink',shell(OUT/(meshname+'.asset')),ig,parent=t)
   r=s.component(outline,23);s.set(r,'m_CastShadows',0);s.set(r,'m_ReceiveShadows',0)
  path.write_text(s.header+''.join(s.blocks.values()))
  report[kind]={'meshTriangles':triangles,'articulatedParts':6,'outlinedParts':6,'prefabRootPreserved':root}
 (ROOT/'tools/living-world/combat-report.json').write_text(json.dumps(report,indent=2))
 return report

if __name__=='__main__':print(json.dumps(apply(),indent=2))
