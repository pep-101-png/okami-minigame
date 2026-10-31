"""Author the existing Windflower, keeping native geometry/paint and gameplay IDs."""
from pathlib import Path
import sys,json,re,subprocess,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/repair'),str(ROOT/'tools/original-remake'),str(ROOT/'tools/playtest-repair')]
from scene_data import World,ref,Terrain
from native import Scene,Mesh,vec,fmt
from export_assets import A,OUT,RES,guid
import importlib.util
_spec=importlib.util.spec_from_file_location("original_world_helpers",ROOT/"tools/original-remake/install_world.py");_old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_old);add_component,patch=_old.add_component,_old.patch
import install_repairs as previous
BASE='1a47fd212f238f7cfa54eea5cc82c63481ddcb9b'
MODELS=dict(previous.MODELS)
for e in json.loads(Path(__file__).with_name("furniture-sources.json").read_text()):MODELS[e["package"]]=e

def run():
 path=A/'Sunward/Scenes/Windflower.unity';path.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT));w=World();s=w.scene;t=Terrain(w);ledger=[]
 def empty(name,p=(0,0,0),parent=0):
  part=MODELS['vt08']['meshes'][0];go=s.add(name,part['mesh'],part['material'],p=p,parent=parent);s.set(s.component(go,23),'m_Enabled',0);return go
 def collider(go,mesh=None,size=None,center=(0,0,0)):
  kind=64 if mesh else 65;sample=next(b for i,b in s.blocks.items() if s.kind(i)==kind and 'stripped' not in b);id=s.alloc();sample=re.sub(r'^--- !u!\d+ &-?\d+.*',f'--- !u!{kind} &{id}',sample);sample=re.sub(r'  m_GameObject: .*','  m_GameObject: {fileID: '+str(go)+'}',sample);sample=re.sub(r'  m_Enabled: .*','  m_Enabled: 1',sample)
  if mesh:sample=re.sub(r'  m_Mesh: .*','  m_Mesh: {fileID: 4300000, guid: '+mesh+', type: 2}',sample)
  else:sample=re.sub(r'  m_Size: .*','  m_Size: '+fmt(size),sample);sample=re.sub(r'  m_Center: .*','  m_Center: '+fmt(center),sample)
  s.blocks[id]=sample;s.blocks[go]=s.blocks[go].replace('  m_Layer:',f'  - component: {{fileID: {id}}}\n  m_Layer:',1);s.set(go,'m_Layer',6);return id
 mats={}
 def depths_mat(original):
  if original in mats:return mats[original]
  p=OUT/'Materials'/('Depths-'+original+'.mat');raw=w.assets[original].read_text();raw=re.sub(r'm_Shader: \{[^}]+\}','m_Shader: {fileID: 4800000, guid: '+guid(OUT/'Shaders/OriginalDepthsPaint.shader')+', type: 3}',raw);p.write_text(raw);mats[original]=guid(p);return mats[original]
 def screen_mat(original):
  p=OUT/'Materials'/('Home-paper-screen-'+original+'.mat');raw=w.assets[original].read_text();raw=re.sub(r'm_Shader: \{[^}]+\}','m_Shader: {fileID: 4800000, guid: '+guid(OUT/'Shaders/OriginalBlossomCards.shader')+', type: 3}',raw);p.write_text(raw);return guid(p)
 def place(package,pos,size=None,height=None,yaw=0,parent=0,label='',depths=False):
  e=MODELS[package];lo=np.array(e['boundsMin']);hi=np.array(e['boundsMax']);ext=np.maximum(hi-lo,.001);scale=np.array(size)/ext if size else np.repeat((height/ext[1] if height else 1),3);a=math.radians(yaw);rot=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]);offset=np.array(pos)-rot@(np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*scale);objects=[]
  for part in e['meshes']:
   go=s.add('Original Okami · '+label,part['mesh'],depths_mat(part['material']) if depths else screen_mat(part['material']) if 'paper screen' in label else part['material'],p=offset,scale=scale,parent=parent);s.set(s.transform(go),'m_LocalRotation','{x: 0, y: %.9g, z: 0, w: %.9g}'%(math.sin(a/2),math.cos(a/2)));objects.append(go)
   if (depths and ('ink cliff' in label or 'stone vault' in label)) or (label.startswith('home ') and package in ['vt90','vt9a']):collider(go,part['mesh'])
  ledger.append(dict(label=label,package=package,sourceSHA256=e.get('sourceSHA256'),position=pos,objects=objects));return objects
 def move_world(go,pos):
  tr=s.transform(go);parent=ref(s.blocks[tr],'m_Father')[0];matrix=w.matrix(0,parent);s.set(tr,'m_LocalPosition',fmt((np.linalg.inv(matrix)@np.r_[pos,1])[:3]))
 # User explicitly removed this shrine; preserve its blessing via the old memory mirror.
 old=json.loads((ROOT/'tools/original-remake/world-install.json').read_text())
 shrine=next(r for r in old['nativePlacements'] if r['category']=='offering shrine')
 for go in shrine['objects']:s.set(go,'m_IsActive',0)
 # Keep outdoor vegetation out of the home floor.
 for r in old["nativePlacements"]:
  if r["category"] in ["grass","flowers","roadside flowers"] and abs(r["position"][0]+34)<4.1 and abs(r["position"][2]+16)<2.9:
   for go in r["objects"]:s.set(go,"m_IsActive",0)
 # Turn the original room and every practice pair around the same pivot.
 for go,b in list(s.blocks.items()):
  if s.kind(go)!=1 or 'stripped' in b:continue
  name=s.name(go)
  if 'training hall · dojo-' in name or name.startswith('Original training dummy ') or name.startswith('Original native dummy partner '):
   tr=s.transform(go);p=vec(s.blocks[tr],'m_LocalPosition');p[[0,2]]=-p[[0,2]]+[0,50];s.set(tr,'m_LocalPosition',fmt(p));s.set(tr,'m_LocalRotation','{x: 0, y: 1, z: 0, w: 0}')
 # Calibrate every training pair against the actual rotated native floor.
 w.transforms.clear();floors=[]
 for r in w.renderers():
  if 'training hall · dojo-floor' not in r['name']:continue
  d=w.mesh(r['meshGUID'],r['meshID']);v=np.asarray(d['vertices'])@r['matrix'][:3,:3].T+r['matrix'][:3,3];floors.append((v,np.asarray(d['triangles'])))
 def floor_height(x,z):
  values=[]
  for v,ix in floors:
   a,b,c=v[ix[:,0]],v[ix[:,1]],v[ix[:,2]];u=b[:,[0,2]]-a[:,[0,2]];q=c[:,[0,2]]-a[:,[0,2]];p=np.array([x,z])-a[:,[0,2]];den=u[:,0]*q[:,1]-u[:,1]*q[:,0];valid=abs(den)>1e-9;f=np.zeros_like(den);g=f.copy();f[valid]=(p[valid,0]*q[valid,1]-p[valid,1]*q[valid,0])/den[valid];g[valid]=(u[valid,0]*p[valid,1]-u[valid,1]*p[valid,0])/den[valid];hit=valid & (f>=-1e-5)&(g>=-1e-5)&(f+g<=1.00001);values.extend((a[:,1]+f*(b[:,1]-a[:,1])+g*(c[:,1]-a[:,1]))[hit].tolist())
  assert values,(x,z);return max(values)
 training=[]
 for go,b in list(s.blocks.items()):
  if s.kind(go)==1 and (s.name(go).startswith('Original native dummy partner') or s.name(go).startswith('Original training dummy ')):
   tr=s.transform(go);p=vec(s.blocks[tr],'m_LocalPosition');p[1]=floor_height(p[0],p[2])+.015;s.set(tr,'m_LocalPosition',fmt(p));training.append(dict(name=s.name(go),position=p.tolist(),floor=p[1]-.015))
 # Put the native household objects on real furniture, inside the walls.
 home=next(i for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.HomeCutaway\n' in b)
 newhome=[];retired=[]
 newhome+=place('vt90',[-37.15,.11,-18.15],size=[2.2,.75,.65],label='home wooden weapon stand')
 newhome+=place('vt90',[-34.9,.11,-18.15],size=[1.8,.60,.65],label='home wooden glaive stand')
 newhome+=place('vt90',[-30.6,.11,-17.2],size=[2.0,1.5,.65],yaw=270,label='home collection cabinet')
 newhome+=place('vt65',[-33.7,.59,-14.0],height=.22,label='home cup on low table')
 newhome+=place('vt9a',[-33.7,.11,-14.0],size=[1.7,.48,1.1],label='home low tea furniture')
 for r in old['nativePlacements']:
  if r['category']=='collectible shelf':
   for go in r['objects']:s.set(go,'m_IsActive',0);retired.append(go)
  if r['category']=='tea set':
   for go in r['objects']:s.set(go,'m_IsActive',0);retired.append(go)
 # Replace the old black interior slab with native wood/tatami floor art.
 oldfloor=next(r for r in w.renderers() if r['name']=='TownV3-601');patch(s,oldfloor['instance'],oldfloor['renderer'],'m_Enabled',0)
 homefloors=[r for r in w.renderers() if 'food house floor' in r['name']]
 for k,r in enumerate(homefloors):
  d=w.mesh(r['meshGUID'],r['meshID']);m=Mesh();q=np.asarray(d['vertices']).copy();q[:,0]*=8.2/8.8;q[:,2]*=5.8/7.2;q[:,1]=0;m.v=q.tolist();raw3=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',d['raw'])[1]),'<f4').reshape(len(q),d['stride']//4);m.c=raw3[:,6:9].tolist();m.uv=raw3[:,10:12].tolist();m.tri=d['triangles'].tolist();m.bones=[0]*len(q);p=OUT/'Meshes'/('Native-home-floor-'+str(k)+'.asset');m.write(p);go=s.add('Original home wood and tatami '+str(k),guid(p),r['materials'][0],p=[-34,.107,-16]);collider(go,guid(p));newhome.append(go)
 newhome+=place('vt61',[-35.8,.11,-18.65],size=[3.5,2.2,.15],label='home paper screen behind cabinets')
 newhome+=place('vt61',[-30.15,.11,-17.1],size=[2.0,2.2,.15],yaw=90,label='home paper screen behind collection')
 # Move the native wall-cradle Solar Flare to the supported wooden stand.
 for i,b in s.blocks.items():
  if 'Assembly-CSharp::Sunward.Remaster.NativeSolarFlare\n' in b:
   go=s.owner(i);s.set(go,'m_IsActive',0)
 for r in old['nativePlacements']:
  if r['category']=='home Solar Flare display':
   for go in r['objects']:
    tr=s.transform(go);s.set(tr,'m_LocalPosition',fmt(vec(s.blocks[tr],'m_LocalPosition')+np.array([.65,-.1,.75])))
 for r in old['nativePlacements']:
  if r['category']=='home native glaive display':
   delta=np.array([.9,.10,.75])
   for go in r['objects']:
    tr=s.transform(go);s.set(tr,'m_LocalPosition',fmt(vec(s.blocks[tr],'m_LocalPosition')+delta))
 # Support the visible source weapon parts on their cabinet tops, not on
 # bounds inflated by hidden effect meshes in the original archive.
 home_support=[]
 for category,centre,top in [('home Solar Flare display',[-37.15,-18.15],.86),('home native glaive display',[-34.9,-18.15],.71)]:
  record=next(r for r in old['nativePlacements'] if r['category']==category);w.transforms.clear();points=[]
  for r in w.renderers():
   if r['go'] not in record['objects']:continue
   d=w.mesh(r['meshGUID'],r['meshID']);points.append(np.asarray(d['vertices'])@r['matrix'][:3,:3].T+r['matrix'][:3,3])
  assert points,category
  pts=np.concatenate(points);low=pts.min(0);high=pts.max(0);delta=np.array([centre[0]-(low[0]+high[0])/2,top-low[1],centre[1]-(low[2]+high[2])/2])
  for go in record['objects']:
   tr=s.transform(go);parent=ref(s.blocks[tr],'m_Father')[0];local=np.linalg.solve(w.matrix(0,parent)[:3,:3],delta) if parent else delta;s.set(tr,'m_LocalPosition',fmt(vec(s.blocks[tr],'m_LocalPosition')+local))
  home_support.append(dict(category=category,top=top,originalMinimumY=float(low[1]),correction=delta.tolist(),objects=record['objects']))
 # Retired loom/cup roots must be removed from both visibility lists.
 for go in retired:
  rid=s.component(go,23);s.blocks[home]=s.blocks[home].replace('  - {fileID: '+str(go)+'}\n','').replace('  - {fileID: '+str(rid)+'}\n','')
 for b in s.blocks.values():
  if 'Assembly-CSharp::Sunward.CollectibleShelf\n' not in b:continue
  slots=[int(i) for i in re.findall(r'fileID: (\d+)',b.split('  slots:\n')[1].split('  game:')[0])]
  for k,tr in enumerate(slots):
   go=s.owner(tr);move_world(go,[-30.6+(-.16 if k<3 else .16),1.61,-17.2+(k%3-1)*.65]);newhome.append(go)
 s.blocks[home]+=''.join('  - {fileID: '+str(go)+'}\n' for go in newhome)
 # Rotate the new stalls to face the village street, merchant behind each counter.
 for side,inst,index in [(-1,2027807467,0),(1,1439298636,1)]:
  oldcentre=np.array([side*7,0,0]);centre=np.array([side*7.5,0,0]);angle=math.radians(side*90);rot=np.array([[math.cos(angle),0,math.sin(angle)],[0,1,0],[-math.sin(angle),0,math.cos(angle)]]);yaw=180+side*90
  for go,b in list(s.blocks.items()):
   if s.kind(go)!=1 or 'Original larger centred' not in s.name(go):continue
   tr=s.transform(go);p=vec(s.blocks[tr],'m_LocalPosition')
   if np.sign(p[0])!=side:continue
   s.set(tr,'m_LocalPosition',fmt(centre+rot@(p-oldcentre)));s.set(tr,'m_LocalRotation','{x: 0, y: %.9g, z: 0, w: %.9g}'%(math.sin(math.radians(yaw/2)),math.cos(math.radians(yaw/2))))
  station=np.array([side*8.6,t.height(side*8.6,0)+.1,0]);src=w.prefabs[inst];root=next(i for i in src.blocks if src.kind(i)==4 and ref(src.blocks[i],'m_Father')[0]==0)
  for axis,val in zip('xyz',station):patch(s,inst,root,'m_LocalPosition.'+axis,val)
  for axis,val in [('y',math.sin(math.radians(yaw/2))),('w',math.cos(math.radians(yaw/2)))]:patch(s,inst,root,'m_LocalRotation.'+axis,val)
  for i,b in list(s.blocks.items()):
   if 'Assembly-CSharp::Sunward.VillageResident\n' in b and '  index: '+str(index)+'\n' in b:s.set(i,'station',fmt(station))
 # Match the four original counter/collision roots to the rotated stalls.
 for cid,x in [(204672430,6.8),(249600521,-6.8),(688100575,7.5),(1530535325,-7.5)]:
  tr=s.transform(s.owner(cid));p=vec(s.blocks[tr],'m_LocalPosition');p[0]=x;s.set(tr,'m_LocalPosition',fmt(p));size=vec(s.blocks[cid],'m_Size');size[[0,2]]=size[[2,0]];s.set(cid,'m_Size',fmt(size))
 # Split only the original terrain's centre triangles; retain original vertices/UVs.
 ground=next(r for r in w.renderers() if r['name']=='TownV3-752');data=w.mesh(ground['meshGUID'],ground['meshID']);v=np.asarray(data['vertices']);tri=np.asarray(data['triangles']);c=v[tri][:,:,[0,2]]-np.array([35,0]);centres=c.mean(1);cut=np.any(np.linalg.norm(c,axis=2)<4.8,axis=1)|(np.linalg.norm(centres,axis=1)<4.8)
 assert 0<sum(cut)<len(tri)/20
 raw=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',data['raw'])[1]),'<f4').reshape(len(v),data['stride']//4);colors=raw[:,6:9];uv=raw[:,10:12]
 def fragment(name,faces,origin=(0,0,0)):
  ids=np.unique(faces);m=Mesh();m.v=(v[ids]-origin).tolist();m.uv=np.asarray(uv)[ids].tolist();m.c=colors[ids].tolist();m.bones=[0]*len(ids);m.tri=np.searchsorted(ids,faces).tolist();p=OUT/'Meshes'/(name+'.asset');m.write(p);return guid(p)
 cutmesh=fragment('Existing-ground-with-seal-opening',tri[~cut]);src=w.prefabs[ground['instance']];patch(s,ground['instance'],ground['renderer'],'m_Enabled',0);patch(s,ground['instance'],src.component(ground['go'],64),'m_Enabled',0)
 go=s.add('Existing native-painted ground · centre opening',cutmesh,ground['materials'][0]);collider(go,cutmesh);groundrenderer=s.component(go,23)
 cover=empty('Upper arena original floor · breakable seal',[35,0,0]);fragments=[];lidcolliders=[]
 sector=((np.arctan2(centres[:,1],centres[:,0])+math.pi)/(math.tau)*6).astype(int)%6
 for j in range(6):
  faces=tri[cut & (sector==j)];points=v[np.unique(faces)];origin=(points.min(0)+points.max(0))/2;mesh=fragment('Original-seal-fragment-'+str(j),faces,origin);go=s.add('Original terrain seal fragment '+str(j),mesh,ground['materials'][0],p=origin-[35,0,0],parent=s.transform(cover));fragments.append(s.transform(go));lidcolliders.append(collider(go,mesh))
 chamber=empty('Lower arena · original Okami chamber')
 # A broad level floor assembled from the original training-room floor parts.
 e=MODELS['dojo-floor'];lo=np.array(e['boundsMin']);hi=np.array(e['boundsMax']);extent=hi-lo
 for k,part in enumerate(e['meshes']):
  d=w.mesh(part['mesh'],4300000);m=Mesh();source=np.asarray(d['vertices']);q=source.copy();q[:,0]=(q[:,0]-(lo[0]+hi[0])/2)*63/extent[0];q[:,2]=(q[:,2]-(lo[2]+hi[2])/2)*63/extent[2];q[:,1]=(source[:,1]-lo[1])*.002
  faces=np.asarray(d['triangles']);normal=np.cross(source[faces[:,1]]-source[faces[:,0]],source[faces[:,2]]-source[faces[:,0]]);faces=faces[normal[:,1]>1e-8]
  if not len(faces):continue
  m.v=q.tolist();raw2=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',d['raw'])[1]),'<f4').reshape(len(q),d['stride']//4);m.c=raw2[:,6:9].tolist();m.uv=raw2[:,10:12].tolist();m.tri=faces.tolist();m.bones=[0]*len(q);p=OUT/'Meshes'/('Native-lower-floor-'+str(k)+'.asset');m.write(p);go=s.add('Original painted lower arena floor '+str(k),guid(p),depths_mat(part['material']),p=[35,-20,0],parent=s.transform(chamber));collider(go,guid(p))
 # Original rock/cliff models, carved timber, lanterns and shrine pillars.
 rock='vt28'
 for j in range(24):
  a=j*math.tau/24;pos=[35+math.cos(a)*33,-20,math.sin(a)*33];place(rock,pos,size=[12,21+(j%3)*1.1,10],yaw=-j*15,parent=s.transform(chamber),label='depths ink cliff '+str(j),depths=True)
 for j in range(12):
  a=j*math.tau/12;pos=[35+math.cos(a)*27.8,-20,math.sin(a)*27.8];place('vt60',pos,height=2.6,parent=s.transform(chamber),label='depths lantern '+str(j),depths=True)
 for j in range(4):
  a=math.pi/4+j*math.pi/2;place('vt35',[35+math.cos(a)*29,-20,math.sin(a)*29],height=5,parent=s.transform(chamber),label='depths carved corner '+str(j),depths=True)
 for j in range(4):
  a=math.pi/4+j*math.pi/2;place('vt70',[35+math.cos(a)*24,-20,math.sin(a)*24],height=5,parent=s.transform(chamber),label='depths original crystal cluster '+str(j),depths=True)
 # An overhead vault assembled from original rock models, leaving the shaft clear.
 for j,(x,z,size) in enumerate([(22,0,28),(-22,0,28),(0,22,28),(0,-22,28),(23,23,20),(-23,23,20),(23,-23,20),(-23,-23,20)]):
  place(rock,[35+x,-7,z],size=[size,7,size],parent=s.transform(chamber),label='depths native stone vault '+str(j),depths=True)
 mirror=empty('Lower arena memory mirror · E returns home',[15,-20,-18],parent=s.transform(chamber));place('et19',[0,0,0],height=2.7,yaw=45,parent=s.transform(mirror),label='depths return mirror',depths=True)
 controller=empty('Lower arena controller');game=next(i for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.GameFlow\n' in b)
 fields='  game: {fileID: '+str(game)+'}\n  cover: {fileID: '+str(cover)+'}\n  chamber: {fileID: '+str(chamber)+'}\n  fragments:\n'+''.join('  - {fileID: '+str(i)+'}\n' for i in fragments)+'  lidColliders:\n'+''.join('  - {fileID: '+str(i)+'}\n' for i in lidcolliders)+'  upperGround: {fileID: '+str(groundrenderer)+'}\n  mirror: {fileID: '+str(s.transform(mirror))+'}\n';add_component(s,controller,'LowerArena',fields)
 s.set(chamber,'m_IsActive',0);s.save();result=dict(base=BASE,placements=ledger,removedShrineObjects=shrine['objects'],rotatedDojo=True,trainingGrounding=training,homeDisplaySupports=home_support,cutOriginalGroundTriangles=int(sum(cut)),preservedGroundTriangles=int(sum(~cut)),coverFragments=fragments,coverColliders=lidcolliders,chamber=chamber,mirror=mirror,lowerFloorY=-20,lowerRadius=31,oldGroundSource=ground['meshGUID'],newGround=cutmesh)
 Path(__file__).with_name('world-changes.json').write_text(json.dumps(result,indent=2)+'\n');print('Existing Windflower updated; native lower chamber authored')
if __name__=='__main__':run()
