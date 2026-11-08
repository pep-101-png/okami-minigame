"""Focused saved-scene house/collision changes; preserve existing gameplay source."""
from pathlib import Path
import sys,re,json,numpy as np
sys.path.insert(0,'/workspace/sunward-remaster/tools/repair');import scene_data as d
d.A=Path('/workspace/sunward-tundra-desktop/Sunward-Unity/Assets');w=d.World();s=w.scene
from native import fmt
base=Path('/workspace/work/village-complete');ledger={};centre=np.array([14.,0,29.]);R=np.array([[0,0,-1],[0,1,0],[1,0,0]])
def rotate(go):
 t=s.transform(go);raw=s.blocks[t];p=d.vec(raw,'m_LocalPosition');s.set(t,'m_LocalPosition',fmt(centre+R@(p-centre)))
 q=np.array([float(v) for v in re.search(r'm_LocalRotation: \{x: ([^,]+), y: ([^,]+), z: ([^,]+), w: ([^}]+)',raw).groups()]);a=np.array([0,-np.sqrt(.5),0,np.sqrt(.5)]);v=a[3]*q[:3]+q[3]*a[:3]+np.cross(a[:3],q[:3]);qw=a[3]*q[3]-a[:3]@q[:3];s.set(t,'m_LocalRotation','{x: %.9g, y: %.9g, z: %.9g, w: %.9g}'%(*v,qw))
removed=[];rotated=[]
for i,b in list(s.blocks.items()):
 if s.kind(i)!=1 or not s.transform(i):continue
 n=s.name(i)
 if 'village house 6 ·' in n or 'repaired village house 6 ·' in n:s.set(i,'m_IsActive',0);removed.append(i)
 if 'village house 7 ·' in n:rotated.append(i)
# Rotate the entire shell in its world-positioned parent, keeping native children local.
rotate(8000000000000000309)
removedParent=s.owner(d.ref(s.blocks[s.transform(8000000000000005219)],'m_Father')[0]);s.set(removedParent,'m_IsActive',0)
# The real shell collider follows the rotated house.
rotate(1611424238)
# Retired house six's old solid footprint is the invisible obstacle across the river.
for c in s.refs(1808887473):
 if s.kind(c)==65:s.set(c,'m_Enabled',0)
# House thirteen was relocated in an earlier update; move its leftover walls too.
delta=np.array([7.89,0,15.]);t=s.transform(1166610200);s.set(t,'m_LocalPosition',fmt(d.vec(s.blocks[t],'m_LocalPosition')+delta))
for i,b in list(s.blocks.items()):
 if s.kind(i)!=114 or 'Assembly-CSharp::Sunward.Remaster.NativeHomeRoom' not in b:continue
 num=int(re.search(r'  number: (\d+)',b)[1])
 if num==6:s.set(s.owner(i),'m_IsActive',0)
 if num==7:
  for key in ['door','exitPoint']:s.set(i,key,fmt(centre+R@(d.vec(b,key)-centre)))
  s.set(i,'doorInward',fmt(R@d.vec(b,'doorInward')))
 if num==13:
  for key in ['door','exitPoint']:s.set(i,key,fmt(d.vec(b,key)+delta))
# Remove the scattered lip pebbles; terrain banks own the new waterfall silhouette.
for r in list(w.renderers()):
 if r['instance'] or 'rock · vt2a' not in r['name']:continue
 p=(r['lo']+r['hi'])/2
 if -30<p[0]<-15 and 33<p[2]<44:s.set(r['go'],'m_IsActive',0)
p=d.A/'Sunward/Data/Valley.json';j=json.loads(p.read_text());boxes=[];moved=[]
for box in j['world']['boxes']:
 pos=np.array([box['x'],0,-box['z']])
 if np.linalg.norm(pos-np.array([-13.4,0,18]))<4:continue
 if np.linalg.norm(pos-np.array([-27,0,8]))<4:
  box['x']+=delta[0];box['z']-=delta[2];moved.append(box)
 if np.linalg.norm(pos-centre)<4:
  pos=centre+R@(pos-centre);box['x']=float(pos[0]);box['z']=float(-pos[2]);box['halfX'],box['halfZ']=box['halfZ'],box['halfX']
 boxes.append(box)
j['world']['boxes']=boxes;p.write_text(json.dumps(j,separators=(',',':'))+'\n');s.save();ledger.update(removedHouseBehindDojo=removed,rotatedHouseByBoarPen=rotated,rotationDegrees=-90,newDoorFacing='South, toward the open village approach',retiredCollisionGo=1808887473,relocatedCollisionGo=1166610200,relocatedHouse13Delta=delta.tolist());(base/'spatial-repair.json').write_text(json.dumps(ledger,indent=2));print(json.dumps(ledger))
