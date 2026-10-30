"""Apply the twelve-request village pass to the existing saved Windflower scene.
Authoring command only. Does not run on the user's PC or rebuild the project.
"""
import json,math,re,random,collections
from pathlib import Path
import numpy as np
from native import *
from characters import resident,ROLES
from environment import rock,tree,vegetation,house,gate,TIMBER

class Sources:
 def __init__(self,scene):
  self.scene=scene;self.data=json.loads((ASSETS/'Data/Valley.json').read_text());self.records=[m for a in self.data['assets'] for m in a.get('meshes',[])]
  text=(ASSETS/'Generated/ValleyMeshes.asset').read_text();self.native={};self.fileids={}
  for b in text.split('--- !u!43 &')[1:]:
   n=re.search(r'm_Name: Valley-(\d+)',b)
   if n:self.native[int(n[1])]='--- !u!43 &'+b;self.fileids[int(b.splitlines()[0])]=int(n[1])
  self.prefab=Scene(ASSETS/'Generated/TownV3.prefab');self.prefab_guid=guid(ASSETS/'Generated/TownV3.prefab')
  self.instance=next(i for i in scene.blocks if scene.kind(i)==1001 and 'preserved painted valley' in scene.blocks[i])
  self.objects={int(self.prefab.name(i).split('-')[-1]):i for i in self.prefab.blocks if self.prefab.kind(i)==1 and self.prefab.name(i).startswith('TownV3-')}
  # Home roof renderers have HomeRoof-* names; map by their actual mesh IDs.
  for i,b in self.prefab.blocks.items():
   if self.prefab.kind(i)!=33:continue
   match=re.search(r'm_Mesh: \{fileID: (-?\d+), guid: 1aa5e7ba7e3b6c64889eadc3b9e05f0b',b)
   if match and int(match[1]) in self.fileids:self.objects[self.fileids[int(match[1])]]=self.prefab.owner(i)
  self.groups=[];start=0
  for a in self.data['assets']:
   if a.get('meshes'):self.groups.append((start,list(range(start,start+len(a['meshes']))),a['name']))
   start+=len(a.get('meshes',[]))
  self.grid={(round(p[0],3),round(p[2],3)):p[1] for p in self.positions(751)}
  self.overrides={}
  for m in re.finditer(r'    - target: \{fileID: (-?\d+),[^\n]+\}\n      propertyPath: ([^\n]+)\n      value: ([^\n]*)',scene.blocks[self.instance]):self.overrides[(int(m[1]),m[2].strip("'"))]=m[3]
 def patch(self,target,key,value=None,reference=None):
  raw=self.scene.blocks[self.instance]
  pattern=r'    - target: \{fileID: '+str(target)+r',[^\n]+\}\n      propertyPath: [\x27]?'+re.escape(key)+r'[\x27]?\n      value:[ \t]*[^\n]*\n      objectReference: [^\n]*\n'
  record=f'    - target: {{fileID: {target}, guid: {self.prefab_guid}, type: 3}}\n      propertyPath: {key}\n      value: {value if value is not None else ""}\n      objectReference: {reference or "{fileID: 0}"}\n'
  matches=list(re.finditer(pattern,raw));count=len(matches)
  if matches:
   # Unity serializes empty reference-only values as "value:". Match that
   # form, replace the first occurrence and remove duplicates of this property.
   first=True
   def replace(match):
    nonlocal first
    value=record if first else '';first=False;return value
   raw=re.sub(pattern,replace,raw)
  if not count:raw=raw.replace('    m_RemovedComponents:',record+'    m_RemovedComponents:')
  self.scene.blocks[self.instance]=raw
  self.overrides[(target,key)]=str(value)
 def visible(self,n):
  if n not in self.native:return False
  if 'indexCount: 0\n' in self.native[n]:return False
  if n in self.objects:
   go=self.objects[n];r=self.prefab.component(go,23)
   if self.overrides.get((go,'m_IsActive'))=='0' or self.overrides.get((r,'m_Enabled'))=='0':return False
   if '  m_Enabled: 0\n' in self.prefab.blocks[r] and self.overrides.get((r,'m_Enabled'))!='1':return False
   return True
  return any(self.scene.kind(i)==33 and re.search(r'm_Mesh: \{fileID: (-?\d+), guid: 1aa5e7ba7e3b6c64889eadc3b9e05f0b',b) and self.fileids.get(int(re.search(r'm_Mesh: \{fileID: (-?\d+)',b)[1]))==n for i,b in self.scene.blocks.items())
 def hide(self,n):
  if n in self.objects:self.patch(self.objects[n],'m_IsActive','0')
  for i,b in list(self.scene.blocks.items()):
   if self.scene.kind(i)!=33:continue
   m=re.search(r'm_Mesh: \{fileID: (-?\d+), guid: 1aa5e7ba7e3b6c64889eadc3b9e05f0b',b)
   if m and self.fileids.get(int(m[1]))==n:
    owner=self.scene.owner(i)
    # Unpacked source visual, never its separate physics proxy.
    if owner in self.scene.blocks and self.scene.kind(owner)==1:self.scene.set(owner,'m_IsActive',0)
 def positions(self,n):
  s=self.native[n];nv=int(re.search(r'm_VertexCount: (\d+)',s)[1]);raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',s)[1]);stride=int(re.search(r'm_DataSize: (\d+)',s)[1])//nv
  return np.array([struct.unpack_from('<3f',raw,k*stride) for k in range(nv)])
 def bounds(self,ids):
  points=np.concatenate([self.positions(n) for n in ids if n in self.native]);return points.min(0),points.max(0)
 def kind(self,n):return self.data['materials'][self.records[n]['material']]['kind']
 def set_material(self,n,mat):
  if n in self.objects:
   go=self.objects[n];self.patch(go,'m_IsActive','1');r=self.prefab.component(go,23);self.patch(r,'m_Enabled','1');self.patch(r,'m_Materials.Array.data[0]',reference=f'{{fileID: 2100000, guid: {mat}, type: 2}}')
  for i,b in list(self.scene.blocks.items()):
   if self.scene.kind(i)!=33:continue
   m=re.search(r'm_Mesh: \{fileID: (-?\d+), guid: 1aa5e7ba7e3b6c64889eadc3b9e05f0b',b)
   if m and self.fileids.get(int(m[1]))==n:
    owner=self.scene.owner(i);r=self.scene.component(owner,23)
    if r:self.scene.set(r,'m_Enabled',1);self.scene.blocks[r]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mat}, type: 2}}\n',self.scene.blocks[r],flags=re.S)
 def trim_region(self,n,predicate,label):
  raw=self.native[n];dtype='<u4' if 'm_IndexFormat: 1' in raw else '<u2'
  ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',raw)[1]),dtype=dtype).reshape(-1,3)
  v=self.positions(n);remove=predicate(v[ix]).all(axis=1)
  if not remove.any():return 0
  keep=ix[~remove]
  if not len(keep):self.hide(n);return int(remove.sum())
  copy=re.sub(r'^--- !u!43 &-?\d+', '--- !u!43 &4300000',raw)
  copy=re.sub(r'm_Name: .*','m_Name: '+label+'-'+str(n),copy,count=1)
  copy=re.sub(r'indexCount: \d+','indexCount: '+str(keep.size),copy,count=1)
  copy=re.sub(r'(?m)^  m_IndexBuffer: .*','  m_IndexBuffer: '+keep.astype(dtype).tobytes().hex(),copy)
  copy=repaired_normals(copy)
  self.native[n]=copy
  path=OUT/(label+'-'+str(n)+'.asset');path.write_text('%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'+copy);g=guid(path)
  ref=f'{{fileID: 4300000, guid: {g}, type: 2}}'
  if n in self.objects:self.patch(self.prefab.component(self.objects[n],33),'m_Mesh',reference=ref)
  for i,b in list(self.scene.blocks.items()):
   if self.scene.kind(i)!=33:continue
   m=re.search(r'm_Mesh: \{fileID: (-?\d+), guid: 1aa5e7ba7e3b6c64889eadc3b9e05f0b',b)
   if m and self.fileids.get(int(m[1]))==n:self.scene.set(i,'m_Mesh',ref)
  return int(remove.sum())
 def ground(self,x,z):
  t=self.data['world']['terrain'];xx=(x-t['minX'])/t['step'];zz=(-z-t['minZ'])/t['step'];i=max(0,min(t['nx']-2,int(xx)));j=max(0,min(t['nz']-2,int(zz)));u=xx-i;v=zz-j
  # Original physical grid + the same small visual relief; new roots seat slightly below it.
  h00=t['heights'][j*t['nx']+i];h10=t['heights'][j*t['nx']+i+1];h01=t['heights'][(j+1)*t['nx']+i];h11=t['heights'][(j+1)*t['nx']+i+1]
  x0=t['minX']+i*t['step'];z0=-(t['minZ']+j*t['step']);step=t['step']
  h00=self.grid.get((round(x0,3),round(z0,3)),h00);h10=self.grid.get((round(x0+step,3),round(z0,3)),h10);h01=self.grid.get((round(x0,3),round(z0-step,3)),h01);h11=self.grid.get((round(x0+step,3),round(z0-step,3)),h11)
  h=h00+(h10-h00)*u+(h01-h00)*v if u+v<=1 else h11+(h01-h11)*(1-u)+(h10-h11)*(1-v)
  return h

