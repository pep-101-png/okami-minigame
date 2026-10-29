"""Ground existing vegetation and boulders against the actual rendered triangles."""
import json,re
import numpy as np
from scene_data import A,ROOT,World,Terrain,ref,vec
def run():
    w=World();rows=list(w.renderers());terrain=Terrain(w,rows);s=w.scene;changes=[];datafile=A/'Sunward/Data/Valley.json';data=json.loads(datafile.read_text());nav=data['world']['obstacles']
    for r in rows:
        if not re.match(r'Native Windflower · original ST2 rock \d+$',r['name']):continue
        parent=ref(s.blocks[s.transform(r['go'])],'m_Father')[0];center=w.matrix(0,parent)[:3,3];lo=r['lo'];hi=r['hi'];extent=(hi-lo)/2
        ground=min(terrain.height(center[0]+dx*extent[0]*.85,center[2]+dz*extent[2]*.85) for dx,dz in [(0,0),(-1,-1),(-1,1),(1,-1),(1,1)])-.06
        dy=ground-lo[1]
        if abs(dy)>.01:
            p=vec(s.blocks[parent],'m_LocalPosition');p[1]+=dy;s.set(parent,'m_LocalPosition','{x: %.8g, y: %.8g, z: %.8g}'%tuple(p));changes.append(dict(kind='rock-base',name=r['name'],deltaY=dy))
        radius=float(np.linalg.norm(extent[[0,2]]))
        for obstacle in nav:
            if (obstacle['x']-center[0])**2+(-obstacle['z']-center[2])**2<.12**2:obstacle['r']=max(obstacle['r'],radius)
    for go in s.blocks:
        if s.kind(go)!=1 or not s.name(go).startswith(('Folded meadow blades','Dimensional flowers','Living bamboo')):continue
        t=s.transform(go);raw=s.blocks[t]
        if ref(raw,'m_Father')[0]!=0:continue
        p=vec(raw,'m_LocalPosition');target=terrain.height(p[0],p[2])-.025
        if abs(p[1]-target)>.01:
            old=float(p[1]);p[1]=target;s.set(t,'m_LocalPosition','{x: %.8g, y: %.8g, z: %.8g}'%tuple(p));changes.append(dict(kind='vegetation-base',name=s.name(go),deltaY=target-old))
    s.save();datafile.write_text(json.dumps(data,separators=(',',':'))+'\n');return changes
if __name__=='__main__':
    changes=run();(ROOT/'tools/repair/grounding-checks.json').write_text(json.dumps(changes,indent=2)+'\n');print('Grounded cosmetic objects:',len(changes))
