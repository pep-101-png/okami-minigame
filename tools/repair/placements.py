"""Repair actual Windflower visual footprints and plan clearance-tested animal routes."""
from pathlib import Path
import json,math,re,sys
import numpy as np
from scene_data import A,ROOT,World,ref,vec
from ground import guid,river
from farm_data import read as animals
OUT=A/'OkamiRemaster/Windflower';EPS=.12
def intersects(a,b,margin=0):return bool(np.all(a[0][[0,2]]<b[1][[0,2]]+margin) and np.all(a[1][[0,2]]>b[0][[0,2]]-margin))
def bounds(rows):return np.min([r['lo'] for r in rows],0),np.max([r['hi'] for r in rows],0)
def moved(box,delta):return box[0]+delta,box[1]+delta
def circle_box(x,z,r,box):
    q=np.maximum(box[0][[0,2]]-[x,z],0)+np.minimum(box[1][[0,2]]-[x,z],0)
    return float(q@q)<r*r
def road(x,z,r=0):
    if abs(x)<3.5+r and abs(z)<24+r:return True
    if abs(x+32)<1.8+r and abs(z)<28+r:return True
    if -34-r<x<-12+r and (abs(z+8)<1.5+r or abs(z-14)<1.5+r):return True
    return -1-r<x<19+r and abs(z)<2.5+r
def water(x,z,r=0):
    width=2.45+.4*math.sin(-z*.17+.4)+.25*math.cos(-z*.31)
    if abs(x-float(river(-z)))<width+r+.35:return True
    return ((x+15)/(3.05+r+.3))**2+((z+22)/(2.05+r+.3))**2<1
def candidates(x,z,step=.75,limit=15):
    yield x,z
    for distance in np.arange(step,limit+step/2,step):
        count=max(16,int(2*math.pi*distance/step))
        for i in range(count):
            angle=2*math.pi*i/count;yield x+math.cos(angle)*distance,z+math.sin(angle)*distance