def replace_residents(scene):
 mat=material('Character-cloth-and-features');template=(ASSETS/'Generated/Renovation/Resident-0-0.asset').read_text()
 models={role:resident(role).save('Resident-'+role,True,template) for role in ROLES}
 groups={}
 for i,b in scene.blocks.items():
  if scene.kind(i)!=137:continue
  match=re.search(r'm_RootBone: \{fileID: (-?\d+)\}',b)
  if match:groups.setdefault(int(match[1]),[]).append(i)
 count=0
 for root,candidates in groups.items():
  source=next((re.match(r'Skinned · NPC-(\d+)-\d+$',scene.name(scene.owner(i))) for i in candidates if re.match(r'Skinned · NPC-(\d+)-\d+$',scene.name(scene.owner(i)))),None)
  if not source:continue
  live=[i for i in candidates if '  m_Enabled: 1\n' in scene.blocks[i]]
  if not live:continue
  index=int(source[1]);rig=int(re.search(r'm_Father: \{fileID: (-?\d+)\}',scene.blocks[root])[1]);npc=int(re.search(r'm_Father: \{fileID: (-?\d+)\}',scene.blocks[rig])[1])
  shopper=scene.name(scene.owner(npc)).startswith('Ambient shopper')
  # Keep named villagers' established gardening/merchant/elder/shrine roles.
  role=(['Chef','Samurai','Geisha','Merchant','Gardener','ShrineMaiden'][index] if shopper else ['Gardener','Merchant','Elder','Samurai','ShrineMaiden','Geisha','Gardener'][index])
  chosen=live[0]
  for i in candidates:
   if i!=chosen:scene.disabled(i)
  scene.set(chosen,'m_Mesh',f'{{fileID: 4300000, guid: {models[role]}, type: 2}}')
  raw=scene.blocks[chosen];raw=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mat}, type: 2}}\n',raw,flags=re.S);scene.blocks[chosen]=raw
  scene.set(scene.owner(chosen),'m_Name',json.dumps('Villager · '+role));count+=1
 assert count==13, ('Expected seven named villagers and six shoppers',count)
 return count

