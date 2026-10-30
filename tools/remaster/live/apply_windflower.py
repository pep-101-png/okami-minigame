#!/usr/bin/env python3
"""Offline authoring of the existing Windflower scene. Never invoked on the user's PC.
Preserves every existing object, gameplay component, transform, collider and ID.
Replaces selected visual bindings and adds native village geometry/ambient animals.
"""
from pathlib import Path
import sys,re,json,hashlib,struct,gzip,subprocess,collections,math
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];PROJECT=ROOT/'Sunward-Unity';A=PROJECT/'Assets'
sys.path.insert(0,str(ROOT/'tools/village'));import native
from native import Scene,Mesh,vec,fmt
OUT=A/'OkamiRemaster/Windflower';SOURCE=A/'OkamiRemaster/Village';BASE='1ba3426de6557d7bd494f6ba0deb7ef55aa6a354'
REFERENCE=ROOT/'tools/remaster/reference';SCENE=A/'Sunward/Scenes/Windflower.unity';TEMPLATE=(A/'Sunward/Generated/Renovation/Detail-18.asset').read_text()
GROUPS=json.loads(Path(__file__).with_name('source_groups.json').read_text());REPORT={};native.OUT=OUT/'Meshes'

def guid(p):
 p=Path(p);meta=Path(str(p)+'.meta')
 if meta.exists():return re.search(r'^guid: (\w+)',meta.read_text(),re.M)[1]
 g=hashlib.sha256(('SunwardNativeWindflower/'+str(p.relative_to(A))).encode()).hexdigest()[:32]
 if p.is_dir():kind='folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n'
 elif p.suffix=='.mat':kind='NativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 2100000\n'
 elif p.suffix=='.asset':kind='NativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 4300000\n'
 elif p.suffix=='.shader':kind='ShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n'
 elif p.suffix=='.cs':kind='MonoImporter:\n  externalObjects: {}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n'
 elif p.suffix=='.png':
  template=next((SOURCE/'Demo/Textures').glob('*.png.meta')).read_text();meta.write_text(re.sub(r'^guid: \w+','guid: '+g,template,flags=re.M));return g
 else:kind='TextScriptImporter:\n  externalObjects: {}\n'
 meta.write_text('fileFormatVersion: 2\nguid: '+g+'\n'+kind+'  userData:\n  assetBundleName:\n  assetBundleVariant:\n');return g

def native_meshes():
 dt=np.dtype([('p','<f4',3),('n','<i2',3),('c','u1',4),('uv','<f4',2)])
 data=gzip.decompress((REFERENCE/'DemoGeometry/VillageWorld.bytes').read_bytes());off=12;out=[]
 assert struct.unpack_from('<ii',data)==(0x32565753,1)
 def string():
  nonlocal off
  n=struct.unpack_from('<i',data,off)[0];off+=4;s=data[off:off+n].decode();off+=n;return s
 for _ in range(struct.unpack_from('<i',data,8)[0]):
  name=string();mat=string();coll,nv,ni=struct.unpack_from('<Bii',data,off);off+=9
  v=np.frombuffer(data,dt,nv,off).copy();off+=nv*dt.itemsize;ix=np.frombuffer(data,'<i4',ni,off).reshape(-1,3).copy();off+=ni*4
  out.append(dict(name=name,mat=mat,v=v,ix=ix))
 assert off==len(data);return out

GUIDS={re.search(r'^guid: (\w+)',m.read_text(),re.M)[1]:m.with_suffix('') for m in A.rglob('*.meta') if re.search(r'^guid: (\w+)',m.read_text(),re.M)}
MODELS=native_meshes()
def index(m):return int(m['name'].split('-')[1]) if m['name'].startswith('Mesh-') else -1
def reference(text,key):
 m=re.search(re.escape(key)+(r' \{fileID: ' if key.endswith('-') else r': \{fileID: ')+r'(-?\d+)(?:, guid: (\w+))?',text);return (int(m[1]),m[2]) if m else (0,None)
def mat_path(m):return REFERENCE/'DemoMaterials'/('Mat-'+m['mat']+'.mat')
def source_texture(m,slot='_MainTex'):
 text=mat_path(m).read_text();match=re.search(r'- '+slot+r':\n        m_Texture:.*guid: (\w+)',text)
 return GUIDS[match[1]] if match else None

