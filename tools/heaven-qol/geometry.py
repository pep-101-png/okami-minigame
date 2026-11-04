from pathlib import Path
import json,math,numpy as np
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami'
layout=json.loads((D/'CelestialGarden.json').read_text())['items'];surfaces=[]
def height(x,z):
 if not surfaces:return None
 tri=np.concatenate(surfaces);a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a;det=b[:,0]*c[:,2]-b[:,2]*c[:,0];valid=abs(det)>1e-8;d0=x-a[:,0];d1=z-a[:,2];u=np.divide(d0*c[:,2]-d1*c[:,0],det,out=np.full(len(a),-1.),where=valid);v=np.divide(b[:,0]*d1-b[:,2]*d0,det,out=np.full(len(a),-1.),where=valid);hit=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001);return float(np.max((a[:,1]+u*b[:,1]+v*c[:,1])[hit])) if hit.any() else None
def triangles(item):
 m=json.loads((D/item['resource'].split('/')[-1]/'Model.json').read_text());ps=m['parts'];v=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in ps]);lo=v.min(0);hi=v.max(0);sc=np.array(list(item['size'].values()))/np.maximum(.001,hi-lo);off=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*sc;p=np.array(list(item['position'].values()),dtype=float)
 if item['kind']=='ground' and not item.get('absoluteHeight') and item['resource'] not in ['Okami/celestial-meadow','Okami/celestial-terrace']:
  base=height(p[0],p[2]) or 0
  if item['resource']=='Okami/vt0a' and item['size']['y']>.5:base=min([base]+[height(p[0]+x,p[2]+z) or 0 for x,z in [(-4,-4),(4,-4),(-4,4),(4,4)]])
  p[1]+=base
 a=math.radians(item['yaw']);rot=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
 return np.concatenate([((np.array(part['positions']).reshape(-1,3)*sc+off)@rot.T+p)[np.array(part['indices']).reshape(-1,3)] for part in ps])
for item in layout:
 if item['kind']=='ground':surfaces.append(triangles(item))
if __name__=='__main__':
 for p in [(0,-25),(0,-20),(0,-14),(-5,-8),(-10,-2),(0,3),(0,17),(0,22),(18,-12),(-23,7)]:print(p,height(*p))
 for i,item in enumerate(layout):
  if item['kind']=='ground':
   t=triangles(item);print(i,item['resource'],'y',t[:,:,1].min(),t[:,:,1].max())
