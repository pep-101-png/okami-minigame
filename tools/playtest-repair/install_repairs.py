"""Apply saved-scene repairs to the exact playtested remake source.

Uses a pinned source snapshot for repeatable authoring; not a Unity startup task.
The same Windflower scene, GUID, save data and existing gameplay are retained.
"""
from pathlib import Path
import json,re,struct,subprocess,sys,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/original-remake'))
from export_assets import A,OUT,RES,guid,skin
from install_world import add_component,patch
sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref,Terrain
from native import Scene,vec,fmt
BASE='72336e1aa558d1344c1b52b93bac882b3dd31eb4'
REVIEW={};MODELS={r['package']:r for r in json.loads((ROOT/'tools/original-remake/original-assets.json').read_text())['models']}
for r in json.loads(Path(__file__).with_name('asset-conversions.json').read_text()):
    if r.get('meshes'):MODELS[r['package']]=r
for r in json.loads(Path(__file__).with_name('stage-conversions.json').read_text()):MODELS[r['package']]=r

def pose(package,name):
    raw=(RES/package/'Poses.bytes').read_bytes();_,_,bones,count=struct.unpack_from('<4sIII',raw);offset=16
    for _ in range(count):
        n=struct.unpack_from('<I',raw,offset)[0];offset+=4;label=raw[offset:offset+n].decode();offset+=n;samples,duration,loop=struct.unpack_from('<IfI',raw,offset);offset+=12
        if label==name:return np.frombuffer(raw,'<f4',bones*10,offset).reshape(bones,10).copy()
        offset+=samples*bones*40
    raise ValueError((package,name))

def calibration(package,idle,height,external=1):
    m=json.loads((RES/package/'Model.json').read_text());parts=skin(m,pose(package,idle));groups=m.get('visibleGroups');v=np.concatenate([v for p,v in zip(m['parts'],parts) if not groups or int(p['name'].split('-')[1]) in groups]);lo=v.min(0);hi=v.max(0);scale=height/(hi[1]-lo[1])/external;center=(lo+hi)/2;offset=np.array([-center[0],-lo[1],-center[2]])*scale;return scale,offset

