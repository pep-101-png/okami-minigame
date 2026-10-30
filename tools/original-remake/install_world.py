"""Author the existing Windflower scene and gameplay prefabs from original assets.

Reproducible against the pre-remake repair commit. No Unity editor startup task,
new scene, controller replacement, progression change or save migration.
"""
from pathlib import Path
import collections,hashlib,json,math,re,subprocess,sys
import numpy as np
from export_assets import A,ROOT,OUT,RES,guid
sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref,Terrain
sys.path.insert(0,str(ROOT/'tools/village'));from native import Scene,Mesh,vec,fmt
BASE='ee9af00b74c8157bfc93a150068b31e23d3c331f'
REPORT={};MODELS={e['package']:e for e in json.loads(Path(__file__).with_name('original-assets.json').read_text())['models']}

def patch(scene,instance,target,key,value=None,reference=None):
    raw=scene.blocks[instance];sourceguid=ref(raw,'m_SourcePrefab')[1]
    pattern=r'    - target: \{fileID: '+str(target)+r',[^\n]+\}\n      propertyPath: [\x27]?'+re.escape(key)+r'[\x27]?\n      value:[ \t]*[^\n]*\n      objectReference: [^\n]*\n'
    record=f'    - target: {{fileID: {target}, guid: {sourceguid}, type: 3}}\n      propertyPath: {key}\n      value: {value if value is not None else ""}\n      objectReference: {reference or "{fileID: 0}"}\n'
    if re.search(pattern,raw):raw=re.sub(pattern,record,raw)
    else:raw=raw.replace('    m_RemovedComponents:',record+'    m_RemovedComponents:',1)
    scene.blocks[instance]=raw

def add_component(scene,go,classname,fields):
    id=scene.alloc();script=guid(OUT/'Scripts'/(classname+'.cs'))
    scene.blocks[id]=f'''--- !u!114 &{id}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: Assembly-CSharp::Sunward.Remaster.{classname}
'''+fields
    assert 'stripped\n' not in scene.blocks[go], 'Use source prefab for inherited components'
    scene.blocks[go]=scene.blocks[go].replace('  m_Layer:',f'  - component: {{fileID: {id}}}\n  m_Layer:',1)
    return id

def root_go(scene):
    return next(i for i in scene.blocks if scene.kind(i)==1 and scene.transform(i) and ref(scene.blocks[scene.transform(i)],'m_Father')[0]==0)

def write_prefab(scene):scene.path.write_text(scene.header+''.join(scene.blocks.values()))

def actor_fields(package,height,external_scale=1,resource=None):
    e=MODELS[package];lo=np.asarray(e['boundsMin']);hi=np.asarray(e['boundsMax']);scale=height/max(.01,hi[1]-lo[1])/external_scale
    center=(lo+hi)/2;offset=np.array([-center[0],-lo[1],-center[2]])*scale
    names=[m['name'] for m in e['motions']]
    def clip(suffix,fallback='000'):return next((n for n in names if n.endswith('_'+suffix)),next((n for n in names if n.endswith('_'+fallback)),e['idle']))
    bindings=dict(idle=clip('000'),walk=clip('010'),run=clip('012'),windup=clip('020'),strike=clip('130','021'),recover=clip('030'),death=clip('040'))
    if e['group']=='EM':
        attack=clip('130','020');bindings.update(windup=attack,strike=attack,recover=attack)
        if not any(n.endswith('_040') for n in names):bindings['death']=clip('030')
    fields='  resource: '+(resource or 'Okami/'+package)+'\n'+''.join('  '+k+': '+v+'\n' for k,v in bindings.items())+'  modelOffset: '+fmt(offset)+'\n  modelScale: '+str(scale)+'\n  game: {fileID: 0}\n'
    if e['group']=='EM':fields+='  splitAttackClip: 1\n'
    return fields,dict(package=package,resource=resource or 'Okami/'+package,modelScale=scale,modelOffset=offset.tolist(),bindings=bindings)