def write_mesh(name,v,ix,normals,colors,uv):
 assert len(ix)>0 and np.isfinite(v).all() and np.isfinite(normals).all()
 # Weld only byte-identical complete vertices; preserve UV seams and authored normals.
 records=np.column_stack([v,normals,colors,uv]).astype('<f4');records[records==0]=0
 _,first=np.unique(records,axis=0,return_index=True)
 first=np.sort(first)
 # Use an explicit full-record lookup so index ordering is stable across NumPy versions.
 mapping={records[i].tobytes():j for j,i in enumerate(first)};mapped=np.array([mapping[row.tobytes()] for row in records],dtype=np.int32)
 records=records[first];ix=mapped[ix];_,keep=np.unique(np.sort(ix,axis=1),axis=0,return_index=True);ix=ix[np.sort(keep)]
 valid=(ix[:,0]!=ix[:,1])&(ix[:,1]!=ix[:,2])&(ix[:,2]!=ix[:,0]);ix=ix[valid]
 used=np.unique(ix);renumber=np.full(len(records),-1,dtype=np.int32);renumber[used]=np.arange(len(used));records=records[used];ix=renumber[ix]

 # Repair only invalid source normals after removing redundant opposite faces.
 missing=np.linalg.norm(records[:,3:6],axis=1)<1e-7;repaired=int(missing.sum())
 if repaired:
  accumulated=np.zeros((len(records),3));positions=records[:,:3];face_normals=np.cross(positions[ix[:,1]]-positions[ix[:,0]],positions[ix[:,2]]-positions[ix[:,0]])
  for corner in range(3):np.add.at(accumulated,ix[:,corner],face_normals)
  length=np.linalg.norm(accumulated,axis=1);accumulated[length<1e-8]=(0,1,0);accumulated/=np.maximum(np.linalg.norm(accumulated,axis=1,keepdims=True),1e-8);records[missing,3:6]=accumulated[missing]

 p=OUT/'Meshes'/(name+'.asset');m=Mesh();m.v=records[:,:3].tolist();m.c=records[:,6:9].tolist();m.uv=records[:,10:12].tolist();m.bones=[0]*len(records);m.tri=ix.tolist();m.write(p,template=TEMPLATE)
 raw=p.read_text();buffer=records.tobytes();raw=re.sub(r'(?m)^    _typelessdata: .*','    _typelessdata: '+buffer.hex(),raw);raw=re.sub(r'(?m)^    m_DataSize: .*','    m_DataSize: '+str(len(buffer)),raw);p.write_text(raw)
 return guid(p),dict(vertices=len(records),triangles=len(ix),invalidSourceNormalsRepaired=repaired)

def rotation(yaw):
 a=math.radians(yaw);return np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
def live_material(source):
 text=source.read_text();text=re.sub(r'(?m)^  m_EnableInstancingVariants: .*','  m_EnableInstancingVariants: 1',text)
 out=OUT/'Materials'/('Original-'+source.stem+'.mat');out.write_text(text);return guid(out)

def write_group(name,parts,transform,normal_transform=None):
 by_mat=collections.defaultdict(list);report=[]
 for m in parts:by_mat[m['mat']].append(m)
 for i,(mat,group) in enumerate(by_mat.items()):
  vertices=[];normals=[];colors=[];uv=[];indices=[];offset=0
  for m in group:
   vertices.append(transform(m['v']['p'].astype(float)))
   n=m['v']['n'].astype(float)/32767
   n=normal_transform(m['v']['p'].astype(float),n) if normal_transform else n
   n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-10);normals.append(n)
   colors.append(m['v']['c'].astype(float)/255);uv.append(m['v']['uv']);indices.append(m['ix']+offset);offset+=len(m['v'])
  mesh,stats=write_mesh(name+'-'+str(i),np.concatenate(vertices),np.concatenate(indices),np.concatenate(normals),np.concatenate(colors),np.concatenate(uv))
  report.append(dict(mesh=mesh,material=live_material(mat_path(group[0])),sourceMeshes=[m['name'] for m in group],**stats))
 return report

def hide_visual_tree(scene,go):
 renderer=scene.component(go,23)
 if renderer:scene.set(renderer,'m_Enabled',0)
 t=scene.transform(go)
 if t:
  children=[int(x) for x in re.findall(r'fileID: (-?\d+)',re.search(r'  m_Children:.*?(?=  m_Father:)',scene.blocks[t],re.S)[0])]
  for child in children:
   owner=scene.owner(child)
   if owner:hide_visual_tree(scene,owner)

