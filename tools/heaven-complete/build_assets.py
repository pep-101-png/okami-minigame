from pathlib import Path
import sys,json,copy,shutil,hashlib,math,subprocess
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/heaven-complete');W.mkdir(exist_ok=True)
sys.path[:0]=['/workspace/work/reference-repairs','/workspace/work/heaven-complete','/workspace/work/full-asset-inspection','/workspace/sunward-remaster/tools/playtest-followup'];import assets;from meta import meta;from components import components
sys.path.insert(0,str(ROOT/'tools/heaven-qol'));import geometry as base
layout=json.loads(subprocess.check_output(['git','show','4a462f1:Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/CelestialGarden.json'],cwd=ROOT));ledger=[]
def save(name,m,source):
 dest=D/name;dest.mkdir(exist_ok=True);(dest/'Model.json').write_text(json.dumps(m,separators=(',',':')))
 for t in m['textures']:
  if not t.get('vertexOnly'):shutil.copyfile(D/source/t['path'],dest/t['path'])
 for p in [dest,*dest.iterdir()]:
  if p.suffix!='.meta':meta(p)
 ledger.append(dict(resource=name,source=source,sourceSHA256=m.get('sourceSHA256'),derivation=m.get('derivation','Selected original geometry')))
base.surfaces=[]
for item in layout['items']:
 if item['kind']=='ground':base.surfaces.append(base.triangles(item))
# Four auxiliary torii lantern-post groups move outward; main uprights remain intact.
m=json.load(open(D/'celestial-gate/Model.json'))
for p in m['parts']:
 v=np.array(p['positions']).reshape(-1,3)
 for j,ids in enumerate(components(p)):
  if p['name']=='Native-0-0' and j in range(8,16):continue
  if (p['name']=='Native-0-0' and j in [4,5,6,7]) or p['name']=='Native-1-0':
   v[ids,0]+=2.4 if v[ids,0].mean()>0 else -2.4
 # Remove the old braces which would otherwise terminate in empty space.
 if p['name']=='Native-0-0':
  omit=set(i for j,ids in enumerate(components(p)) if j in range(8,16) for i in ids);f=np.array(p['indices']).reshape(-1,3);p['indices']=[int(i) for t in f if not any(int(i) in omit for i in t) for i in t]
 p['positions']=v.ravel().tolist()
m['derivation']='Original torii with intact auxiliary lantern-post groups moved outward 2.4 source metres to clear the main uprights; obsolete small braces omitted.';save('heaven-gate',m,'celestial-gate')
# Original tea cup, extracted as complete connected cup/ink components, not the tray.
m=json.load(open(D/'vt65/Model.json'));p=m['parts'][0];keep=set(i for j,ids in enumerate(components(p)) if j in [0,2] for i in ids);f=np.array(p['indices']).reshape(-1,3);p['indices']=[int(i) for t in f if all(int(i) in keep for i in t) for i in t];v=np.array(p['positions']).reshape(-1,3);used=sorted(set(p['indices']));mapping={i:j for j,i in enumerate(used)}
for key,dim in [('positions',3),('uv',2),('colors',4),('boneIndices',3),('weights',3)]:p[key]=np.array(p[key]).reshape(-1,dim)[used].ravel().tolist()
p['indices']=[mapping[i] for i in p['indices']];m['derivation']='One intact original tea cup and its ink shell selected from the VT65 tea tray; original UVs and paint retained.';save('heaven-tea-cup',m,'vt65')
# Keep the original tea tray, cups and ink shell; omit an unrelated low component.
m=json.load(open(D/'vt65/Model.json'));p=m['parts'][0];keep=set(i for j,ids in enumerate(components(p)) if j!=3 for i in ids);f=np.array(p['indices']).reshape(-1,3);p['indices']=[int(i) for t in f if all(int(i) in keep for i in t) for i in t];used=sorted(set(p['indices']));mapping={i:j for j,i in enumerate(used)}
for key,dim in [('positions',3),('uv',2),('colors',4),('boneIndices',3),('weights',3)]:p[key]=np.array(p[key]).reshape(-1,dim)[used].ravel().tolist()
p['indices']=[mapping[i] for i in p['indices']];m['derivation']='Original VT65 tray, cups and ink outline; unrelated disconnected lower component omitted so tray rests on table.';save('heaven-tea-tray',m,'vt65')
# Native sloped roof pieces for an open lookout, with original timber posts at runtime.
m=json.load(open(D/'vt05/Model.json'));p=m['parts'][0];v=np.array(p['positions']).reshape(-1,3);keep=set(i for ids in components(p) if v[ids,1].min()>3 for i in ids);f=np.array(p['indices']).reshape(-1,3);p['indices']=[int(i) for t in f if all(int(i) in keep for i in t) for i in t];used=sorted(set(p['indices']));mapping={i:j for j,i in enumerate(used)}
for key,dim in [('positions',3),('uv',2),('colors',4),('boneIndices',3),('weights',3)]:p[key]=np.array(p[key]).reshape(-1,dim)[used].ravel().tolist()
p['indices']=[mapping[i] for i in p['indices']];m['derivation']='Original sloped VT05 roof/rafters selected without the well, bucket or rope; reused as the lookout shelter roof.';save('heaven-lookout-roof',m,'vt05')
# Native pond rocks and water; omit oversized separate foam, keep water entirely inside rim.
m=json.load(open(D/'celestial-pond/Model.json'));m['parts']=[p for p in m['parts'] if p['name']!='Native-0-0'];rim=next(p for p in m['parts'] if p['name']=='Native-2-0');rv=np.array(rim['positions']).reshape(-1,3);lo,hi=rv.min(0),rv.max(0);cx,cz=(lo[[0,2]]+hi[[0,2]])/2
water=next(p for p in m['parts'] if p['name']=='Native-1-0');v=np.array(water['positions']).reshape(-1,3)
for axis,centre in [(0,cx),(2,cz)]:
 q=v[:,axis];v[:,axis]=centre+(q-(q.min()+q.max())/2)/max(.001,np.ptp(q))*(hi[axis]-lo[axis])*.58