def replace_rocks(scene):
 shapes=[rock(i).save('Carved-rock-'+str(i)) for i in range(8)];mats=[material('Stone-'+n,family='stone') for n in ['sandy','granite','basalt','weathered']];count=0
 for i,b in list(scene.blocks.items()):
  if scene.kind(i)!=1 or not scene.name(i).startswith('Grounded stone '):continue
  mf=scene.component(i,33);r=scene.component(i,23);t=scene.transform(i)
  g=re.search(r'guid: (\w+)',re.search(r'm_Mesh: (.*)',scene.blocks[mf])[1])[1]
  meta=next((ASSETS/'Generated/Waterside').glob('Stone-'+str(int(re.search(r'Grounded stone (\d+)',scene.name(i))[1]))+'.asset'))
  raw=meta.read_text();center=vec(raw,'m_Center');extent=vec(raw,'m_Extent');size=extent*2
  scene.set(t,'m_LocalPosition',fmt([center[0],center[1]-extent[1],center[2]]));scene.set(t,'m_LocalScale',fmt(size));scene.set(mf,'m_Mesh',f'{{fileID: 4300000, guid: {shapes[count%8]}, type: 2}}')
  scene.blocks[r]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mats[count%4]}, type: 2}}\n',scene.blocks[r],flags=re.S);count+=1
 return count