def replace_houses(scene):
 groups={};report=[]
 for key in ['WillowHouse','CarpHouse','CommunityHall']:
  spec=GROUPS[key];parts=[m for m in MODELS if spec['indices'][0]<=index(m)<=spec['indices'][1]];r=rotation(180-spec['yaw'])
  body=next(m for m in parts if index(m)==spec['bodyIndex']);b=body['v']['p']@r.T;center=(b.min(0)+b.max(0))/2;center[1]=0
  size=b.max(0)-b.min(0);points=np.concatenate([m['v']['p']@r.T for m in parts]);height=points[:,1].max()
  converted=write_group(key,parts,lambda v:v@r.T-center,lambda v,n:n@r.T)
  groups[key]=(converted,size,height)
 for go in list(scene.blocks):
  name=scene.name(go)
  if scene.kind(go)!=1 or not re.match(r'Village house \d+ .*joined cedar',name):continue
  number=int(re.search(r'Village house (\d+)',name)[1]);t=scene.transform(go)
  # Match the established physical building box, rather than moving streets/NPCs.
  pos=vec(scene.blocks[t],'m_LocalPosition');world=json.loads((A/'Sunward/Data/Valley.json').read_text())['world'];box=min(world['boxes'][:19],key=lambda q:(q['x']-pos[0])**2+(-q['z']-pos[2])**2)
  q=re.search(r'm_LocalRotation: \{x: ([^,]+), y: ([^,]+), z: ([^,]+), w: ([^}]+)',scene.blocks[t]);yaw=2*math.degrees(math.atan2(float(q[2]),float(q[4])))
  width=box['halfX']*2;depth=box['halfZ']*2
  if abs(math.sin(math.radians(yaw)))>.7:width,depth=depth,width
  key='CommunityHall' if number==8 else 'CarpHouse' if number in [0,3,10] else 'WillowHouse';parts,size,height=groups[key]
  old_roots=[o for o in scene.blocks if scene.kind(o)==1 and scene.name(o).startswith('Village house '+str(number)+' ·')]
  roof=next(o for o in old_roots if 'closed supported' in scene.name(o));oldmesh=GUIDS[reference(scene.blocks[scene.component(roof,33)],'m_Mesh')[1]].read_text();target_height=float(vec(oldmesh,'m_Center')[1]+vec(oldmesh,'m_Extent')[1]);target_height=7.6 if key=='CommunityHall' else max(4.8 if key=='CarpHouse' else 3.9,min(7.8,target_height))
  scale=np.array([width/size[0],target_height/height,depth/size[2]])
  for o in old_roots:hide_visual_tree(scene,o)
  added=[]
  for part in parts:
   obj=scene.add('Native Windflower · '+key+' house '+str(number),part['mesh'],part['material'],parent=t,scale=scale);added.append(obj)
  report.append(dict(house=number,sourceGroup=key,sourceKind=GROUPS[key]['kind'],position=pos.tolist(),scale=scale.tolist(),existingColliderBox=box,newObjects=added,oldVisualRoots=old_roots))
 assert len(report)==14,len(report);REPORT['houses']=report;REPORT['houseMeshes']=groups
 # Avoid serializing ndarray/helper tuple in the report.
 REPORT['houseMeshes']={k:v[0] for k,v in groups.items()}

def replace_bridges(scene):
 parts=[m for m in MODELS if 417<=index(m)<=420];deck=next(m for m in parts if index(m)==419)['v']['p'];xs=np.unique(deck[:,0]);ys=np.array([deck[np.isclose(deck[:,0],x,atol=1e-5),1].max() for x in xs]);lo=float(xs.min());hi=float(xs.max());sx=9.6/(hi-lo);sz=2.52/np.ptp(deck[:,2]);
 for m in MODELS:
  if not m['name'].startswith('Village Breeze detail batch'):continue
  p=m['v']['p'];inside=(p[:,0]>9)&(p[:,0]<17)&(p[:,2]>4)&(p[:,2]<7.2)&(p[:,1]<2)
  keep=inside[m['ix']].all(1)
  if keep.any():parts.append(dict(m,ix=m['ix'][keep]))
 def f(x):
  u=np.clip((x-lo)/(hi-lo),0,1);return .10+.42*np.maximum(0,np.sin(np.pi*u))**1.5-np.interp(x,xs,ys)
 def position(p):
  out=p.copy();out[:,0]=-4.8+(p[:,0]-lo)*sx;out[:,1]+=f(p[:,0]);out[:,2]=(p[:,2]-5.6)*sz;return out
 def normal(p,n):
  d=(f(p[:,0]+.001)-f(p[:,0]-.001))/.002;out=n.copy();out[:,0]=(n[:,0]-d*n[:,1])/sx;out[:,2]=n[:,2]/sz;return out
 mesh=write_group('ST2-bridge',parts,position,normal);new=[]
 for go in list(scene.blocks):
  if scene.kind(go)==1 and (scene.name(go).startswith('Ink world · vermilion bridge at') or scene.name(go)=='Second bridge · solid arched planks'):hide_visual_tree(scene,go)
 for z in [-8,14]:
  for part in mesh:new.append(scene.add('Native Windflower · ST2 bridge '+str(z),part['mesh'],part['material'],p=(-23,0,z)))
 # Existing baked bridge visual batches were already hidden by the prior ink pass;
 # preserve their components and both original arched physics meshes.
 REPORT['bridges']=dict(meshes=mesh,newObjects=new,walkDeckX=[-27.8,-18.2],walkDeckZ=[-8,14],walkWidth=2.52,source='ST2 r200.dat/3.SCR plus recovered authored 27 board/ink detail')
 from build import Sources
 legacy=Sources(scene);hidden=[]
 for number in [795,800]:
  go=legacy.objects[number];renderer=legacy.prefab.component(go,23);legacy.patch(renderer,'m_Enabled','0');hidden.append(renderer)
 REPORT['bridges']['hiddenLegacyDeckRenderers']=hidden


