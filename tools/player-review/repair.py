"""Targeted fixes from the player's screenshots; applied after the existing art passes."""
from pathlib import Path
import sys,re,math,random,json,importlib.util,hashlib
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from scene_tools import *
from build import Sources
import native
OUT=ASSETS/'Generated/PlayerReview2'

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def apply(scene):
 OUT.mkdir(exist_ok=True);native.OUT=OUT
 Path(str(OUT)+'.meta').write_text('fileFormatVersion: 2\nguid: '+hashlib.md5(str(OUT.relative_to(ROOT)).encode()).hexdigest()+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
 ink=load('review_ink',ROOT/'tools/ink-world/apply.py');ink.OUT=OUT
 src=Sources(scene);index=asset_index();cache={};report={}
 # These two original planar wash meshes are the green/red remnants over bridge one.
 for n in [371,408,409]:src.hide(n)
 report['retiredSourceMeshes']=[371,408,409]
 # All original source bamboo is superseded by the seven uniquely authored clumps.
 for n in range(841,876):src.hide(n)
 report['legacyBambooPartsDisabled']=35
 def add(name,mesh,mat,p=(0,0,0),scale=(1,1,1),parent=0,outline=True):
  path=OUT/(name+'.asset');mesh.write(path);g=guid(path)
  go=scene.add('Review 2 · '+name,g,mat,p=p,scale=scale,parent=parent)
  if outline:
   shell=ink.shell_mesh(path,{});o=scene.add('Review 2 ink · '+name,shell,guid(ASSETS/'Generated/InkWorld/Ink-contour.mat'),parent=scene.transform(go));scene.set(scene.component(o,23),'m_CastShadows',0)
  return go
 def disable_rock(go):
  bb=bounds(scene,go,src,index,cache);scene.set(go,'m_IsActive',0)
  marker=next((i for i,b in scene.blocks.items() if scene.kind(i)==114 and 'Assembly-CSharp::Sunward.EnvironmentReviewState' in b),None)
  if marker:
   p=world(scene,scene.transform(go),cache)[:3,3]
   scene.blocks[marker]=scene.blocks[marker].rstrip()+'\n  - '+fmt(p)+'\n'
  if bb is None:return
  lo,hi=bb
  for other in list(scene.blocks):
   if scene.kind(other)!=1 or scene.name(other)!='Trunk / rock collider':continue
   t=scene.transform(other);p=world(scene,t,cache)[:3,3]
   if (p[[0,2]]>=lo[[0,2]]-.18).all() and (p[[0,2]]<=hi[[0,2]]+.18).all():
    for c in scene.refs(other):
     if scene.kind(c) in (65,136):scene.disabled(c)
 # Remove only stones intruding into the bridge walking surface or mill footprint.
 removed=[]
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or not scene.name(go).startswith('Grounded stone ') or not active(scene,go):continue
  bb=bounds(scene,go,src,index,cache)
  if bb is None:continue
  lo,hi=bb
  bridge=any(hi[0]>-27.6 and lo[0]<-18.4 and hi[2]>z-1.27 and lo[2]<z+1.27 and hi[1]>.08 for z in [-8,14])
  mill=(hi[0]>-30.2 and lo[0]<-18.1 and hi[2]>4.5 and lo[2]<11.5 and hi[1]>-.6)
  if bridge or mill:disable_rock(go);removed.append({'name':scene.name(go),'reason':'bridge' if bridge else 'mill'})
 report['removedIntrudingStones']=removed
 # Stop original ropes/posts and folded decorations surviving beside new stalls.
 retired=[]
 for go in list(scene.blocks):
  if scene.kind(go)!=1:continue
  name=scene.name(go)
  if name in ('Market · five vibrant festival spans','Market · supported festival line'):
   scene.set(go,'m_IsActive',0);retired.append(name)
  if name in ('Cedar support','Festival cedar support'):
   p=world(scene,scene.transform(go),cache)[:3,3]
   if abs(p[0])<9 and abs(p[2])<9:scene.set(go,'m_IsActive',0);retired.append(name)
 report['retiredMarketDecorations']=retired
 # Lower/flatten the curved door headers below the roof eave; keep their child ink.
 arches=0
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or not scene.name(go).startswith('Ink world · curved entrance fascia'):continue
  t=scene.transform(go);p=vec(scene.blocks[t],'m_LocalPosition');p[1]=2.02;p[2]+=.27
  scene.set(t,'m_LocalPosition',fmt(p));scene.set(t,'m_LocalScale',fmt((1,.70,1)));arches+=1
 report['doorFasciaPartsRepositioned']=arches
 # Audit every stone lantern family, not only the original five source lanterns.
 lanterns=[go for go in list(scene.blocks) if scene.kind(go)==1 and scene.name(go).startswith(('Kasuga lantern','Arena perimeter lantern'))]
 roots=[world(scene,scene.transform(go),cache)[:3,3] for go in lanterns]
 for go in list(scene.blocks):
  if scene.kind(go)==1 and scene.name(go).startswith('Ink world · open garden lantern'):
   p=world(scene,scene.transform(go),cache)[:3,3]
   if any(np.linalg.norm((p-q)[[0,2]])<.7 for q in roots):scene.set(go,'m_IsActive',0)
 stone=guid(ASSETS/'Generated/InkWorld/Ink-ochre-cliff.mat');light=guid(ASSETS/'Generated/LivingPlaces/Evening-glowing-paper.mat')
 for number,go in enumerate(lanterns):
  t=scene.transform(go)
  for obj in list(scene.blocks):
   if scene.kind(obj)!=1:continue
   child=scene.transform(obj);cur=child
   while cur and cur!=t:cur=parent(scene,cur)
   if cur==t:
    r=scene.component(obj,23)
    if r:scene.set(r,'m_Enabled',0)
  # One shared solid frame with an open fire chamber, plus a separate light insert.
  g=guid(ASSETS/'Generated/InkWorld/Stone-lantern-stone.asset');body=scene.add('Review 2 · coherent stone lantern '+str(number),g,stone,parent=t)
  scene.add('Review 2 · lantern chamber '+str(number),guid(ASSETS/'Generated/InkWorld/Stone-lantern-light.asset'),light,parent=t)
  contour=scene.add('Review 2 · lantern ink '+str(number),guid(ASSETS/'Generated/InkWorld/Contour-Stone-lantern-stone.asset'),guid(ASSETS/'Generated/InkWorld/Ink-contour.mat'),parent=t)
  scene.set(scene.component(contour,23),'m_CastShadows',0)
 paper=shadow=0
 for r,b in list(scene.blocks.items()):
  if scene.kind(r)==108 and '  m_Type: 2\n' in b:
   scene.blocks[r]=re.sub(r'(  m_Shadows:\n    m_Type:) \d+',r'\g<1> 0',b)
  if scene.kind(r)!=23:continue
  name=scene.name(scene.owner(r))
  if any(w in name.lower() for w in ['paper lantern','swaying coloured lantern']):
   scene.blocks[r]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {light}, type: 2}}\n',scene.blocks[r],flags=re.S);paper+=1
  if any(w in name.lower() for w in ['ink ·','contour','awning','paper','rope','lantern rib','blossom arrangement']):
   scene.set(r,'m_CastShadows',0);shadow+=1
 report.update({'rebuiltStoneLanterns':len(lanterns),'paperLanternRenderersAudited':paper,'smallDecorationShadowCastersDisabled':shadow})
 # Natural rooted ground transitions for all tree bases and upright arena stumps.
 timber=guid(ASSETS/'Generated/InkWorld/Ink-painted-timber.mat');leafmat=guid(ASSETS/'Generated/InkWorld/Ink-living-foliage.mat')
 root_meshes=[]
 for variant in range(5):
  rng=random.Random(812+variant);m=Mesh();leaves=Mesh()
  for j in range(6+variant%3):
   a=j*math.tau/(6+variant%3)+rng.uniform(-.12,.12);length=rng.uniform(.65,1.15)
   pts=[(math.cos(a)*r,y,math.sin(a)*r) for r,y in [(.13,.28),(.34,.17),(length*.72,.045),(length,-.035)]]
   m.tube(pts,[.13,.10,.06,.008],(.32,.18,.085),n=9,groove=.10)
   for k in range(3):leaves.leaf((math.cos(a)*(length+.12),-.025,math.sin(a)*(length+.12)),rng.uniform(.14,.23),.07,a+k, (.35,.39,.12) if k%2 else (.56,.28,.09),tip=.03)
  path=OUT/('Root-flare-'+str(variant)+'.asset');m.write(path);root_meshes.append((guid(path),leaves))
 trees=stumps=0
 for go in list(scene.blocks):
  if scene.kind(go)!=1:continue
  name=scene.name(go);is_tree=name.startswith('Living tree ') and 'bark and branching' in name
  is_log=name.startswith('Arena · full cedar log')
  if not (is_tree or is_log):continue
  t=scene.transform(go);w=world(scene,t,cache);up=w[:3,1]/max(np.linalg.norm(w[:3,1]),1e-6)
  if is_log:
   old=vec(scene.blocks[t],'m_LocalScale');seed=int(name.rsplit(' ',1)[1]);factor=.92+.16*((seed*37)%101)/100
   before=bounds(scene,go,src,index,{})
   scene.set(t,'m_LocalScale',fmt(old*np.array([factor, .88+.24*((seed*17)%101)/100, factor])))
   after=bounds(scene,go,src,index,{})
   if before is not None and after is not None:
    local=vec(scene.blocks[t],'m_LocalPosition');local[1]+=before[0][1]-after[0][1];scene.set(t,'m_LocalPosition',fmt(local))
  if is_log and up[1]<.75:continue
  p=w[:3,3].copy();p[1]=src.ground(p[0],p[2])-.035;v=(trees+stumps)%5
  scale=(.72,.8,.72) if is_tree else (.45,.65,.45)
  scene.add('Review 2 · rooted tree transition '+str(trees+stumps),root_meshes[v][0],timber,p=p,scale=scale)
  add('leaf litter '+str(trees+stumps),root_meshes[v][1],leafmat,p=p,scale=scale,outline=False)
  trees+=int(is_tree);stumps+=int(is_log)
 report.update({'treeRootTransitions':trees,'uprightStumpRoots':stumps})
 # Bind a dedicated emissive shader to the equipped shield, so builds retain it.
 mat=OUT/'Sundial-spectral-flame.mat';raw=(ASSETS/'Generated/InkWorld/Ink-painted-plaster.mat').read_text();raw=re.sub(r'm_Name: .*','m_Name: Sundial-spectral-flame',raw,count=1);raw=re.sub(r'm_Shader: .*','m_Shader: {fileID: 4800000, guid: '+guid(ASSETS/'Shaders/SpectralFlame.shader')+', type: 3}',raw)
 raw=re.sub(r'- _BaseColor: .*','- _BaseColor: {r: 1, g: 1, b: 1, a: 1}',raw);mat.write_text(raw)
 combat=next(i for i,b in scene.blocks.items() if scene.kind(i)==114 and 'Assembly-CSharp::Sunward.WolfCombat\n' in b)
 scene.blocks[combat]=scene.blocks[combat].rstrip()+'\n  sundialFlameMaterial: {fileID: 2100000, guid: '+guid(mat)+', type: 2}\n'
 return report