water['positions']=v.ravel().tolist();m['derivation']='Original complete pond rim and native water quad; detached oversized foam omitted and the original quad fitted inside the bank. Water level/shore mask handled by the water adapter.';save('heaven-pond-basin',m,'celestial-pond')
pools=[]
for item in layout['items']:
 if item['kind']!='pond':continue
 x,z=item['position']['x'],item['position']['z'];sx,sz=item['size']['x'],item['size']['z'];level=base.height(x,z)-.06;root=min(base.height(x+dx,z+dz) for dx,dz in [(-.4*sx,-.4*sz),(.4*sx,-.4*sz),(-.4*sx,.4*sz),(.4*sx,.4*sz)])-.10
 pools.append(dict(position=dict(x=x,y=level,z=z),radius=dict(x=sx*.265,y=sz*.265),depth=.85))
 item['resource']='Okami/heaven-pond-basin';item['position']['y']=root;item['absoluteHeight']=True;item['yaw']=0
# Refine original terrain triangles around ponds, then lower those vertices into real basins.
m=json.load(open(D/'celestial-grounded/Model.json'));origin=np.array([0,-.18,0]);refined=[]
for part in m['parts']:
 v=np.array(part['positions']).reshape(-1,3);uv=np.array(part['uv']).reshape(-1,2);col=np.array(part['colors']).reshape(-1,4);records=[];faces=[]
 def near(t):
  vs=t[:,:3]+origin;low=vs[:,[0,2]].min(0);high=vs[:,[0,2]].max(0)
  return any(np.all(high>=np.array([p['position']['x'],p['position']['z']])-np.array([p['radius']['x'],p['radius']['y']])*1.85) and np.all(low<=np.array([p['position']['x'],p['position']['z']])+np.array([p['radius']['x'],p['radius']['y']])*1.85) for p in pools)
 def emit(t,steps):
  if steps and near(t):
   a,b,c=t;ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
   for q in [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]:emit(np.array(q),steps-1)
  else:
   ix=len(records);records.extend(t);faces.append([ix,ix+1,ix+2])
 data=np.concatenate([v,uv,col],1)
 for f in np.array(part['indices']).reshape(-1,3):emit(data[f],5)
 rec=np.array(records);world=rec[:,:3]+origin
 for p in pools:
  xx=(world[:,0]-p['position']['x'])/p['radius']['x'];zz=(world[:,2]-p['position']['z'])/p['radius']['y'];r=np.sqrt(xx*xx+zz*zz);t=np.clip((r-.72)/(1.7-.72),0,1);weight=1-t*t*(3-2*t);bed=p['position']['y']-p['depth'];world[:,1]=world[:,1]*(1-weight)+bed*weight
 rec[:,:3]=world-origin;n=len(rec);q=dict(part);q['positions']=rec[:,:3].ravel().tolist();q['uv']=rec[:,3:5].ravel().tolist();q['colors']=rec[:,5:9].ravel().tolist();q['indices']=np.array(faces).ravel().tolist();q['boneIndices']=[-1]*(n*3);q['weights']=[a for _ in range(n) for a in [1,0,0]];refined.append(q)
m['parts']=refined;m['derivation']='Original r108 terrain triangles locally refined by midpoint interpolation around native pond banks, then lowered into 0.85m basins. Original UV/pigment are interpolated; no new painted artwork.';save('heaven-basin-terrain',m,'celestial-grounded')
# Place terrain without renormalising its new lower bound: compensate bottom origin.
allv=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in m['parts']]);lo,hi=allv.min(0),allv.max(0)
for i in layout['items']:
 if i['kind']=='ground':i['resource']='Okami/heaven-basin-terrain';i['position']['y']=float(lo[1]-.18);i['size']['y']=float(hi[1]-lo[1])
 if i['resource']=='Okami/celestial-gate':i['resource']='Okami/heaven-gate';i['size']['z']=3.4