def replace_bell_frame(scene):
 parts=[m for m in MODELS if 425<=index(m)<=428];center=np.array([-1.6,-.025,-10.7]);scale=.72
 mesh=write_group('ST2-bell-torii',parts,lambda p:(p-center)*scale)
 old=next(go for go in scene.blocks if scene.kind(go)==1 and scene.name(go)=='Hollow Bell entrance · joined timber frame');t=scene.transform(old);hide_visual_tree(scene,old)
 objects=[scene.add('Native Windflower · ST2 torii at trial bell',p['mesh'],p['material'],parent=t) for p in mesh]
 REPORT['trialBellFrame']=dict(meshes=mesh,oldVisualRoot=old,newObjects=objects,gameplayBellAndPullPreserved=True)
 # Two post proxies, leaving the existing central bell approach open.
 post=next(m for m in parts if index(m)==426)['v']['p'];physical=[]
 template=next(scene.blocks[i] for i in scene.blocks if scene.kind(i)==65 and '  m_IsTrigger: 0\n' in scene.blocks[i] and '  m_Enabled: 1\n' in scene.blocks[i])
 for side in [-1,1]:
  subset=post[(post[:,1]<2.4)&(((post[:,0]-center[0])*side)>.6)]
  points=(subset-center)*scale;lo=points.min(0);hi=points.max(0);owner=objects[0];component=scene.alloc()
  raw=re.sub(r'^--- !u!65 &-?\d+','--- !u!65 &'+str(component),template)
  raw=re.sub(r'm_GameObject: \{fileID: -?\d+\}','m_GameObject: {fileID: '+str(owner)+'}',raw)
  raw=re.sub(r'(?m)^  m_Size: .*','  m_Size: '+fmt(hi-lo),raw);raw=re.sub(r'(?m)^  m_Center: .*','  m_Center: '+fmt((lo+hi)/2),raw)
  scene.blocks[component]=raw;scene.blocks[owner]=scene.blocks[owner].replace('  m_Layer:',f'  - component: {{fileID: {component}}}\n  m_Layer:',1);scene.set(owner,'m_Layer',6)
  physical.append(dict(component=component,center=((lo+hi)/2).tolist(),size=(hi-lo).tolist()))
 REPORT['trialBellFrame']['newPostColliders']=physical


def fprop(text,key,value):
 pattern=r'(?m)^    - '+re.escape(key)+r': .*';line='    - '+key+': '+str(value)
 return re.sub(pattern,line,text) if re.search(pattern,text) else text.replace('    m_Floats:\n','    m_Floats:\n'+line+'\n')
def crop(source,name,box=None):
 out=OUT/'Textures'/(name+'.png');im=Image.open(source)
 if box:im=im.crop(box)
 im.save(out);return guid(out),dict(path=str(source.relative_to(PROJECT)),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),crop=box,output=str(out.relative_to(PROJECT)))