def replace_trees(scene,src):
 woodmat=material('Living-bark',family='wood',wind=.12);leafmat=material('Living-canopy',wind=.45)
 models=[]
 for seed in range(6):
  wood,leaves=tree(seed);models.append((wood.save('Tree-'+str(seed)+'-bark'),leaves.save('Tree-'+str(seed)+'-canopy')))
 count=0;bamboo=0
 for first,ids,name in src.groups:
  if name!='TownV3' or not any(src.kind(n)=='leaves' for n in ids) or not any(src.visible(n) for n in ids):continue
  lo,hi=src.bounds(ids);size=hi-lo
  if size[1]<2 or size[1]>16 or max(size[0],size[2])>24:continue
  center=(lo+hi)/2;trunks=[o for o in src.data['world']['obstacles'] if .24<o['r']<.8]
  trunk=min(trunks,key=lambda o:(o['x']-center[0])**2+(-o['z']-center[2])**2)
  x,z=(trunk['x'],-trunk['z']) if math.hypot(trunk['x']-center[0],-trunk['z']-center[2])<2.8 else (center[0],center[2])
  if first>=840:
   mesh=vegetation(first,'bamboo').save('Bamboo-'+str(bamboo%4)) if bamboo<4 else guid(OUT/f'Bamboo-{bamboo%4}.asset');scene.add('Living bamboo · '+str(bamboo),mesh,leafmat,p=(x,src.ground(x,z)-.025,z));bamboo+=1
  else:
   kind=0 if any(src.data['materials'][src.records[n]['material']].get('texture')==1 for n in ids) else 1 if any(src.data['materials'][src.records[n]['material']].get('texture')==3 for n in ids) else 2
   model=models[kind+(count%2)*3];scale=max(.72,min(1.5,size[1]/4.7));pos=(x,src.ground(x,z)-.045,z)
   for part,mat,label in [(model[0],woodmat,'bark and branching limbs'),(model[1],leafmat,'cupped blossom and leaf crown')]:scene.add('Living tree '+str(count)+' · '+label,part,mat,p=pos,scale=(scale,scale,scale))
   count+=1
  for n in ids:src.hide(n)
 return count,bamboo

def replace_houses(scene,src):
 mats=[material('House-cedar',family='wood'),material('House-plaster',family='plaster'),material('House-foundation',family='stone'),material('House-kawara',family='roof')];count=0
 for first,ids,name in src.groups:
  if name!='TownV3' or not any(src.kind(n)=='roof' for n in ids):continue
  lo,hi=src.bounds(ids);size=hi-lo
  if not(4<size[0]<13 and 3<size[2]<12 and 2.5<size[1]<9) or not any(src.visible(n) for n in ids):continue
  center=(lo+hi)/2;boxes=src.data['world']['boxes'][:19];box=min(boxes,key=lambda q:(q['x']-center[0])**2+(-q['z']-center[2])**2)
  home=first==600
  if home:box={'x':-34,'z':16,'halfX':5,'halfZ':4}
  if not home and (abs(box['x']-center[0])>1.4 or abs(-box['z']-center[2])>1.4):continue
  x,z=box['x'],-box['z'];w=box['halfX']*2;d=box['halfZ']*2
  yaw=0 if home else 90 if (x<0 and (x>-20 or x<-37)) else -90 if x!=0 else 180
  if abs(yaw)==90:w,d=d,w
  parts=house(w,d,count,home)
  for mesh,mat,label in zip(parts,mats,['joined cedar, frames and rafters','recessed plaster and shoji','laid foundation','closed supported tile roof']):
   if not mesh.v:continue
   g=mesh.save('House-'+str(first)+'-'+label.split()[0]);obj=scene.add(('Home' if home else 'Village house '+str(count))+' · '+label,g,mat,p=(x,.02 if home else src.ground(x,z)-.05,z))
   scene.set(scene.transform(obj),'m_LocalRotation','{x: 0, y: %g, z: 0, w: %g}'%(math.sin(math.radians(yaw)/2),math.cos(math.radians(yaw)/2)))
   if home:
    renderer=scene.component(obj,23)
    for component,b in list(scene.blocks.items()):
     if scene.kind(component)==114 and 'Assembly-CSharp::Sunward.HomeCutaway' in b:scene.blocks[component]=b.rstrip()+'\n  - {fileID: '+str(renderer)+'}\n'
  for n in ids:
   if not home or src.kind(n)=='roof' or src.prefab.name(src.objects.get(n,0)).startswith('HomeRoof'):src.hide(n)
  count+=1
 return count

