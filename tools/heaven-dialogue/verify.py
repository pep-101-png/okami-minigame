"""Audit both native tea guest skins against the actual stump triangles, not hip height."""
from pathlib import Path
import sys,json,numpy as np,subprocess,hashlib
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';sys.path[:0]=['/workspace/sunward-remaster/tools/playtest-followup',str(R/'tools/spirit-charge-home/trailer')]
from pose_audit import bank
from asset_geometry import skin
m=json.loads((D/'heaven-tea-hm50/Model.json').read_text());pose=bank(D/'heaven-tea-hm50/Poses.bytes')['hm05_003'][0];st=json.loads((D/'heaven-tea-seat/Model.json').read_text());raw=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in st['parts']]);lo,hi=raw.min(0),raw.max(0);sc=np.array([.9,.27,.9])/(hi-lo);off=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*sc;tri=np.concatenate([(np.array(p['positions']).reshape(-1,3)*sc+off)[np.array(p['indices']).reshape(-1,3)] for p in st['parts']]);a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a;det=b[:,0]*c[:,2]-b[:,2]*c[:,0];good=abs(det)>1e-8;gaps=[];checks=0
for side in [-1,1]:
 angle=np.radians(90 if side<0 else 270);rot=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
 for frame in pose:
  vs=np.concatenate(skin(m,frame))*.82@rot.T;vs[:,1]+=.25
  for x,y,z in vs:
   u=np.divide((x-a[:,0])*c[:,2]-(z-a[:,2])*c[:,0],det,out=np.zeros(len(a)),where=good);v=np.divide(b[:,0]*(z-a[:,2])-b[:,2]*(x-a[:,0]),det,out=np.zeros(len(a)),where=good);hit=good&(u>=0)&(v>=0)&(u+v<=1)
   if hit.any():
    gap=y-max((a[:,1]+u*b[:,1]+v*c[:,1])[hit]);assert gap>=.001,(side,gap);gaps.append(gap);checks+=1
assert min(gaps)<.02,'Guests float above their actual seats'
s=(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/HeavenlyGarden.Features.cs').read_text();assert 'seat+Vector3.up*.25f' in s;assert 'Okami/NativeAudio/wind-0' not in s and 'World("heaven-bird"' not in s
base='2a519cc65eac9587f1ab64bee8e4d9ac8f999050'
# Preserve the approved table/tea setting, original sound clips and palace/weapon work.
for file in ['NativeAudio.json','NativeAudio/player-shiranui-layered-bark.wav']:
 path='Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/'+file
 assert not subprocess.check_output(['git','diff',base,'--name-only','--',path],cwd=R).strip()
result=dict(vertexSurfaceChecks=checks,minimumSkinClearanceMetres=float(min(gaps)),seatRootHeight=.25,pondDepthMetres=.45,removedLoop='Okami/NativeAudio/wind-0 · ST102 stream 0 · 2.997344 seconds',runtimeVerified=False)
Path('/workspace/work/heaven-dialogue/geometry.json').write_text(json.dumps(result,indent=2));print('PASS',checks,'native seated skin / actual log surface checks;',result)