def rebind_paint(scene):
 tex={};records={};find=lambda n:next(m for m in MODELS if m['name']==n)
 source_ground=next(p for p in (REFERENCE/'DemoMaterials').glob('*.mat') if reference(p.read_text(),'m_Shader')[1]==guid(SOURCE/'Demo/Shaders/PaintedGround.shader'))
 def slot(path,name):return GUIDS[re.search(r'- '+name+r':\n        m_Texture:.*guid: (\w+)',path.read_text())[1]]
 inputs={'Timber':(source_texture(find('Mesh-0417-0')),None),'Roof':(source_texture(find('Mesh-0430-0')),None),'RoofIndigo':(source_texture(find('Mesh-0430-0')),None),'Cliff':(source_texture(find('Mesh-0446-0')),None),'Bark':(source_texture(find('Mesh-0094-0')),None),'Meadow':(slot(source_ground,'_MainTex'),None),'Path':(slot(source_ground,'_DirtTex'),None),'Plaster':(source_texture(find('Mesh-0005-0')),(0,512,512,1024))}
 for family,(source,box) in inputs.items():tex[family],records[family]=crop(source,'Recovered-'+family,box)
 families=json.loads((A/'Sunward/Textures/InkWorld/painting-manifest.json').read_text());known={e['guids']['color']:k for k,e in families.items()};mapping={};changed=[]
 for original in (A/'Sunward/Generated').rglob('*.mat'):
  text=original.read_text();match=re.search(r'- _DetailMap:\n        m_Texture:.*guid: (\w+)',text)
  if not match or match[1] not in known:continue
  family=known[match[1]]
  if family not in tex:continue
  if re.search(r'(?m)^    - _ArtStrength: 0(?:\.0*)?$',text):continue
  if family=='Timber' and any(x in original.stem.lower() for x in ['trunk','bark']):family='Bark'
  originalguid=guid(original);text=re.sub(r'(- _DetailMap:\n        m_Texture: )[^\n]+',lambda m:m[1]+'{fileID: 2800000, guid: '+tex[family]+', type: 3}',text)
  if family=='Meadow':text=re.sub(r'(- _PathMap:\n        m_Texture: )[^\n]+',lambda m:m[1]+'{fileID: 2800000, guid: '+tex['Path']+', type: 3}',text)
  for key,value in {'_NormalStrength':0,'_Relief':0,'_Pigment':.05,'_ArtStrength':1}.items():text=fprop(text,key,value)
  text=re.sub(r'(?m)^    - _BaseColor: .*','    - _BaseColor: {r: 1, g: 1, b: 1, a: 1}',text)
  path=OUT/'Materials'/('Recovered-'+original.stem+'-'+originalguid[:8]+'.mat');path.write_text(text);mapping[originalguid]=guid(path);changed.append(dict(original=str(original.relative_to(PROJECT)),clone=str(path.relative_to(PROJECT)),family=family))
 # Serialized bindings and existing prefab overrides only; leave asset definitions intact.
 for old,new in mapping.items():
  for i,text in list(scene.blocks.items()):
   if old in text:scene.blocks[i]=text.replace(old,new)
 # Prefab renderers that inherit a material without an override need explicit
 # overrides on the existing TownV3 instance, rather than a prefab-wide rewrite.
 from build import Sources
 sources=Sources(scene)
 for i,text in sources.prefab.blocks.items():
  if sources.prefab.kind(i)!=23:continue
  inherited=reference(text,'m_Materials:\n  -')[1]
  if inherited in mapping:sources.patch(i,'m_Materials.Array.data[0]',reference='{fileID: 2100000, guid: '+mapping[inherited]+', type: 2}')
 REPORT['paintRebindings']=changed;REPORT['paintSourceProvenance']=records
 # Keep river shader/geometry/depth contacts; substitute the recovered water painting only.
 water_shader=guid(SOURCE/'Demo/Shaders/PaintedWater.shader');water_source=next(p for p in (REFERENCE/'DemoMaterials').glob('*.mat') if reference(p.read_text(),'m_Shader')[1]==water_shader);water_texture=slot(water_source,'_MainTex')
 waterguid,water_prov=crop(water_texture,'Recovered-River')
 river_shader=OUT/'Shaders/RecoveredRiver.shader';river_text=(A/'Sunward/Shaders/BrushWater.shader').read_text().replace('Shader "Sunward/Brush River"','Shader "Sunward/Brush River Recovered Paint"')
 river_text=river_text.replace('c*=lerp(half3(.93,.97,.94),half3(1.05,1.06,1.02),painted.r);','c=lerp(c,painted,.35+.20*saturate(absorption));')
 river_text=river_text.replace('fresnel*.17','fresnel*.06');river_shader.write_text(river_text);river_shader_guid=guid(river_shader)
 water_changes=[]
 for old in (A/'Sunward/Generated').rglob('*.mat'):
  text=old.read_text()
  if '- _FlowMap:' not in text:continue
  text=re.sub(r'(- _FlowMap:\n        m_Texture: )[^\n]+',lambda m:m[1]+'{fileID: 2800000, guid: '+waterguid+', type: 3}',text);text=re.sub(r'm_Shader: .*','m_Shader: {fileID: 4800000, guid: '+river_shader_guid+', type: 3}',text);new=OUT/'Materials'/('Recovered-'+old.stem+'.mat');new.write_text(text);oldguid=guid(old);newguid=guid(new)
  for i,b in list(scene.blocks.items()):
   if oldguid in b:scene.blocks[i]=b.replace(oldguid,newguid)
  water_changes.append(dict(original=str(old.relative_to(PROJECT)),clone=str(new.relative_to(PROJECT))))
  # The river renderer inherits its material from TownV3; redirect that live
  # prefab instance too, not merely material GUIDs already written in the scene.
  for renderer,b in sources.prefab.blocks.items():
   if sources.prefab.kind(renderer)==23 and reference(b,'m_Materials:\n  -')[1]==oldguid:sources.patch(renderer,'m_Materials.Array.data[0]',reference='{fileID: 2100000, guid: '+newguid+', type: 2}')

 REPORT['riverPaint']=dict(source=water_prov,bindings=water_changes)
 pond_shader=OUT/'Shaders/RecoveredPond.shader';text=(A/'Sunward/Shaders/GardenPond.shader').read_text().replace('Shader "Sunward/Garden Pond"','Shader "Sunward/Garden Pond Recovered Paint"')
 text=text.replace('Properties { _BaseColor','Properties { _OriginalPaint("Recovered water brushwork",2D)="white"{} _BaseColor')
 text=text.replace(' CBUFFER_START(UnityPerMaterial)',' TEXTURE2D(_OriginalPaint);SAMPLER(sampler_OriginalPaint);\n CBUFFER_START(UnityPerMaterial)')
 text=text.replace(' half3 sky=GlossyEnvironmentReflection', ' half3 pigment=SAMPLE_TEXTURE2D(_OriginalPaint,sampler_OriginalPaint,i.world.xz*.31+float2(0,-t*.025)).rgb;\n c=lerp(c,pigment,.35+.15*saturate(depth));\n half3 sky=GlossyEnvironmentReflection')
 text=text.replace('fresnel*.16','fresnel*.06');pond_shader.write_text(text);old=A/'Sunward/Generated/Waterside/Recessed pond water.mat';text=old.read_text()
 text=re.sub(r'm_Shader: .*','m_Shader: {fileID: 4800000, guid: '+guid(pond_shader)+', type: 3}',text)
 text=text.replace('    m_TexEnvs: []','    m_TexEnvs:')
 if '    m_TexEnvs:\n' not in text:text=text.replace('    m_TexEnvs:', '    m_TexEnvs:\n')
 text=text.replace('    m_TexEnvs:\n','    m_TexEnvs:\n    - _OriginalPaint:\n        m_Texture: {fileID: 2800000, guid: '+waterguid+', type: 3}\n        m_Scale: {x: 1, y: 1}\n        m_Offset: {x: 0, y: 0}\n',1)
 new=OUT/'Materials/Recovered-Pond.mat';new.write_text(text);oldguid=guid(old);newguid=guid(new)
 for i,b in list(scene.blocks.items()):
  if oldguid in b:scene.blocks[i]=b.replace(oldguid,newguid)
 REPORT['pondPaint']=dict(source=water_prov,material=str(new.relative_to(PROJECT)))


