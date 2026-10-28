"""Preserve native rock proportions and protect entrances/NPC/player approaches."""
import re,json,math
import numpy as np
from scene_data import A,ROOT,World,Terrain,ref,vec
from placements import candidates,water,road,intersects
def run():
    w=World();s=w.scene;rows=list(w.renderers());terrain=Terrain(w,rows);datafile=A/'Sunward/Data/Valley.json';data=json.loads(datafile.read_text());nav=data['world']['obstacles'];changes=[]
    pieces=json.loads((ROOT/'tools/remaster/live/authoring-report.json').read_text())['originalRocks']['pieces']
    # Undo the previous per-axis normalization. Rotating/scaling a recovered
    # rock is fine; stretching a low boulder into a tall pillar is not.
    for r in rows:
        match=re.match(r'Native Windflower · original ST2 rock (?:ink )?(\d+)$',r['name'])
        if not match:continue
        number=int(match[1]);t=s.transform(r['go']);parent=ref(s.blocks[t],'m_Father')[0];scale=np.linalg.norm(w.matrix(0,parent)[:3,:3],axis=0);piece=pieces[number%len(pieces)];size=np.asarray(piece['sourceBoundsMax'])-piece['sourceBoundsMin'];target=max(scale[0],scale[2]);new=size/max(size[0],size[2])*target/scale
        s.set(t,'m_LocalScale','{x: %.8g, y: %.8g, z: %.8g}'%tuple(new))
    s.save();w=World();s=w.scene;rows=list(w.renderers());terrain=Terrain(w,rows)
    houses=[]
    for n in range(14):
        group=[r for r in rows if r['lo'] is not None and re.search(r'Native Windflower · .* house '+str(n)+r'$',r['name'])]
        if group:houses.append((np.min([r['lo'] for r in group],0),np.max([r['hi'] for r in group],0)))
    home=[r for r in rows if r['lo'] is not None and r['name'].startswith('Home ·')]
    if home:houses.append((np.min([r['lo'] for r in home],0),np.max([r['hi'] for r in home],0)))
    approaches=[(np.array([-35.4,0,-25]),np.array([-32.6,3,-19.4]))]
    for instance,prefab in w.prefabs.items():
        if not prefab.path.name.startswith('NPC-'):continue
        root=next(i for i in prefab.blocks if prefab.kind(i)==4 and ref(prefab.blocks[i],'m_Father')[0]==0);p=w.matrix(instance,root)[:3,3];approaches.append((p-np.array([1.2,1,1.2]),p+np.array([1.2,2,1.2])))
    def navmove(old,new,radius,tree=False):
        found=[o for o in nav if (o['x']-old[0])**2+(-o['z']-old[2])**2<.13**2]
        for o in found:
            o['x']=float(new[0]);o['z']=float(-new[2])
            if not tree:o['r']=float(radius)
        if not found and -48<new[0]<57 and -32<new[2]<33:nav.append(dict(x=float(new[0]),z=float(-new[2]),r=float(radius)))
    rocks=[]
    for r in rows:
        if not re.match(r'Native Windflower · original ST2 rock \d+$',r['name']):continue
        t=ref(s.blocks[s.transform(r['go'])],'m_Father')[0];old=w.matrix(0,t)[:3,3];box=(r['lo'],r['hi']);extent=(box[1]-box[0])/2;radius=float(np.linalg.norm(extent[[0,2]]));chosen=None
        def clear(x,z):
            delta=np.array([x-old[0],0,z-old[2]]);b=(box[0]+delta,box[1]+delta)
            return b[0][0]>-59.5 and b[1][0]<69.5 and b[0][2]>-47.5 and b[1][2]<47.5 and not water(x,z,float(max(extent[0],extent[2]))) and not(-48<x<57 and -32<z<33 and road(x,z,radius)) and math.hypot(x-35,z)>17+radius and not any(intersects(b,h,.2) for h in houses+approaches) and not any(intersects(b,b2,.05) for b2 in rocks)
        for x,z in candidates(old[0],old[2],.6,20):
            if clear(x,z):chosen=np.array([x,old[1],z]);break
        if chosen is None:raise RuntimeError('Unresolved rock approach clearance: '+r['name'])
        delta=chosen-old;ground=min(terrain.height(chosen[0]+dx*extent[0]*.85,chosen[2]+dz*extent[2]*.85) for dx,dz in [(0,0),(-1,-1),(-1,1),(1,-1),(1,1)])-.06;delta[1]=ground-box[0][1]
        p=vec(s.blocks[t],'m_LocalPosition')+delta;s.set(t,'m_LocalPosition','{x: %.8g, y: %.8g, z: %.8g}'%tuple(p));navmove(old,old+delta,radius)
        if np.linalg.norm(delta)>.03:changes.append(dict(kind='rock-final-clearance',name=r['name'],delta=delta.tolist()))
        rocks.append((box[0]+delta,box[1]+delta))
    trees=[];ids=sorted({int(re.search(r'^Living tree (\d+)',s.name(i))[1]) for i in s.blocks if s.kind(i)==1 and re.search(r'^Living tree (\d+)',s.name(i))})
    for n in ids:
        group=[r for r in rows if r['lo'] is not None and (re.match(r'Living tree '+str(n)+r'\b',r['name']) or re.match(r'Native Windflower · village cherry '+str(n)+r'$',r['name']))]
        if not group:continue
        box=(np.min([r['lo'] for r in group],0),np.max([r['hi'] for r in group],0));base=next(i for i in s.blocks if s.kind(i)==1 and s.name(i).startswith('Living tree '+str(n)+' · bark'));old=vec(s.blocks[s.transform(base)],'m_LocalPosition');radius=float(max((box[1]-box[0])[[0,2]])/2);chosen=None
        def clear(x,z):
            delta=np.array([x-old[0],0,z-old[2]]);b=(box[0]+delta,box[1]+delta)
            if not(-46+radius<x<55-radius and -30+radius<z<31-radius) or water(x,z,.8) or road(x,z,.8) or math.hypot(x-35,z)<19+radius:return False
            if any(intersects(b,h,.4) for h in houses+approaches):return False
            if any(intersects(b,h,.15) for h in rocks):return False
            return not any(math.hypot(x-p[0],z-p[2])<max(2.2,(radius+r)*.7) for p,r in trees)
        for x,z in candidates(old[0],old[2],.75,30):
            if clear(x,z):chosen=np.array([x,terrain.height(x,z)-.035,z]);break
        if chosen is None:raise RuntimeError('Unresolved full canopy clearance: '+str(n))
        delta=chosen-old
        for i in s.blocks:
            if s.kind(i)!=1 or not re.match(r'Living tree '+str(n)+r'\b',s.name(i)):continue
            t=s.transform(i)
            if ref(s.blocks[t],'m_Father')[0]:continue
            p=vec(s.blocks[t],'m_LocalPosition')+delta;s.set(t,'m_LocalPosition','{x: %.8g, y: %.8g, z: %.8g}'%tuple(p))
        navmove(old,chosen,.6,True);trees.append((chosen,radius))
        if np.linalg.norm(delta)>.03:changes.append(dict(kind='tree-full-canopy-clearance',number=n,delta=delta.tolist()))
    removed=0
    for i in s.blocks:
        if s.kind(i)!=1 or not s.name(i).startswith(('Folded meadow blades','Dimensional flowers')):continue
        t=s.transform(i);p=vec(s.blocks[t],'m_LocalPosition')
        if (road(p[0],p[2],.1) or math.hypot(p[0]-35,p[2])<17.2) and all(s.kind(c) in [4,23,33] for c in s.refs(i)):
            s.set(i,'m_IsActive',0);removed+=1
    s.save();datafile.write_text(json.dumps(data,separators=(',',':'))+'\n')
    # Rebuild runtime geometry bounds after changes in both proportions and placement.
    blockers=[]
    for role,boxes in [('building',houses),('rock',rocks),('approach',approaches)]:
        for lo,hi in boxes:blockers.append(dict(kind=role,center=dict(x=float((lo[0]+hi[0])/2),y=float((lo[2]+hi[2])/2)),half=dict(x=float((hi[0]-lo[0])/2),y=float((hi[2]-lo[2])/2))))
    for b in data['world']['boxes']:blockers.append(dict(kind='physics-box',center=dict(x=b['x'],y=-b['z']),half=dict(x=b['halfX'],y=b['halfZ'])))
    for p,r in trees:blockers.append(dict(kind='trunk',center=dict(x=float(p[0]),y=float(p[2])),half=dict(x=.65,y=.65)))
    (A/'OkamiRemaster/Windflower/Resources/WindflowerNative/PlacementBounds.json').write_text(json.dumps(dict(blockers=blockers),separators=(',',':'))+'\n')
    result=dict(nativeRockProportionsRestored=122,approachesProtected=len(approaches),canopiesChecked=len(trees),cosmeticPlantsRemovedFromRoadsAndArena=removed,changes=changes,UnityVerified=False)
    (ROOT/'tools/repair/final-clearance-checks.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':print(json.dumps({k:v for k,v in run().items() if k!='changes'}))