def install():
    scene_path=A/'Sunward/Scenes/Windflower.unity'
    source=subprocess.check_output(['git','show',BASE+':Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'],cwd=ROOT,text=True)
    scene_path.write_text(source)
    w=World();scene=w.scene;rows=list(w.renderers());terrain=Terrain(w,rows);REPORT['beforeVisibleRendererCount']=len(rows)
    colliders={i:b for i,b in scene.blocks.items() if scene.kind(i) in [65,64,135,136,143,154]}
    game_data=(A/'Sunward/Data/Valley.json').read_bytes()
    anchors=[];actors=[]

    def point(r):
        if r['lo'] is None:return np.asarray(r['matrix'][:3,3])
        return (r['lo']+r['hi'])/2
    def disable(r):
        if r['instance']:patch(scene,r['instance'],r['renderer'],'m_Enabled',0)
        else:scene.set(r['renderer'],'m_Enabled',0)
    # Preserve layout surfaces and their collision heights, repaint with directly
    # identified original DDS. All old object artwork is replaced or removed.
    surfaces=[]
    for r in rows:
        keep=False
        for g in r['materials']:
            p=w.assets.get(g)
            if p and p.suffix=='.mat':
                text=p.read_text()
                keep|=p.name=='Continuous-Ground.mat' or '_FlowMap:' in text or p.name=='Recovered-Pond.mat'
        if r['lo'] is not None:
            keep|=r['hi'][0]-r['lo'][0]>120 and r['hi'][1]<2
            keep|=r['lo'][0]>17 and r['hi'][0]<54 and r['hi'][1]<.25 and r['hi'][0]-r['lo'][0]>20
            keep|=r['lo'][0]>-40 and r['hi'][0]<-28 and r['lo'][2]>-21 and r['hi'][2]<-11 and r['hi'][1]<.14 and r['hi'][0]-r['lo'][0]>6
        if keep:surfaces.append(r)
        else:disable(r)
    retired_particles=[]
    for id in list(scene.blocks):
        if scene.kind(id) in [96,120,199]:
            scene.set(id,'m_Enabled',0);retired_particles.append(id)
    REPORT['retiredNonOriginalParticleRenderers']=retired_particles
    REPORT['retainedLayoutSurfaceRenderers']=[dict(name=r['name'],renderer=r['renderer'],instance=r['instance']) for r in surfaces]

    def place(package,position,size=None,parent=0,yaw=0,height=None,category='prop',scale=None):
        e=MODELS[package];lo=np.asarray(e['boundsMin']);hi=np.asarray(e['boundsMax']);extent=np.maximum(hi-lo,.001);center=(lo+hi)/2
        if scale is None:
            if size is not None:scale=np.asarray(size)/extent
            else:scale=np.ones(3)*(height/extent[1] if height else 1)
        scale=np.broadcast_to(scale,(3,)).copy();rad=math.radians(yaw);rot=np.array([[math.cos(rad),0,math.sin(rad)],[0,1,0],[-math.sin(rad),0,math.cos(rad)]])
        offset=np.asarray(position)-rot@(np.array([center[0],lo[1],center[2]])*scale)
        objects=[]
        for part in e['meshes']:
            go=scene.add('Original Okami · '+category+' · '+package,part['mesh'],part['material'],parent=parent,p=offset,scale=scale)
            t=scene.transform(go);scene.set(t,'m_LocalRotation','{x: 0, y: %.8g, z: 0, w: %.8g}'%(math.sin(rad/2),math.cos(rad/2)));objects.append(go)
        anchors.append(dict(category=category,package=package,position=np.asarray(position).tolist(),scale=scale.tolist(),yaw=yaw,parent=parent,objects=objects,sourceSHA256=e['sourceSHA256']))
        return objects
    def ground(p):return terrain.height(p[0],p[2])
    def roots(match):return [(i,scene.name(i)) for i in list(scene.blocks) if scene.kind(i)==1 and match(scene.name(i))]

    # The same 14 village house roots, centres, rotations and physical footprints.
    data=json.loads(game_data)['world'];choices=['vta3','vta0','vtb2','vta1','vta2','vtb0','vtb4','vta9','vta8','vtae','vta3','vtb2','vta0','vtb4']
    houses=[]
    for go,name in roots(lambda n:re.match(r'Village house \d+ .*joined cedar',n)):
        number=int(re.search(r'house (\d+)',name)[1]);t=scene.transform(go);pos=vec(scene.blocks[t],'m_LocalPosition');box=min(data['boxes'][:19],key=lambda b:(b['x']-pos[0])**2+(-b['z']-pos[2])**2)
        q=re.search(r'm_LocalRotation: \{x: [^,]+, y: ([^,]+), z: [^,]+, w: ([^}]+)',scene.blocks[t]);yaw=2*math.atan2(float(q[1]),float(q[2]));width,depth=box['halfX']*2,box['halfZ']*2
        if abs(math.sin(yaw))>.7:width,depth=depth,width
        package=choices[number];size=np.asarray(MODELS[package]['boundsMax'])-MODELS[package]['boundsMin'];uniform=min(width/size[0],depth/size[2]);scale=np.array([uniform,uniform,uniform]);scale[1]=min(scale[1],6.8/size[1])
        added=place(package,[0,.025,0],parent=t,scale=scale,category='village house '+str(number));houses.append(dict(number=number,root=go,package=package,oldPosition=pos.tolist(),colliderBox=box,objects=added))
    assert len(houses)==14;REPORT['houses']=houses

    # Existing main home: original house exterior, original futon and furnishings.
    home=place('vtb2',[-34,.025,-16],size=[10.0,4.8,7.9],yaw=180,category='playable home exterior')
    for id,b in list(scene.blocks.items()):
        if 'Assembly-CSharp::Sunward.HomeCutaway\n' in b:
            scene.blocks[id]=re.sub(r'  roof:\n.*', '  roof:\n'+''.join('  - {fileID: '+str(scene.component(go,23))+'}\n' for go in home),b,flags=re.S)
    place('vt64',[-36.1,.11,-14.8],size=[2.5,.13,1.35],category='sleep interaction futon')
    place('et19',[-30.5,.3,-14.2],height=1.4,yaw=90,category='memory mirror appearance')
    place('vt7c',[-29.65,.11,-17.8],size=[2.6,1.8,.6],yaw=90,category='collectible shelf')
    place('vt65',[-34.8,.12,-13.0],height=.3,category='tea set')
    place('vt60',[-37.8,.12,-18.3],height=.65,category='home lantern')
    displays=next(go for go,n in roots(lambda n:n=='Home · separate wall-mounted weapon displays'))
    display_parent=scene.transform(displays)
    place('wp24',[-37.8,1.0,-18.9],height=1.15,parent=display_parent,category='home Solar Flare display')
    place('wp25',[-35.8,.6,-18.9],height=1.7,parent=display_parent,category='home native glaive display')

    # Original stalls occupy the established Taro/Hana market footprints.
    for package,x in [('vtab',4.8),('vtb5',-4.8)]:
        place(package,[x,terrain.height(x,0),0],size=[2.4,2.25,1.4],yaw=180 if x>0 else 0,category='working market')
    for id,p in [('garden',[-3,0,-7]),('mill',[-15,0,13]),('shrine',[2,0,12])]:
        p[1]=ground(p);added=place('vt47',p,height=.7,category='quest flower '+id)
        for j,go in enumerate(added):scene.set(go,'m_Name','OriginalQuestFlower-'+id+'-'+str(j))

    # Source trees and bamboo at the established tree/bamboo roots.
    trees=roots(lambda n:bool(re.match(r'Living tree \d+ .*bark',n)))
    for k,(go,n) in enumerate(trees):
        t=scene.transform(go);p=vec(scene.blocks[t],'m_LocalPosition');package=['vte4','vte3','vte5','vt17'][k%4]
        part=MODELS[package]['meshes'][0];anchor=scene.add('Original Okami · tree painting anchor',part['mesh'],part['material'],parent=t);scene.set(scene.component(anchor,23),'m_Enabled',0);add_component(scene,anchor,'OriginalBillboard','')
        place(package,[0,0,0],parent=scene.transform(anchor),height=4.5+(k%4)*.5,category='living tree')
    for go,n in roots(lambda n:n.startswith('Living bamboo ·')):
        part=MODELS['vt19']['meshes'][0];anchor=scene.add('Original Okami · bamboo painting anchor',part['mesh'],part['material'],parent=scene.transform(go));scene.set(scene.component(anchor,23),'m_Enabled',0);add_component(scene,anchor,'OriginalBillboard','')
        place('vt19',[0,0,0],parent=scene.transform(anchor),height=4.4,category='bamboo')

    # Replace decorative landscape groups using their saved world-space bounds.
    seen=set()
    for r in rows:
        name=r['name'];package=None;category=None;height=None
        if name.startswith('Folded meadow blades'):package=['vt3e','vt3f','vte6'][r['renderer']%3];category='grass';height=.28
        elif name=='Native Windflower · decorative flower Petals':package=['vt29','vt46','vt47'][r['renderer']%3];category='flowers';height=.25
        elif name=='Painted wildflower verge':package='vt48';category='roadside flowers';height=.38
        elif name.startswith('Ink world · layered boundary cliff'):package='vt28';category='boundary rock'
        elif name.startswith('Native Windflower · original ST2 rock ') and ' ink ' not in name:package='vt2a';category='rock'
        elif any(t in name.lower() for t in ['grounded stone','native windflower · recovered rock','ink world · boulder']):package='vt2a';category='rock'
        elif name.startswith('Arena · full cedar log'):package='vt00';category='arena boundary'
        elif name=='Bridge approach flagstone':package='vt28';category='bridge approach stone'
        if not package or r['lo'] is None:continue
        # vt00 is not needed for any other placement; source original trunk.
        if package not in MODELS:package='vt08'
        p=point(r);key=(category,name) if category=='boundary rock' else (category,round(float(p[0]),2),round(float(p[2]),2))
        if key in seen:continue
        seen.add(key);p[1]=ground(p)-.015
        if category=='boundary rock':size=np.maximum(r['hi']-r['lo'],[1,1,1]);place(package,p,size=size,category=category)
        elif category=='rock':place(package,p,size=np.maximum(r['hi']-r['lo'],[.2,.2,.2]),category=category)
        elif category=='arena boundary':place(package,p,height=.6,category=category)
        elif category=='bridge approach stone':place(package,p,size=np.maximum(r['hi']-r['lo'],[.4,.08,.4]),category=category)
        else:place(package,p,height=height or max(.4,min(3,float(r['hi'][1]-r['lo'][1]))),category=category)

    for go,n in roots(lambda n:n.startswith('Kasuga lantern ·') or n.startswith('Arena perimeter lantern ·') or n.startswith('Bridge approach · clear')):
        t=scene.transform(go);place('vt35',[0,0,0],parent=t,height=1.35,category='stone lantern')
    for go,n in roots(lambda n:n.startswith('River-driven rice mill ·')):
        t=scene.transform(go);p=vec(scene.blocks[t],'m_LocalPosition');part=MODELS['vt6a']['meshes'][0]
        anchor=scene.add('Original Okami · native animated waterwheel',part['mesh'],part['material'],parent=t,p=[0,terrain.height(p[0],p[2])-p[1],0]);scene.set(scene.component(anchor,23),'m_Enabled',0)
        fields,record=actor_fields('vt6a',3.6);add_component(scene,anchor,'OriginalActor',fields)
        REPORT['waterwheel']=dict(root=anchor,**record)
    for go,n in roots(lambda n:n.startswith('Hollow Bell entrance · joined')):
        place('stage-torii',[0,0,0],parent=scene.transform(go),size=[4.032,3.01,.537],category='trial bell gate')
    place('vt4a',[12.8,terrain.height(12.8,0),0],height=1.8,category='trial bell gong')
    # GT18 contains native restoration states. Use the complete second mesh
    # group and fit its deck to the preserved physical arch, rather than drawing
    # both states or leaving Amaterasu's feet below the new visible planks.
    bridge=MODELS['gt18'];native_parts=json.loads((RES/'gt18/Model.json').read_text())['parts']
    selected=[i for i,p in enumerate(native_parts) if p['name'].startswith('Native-1-')]
    assert selected and len(native_parts)==len(bridge['meshes'])
    deck=next(i for i in selected if native_parts[i]['texture']==1)
    deck_vertices=w.mesh(bridge['meshes'][deck]['mesh'],4300000)['vertices'];xs=np.unique(deck_vertices[:,0]);ys=np.array([deck_vertices[np.isclose(deck_vertices[:,0],x,atol=.0001),1].max() for x in xs])
    allpoints=np.concatenate([w.mesh(bridge['meshes'][i]['mesh'],4300000)['vertices'] for i in selected]);lo=allpoints.min(0);hi=allpoints.max(0);sx=9.6/(hi[0]-lo[0]);sz=2.52/(hi[2]-lo[2]);newparts=[];deck_error=[]
    for i in selected:
        part=bridge['meshes'][i];data=w.mesh(part['mesh'],4300000);v=data['vertices'].copy();u=np.clip((v[:,0]-lo[0])/(hi[0]-lo[0]),0,1);height=.1+.42*np.maximum(0,np.sin(np.pi*u))**1.5
        v[:,1]=(v[:,1]-np.interp(v[:,0],xs,ys))*sx+height;v[:,0]=-4.8+u*9.6;v[:,2]=(v[:,2]-(lo[2]+hi[2])/2)*sz
        buf=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',data['raw'])[1]);streams=np.frombuffer(buf,'<f4').reshape(len(v),data['stride']//4)
        m=Mesh();m.v=v.tolist();m.c=streams[:,6:9].tolist();m.uv=streams[:,10:12].tolist();m.bones=[0]*len(v);m.tri=data['triangles'].tolist();target=OUT/'Meshes'/('gt18-walk-deck-'+str(i)+'.asset');m.write(target);newparts.append(dict(mesh=guid(target),material=part['material']))
        if i==deck:deck_error=(v[:,1]-height).tolist()
    for z in [-8,14]:
        added=[scene.add('Original Okami · fitted GT18 bridge',p['mesh'],p['material'],p=[-23,0,z]) for p in newparts]
        anchors.append(dict(category='river bridge',package='gt18',position=[-23,0,z],scale=[1,1,1],yaw=0,parent=0,objects=added,sourceSHA256=bridge['sourceSHA256']))
    REPORT['bridgeAdaptation']=dict(source='gt18',nativeMeshGroup=1,deckMotion='Existing collision arch preserved; original native bridge vertices fitted to it.',maximumDeckVertexHeightDifference=max(abs(x) for x in deck_error))
    for k,p in enumerate([[-46,0,8],[-34,0,29],[-38,0,3]]):
        p[1]=ground(p);place('vt05',p,height=1.8,category='well')
    p=[0,0,20];p[1]=ground(p);place('et0d',p,size=[2.4,2.2,1.8],category='offering shrine')
    for j,p in enumerate([[-42,0,18],[-45,0,16],[-40,0,20],[-43,0,22]]):
        p[1]=ground(p);place(['it24','it26','it27','it28'][j],p,height=.35,category='farm produce')

    # Source prefabs preserve NPC identity, dialogue, rigidbodies and routes.
    npc_models=['hm01','hm29','hm44','hm00','hm05','hm68','hm0f']
    for k,package in enumerate(npc_models):
        path=A/'Sunward/Generated'/('NPC-'+str(k)+'.prefab');prefab=Scene(path,text=subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True))
        for id,b in list(prefab.blocks.items()):
            if prefab.kind(id) in [23,137]:prefab.set(id,'m_Enabled',0)
        fields,record=actor_fields(package,1.8);add_component(prefab,root_go(prefab),'OriginalActor',fields);write_prefab(prefab)
    index_by_owner={scene.owner(i):int(re.search(r'  index: (\d+)',b)[1]) for i,b in scene.blocks.items() if 'Assembly-CSharp::Sunward.VillageResident\n' in b}
    for id,b in list(scene.blocks.items()):
        if 'Assembly-CSharp::Sunward.ResidentLocomotion\n' not in b:continue
        go=scene.owner(id);scene.set(id,'m_Enabled',0)
        if go in index_by_owner:
            index=index_by_owner[go];package=npc_models[index];fields,record=actor_fields(package,1.8)
            instance=ref(scene.blocks[go],'m_PrefabInstance')[0];sourcego=ref(scene.blocks[go],'m_CorrespondingSourceObject')[0]
            matrix=w.matrix(instance,w.prefabs[instance].transform(sourcego))
        else:
            package=['hm2d','hm09','hm29','hm00','hm05','hm2d'][len(actors)%6];fields,record=actor_fields(package,1.8);add_component(scene,go,'OriginalActor',fields);matrix=w.matrix(0,scene.transform(go))
        actors.append(dict(root=go,matrix=matrix.tolist(),**record))
    assert len(actors)==13;REPORT['humanActors']=actors

    enemies=[]
    for role,package,height in [('wisp','em00',1.5),('reed','em01',1.6),('ranged','em02',1.7),('heavy','em03',2),('elite','em04',1.85),('boss','em11',3.6)]:
        definition=A/'Sunward/Generated'/('Spirit-'+role+'.asset');scale=float(re.search(r'^  scale: ([^\n]+)',definition.read_text(),re.M)[1]);path=A/'Sunward/Generated'/('Enemy-'+role+'.prefab')
        prefab=Scene(path,text=subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True))
        for id in list(prefab.blocks):
            if prefab.kind(id) in [23,137]:prefab.set(id,'m_Enabled',0)
        fields,record=actor_fields(package,height,scale);add_component(prefab,root_go(prefab),'OriginalActor',fields);write_prefab(prefab);enemies.append(dict(role=role,**record))
    REPORT['enemyVisuals']=enemies

    # The existing second weapon also gets original geometry and native motion.
    path=A/'Sunward/Generated/Spear.prefab';prefab=Scene(path,text=subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True))
    for id in list(prefab.blocks):
        if prefab.kind(id) in [23,137]:prefab.set(id,'m_Enabled',0)
    fields,record=actor_fields('wp25',1);fields=re.sub(r'  modelOffset: .*','  modelOffset: {x: 0, y: 0, z: 0}',fields);fields=re.sub(r'  modelScale: .*','  modelScale: 1',fields);record['modelScale']=1;record['modelOffset']=[0,0,0];add_component(prefab,root_go(prefab),'OriginalActor',fields);write_prefab(prefab)
    REPORT['secondWeapon']=record

    # Stop all serialized non-original ambience/music. Native voice clips are
    # loaded explicitly by ValleyAudio; missing authentic banks stay silent.
    muted=0
    for id,b in list(scene.blocks.items()):
        if scene.kind(id)==82:
            scene.blocks[id]=re.sub(r'(m_[Aa]udioClip: )[^\n]+',r'\g<1>{fileID: 0}',b);scene.set(id,'m_PlayOnAwake',0);muted+=1
    REPORT['removedNonOriginalAudioSources']=muted
    for id,b in colliders.items():assert scene.blocks[id]==b,('Gameplay collider changed',id)
    assert (A/'Sunward/Data/Valley.json').read_bytes()==game_data
    scene.save();REPORT.update(baseCommit=BASE,modifiedScene=str(scene_path.relative_to(A)),nativePlacements=anchors,unchangedColliderBlocks=len(colliders),worldDataUnchanged=True,UnityCompilationVerified=False,UnityPlaybackVerified=False,completeSolarEffects=False)
    Path(__file__).with_name('world-install.json').write_text(json.dumps(REPORT,indent=2));print(json.dumps({k:v for k,v in REPORT.items() if k not in ['nativePlacements','humanActors','enemyVisuals','houses']},indent=2))
    for file in [OUT,*sorted(OUT.rglob('*'))]:
        if not file.name.endswith('.meta'):guid(file)

if __name__=='__main__':install()