def replace_market_roofs(scene):
 source=next(m for m in MODELS if m['name']=='Mesh-0082-0');p=source['v']['p'];lo=p.min(0);hi=p.max(0);center=(lo+hi)/2;size=hi-lo
 scale=np.array([3.1/size[0],.62/size[1],2.12/size[2]])
 parts=write_group('Village-market-roof',[source],lambda p:(p-center)*scale+np.array([0,2.32,0]),lambda p,n:n/scale)
 modified=[]
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or scene.name(go) not in ['Hana · produce and flowers','Taro · tea and pottery']:continue
  t=scene.transform(go)
  for child in list(scene.blocks):
   if scene.kind(child)!=1 or scene.name(child) not in ['Layered painted cloth canopy','Cloth valance']:continue
   ct=scene.transform(child)
   if reference(scene.blocks[ct],'m_Father')[0]==t:hide_visual_tree(scene,child)
  for part in parts:scene.add('Native Windflower · painted village market roof',part['mesh'],part['material'],parent=t)
  modified.append(go)
 assert len(modified)==2;REPORT['markets']=dict(roots=modified,source='Recovered village reference canopy Mesh-0082-0; existing stall counters, merchandise, lanterns and interactions retained',meshes=parts)

def replace_cherry_trees(scene):
 # Preserve the distinct pines/olive trees. Replace cherry models using the
 # reference village's painted core crown/trunk, not its dense extra flower overlays.
 selected=[m for m in MODELS if 94<=index(m)<=100];source_center=np.array([-7,0,-5.4]);points=np.concatenate([m['v']['p']-source_center for m in selected]);lo=points.min(0);hi=points.max(0);height=hi[1]-lo[1]
 converted=write_group('Village-reference-cherry',selected,lambda p:p-source_center-np.array([0,lo[1],0]))
 changed=[]
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or not scene.name(go).startswith('Living tree ') or 'bark and branching' not in scene.name(go):continue
  mf=scene.component(go,33);path=GUIDS.get(reference(scene.blocks[mf],'m_Mesh')[1])
  if path is None or not path.stem.startswith('Cherry-'):continue
  number=int(re.search(r'Living tree (\d+)',scene.name(go))[1]);t=scene.transform(go)
  leaf=next(o for o in scene.blocks if scene.kind(o)==1 and scene.name(o).startswith('Living tree '+str(number)+' · cupped'))
  old=GUIDS[reference(scene.blocks[scene.component(leaf,33)],'m_Mesh')[1]].read_text();targetheight=vec(old,'m_Center')[1]+vec(old,'m_Extent')[1]
  scale=targetheight/height
  hide_visual_tree(scene,go);hide_visual_tree(scene,leaf)
  for part in converted:scene.add('Native Windflower · village cherry '+str(number),part['mesh'],part['material'],parent=t,scale=(scale,scale,scale))
  changed.append(number)
 REPORT['cherryTrees']=dict(treeIndices=changed,meshes=converted,source='Recovered reference village core tree meshes 94–100; authored/composite provenance, not a newly identified original game tree model',oldTreePositionsAndTrunkCollidersPreserved=True)