def replace_plants(scene,src):
 mat=material('Living-groundcover',wind=.60);models=[]
 for kind in ['grass','flower']:
  for i in range(4):models.append(vegetation(i,kind).save(kind+'-'+str(i)))
 count=0;budgets={False:360,True:180};placed={False:0,True:0}
 for n,record in enumerate(src.records):
  if n not in src.native or not src.visible(n):continue
  family=src.kind(n);lo,hi=src.bounds([n]);size=hi-lo
  flower=family=='wash' and hi[1]<.9 and lo[1]>-.5 and size[0]>4 and size[2]>4
  if family not in ('grass','grass-blade') and not flower:continue
  # Read referenced components, retaining original authored planting positions.
  raw=src.native[n];ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',raw)[1]),dtype='<u4' if 'm_IndexFormat: 1' in raw else '<u2').reshape(-1,3)
  v=src.positions(n);cells={}
  for t in ix:
   p=v[t].mean(0);cell=(round(p[0]/.55),round(p[2]/.55));cells[cell]=p
  for cell,p in sorted(cells.items(),key=lambda item:abs(item[1][0])+abs(item[1][2])):
   # Retain paths/arena visibility. The data marks water and structures separately.
   if placed[flower]>=budgets[flower]:break
   if abs(p[0])<3.5 or ((p[0]-35)**2+p[2]**2)<17**2 or src.ground(p[0],p[2])<-.30:continue
   if ((p[0]+15)/3.05)**2+((p[2]+22)/2.05)**2<1.15**2:continue
   x,z=p[0],p[2];kind=(4 if flower else 0)+count%4
   scene.add(('Dimensional flowers' if flower else 'Folded meadow blades')+' · '+str(count),models[kind],mat,p=(x,src.ground(x,z)-.025,z),scale=(.7,.7,.7));count+=1;placed[flower]+=1
  src.hide(n)
 return count

def repair_bridge(scene,src):
 mat=material('Bridge-solid-timber',family='wood')
 for n in range(800,805):src.set_material(n,mat)
 # A closed plank deck follows the SAME walking arch. No physics/collider replacement.
 deck=Mesh()
 for j in range(48):
  u=(j+.5)/48;x=-27.8+9.6*u;y=.10+.42*max(0,math.sin(math.pi*u))**1.5
  deck.box((x,y-.055,14),(.197,.11,2.52),TIMBER,bevel=.012)
 g=deck.save('Second-bridge-closed-deck');scene.add('Second bridge · solid arched planks',g,mat)
 return 1

def arena_entrance(scene,src):
 # Existing gameplay entry point remains E at (12.8,0,0).
 mat=material('Bell-cedar',family='wood');bronze=material('Bell-patinated-bronze');rope=material('Bell-braided-rope')
 for m,material_,label in zip(gate(),[mat,bronze,rope],['joined timber frame','cast bronze bell','hanging woven pull']):scene.add('Hollow Bell entrance · '+label,m.save('Arena-'+label.split()[0]),material_,p=(12.8,src.ground(12.8,0)-.02,0))
 # Remove the old stick at (12,0) and adjacent legacy lantern at (13,-1),
 # including pieces batched with other village objects. Preserve other lamps.
 removed=[]
 def in_region(v):return (v[...,0]>11.5)&(v[...,0]<13.8)&(v[...,2]>-1.8)&(v[...,2]<.65)&(v[...,1]>-.6)&(v[...,1]<3)
 for n in range(len(src.records)):
  if n not in src.native or not src.visible(n) or src.kind(n) not in ('wood','stone','wash','ink'):continue
  lo,hi=src.bounds([n])
  if hi[0]<11.5 or lo[0]>13.8 or hi[2]<-1.8 or lo[2]>.65:continue
  count=src.trim_region(n,in_region,'Arena-entry-cleared')
  if count:removed.append(n)
 for i,b in list(scene.blocks.items()):
  if scene.kind(i)!=1 or scene.name(i)!='Trunk / rock collider':continue
  t=scene.transform(i);p=vec(scene.blocks[t],'m_LocalPosition')
  if any(np.linalg.norm(p[[0,2]]-np.array(q))<.15 for q in [(13,-1),(12,0)]):
   for c in scene.refs(i):
    if scene.kind(c) in (65,136):scene.disabled(c)
 for i,b in list(scene.blocks.items()):
  if scene.kind(i)==114 and 'Assembly-CSharp::Sunward.EnvironmentReviewState' in b:
   assert '  removedObstacles:' in b
   scene.blocks[i]=b.rstrip()+'\n  - {x: 13, y: 0, z: -1}\n  - {x: 12, y: 0, z: 0}\n'

 return removed