def install():
    path=A/'Sunward/Scenes/Windflower.unity';path.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT))
    w=World();s=w.scene;terrain=Terrain(w);old=json.loads((ROOT/'tools/original-remake/world-install.json').read_text());placed=[]
    def empty(name,p=(0,0,0),parent=0):
        part=MODELS['vt08']['meshes'][0];go=s.add(name,part['mesh'],part['material'],p=p,parent=parent);s.set(s.component(go,23),'m_Enabled',0);return go
    def place(package,position,size=None,height=None,yaw=0,scale=None,mask=None,parent=0,label=None):
        e=MODELS[package];lo=np.array(e['boundsMin']);hi=np.array(e['boundsMax']);native=None
        if mask is not None and (RES/package/'Model.json').exists():
            native=json.loads((RES/package/'Model.json').read_text())['parts']
            points=[w.mesh(part['mesh'],4300000)['vertices'] for i,part in enumerate(e['meshes']) if int(native[i]['name'].split('-')[1]) in mask]
            if points:
                v=np.concatenate(points);lo=v.min(0);hi=v.max(0)
        extent=np.maximum(.001,hi-lo)
        scale=np.broadcast_to(np.array(scale) if scale is not None else np.array(size)/extent if size is not None else (height/extent[1] if height else 1),(3,)).copy()
        rad=math.radians(yaw);rot=np.array([[math.cos(rad),0,math.sin(rad)],[0,1,0],[-math.sin(rad),0,math.cos(rad)]]);offset=np.array(position)-rot@(np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*scale)
        objects=[]
        for i,part in enumerate(e['meshes']):
            if native and int(native[i]['name'].split('-')[1]) not in mask:continue
            go=s.add('Original Okami · '+(label or package),part['mesh'],part['material'],parent=parent,p=offset,scale=scale);s.set(s.transform(go),'m_LocalRotation','{x: 0, y: %.9g, z: 0, w: %.9g}'%(math.sin(rad/2),math.cos(rad/2)));objects.append(go)
        placed.append(dict(package=package,position=list(position),size=size,height=height,objects=objects,label=label));return objects
    def collider(go,mesh=None,size=None,center=(0,0,0)):
        id=s.alloc();typ=64 if mesh else 65
        s.blocks[id]=f'''--- !u!{typ} &{id}
{ 'MeshCollider' if mesh else 'BoxCollider' }:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: {5 if mesh else 3}
'''+('  m_Convex: 0\n  m_CookingOptions: 30\n  m_Mesh: {fileID: 4300000, guid: '+mesh+', type: 2}\n' if mesh else '  m_Size: '+fmt(size)+'\n  m_Center: '+fmt(center)+'\n')
        s.blocks[go]=s.blocks[go].replace('  m_Layer:',f'  - component: {{fileID: {id}}}\n  m_Layer:',1);s.set(go,'m_Layer',6);return id
    def actor(package,p,height=1.8,idle=None,name='resident'):
        motions=next((r['motions'] for r in json.loads(Path(__file__).with_name('asset-conversions.json').read_text()) if r.get('package')==package and r.get('motions')),None)
        if not motions:motions=MODELS[package]['motions']
        standing=next(r['name'] for r in motions if r['name'].endswith('_000'))
        idle=idle or standing;scale,offset=calibration(package,standing,height)
        assert any(r['name']==idle for r in motions),('Requested native actor motion is absent',package,idle)
        go=empty('Original Okami · '+name,p);fields='  resource: Okami/'+package+'\n'+''.join('  '+key+': '+idle+'\n' for key in ['idle','walk','run','windup','strike','recover','death'])+'  modelOffset: '+fmt(offset)+'\n  modelScale: '+str(scale)+'\n  game: {fileID: 0}\n'
        if idle.endswith('_037'):fields+='  holdIdlePose: 1\n'
        add_component(s,go,'OriginalActor',fields);return go
    def hide(objects):
        for go in objects:
            mr=s.component(go,23)
            if mr:s.set(mr,'m_Enabled',0)
    # Keep native proportions, enlarge doors with the whole exterior, and
    # remove helper/interior planes from the outdoor house appearance.
    resized=[];house_masks={'vta3':[1],'vta0':[1],'vtb2':[1],'vta1':[0,2],'vta2':[1],'vtb0':[1],'vtb4':[0],'vta9':[0],'vta8':[0],'vtae':[3]}
    house_moves={3:(11,-7),4:(-11,7),6:(-13.4,18),7:(14,29)}
    for h in old['houses']:
        matching=next(r for r in old['nativePlacements'] if r['objects']==h['objects']);e=MODELS[h['package']];parts=json.loads((RES/h['package']/'Model.json').read_text())['parts']
        if h['number'] in [1,8]:hide(h['objects']);continue
        for i,go in enumerate(h['objects']):
            if len(parts)>i and int(parts[i]['name'].split('-')[1]) not in house_masks[h['package']]:s.set(s.component(go,23),'m_Enabled',0)
            t=s.transform(go);position=vec(s.blocks[t],'m_LocalPosition');scale=vec(s.blocks[t],'m_LocalScale');factor=1.75
            position*=factor;position[1]=.025+(vec(s.blocks[t],'m_LocalPosition')[1]-.025)*factor;s.set(t,'m_LocalPosition',fmt(position));s.set(t,'m_LocalScale',fmt(scale*factor))
        resized.append(dict(number=h['number'],factor=1.75,root=h['root']))
        if h['number'] in house_moves:
            x,z=house_moves[h['number']];t=s.transform(h['root']);p=vec(s.blocks[t],'m_LocalPosition');p[0]=x;p[2]=z;s.set(t,'m_LocalPosition',fmt(p))
    REVIEW['resizedVillageHouses']=resized
    # Rescale both working stalls with clear counter access.
    for r in old['nativePlacements']:
        if r['category']!='working market':continue
        hide(r['objects']);x=5.8 if r['position'][0]>0 else -5.8;place(r['package'],[x,terrain.height(x,0),0],size=[4.8,3.6,3.2],yaw=180 if x>0 else 0,label='enlarged working market')
    # Hide interior furnishings from outside the home, even through openings.
    interior=[]
    for r in old['nativePlacements']:
        if r['category'] in ['sleep interaction futon','memory mirror appearance','collectible shelf','tea set','home lantern','home Solar Flare display','home native glaive display']:
            weapon_parts=None;mask=None
            if r['category'] in ['home Solar Flare display','home native glaive display']:
                data=json.loads((RES/r['package']/'Model.json').read_text());weapon_parts=data['parts'];mask=data['visibleGroups']
            for i,go in enumerate(r['objects']):
                if weapon_parts and int(weapon_parts[i]['name'].split('-')[1]) not in mask:hide([go])
                else:interior.append(s.component(go,23))
    for id,b in list(s.blocks.items()):
        if 'Assembly-CSharp::Sunward.HomeCutaway\n' in b:s.blocks[id]=b+'  interior:\n'+''.join('  - {fileID: '+str(r)+'}\n' for r in interior)
    # Runtime actor bounds must exclude hidden variants/props. This corrects
    # the merchant's previous umbrella-derived floating offset.
    for prefab in ['NPC-'+str(i) for i in range(7)]+['Enemy-'+n for n in ['wisp','reed','ranged','heavy','elite','boss']]:
        path=A/'Sunward/Generated'/(prefab+'.prefab');text=subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True);scene=Scene(path,text=text)
        for id,b in scene.blocks.items():
            if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b:continue
            package=re.search(r'  resource: Okami/(\w+)',b)[1];idle=re.search(r'  idle: (\w+)',b)[1];external=1;target=1.8
            if prefab.startswith('Enemy-'):
                role=prefab[6:];external=float(re.search(r'  scale: ([^\n]+)',(A/'Sunward/Generated'/('Spirit-'+role+'.asset')).read_text())[1]);target=dict(wisp=1.5,reed=1.6,ranged=1.7,heavy=2,elite=1.85,boss=3.6)[role]
            scale,offset=calibration(package,idle,target,external);scene.set(id,'modelScale',scale);scene.set(id,'modelOffset',fmt(offset))
        path.write_text(scene.header+''.join(scene.blocks.values()))
    for id,b in list(s.blocks.items()):
        if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b:continue
        package=re.search(r'  resource: Okami/(\w+)',b)[1];idle=re.search(r'  idle: (\w+)',b)[1];height=3.6 if package=='vt6a' else 1.8;scale,offset=calibration(package,idle,height);s.set(id,'modelScale',scale);s.set(id,'modelOffset',fmt(offset))
    # Lower the cliff bases into the actual terrain under their footprints.
    buried=[]
    for r in old['nativePlacements']:
        if r['category']!='boundary rock':continue
        e=MODELS[r['package']];height=(e['boundsMax'][1]-e['boundsMin'][1])*r['scale'][1];x,y,z=r['position'];base=min(terrain.height(x+dx,z+dz) for dx in [-1,0,1] for dz in [-1,0,1])-max(.8,height*.38)
        shift=base-y
        for go in r['objects']:
            t=s.transform(go);p=vec(s.blocks[t],'m_LocalPosition');p[1]+=shift;s.set(t,'m_LocalPosition',fmt(p))
        buried.append(dict(objects=r['objects'],base=base))
    REVIEW['groundedBoundaryGroups']=len(buried)
    # New interior collision uses original native meshes. Disable the two old
    # solid building boxes that formerly occupied these playable rooms.
    changed=[]
    for id,b in list(s.blocks.items()):
        if s.kind(id)!=65 or '  m_Enabled: 0\n' in b:continue
        go=s.owner(id);t=s.transform(go)
        if not t:continue
        matrix=w.matrix(0,t);center=matrix[:3,3]
        if any(abs(center[0]-x)<.2 and abs(center[2]-z)<.2 for x,z in [(8,-15),(0,25)]):s.set(id,'m_Enabled',0);changed.append(id)
        for number,(x,z) in house_moves.items():
            h=next(h for h in old['houses'] if h['number']==number);before=np.asarray(h['oldPosition']);delta=np.array([x-before[0],0,z-before[2]])
            if abs(center[0]-before[0])<.2 and abs(center[2]-before[2])<.2:
                # These legacy solid boxes are separate world roots.
                parent=ref(s.blocks[t],'m_Father')[0];local_delta=np.linalg.solve(w.matrix(0,parent)[:3,:3],delta) if parent else delta;s.set(t,'m_LocalPosition',fmt(vec(s.blocks[t],'m_LocalPosition')+local_delta))
    REVIEW['retiredSolidRoomColliders']=changed
    # Existing central dojo slot: original r10c room, not a separate scene.
    dojo_roof=[];dojo_content=[];dojo_surfaces=[]
    for key in ['dojo-floor','dojo-wall','dojo-water','dojo-ceiling','dojo-sign','dojo-entry-roof']:
        e=MODELS[key]
        for part in e['meshes']:
            go=s.add('Original Okami · training hall · '+key,part['mesh'],part['material'],p=[0,1.11875,25],scale=[.25,.25,.25])
            if key in ['dojo-floor','dojo-wall']:collider(go,mesh=part['mesh'])
            if key in ['dojo-ceiling','dojo-entry-roof']:s.set(s.component(go,23),'m_Enabled',0)
            elif key in ['dojo-wall','dojo-sign']:dojo_surfaces.append(s.component(go,23))
    dojo_shell=place('vta8',[0,.05,25],size=[16.4,8.5,20],mask=[0],label='training hall exterior')
    dojo_roof.extend(s.component(go,23) for go in dojo_shell)
    for i,p in enumerate([[-3,.5,22],[3,.5,22],[0,1.25,29]]):
        root=empty('Original training dummy '+str(i),p);place('vt1d',[0,0,0],height=2,parent=s.transform(root),label='native training dummy');s.set(root,'m_Layer',8);add_component(s,root,'TrainingDummy','  game: {fileID: 0}\n')
        dojo_content.append(root)
    for package,idle,p in [('hm0c','hm0c_081',[-3,.5,24.2]),('hm2d','hm2d_080',[3,.5,24.2]),('hm44',None,[-4.7,.5,29])]:dojo_content.append(actor(package,p,height=2.7 if package=='hm0c' else 1.8,idle=idle,name='training samurai '+package))
    # Food house occupies the former eastern house slot, with original native
    # furniture, seated poses and music. No new demonstration scene is added.
    food_shell=place('vta9',[10,.05,-15],size=[12,7.4,8.2],mask=[0],label='food and music house exterior')
    # Reuse an original floor mesh and its UVs, fitted to this room footprint.
    floor_bounds=w.mesh(MODELS['dojo-floor']['meshes'][1]['mesh'],4300000)['vertices'];lo=floor_bounds.min(0);hi=floor_bounds.max(0)
    for index in [1,3,4]:
        floor=MODELS['dojo-floor']['meshes'][index];data=w.mesh(floor['mesh'],4300000);v=data['vertices'].copy()
        # The native central wood strip extends down the dojo's long entrance
        # walkway. Fit just the room footprint alongside its tatami/frame.
        if index==3:v[:,0]=np.clip(v[:,0],lo[0],hi[0]);v[:,2]=np.clip(v[:,2],lo[2],hi[2])
        v[:,0]=(v[:,0]-(lo[0]+hi[0])/2)*8.8/max(.001,hi[0]-lo[0]);v[:,2]=(v[:,2]-(lo[2]+hi[2])/2)*7.2/max(.001,hi[2]-lo[2]);v[:,1]=0
        from native import Mesh
        raw=bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',data['raw'])[1]);streams=np.frombuffer(raw,'<f4').reshape(len(v),data['stride']//4);m=Mesh();m.v=v.tolist();m.c=streams[:,6:9].tolist();m.uv=streams[:,10:12].tolist();m.tri=data['triangles'].tolist();m.bones=[0]*len(v);p=OUT/'Meshes'/('Food-house-native-floor-'+str(index)+'.asset');m.write(p);go=s.add('Original Okami · food house floor',guid(p),floor['material'],p=[10,.65,-15]);collider(go,mesh=guid(p))
    food_content=[]
    for x,z,sx,sz in [(10,-18.65,8.8,.18),(10,-11.35,8.8,.18),(5.55,-15,.18,7.3),(14.45,-17.45,.18,2.4),(14.45,-12.55,.18,2.4)]:
        root=empty('Food house collision',[x,.65,z]);collider(root,size=[sx,3.1,sz],center=[0,1.55,0])
    for p in [[7,.65,-16.7],[12.5,.65,-16.7],[12.5,.65,-13.6]]:
        food_content.extend(place('vt65',p,size=[1.5,.42,1],label='food house table and tea'))
        food_content.append(actor('hm09',[p[0],.65,p[2]+.8],idle='hm05_037',name='seated diner'))
    food_content.extend(place('vt9f',[7,.65,-17.4],size=[2.4,.6,.75],yaw=90,label='original koto'))
    food_content.append(actor('hm09',[7,.65,-18.2],idle='hm05_037',name='music house lady'))
    food_content.extend(place('vt64',[8,.65,-13.4],size=[1.7,.04,1.2],label='Amaterasu sitting mat'))
    for venue,roofs,contents in [('dojo',dojo_roof,dojo_content),('food',[s.component(go,23) for go in food_shell],food_content)]:
        root=empty('Original Okami · '+venue+' visibility');player=next(ref(b,'Player')[0] for b in s.blocks.values() if 'Assembly-CSharp::Sunward.GameFlow\n' in b)
        fields='  venue: '+venue+'\n  player: {fileID: '+str(player)+'}\n  roof:\n'+''.join('  - {fileID: '+str(r)+'}\n' for r in roofs)+'  interiorSurfaces:'+ ('\n'+''.join('  - {fileID: '+str(r)+'}\n' for r in dojo_surfaces) if venue=='dojo' else ' []\n')+'  contents:\n'+''.join('  - {fileID: '+str(go)+'}\n' for go in contents);add_component(s,root,'VenueVisibility',fields)
    # Interior floors must cover grass, not share space with outdoor plant art.
    for record in old['nativePlacements']:
        if record['category'] not in ['grass','flowers','roadside flowers']:continue
        x,y,z=record['position']
        if abs(x)<7.4 and 15.8<z<34.2 or abs(x-10)<4.4 and abs(z+15)<3.6:hide(record['objects'])
    # Native cherry blossoms over the existing pond.
    for p in [[-18.8,0,-21],[-11.6,0,-23]]:
        p[1]=terrain.height(p[0],p[2]);place('vtb1',p,height=6.6,mask=[1,3],label='pond cherry blossom tree')
    # Original fence meshes enclose the existing farm-animal routes. Feed uses
    # original dry grass; water uses original basins, not invented prop artwork.
    relocated=[]
    for go,raw in list(s.blocks.items()):
        if s.kind(go)!=1 or not (s.name(go).startswith('Living tree ') or s.name(go).startswith('Living bamboo')):continue
        t=s.transform(go)
        if not t:continue
        p=vec(s.blocks[t],'m_LocalPosition')
        if abs(p[0]-10)<5.5 and abs(p[2]+15)<4.5:
            oldp=p.copy();p[0]=20;p[2]=-24-len(relocated)*3;p[1]=terrain.height(p[0],p[2]);s.set(t,'m_LocalPosition',fmt(p));relocated.append(dict(root=go,before=oldp.tolist(),after=p.tolist()))
        elif -50<p[0]<-33 and 14<p[2]<33:
            oldp=p.copy();p[0]=-55;p[2]=13+len(relocated)*4;p[1]=terrain.height(p[0],p[2]);s.set(t,'m_LocalPosition',fmt(p));relocated.append(dict(root=go,before=oldp.tolist(),after=p.tolist()))
    REVIEW['treesMovedToFarmBoundary']=relocated
    for x,z,width,depth in [(-40.7,19,12.2,6.0),(-45,27.5,7.2,7.4),(-37.5,29.5,6.5,5.0)]:
        for px,pz,length,yaw in [(x,z-depth/2,width,0),(x,z+depth/2,width,0),(x-width/2,z,depth,90),(x+width/2,z,depth,90)]:
            y=terrain.height(px,pz);objects=place('farm-fence',[px,y,pz],size=[length,1.05,.18],yaw=yaw,label='farm pen fence')
            root=empty('Farm pen collision',[px,y,pz]);collider(root,size=[length,1.05,.18] if yaw==0 else [.18,1.05,length],center=[0,.525,0])
        for px,pz in [(x+width/2-1,z),(x-width/2+1,z)]:
            y=terrain.height(px,pz);place('vt3c',[px,y,pz],size=[1.5,.65,.8],label='farm native water basin');place('vt18',[px-.9,y,pz+.8],height=.55,label='farm native dry-grass feed')
    place('vta3',[-49,terrain.height(-49,34),34],size=[8.2,6.5,6],mask=[1],yaw=180,label='farm stable shelter')
    actor('hm00',[-48,terrain.height(-48,22),22],name='farmer')
    game_go=next(s.owner(i) for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.GameFlow\n' in b);add_component(s,game_go,'OriginalAtmosphere','  game: {fileID: 0}\n')
    # Navigation boxes follow the few exteriors moved to clear the new hall.
    data_path=A/'Sunward/Data/Valley.json';data=json.loads(subprocess.check_output(['git','show',BASE+':'+str(data_path.relative_to(ROOT))],cwd=ROOT))
    for number,(x,z) in house_moves.items():
        h=next(h for h in old['houses'] if h['number']==number);before=h['oldPosition']
        for box in data['world']['boxes']:
            if abs(box['x']-before[0])<.1 and abs(box['z']+before[2])<.1:box['x']=x;box['z']=-z
    data_path.write_text(json.dumps(data,separators=(',',':'))+'\n');REVIEW['houseRelocations']={str(k):list(v) for k,v in house_moves.items()}
    s.save()
    for p in [OUT,*OUT.rglob('*')]:
        if not p.name.endswith('.meta'):guid(p)
    REVIEW.update(baseCommit=BASE,scene='Assets/Sunward/Scenes/Windflower.unity',placements=placed,UnityCompilation=False,UnityPlayback=False)
    Path(__file__).with_name('scene-repairs.json').write_text(json.dumps(REVIEW,indent=2));print('Scene repaired; new native placements',len(placed))

if __name__=='__main__':install()
