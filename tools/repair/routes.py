"""Check entire route segments and give larger animals room for a full stride."""
import json,math
import numpy as np
from scene_data import World,Terrain,A,ROOT
from farm_data import read as animals
from placements import candidates,water,road
def run():
    w=World();terrain=Terrain(w);path=A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json';layout=json.loads(path.read_text());blocks=json.loads((path.parent/'PlacementBounds.json').read_text())['blockers'];assets=animals();placed=[]
    def clear(x,z,r):
        if not(-47+r<x<56-r and -31+r<z<32-r) or water(x,z,r) or road(x,z,r) or math.hypot(x-35,z)<19+r:return False
        h=terrain.height(x,z)
        if any(abs(terrain.height(x+dx*r,z+dz*r)-h)>.26 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):return False
        for b in blocks:
            dx=max(0,abs(x-b['center']['x'])-b['half']['x']);dz=max(0,abs(z-b['center']['y'])-b['half']['y'])
            if dx*dx+dz*dz<(r+.20)**2:return False
        for points,pr in placed:
            if min(math.hypot(x-px,z-pz) for px,pz in points)<r+pr+.3:return False
        return True
    for actor in layout['actors']:
        radius=assets[actor['asset']]['radius']+.12;side=1.3 if radius>1 else 1.0 if radius>.5 else .8;found=None
        for x,z in candidates(actor['position']['x'],actor['position']['z'],.4,25):
            corners=[(x,z),(x+side,z),(x+side,z+side),(x,z+side)];samples=[]
            for i,a in enumerate(corners):
                b=corners[(i+1)%4];samples.extend((a[0]*(1-u)+b[0]*u,a[1]*(1-u)+b[1]*u) for u in np.linspace(0,1,13))
            if all(clear(px,pz,radius) for px,pz in samples):found=(corners,samples);break
        if found is None:raise RuntimeError('No full-route clearance for '+actor['name'])
        corners,samples=found;placed.append((samples,radius));actor['position']=dict(x=corners[0][0],y=terrain.height(*corners[0]),z=corners[0][1]);actor['path']=[dict(x=x,y=z) for x,z in corners]
    path.write_text(json.dumps(layout,indent=2)+'\n');return len(placed)
if __name__=='__main__':print('Full body and segment checked routes:',run())