def mesh_arrays(path):
 raw=path.read_text();count=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);data=bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',raw)[1]);stride=len(data)//count;assert stride==48,(path,stride)
 a=np.frombuffer(data,'<f4').reshape(count,12);ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([a-f0-9]+)',raw)[1]),'<u4').reshape(-1,3);return a,ix

def plant_paint(scene):
 palette=source_texture(next(m for m in MODELS if m['name']=='Mesh-0099-0'))
 leaf,provenance=crop(palette,'Recovered-Leaf-Panel',(1024,0,1536,512));petal_source=SOURCE/'Resources/Farm/PetalPaint0.mat';petal=GUIDS[re.search(r'- _MainTex:\n        m_Texture:.*guid: (\w+)',petal_source.read_text())[1]];petalguid,petal_prov=crop(petal,'Recovered-Blossom-Petal')
 material_cache={};flower_cache={};counts=collections.Counter()
 def painted_material(old,texture,role):
  key=(old,role)
  if key in material_cache:return material_cache[key]
  text=GUIDS[old].read_text();assert '- _BaseMap:' in text
  text=re.sub(r'(- _BaseMap:\n        m_Texture: )[^\n]+',lambda m:m[1]+'{fileID: 2800000, guid: '+texture+', type: 3}',text)
  text=re.sub(r'(?m)^    - _BaseColor: .*','    - _BaseColor: {r: 1, g: 1, b: 1, a: 1}',text)
  for k,v in {'_ArtStrength':0,'_VertexTint':0,'_Pigment':0,'_Relief':0,'_NormalStrength':0}.items():text=fprop(text,k,v)
  text=re.sub(r'(?m)^  m_EnableInstancingVariants: .*','  m_EnableInstancingVariants: 1',text)
  p=OUT/'Materials'/('Recovered-'+role+'-'+old[:8]+'.mat');p.write_text(text);material_cache[key]=guid(p);return material_cache[key]
 for go in list(scene.blocks):
  if scene.kind(go)!=1:continue
  name=scene.name(go);r=scene.component(go,23);mf=scene.component(go,33)
  if not r or not mf:continue
  old=reference(scene.blocks[r],'m_Materials:\n  -')[1]
  if old is None or old not in GUIDS:continue
  if name.startswith(('Folded meadow blades','Living bamboo')):
   role='Bamboo' if name.startswith('Living bamboo') else 'Grass';new=painted_material(old,leaf,role)
   scene.blocks[r]=scene.blocks[r].replace(old,new);counts[role]+=1
  elif name.startswith('Dimensional flowers'):
   mesh_guid=reference(scene.blocks[mf],'m_Mesh')[1]
   if mesh_guid not in flower_cache:
    arrays,ix=mesh_arrays(GUIDS[mesh_guid]);petals=(arrays[:,6]>.60)&(arrays[:,7]>.20);mask=petals[ix].all(1)
    assert mask.any() and (~mask).any(),(name,'Flower partition failed')
    output=[]
    for kind,t in [('Stems',ix[~mask]),('Petals',ix[mask])]:
     g,stats=write_mesh('Flowers-'+kind+'-'+mesh_guid[:8],arrays[:,:3],t,arrays[:,3:6],arrays[:,6:10],arrays[:,10:12]);output.append((g,kind,stats))
    flower_cache[mesh_guid]=output
   hide_visual_tree(scene,go);t=scene.transform(go)
   for mesh,kind,stats in flower_cache[mesh_guid]:
    mat=old if kind=='Stems' else painted_material(old,petalguid,'Flower-Petals')
    scene.add('Native Windflower · decorative flower '+kind,mesh,mat,parent=t)
   counts['Flowers']+=1
 REPORT['botanicalPaint']=dict(counts=dict(counts),leafSource=provenance,petalSource=petal_prov,questFlowersUnchanged=True,windParametersPreserved=True)