def run():
    w=World();s=w.scene;rows=list(w.renderers());rows=[r for r in rows if r['lo'] is not None and r['kind']==23]
    datafile=A/'Sunward/Data/Valley.json';data=json.loads(datafile.read_text());world=data['world'];changes=[]
    terrain=next(r for r in rows if r['hi'][0]-r['lo'][0]>120 and r['hi'][1]<2)
    verts=w.mesh(terrain['meshGUID'],terrain['meshID'])['vertices'];hgrid={(round(float(x),2),round(float(z),2)):float(y) for x,y,z in verts}
    def height(x,z):
        x=np.clip(x,-60,69.999);z=np.clip(z,-47.999,48);ix=math.floor((x+60)*2);iz=math.floor((48-z)*2);u=(x+60)*2-ix;v=(48-z)*2-iz;x0=-60+ix*.5;z0=48-iz*.5
        h00=hgrid[round(x0,2),round(z0,2)];h10=hgrid[round(x0+.5,2),round(z0,2)];h01=hgrid[round(x0,2),round(z0-.5,2)];h11=hgrid[round(x0+.5,2),round(z0-.5,2)]
        return h00+(h10-h00)*u+(h01-h00)*v if u+v<=1 else h11+(h01-h11)*(1-u)+(h10-h11)*(1-v)
    def navmove(old,new,radius):
        found=[o for o in world['obstacles'] if (o['x']-old[0])**2+(-o['z']-old[2])**2<.12**2]
        for o in found:o['x']=float(new[0]);o['z']=float(-new[2])
        if not found and -48<new[0]<57 and -33<-new[2]<32:world['obstacles'].append(dict(x=float(new[0]),z=float(-new[2]),r=float(radius)))
    def relocate(rootids,delta):
        for t in rootids:
            p=vec(s.blocks[t],'m_LocalPosition');s.set(t,'m_LocalPosition','{x: %.8g, y: %.8g, z: %.8g}'%tuple(p+delta))
    # Fit complete prototype structures as coherent groups. These remain
    # prototypes; the script never reclassifies them as original native houses.
    building_rows=[];buildings=[]
    for number in range(14):
        group=[r for r in rows if re.search(r'Native Windflower · .* house '+str(number)+r'$',r['name'])]
        if not group:continue
        parent=ref(s.blocks[s.transform(group[0]['go'])],'m_Father')[0];p=w.matrix(0,parent)[:3,3];box=min(world['boxes'][:19],key=lambda b:(b['x']-p[0])**2+(-b['z']-p[2])**2)
        old=bounds(group);newlocal=[]
        for r in group:newlocal.append(w.mesh(r['meshGUID'],r['meshID'])['vertices'])
        local=np.concatenate(newlocal);lo=local.min(0);hi=local.max(0);matrix=w.matrix(0,parent);rot=matrix[:3,:3];available=np.array([2*box['halfX']+1.0,2*box['halfZ']+1.0]);span=np.abs(rot[:,[0,2]])@np.array([hi[0]-lo[0],hi[2]-lo[2]]);uniform=min(available[0]/max(.01,span[0]),available[1]/max(.01,span[2]))
        center=(lo+hi)/2;center[1]=lo[1];shift=-center*uniform;shift[1]+=height(p[0],p[2])-p[1]-.035
        points=(local*uniform+shift)@rot.T+p;new=(points.min(0),points.max(0))
        for r in group:
            t=s.transform(r['go']);s.set(t,'m_LocalScale','{x: %.8g, y: %.8g, z: %.8g}'%(uniform,uniform,uniform));s.set(t,'m_LocalPosition','{x: %.8g, y: %.8g, z: %.8g}'%tuple(shift))
        buildings.append(new);building_rows.extend(group);changes.append(dict(kind='prototype-house-footprint',number=number,uniformScale=uniform,before=[x.tolist() for x in old],after=[x.tolist() for x in new],originalHouseReplacement=False))
    # Include the unchanged functional home/market/shrine footprints.
    for b in world['boxes'][:19]:buildings.append((np.array([b['x']-b['halfX'],0,-b['z']-b['halfZ']]),np.array([b['x']+b['halfX'],6,-b['z']+b['halfZ']])))
    rocks=[]
    rockrows=[r for r in rows if re.match(r'Native Windflower · original ST2 rock \d+$',r['name'])]
    for r in rockrows:
        number=int(r['name'].split()[-1]);t=ref(s.blocks[s.transform(r['go'])],'m_Father')[0];matrix=w.matrix(0,t);center=(r['lo']+r['hi'])/2;old=matrix[:3,3];box=(r['lo'],r['hi']);extent=(box[1]-box[0])/2;radius=float(np.linalg.norm(extent[[0,2]]));inplay=-48<old[0]<57 and -32<old[2]<33
        def valid(x,z):
            delta=np.array([x-old[0],0,z-old[2]]);b=moved(box,delta)
            if b[0][0]<-59.5 or b[1][0]>69.5 or b[0][2]<-47.5 or b[1][2]>47.5:return False
            if water(x,z,min(radius,2.2)):return False
            if inplay and road(x,z,min(radius,2)):return False
            if math.hypot(x-35,z)<17.0+min(radius,2):return False
            return not any(intersects(b,other,.25) for other in buildings) and not any(intersects(b,other,.08) for other in rocks)
        chosen=None
        for x,z in candidates(old[0],old[2],.6,18):
            if valid(x,z):chosen=np.array([x,old[1],z]);break
        if chosen is None:
            # Decorative out-of-map boulders may overlap each other as an
            # intentional cliff bank. They remain explicit unresolved cases.
            rocks.append(box);changes.append(dict(kind='rock-clearance-unresolved',number=number));continue
        dx=chosen-old;dx[1]=height(chosen[0],chosen[2])-.06-box[0][1]
        if np.linalg.norm(dx)>.025:
            relocate([t],dx);navmove(old,old+dx,min(radius,2.5));changes.append(dict(kind='rock',number=number,delta=dx.tolist()))
        rocks.append(moved(box,dx))
    trees=[]
    treeids=sorted({int(re.search(r'Living tree (\d+)',s.name(i))[1]) for i in s.blocks if s.kind(i)==1 and re.search(r'^Living tree (\d+)',s.name(i))})
    for number in treeids:
        group=[r for r in rows if re.match(r'Living tree '+str(number)+r'\b',r['name']) or re.match(r'Native Windflower · village cherry '+str(number)+r'$',r['name'])]
        if not group:continue
        box=bounds(group);base=next(i for i in s.blocks if s.kind(i)==1 and s.name(i).startswith('Living tree '+str(number)+' · bark'))
        old=vec(s.blocks[s.transform(base)],'m_LocalPosition');radius=float(max((box[1]-box[0])[[0,2]])/2)
        roots=[s.transform(i) for i in s.blocks if s.kind(i)==1 and re.match(r'Living tree '+str(number)+r'\b',s.name(i)) and ref(s.blocks[s.transform(i)],'m_Father')[0]==0]
        def valid(x,z):
            b=moved(box,np.array([x-old[0],0,z-old[2]]))
            if not(-46+radius<x<55-radius and -30+radius<z<31-radius):return False
            if water(x,z,.7) or road(x,z,.8) or math.hypot(x-35,z)<19+radius:return False
            if any(intersects(b,other,.4) for other in buildings):return False
            if any(circle_box(x,z,.9,other) for other in rocks):return False
            return not any(math.hypot(x-c[0],z-c[2])<max(2.2,(radius+rr)*.7) for c,rr in trees)
        chosen=None
        for x,z in candidates(old[0],old[2],.75,24):
            if valid(x,z):chosen=np.array([x,height(x,z)-.035,z]);break
        if chosen is None:chosen=old;changes.append(dict(kind='tree-clearance-unresolved',number=number))
        delta=chosen-old
        if np.linalg.norm(delta)>.025:
            relocate(roots,delta);navmove(old,chosen,.55);changes.append(dict(kind='tree',number=number,delta=delta.tolist()))
        trees.append((chosen,radius))
    # These bounds are also used by the runtime animal preflight/sweep, so a
    # valid route cannot pass through visible geometry lacking a physics proxy.
    blockers=[]
    for role,boxes in [('building',buildings),('rock',rocks)]:
        for lo,hi in boxes:blockers.append(dict(kind=role,center=dict(x=float((lo[0]+hi[0])/2),y=float((lo[2]+hi[2])/2)),half=dict(x=float((hi[0]-lo[0])/2),y=float((hi[2]-lo[2])/2))))
    for p,r in trees:blockers.append(dict(kind='trunk',center=dict(x=float(p[0]),y=float(p[2])),half=dict(x=.65,y=.65)))
    for b in world['boxes'][19:]:blockers.append(dict(kind='rail',center=dict(x=b['x'],y=-b['z']),half=dict(x=b['halfX'],y=b['halfZ'])))
    boundsfile=OUT/'Resources/WindflowerNative/PlacementBounds.json';boundsfile.write_text(json.dumps(dict(blockers=blockers),separators=(',',':'))+'\n');guid(boundsfile)
    layoutfile=OUT/'Resources/WindflowerNative/Animals.json';layout=json.loads(layoutfile.read_text());assets=animals();routes=[]
    def animalclear(x,z,r):
        if not(-47+r<x<56-r and -31+r<z<32-r) or water(x,z,r) or road(x,z,r) or math.hypot(x-35,z)<19+r:return False
        for b in blockers:
            dx=max(0,abs(x-b['center']['x'])-b['half']['x']);dz=max(0,abs(z-b['center']['y'])-b['half']['y'])
            if dx*dx+dz*dz<(r+.18)**2:return False
        h=height(x,z)
        if any(abs(height(x+dx*r,z+dz*r)-h)>.28 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):return False
        if any(math.hypot(x-p[0],z-p[1])<r+pr+.45 for p,pr in routes):return False
        return True
    for actor in layout['actors']:
        r=assets[actor['asset']]['radius']+.12;old=np.array([actor['position']['x'],actor['position']['z']]);center=None
        for x,z in candidates(float(np.clip(old[0],-44,52)),float(np.clip(old[1],-28,29)),.75,36):
            if animalclear(x,z,r) and all(animalclear(x+dx,z+dz,r) for dx,dz in [(.6,0),(0,.6),(.6,.6)]):center=(x,z);break
        if center is None:raise RuntimeError('No full-footprint safe route for '+actor['name'])
        x,z=center;actor['position']=dict(x=x,y=height(x,z),z=z);actor['path']=[dict(x=x+dx,y=z+dz) for dx,dz in [(0,0),(.6,0),(.6,.6),(0,.6)]];routes.append((center,r));changes.append(dict(kind='animal-route',name=actor['name'],radius=r,old=old.tolist(),new=list(center)))
    layoutfile.write_text(json.dumps(layout,indent=2)+'\n');datafile.write_text(json.dumps(data,separators=(',',':'))+'\n');s.save()
    return dict(changes=changes,blockers=len(blockers),nativeHouseReplacement=False,animalRoutes=len(routes),UnityVerified=False)
if __name__=='__main__':
    result=run();(ROOT/'tools/repair/placement-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='changes'}))
