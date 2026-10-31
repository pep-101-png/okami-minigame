"""Repair the same Windflower scene against the exact publicly tested candidate."""
from pathlib import Path
import sys,json,re,math,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/playtest-repair'));import install_repairs as previous
from export_assets import A,OUT,RES,guid
from install_world import add_component
from scene_data import World,ref,Terrain
from native import Scene,vec,fmt
BASE='262519a7ac762e4e1f5af7f472139cedf87f8bd9'

def run():
    path=A/'Sunward/Scenes/Windflower.unity';path.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT));w=World();s=w.scene;terrain=Terrain(w);ledger=[]
    models=dict(previous.MODELS)
    for r in json.loads(Path(__file__).with_name('extra-assets.json').read_text()):models[r['package']]=r
    # Retain only the original tree's bark above the building columns.
    from native import Mesh
    source=models['vtb1']['meshes'][5];data=w.mesh(source['mesh'],4300000);v=data['vertices'];faces=data['triangles'];keep=np.min(v[faces,1],axis=1)>5.2
    raw=bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',data['raw'])[1]);streams=np.frombuffer(raw,'<f4').reshape(len(v),data['stride']//4);selected=faces[keep];used=np.unique(selected);remap=np.full(len(v),-1);remap[used]=np.arange(len(used));m=Mesh();m.v=v[used].tolist();m.c=streams[used,6:9].tolist();m.uv=streams[used,10:12].tolist();m.tri=remap[selected].tolist();m.bones=[0]*len(used);bark=OUT/'Meshes/Pond-sakura-native-bark.asset';m.write(bark);bark_guid=guid(bark);w.assets[bark_guid]=bark
    shader=OUT/'Shaders/OriginalBlossomCards.shader';shader.write_text((OUT/'Shaders/OriginalPaint.shader').read_text().replace('Sunward/Original Okami Paint','Sunward/Original Okami Blossom Cards').replace('Cull Back','Cull Off'));shader_guid=guid(shader)
    mat=OUT/'Materials/Pond-sakura-blossoms.mat';original_mat=OUT/'Materials/vtb1-5.mat';mat.write_text(original_mat.read_text().replace(guid(OUT/'Shaders/OriginalPaint.shader'),shader_guid));mat_guid=guid(mat);w.assets[mat_guid]=mat
    canopy=models['vtb1']['meshes'][1];models['pond-sakura']=dict(meshes=[dict(mesh=canopy['mesh'],material=mat_guid),dict(mesh=bark_guid,material=source['material'])])
    plan=json.loads((ROOT/'tools/playtest-repair/scene-repairs.json').read_text());placements=plan['placements'] if 'placements' in plan else next(v for k,v in plan.items() if isinstance(v,list) and v and isinstance(v[0],dict) and 'package' in v[0] and 'objects' in v[0])
    def place(package,p,height=None,size=None,yaw=0,parts=None,name=None):
        e=models[package];chosen=e['meshes'] if parts is None else [e['meshes'][i] for i in parts];points=np.concatenate([w.mesh(r['mesh'],4300000)['vertices'] for r in chosen]);lo=points.min(0);hi=points.max(0);extent=np.maximum(hi-lo,.001);scale=np.asarray(size)/extent if size else np.repeat(height/extent[1],3);theta=math.radians(yaw);rot=np.array([[math.cos(theta),0,math.sin(theta)],[0,1,0],[-math.sin(theta),0,math.cos(theta)]]);offset=np.array(p)-rot@(np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*scale);objects=[]
        for r in chosen:
            go=s.add('Original Okami · '+(name or package),r['mesh'],r['material'],p=offset,scale=scale);s.set(s.transform(go),'m_LocalRotation','{x: 0, y: %.9g, z: 0, w: %.9g}'%(math.sin(theta/2),math.cos(theta/2)));objects.append(go)
        ledger.append(dict(package=package,objects=objects,position=p,selectedSourceMeshes=parts,label=name));return objects
    # Rotate the actual shell toward the village square (south), not just its prompt.
    for r in placements:
        if r.get('label')!='training hall exterior':continue
        center=np.array([0,0,25]) if r['label']=='training hall exterior' else np.array([10,0,-15])
        for go in r['objects']:
            t=s.transform(go);p=vec(s.blocks[t],'m_LocalPosition');p=center+(p-center)*[-1,1,-1];s.set(t,'m_LocalPosition',fmt(p));s.set(t,'m_LocalRotation','{x: 0, y: 1, z: 0, w: 0}')
    # Remove every wall/roof component from the two mistaken pond buildings.
    for r in placements:
        if r.get('label')=='pond cherry blossom tree':
            for go in r['objects']:s.set(s.component(go,23),'m_Enabled',0)
    # VTB1 mesh 1 is solely blossom canopy, mesh 5 solely painted tree bark.
    # Their own original topology/UVs are kept; building divisions never render.
    for x,z in [(-18.8,-21),(-11.6,-23)]:place('pond-sakura',[x,terrain.height(x,z)-.16,z],height=6.6,name='pond sakura · native tree and blossoms without building')
    # A simple original house shell gives the pub an actual attached doorway;
    # the former dock building's irregular overhangs obscured its room footprint.
    old_food_roof=[]
    for r in placements:
        if r.get('label')=='food and music house exterior':
            for go in r['objects']:
                rid=s.component(go,23);s.set(rid,'m_Enabled',0);old_food_roof.append(rid)
    native_vta0=json.loads((RES/'vta0/Model.json').read_text())['parts'];body_parts=[i for i,part in enumerate(native_vta0) if int(part['name'].split('-')[1])==1]
    pub_shell=place('vta0',[10,.05,-15],size=[8.2,7.4,12],yaw=270,parts=body_parts,name='food house intact original shell')
    # Native paper doors visibly mark the two reachable entrances.
    doors={
        'dojo':place('vt62',[0,.5,15.0],size=[2.6,2.8,.08],yaw=180,name='training hall south door'),
        'food':[]}
    for id,b in list(s.blocks.items()):
        if 'Assembly-CSharp::Sunward.Remaster.VenueVisibility\n' not in b:continue
        venue=re.search(r'  venue: (\w+)',b)[1]
        if venue=='food':
            b=re.sub(r'  roof:\n.*?(?=  interiorSurfaces:)', '  roof:\n'+''.join('  - {fileID: '+str(s.component(go,23))+'}\n' for go in pub_shell),b,flags=re.S)
        extra=''.join('  - {fileID: '+str(s.component(go,23))+'}\n' for go in doors[venue]);s.blocks[id]=b.replace('  interiorSurfaces:',extra+'  interiorSurfaces:',1)
    # Replace the pub's east opening with a clear west doorway away from the enlarged northern house.
    for go,b in list(s.blocks.items()):
        if s.kind(go)==1 and s.name(go)=='Food house collision':
            c=s.component(go,65)
            if c:s.set(c,'m_Enabled',0)
    def box(p,size):
        part=models['vt08']['meshes'][0];go=s.add('Food house corrected collision',part['mesh'],part['material'],p=p);s.set(s.component(go,23),'m_Enabled',0);id=s.alloc();s.blocks[id]=f'''--- !u!65 &{id}
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Material: {{fileID: 0}}
  m_IsTrigger: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {fmt(size)}
  m_Center: {{x: 0, y: 1.55, z: 0}}
''';s.blocks[go]=s.blocks[go].replace('  m_Layer:','  - component: {fileID: '+str(id)+'}\n  m_Layer:',1);s.set(go,'m_Layer',6)
    for x,z,sx,sz in [(10,-18.65,8.8,.18),(10,-11.35,8.8,.18),(14.45,-15,.18,7.3),(5.55,-17.45,.18,2.4),(5.55,-12.55,.18,2.4)]:box([x,.65,z],[sx,3.1,sz])
    # Native activity controllers: varied diners, one musician, three dummy partners.
    diners=0;dummy_ids=[]
    for id,b in s.blocks.items():
        if 'Assembly-CSharp::Sunward.Remaster.TrainingDummy\n' in b:dummy_ids.append(id)
    trainee=0
    for id,b in list(s.blocks.items()):
        if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b:continue
        go=s.owner(id);name=s.name(go);package=None;idle=None;fields=None
        if 'training samurai' in name:
            package=['hm08','hm2d','hm44'][trainee];idle=['hm08_000','hm2d_000','hme5_000'][trainee];attack=['hm08_088','hm2d_080','hm44_080'][trainee]
            position=[[-3,.5,23.6],[3,.5,23.6],[0,1.25,27.4]][trainee];s.set(s.transform(go),'m_LocalPosition',fmt(position));s.set(go,'m_Name','Original native dummy partner '+package)
            fields='  role: training\n  motion: '+attack+'\n  dummy: {fileID: '+str(dummy_ids[trainee])+'}\n  seed: '+str(trainee*.9)+'\n';trainee+=1
        elif 'seated diner' in name:
            package=['hm00','hm01','hm09'][diners];idle={'hm00':'hm00_000','hm01':'hm01_000','hm09':'hm05_000'}[package]
            s.set(go,'m_Name','Original seated diner '+package);fields='  role: diner\n  seed: '+str(1.3+diners*1.9)+'\n';diners+=1
        elif 'music house lady' in name:
            package='hm05';idle='hm05_000';fields='  role: musician\n  seed: .4\n';s.set(go,'m_Name','Original music house performer')
        if not package:continue
        s.set(id,'resource','Okami/'+package)
        for key in ['idle','walk','run','windup','strike','recover','death']:s.set(id,key,idle)
        if '  holdIdlePose:' in s.blocks[id]:s.set(id,'holdIdlePose',0)
        else:s.blocks[id]+='  holdIdlePose: 0\n'
        scale,offset=previous.calibration(package,idle,1.8)
        if fields and '  role: training' not in fields:
            model=json.loads((RES/package/'Model.json').read_text());pose=previous.pose(package,'venue_seated');posed=previous.skin(model,pose);mask=model.get('visibleGroups');points=np.concatenate([v for part,v in zip(model['parts'],posed) if not mask or int(part['name'].split('-')[1]) in mask]);offset[1]=-points[:,1].min()*scale
        s.set(id,'modelScale',scale);s.set(id,'modelOffset',fmt(offset));add_component(s,go,'NativeVenueActor','  actor: {fileID: '+str(id)+'}\n'+fields)
    assert trainee==3 and diners==3
    s.save();Path(__file__).with_name('scene-changes.json').write_text(json.dumps(dict(base=BASE,placements=ledger,trainees=trainee,diners=diners,entrancesFaceVillage=True),indent=2)+'\n');print('Patched existing Windflower entrances, native sakura, varied diners and training partners')
if __name__=='__main__':run()