def clear_lantern_ink(scene,src):
 places=[]
 for i in scene.blocks:
  if scene.kind(i)!=1 or not scene.name(i).startswith(('Kasuga lantern','Arena perimeter lantern','Bridge approach · clear')):continue
  t=scene.transform(i)
  if t:places.append(vec(scene.blocks[t],'m_LocalPosition'))
 def inside(v):
  mask=np.zeros(v.shape[:-1],dtype=bool)
  for p in places:mask|=(abs(v[...,0]-p[0])<.7)&(abs(v[...,2]-p[2])<.7)&(v[...,1]>p[1]-.25)&(v[...,1]<p[1]+2.35)
  return mask
 removed=0
 for n in range(len(src.records)):
  if n in src.native and src.visible(n) and src.kind(n)=='ink':removed+=src.trim_region(n,inside,'Lantern-legacy-ink-cleared')
 return removed

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 folder=Path(str(OUT)+'.meta')
 if not folder.exists():folder.write_text('fileFormatVersion: 2\nguid: 47de22b8c85e4fa1ae173be0bcf628bc\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
 scene=Scene(ASSETS/'Scenes/Windflower.unity')
 if any(scene.name(i).startswith('Village house 0 · joined cedar') for i in scene.blocks):raise SystemExit('Already authored: restore the pre-pass scene before regenerating. No edits made.')
 src=Sources(scene)
 report={};report['residents']=replace_residents(scene);report['rocks']=replace_rocks(scene);report['trees'],report['bamboo']=replace_trees(scene,src);report['houses']=replace_houses(scene,src);report['groundcover']=replace_plants(scene,src);report['bridge']=repair_bridge(scene,src);report['arenaRemovedSourceIds']=arena_entrance(scene,src);report['lanternLegacyInkTrianglesRemoved']=clear_lantern_ink(scene,src)
 # Point lights inside opaque lantern chambers must not cast blocked self shadows.
 report['lanternPointShadowFixes']=0
 for i,b in list(scene.blocks.items()):
  if scene.kind(i)==108 and '  m_Type: 2\n' in b:
   scene.blocks[i]=re.sub(r'(  m_Shadows:\n    m_Type:) \d+',r'\g<1> 0',b);report['lanternPointShadowFixes']+=1
 for i,b in list(scene.blocks.items()):
  if scene.kind(i)==23 and scene.name(scene.owner(i)).startswith(('Folded meadow blades','Dimensional flowers')):scene.set(i,'m_CastShadows',0)
 scene.save();(Path(__file__).parent/'authoring-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 from paint_details import main as paint
 paint()
 refs=set(re.findall(r'guid: ([0-9a-f]{32})',(ASSETS/'Scenes/Windflower.unity').read_text()))
 for mat in OUT.glob('*.mat'):refs.update(re.findall(r'guid: ([0-9a-f]{32})',mat.read_text()))
 for path in OUT.glob('*.asset'):
  if guid(path) not in refs:path.unlink();Path(str(path)+'.meta').unlink()
 for directory in [OUT,ASSETS/'Textures/VillageFinish']:
  for path in directory.iterdir():
   if path.suffix in ('.asset','.mat','.meta'):path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
if __name__=='__main__':main()