# Return is a genuine original handheld mirror on a small native stone support, not a water splash.
layout['items']=[i for i in layout['items'] if i['resource']!='Okami/river-spirit-portal']
def put(res,x,z,sx,sy,sz,kind='prop',y=0,yaw=0,absolute=False):layout['items'].append(dict(resource='Okami/'+res,position=dict(x=x,y=y,z=z),size=dict(x=sx,y=sy,z=sz),kind=kind,yaw=yaw,absoluteHeight=absolute))
put('et19',0,-25,1.2,2.3,.35,y=.65,yaw=180);put('vt0a',0,-25,1.5,.55,1.2,y=0)
# Remove vegetation from the specified tea clearing and the open lookout.
layout['items']=[i for i in layout['items'] if i['kind'] not in ['flower','tree','maze-flower'] or not((i['position']['x']-11)**2+(i['position']['z']-13)**2<10 or (i['position']['x']+26)**2+(i['position']['z']-12)**2<12)]
layout['ponds']=pools;layout['treasure']=dict(x=-19.75,y=0,z=-2.75);layout['lookout']=dict(x=-26,y=0,z=12);layout['tea']=dict(x=11,y=0,z=13)
# Smooth each painted route with a quadratic subdivision while retaining its source-art surface.
# Main promenade rebuilt as a Catmull-Rom chain; branches remain curved softened joins.
main=[(0,-25),(0,-21),(2,-16),(3,-11),(1,-5),(-1,1),(0,7),(1,12),(0,17),(0,22)];walks=[]
def walk(a,b,w):walks.append(dict(a=dict(x=round(a[0],4),y=0,z=round(a[1],4)),b=dict(x=round(b[0],4),y=0,z=round(b[1],4)),width=w))
pts=[main[0]]+main+[main[-1]]
for k in range(1,len(pts)-2):
 a,b,c,d=[np.array(v,dtype=float) for v in pts[k-1:k+3]];last=b
 for t in [.3333333,.6666667,1]:
  q=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);walk(last,q,1.45);last=q
# Other paths include the round garden and a new sheltered lookout branch.
walks+=layout['walks'][9:];walk((-11,4.25),(-19,8),1.0);walk((-19,8),(-25,12),1.0)
layout['walks']=walks;layout['version']=6
(D/'CelestialGarden.json').write_text(json.dumps(layout,indent=2)+'\n')
# All new props and pose banks are recovered originals.
for n in ['vt4b','et19','vt74','vt9a','vt00']:
 if not(D/n/'Model.json').exists():assets.export(n,D/n,names=[r['name'] for r in assets.ROWS if r['package']==n and r['type']=='MOT'])
for pkg,names,out in [('an01',['an01_000'],'heaven-crane'),('hm50',['hm05_003','hm09_004','hm09_005','hm09_083','hm09_0a9','hm05_024'],'heaven-tea-hm50')]:assets.export(pkg,D/out,names=names)
for folder in [D/'vt4b',D/'heaven-crane',D/'heaven-tea-hm50']:
 for p in [folder,*folder.iterdir()]:
  if p.suffix!='.meta':meta(p)
# Identified native metallic strike and crane voice, properly ADX type-8 decoded.
from scan import decrypt,inspect_sound
from repair_audio import render
records=[]
for rawpath,index,name,cue in [(Path('/workspace/work/playtest-repair/source-native/data_pc/se/core/core.ses'),0,'heaven-gong','heaven-gong'),(Path('/workspace/work/heaven-complete/an01.ses'),0,'heaven-crane-call','heaven-bird')]:
 if not rawpath.exists():continue
 raw=rawpath.read_bytes();clear=decrypt(raw);entry=inspect_sound(clear)['ADX'][index];stream=clear[entry['offset']:entry['offset']+entry['bytes']];dest=D/'NativeAudio'/(name+'.wav');info=render(stream,dest,cue);meta(dest);records.append(dict(cue=cue,resource='Okami/NativeAudio/'+name,source=str(rawpath),stream=index,sourceSHA256=hashlib.sha256(stream).hexdigest(),decoding=info))
audio=json.load(open(D/'NativeAudio.json'));audio['cues']=[r for r in audio['cues'] if r['cue'] not in ['heaven-gong','heaven-bird']]+[dict(cue=r['cue'],resource=r['resource']) for r in records];(D/'NativeAudio.json').write_text(json.dumps(audio,indent=2)+'\n')
(W/'asset-provenance.json').write_text(json.dumps(dict(models=ledger,audio=records,terrainTriangles=sum(len(p['indices'])//3 for p in m['parts']),nativeThunderAlternativeInspection='wp49 is unrelated rolled mat, not an evolved glaive; retain the genuine wp29 model with native electric-effect choreography.'),indent=2)+'\n')
print('Built basin terrain:',sum(len(p['indices'])//3 for p in m['parts']),'triangles;',len(walks),'path segments;',len(records),'decoded sound cues')