def replace_original_stones(scene):
 source=next(m for m in MODELS if m['name']=='Mesh-0446-0');positions=source['v']['p'];faces=source['ix']
 _,inverse=np.unique(np.round(positions,5),axis=0,return_inverse=True);parents=list(range(int(inverse.max())+1))
 def root(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for triangle in faces:
  a,b,c=[root(int(inverse[v])) for v in triangle];parents[b]=a;parents[c]=a
 islands=collections.defaultdict(list)
 for i,triangle in enumerate(faces):islands[root(int(inverse[triangle[0]]))].append(i)
 pieces=[]
 for number,selected in enumerate(islands.values()):
  ix=faces[selected];used=np.unique(ix);lo=positions[used].min(0);hi=positions[used].max(0);size=hi-lo;assert min(size)>.05
  center=(lo+hi)/2;center[1]=lo[1]
  part=dict(source,ix=ix);piece=write_group('Original-ST2-rock-'+str(number),[part],lambda p:(p-center)/size,lambda p,n:n*size)[0]
  piece.update(sourceFaceIndices=selected,sourceBoundsMin=lo.tolist(),sourceBoundsMax=hi.tolist());pieces.append(piece)
 assert len(pieces)==10,len(pieces)
 outline=guid(A/'Sunward/Generated/InkWorld/Ink-contour.mat');changed=[]
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or not scene.name(go).startswith('Grounded stone '):continue
  number=int(re.search(r'Grounded stone (\d+)',scene.name(go))[1]);piece=pieces[number%len(pieces)];hide_visual_tree(scene,go);t=scene.transform(go)
  visual=scene.add('Native Windflower · original ST2 rock '+str(number),piece['mesh'],piece['material'],parent=t)
  contour=scene.add('Native Windflower · original ST2 rock ink '+str(number),piece['mesh'],outline,parent=t);scene.set(scene.component(contour,23),'m_CastShadows',0);scene.set(scene.component(contour,23),'m_ReceiveShadows',0)
  changed.append(number)
 assert len(changed)==122,len(changed)
 REPORT['originalRocks']=dict(source='Original ST2 r200.dat/6.SCR rock division, ten disconnected original boulders extracted without triangle simplification',sourceMesh='Mesh-0446-0',pieces=pieces,liveRockIndices=changed,originalPlacementsTransformsAndCollidersPreserved=True)

def main():
 for d in [OUT,OUT/'Meshes',OUT/'Materials',OUT/'Textures',OUT/'Shaders',OUT/'Scripts',OUT/'Resources',OUT/'Resources/WindflowerNative']:
  d.mkdir(exist_ok=True,parents=True);guid(d)
 text=subprocess.check_output(['git','show',BASE+':'+str(SCENE.relative_to(ROOT))],cwd=ROOT,text=True);scene=Scene(SCENE,text=text)
 scene.next=8100000000000000000
 replace_houses(scene);replace_bridges(scene);replace_bell_frame(scene);replace_market_roofs(scene);replace_cherry_trees(scene);replace_original_stones(scene);rebind_paint(scene);plant_paint(scene)
 # Runtime ambient animal component is attached to an existing-scene visual object.
 animal_script=OUT/'Scripts/WindflowerAnimals.cs'
 if animal_script.exists():
  ground=next(i for i,b in scene.blocks.items() if scene.kind(i)==114 and 'Assembly-CSharp::Sunward.GameFlow' in b)
  obj=scene.add('Native Windflower · ambient animal life',REPORT['trialBellFrame']['meshes'][0]['mesh'],REPORT['trialBellFrame']['meshes'][0]['material'],p=(0,-100,0))
  # Hide only the bootstrap object's placeholder renderer; its children use world placement.
  scene.set(scene.component(obj,23),'m_Enabled',0);scene.set(scene.transform(obj),'m_LocalPosition',fmt((0,0,0)))
  component=scene.alloc();go=scene.blocks[obj];go=go.replace('  m_Layer:',f'  - component: {{fileID: {component}}}\n  m_Layer:',1);scene.blocks[obj]=go
  scene.blocks[component]=f'''--- !u!114 &{component}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {obj}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {guid(animal_script)}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: Assembly-CSharp::Sunward.Remaster.WindflowerAnimals
  game: {{fileID: {ground}}}
'''
  REPORT['animalComponent']=component
 scene.save();REPORT['baselineSceneCommit']=BASE;REPORT['scene']=str(SCENE.relative_to(ROOT));REPORT['sceneSHA256']=hashlib.sha256(SCENE.read_bytes()).hexdigest();REPORT['UnityExecuted']=False
 Path(__file__).with_name('authoring-report.json').write_text(json.dumps(REPORT,indent=2)+'\n');print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in REPORT.items() if k in ['houses','paintRebindings','sceneSHA256','UnityExecuted']}))
if __name__=='__main__':main()
