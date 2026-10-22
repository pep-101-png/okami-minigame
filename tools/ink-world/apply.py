"""Offline authoring: connect ink-world artwork to the existing Windflower game.

Always starts from the reviewed PR13 scene. Never executed by the game/updater.
Original objects remain serialized; only superseded visual renderers are hidden.
No physics, gameplay, wolf, animations, tasks, syncing or packages are modified.
"""
from pathlib import Path
import sys, re, json, math, struct, subprocess, collections
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/village'))
import native
from native import Scene, Mesh, ASSETS, guid, vec, fmt
from build import Sources

BASE = 'ce07e12'
OUT = ASSETS/'Generated/InkWorld'
TEX = ASSETS/'Textures/InkWorld'
SCENE = ASSETS/'Scenes/Windflower.unity'
native.OUT = OUT


def float_property(s, key, value):
    pattern = r'(?m)^    - '+re.escape(key)+r': .*'
    s, n = re.subn(pattern, f'    - {key}: {value}', s)
    if not n:
        s = s.replace('    m_Floats:\n', f'    m_Floats:\n    - {key}: {value}\n')
    return s


def color_property(s, key, color):
    value = '{r: %g, g: %g, b: %g, a: 1}' % tuple(color)
    return re.sub(r'(?m)^    - '+re.escape(key)+r': .*', f'    - {key}: {value}', s)


def texture(s, slot, g):
    value = f'{{fileID: 2800000, guid: {g}, type: 3}}'
    return re.sub(r'(- '+re.escape(slot)+r':\n        m_Texture: )[^\n]+', lambda m:m[1]+value, s)


def paint_material(path, family, strength=.82, tint=None):
    info = json.loads((TEX/'painting-manifest.json').read_text())[family]
    s = path.read_text()
    for slot, channel in [('_DetailMap','color'),('_DetailNormal','normal')]:
        s = texture(s, slot, info['guids'][channel])
    for key, value in {'_ArtStrength':strength, '_ArtTiling':info['worldTiling'],
                       '_NormalStrength':.23, '_Pigment':.28,
                       '_SurfaceKind':{'Timber':1,'Cliff':2,'Meadow':3,'Path':3,
                                       'Plaster':6,'Roof':7,'RoofIndigo':7}[family]}.items():
        s = float_property(s,key,value)
    if family == 'Meadow':
        path_info = json.loads((TEX/'painting-manifest.json').read_text())['Path']
        for slot, channel in [('_PathMap','color'),('_PathNormal','normal')]:
            s = texture(s, slot, path_info['guids'][channel])
        s = float_property(s,'_TerrainBlend',1)
    if tint is not None:s = color_property(s,'_BaseColor',tint)
    path.write_text('\n'.join(x.rstrip() for x in s.splitlines())+'\n')


def material(name, family=None, strength=.8, tint=(1,1,1), wind=0):
    path = OUT/(name+'.mat')
    s = (ASSETS/'Generated/VillageFinish/House-cedar.mat').read_text()
    s = re.sub(r'm_Name: .*','m_Name: '+name,s,count=1)
    s = color_property(s,'_BaseColor',tint)
    for k,v in {'_Wind':wind, '_WindObjectSpace':1, '_TreeWind':0,
                '_ArtStrength':0, '_SurfaceKind':5 if wind else 0,
                '_Cull':0 if wind else 2}.items():s = float_property(s,k,v)
    path.write_text(s)
    if family:paint_material(path,family,strength,tint)
    return guid(path)


def bind_existing_materials():
    """All existing environment families, rather than a one-camera showcase."""
    known={guid(ASSETS/f'Textures/Art/Paint-{old}.png'):new for old,new in
           [('wood','Timber'),('stone','Cliff'),('plaster','Plaster'),
            ('roof','RoofIndigo'),('meadow','Meadow')]}
    # Permit deterministic re-authoring without silently skipping materials
    # that already point to the new paintings.
    for family,info in json.loads((TEX/'painting-manifest.json').read_text()).items():
        known[info['guids']['color']]=family
    count=0
    # Only existing environmental painting materials. Wolf's Lit materials and
    # original cloth/skin/effect palettes are deliberately not repainted.
    for path in (ASSETS/'Generated').glob('Paint-*.mat'):
        text=path.read_text()
        match=re.search(r'- _DetailMap:\n        m_Texture: .*guid: (\w+)',text)
        if not match or match[1] not in known:continue
        if '_ArtStrength: 0\n' in text:continue
        family=known[match[1]]
        paint_material(path,family,.78 if family!='Meadow' else .72)
        count+=1
    village=ASSETS/'Generated/VillageFinish'
    for name,family in [('House-cedar','Timber'),('House-plaster','Plaster'),
                        ('House-kawara','Roof'),('House-foundation','Cliff'),
                        ('Bridge-solid-timber','Timber'),('Bell-cedar','Timber')]:
        paint_material(village/(name+'.mat'),family,.83)
        count+=1
    # Existing floor/river-side/home detail materials retain their hues while
    # acquiring the same brush scale as the village architecture.
    for name,family in [('CraftTimber','Timber'),('HomeWeaponLacquer','Timber')]:
        path=ASSETS/'Generated'/(name+'.mat')
        if path.exists():paint_material(path,family,.58);count+=1
    return count


def mesh_guid(name):return guid(OUT/(name+'.asset'))


def rotate(scene, go, yaw):
    a=math.radians(yaw)/2
    scene.set(scene.transform(go),'m_LocalRotation','{x: 0, y: %g, z: 0, w: %g}'%(math.sin(a),math.cos(a)))


def add(scene,name,mesh,mat,p=(0,0,0),scale=(1,1,1),parent=0,yaw=0,shadow=True):
    obj=scene.add('Ink world · '+name,mesh_guid(mesh),mat,parent=parent,p=p,scale=scale)
    if yaw:rotate(scene,obj,yaw)
    renderer=scene.component(obj,23)
    scene.set(renderer,'m_CastShadows',1 if shadow else 0)
    scene.set(renderer,'m_ReceiveShadows',1 if shadow else 0)
    return obj


def replace_trees(scene,mats):
    count=0
    for go in list(scene.blocks):
        if scene.kind(go)!=1:continue
        name=scene.name(go)
        if not name.startswith('Living tree ') or 'bark and branching' not in name:continue
        index=int(re.search(r'Living tree (\d+)',name)[1])
        trunk=scene.component(go,33);p=vec(scene.blocks[scene.transform(go)],'m_LocalPosition')
        # Preserve all existing tree bases and gameplay trunk obstacles.
        if index in (0,2,6,8,9,14,15):kind='Ink-tree';leaf='olive';m=mats['inkwood']
        elif index%3==0:kind='Pine-'+str((index//3)%3);leaf='foliage';m=mats['wood']
        else:kind='Cherry-'+str(index%2);leaf='blossom';m=mats['wood']
        scene.set(trunk,'m_Mesh',f'{{fileID: 4300000, guid: {mesh_guid(kind+"-trunk")}, type: 2}}')
        r=scene.component(go,23)
        scene.blocks[r]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',
                              f'  m_Materials:\n  - {{fileID: 2100000, guid: {m}, type: 2}}\n',scene.blocks[r],flags=re.S)
        leaf_go=next(i for i in scene.blocks if scene.kind(i)==1 and scene.name(i).startswith('Living tree '+str(index)+' · cupped'))
        scene.set(scene.component(leaf_go,33),'m_Mesh',f'{{fileID: 4300000, guid: {mesh_guid(kind+"-"+leaf)}, type: 2}}')
        r=scene.component(leaf_go,23)
        scene.blocks[r]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',
                              f'  m_Materials:\n  - {{fileID: 2100000, guid: {mats["leaves"]}, type: 2}}\n',scene.blocks[r],flags=re.S)
        # Shared root-anchored wind keeps leaf/crown motion consistent. No
        # whole-trunk sway that could separate it from its ink silhouette.
        scene.set(r,'m_CastShadows',1)
        count+=1
    return count


def roof_details(scene,mats):
    count=0
    for go in list(scene.blocks):
        if scene.kind(go)!=1 or not scene.name(go).startswith('Village house '):continue
        if 'closed supported' not in scene.name(go):continue
        t=scene.transform(go);mf=scene.component(go,33)
        g=re.search(r'm_Mesh: .*guid: (\w+)',scene.blocks[mf])[1]
        path=next(p.with_suffix('') for p in (ASSETS/'Generated/VillageFinish').glob('*.asset.meta') if 'guid: '+g in p.read_text())
        raw=path.read_text();center=vec(raw,'m_Center');extent=vec(raw,'m_Extent')
        halfx,halfz=extent[0],extent[2];top=center[1]+extent[1]
        for part,mat in [('Ridge-crest-ceramic',mats['roof']),('Ridge-crest-sun',mats['gold'])]:
            add(scene,'roof sun crest '+str(count),part,mat,p=(0,top-.025,0),parent=t)
        for part,mat in [('Gable-timber',mats['wood']),('Gable-paper',mats['plaster']),('Gable-gold',mats['gold'])]:
            add(scene,'curved entrance fascia '+str(count),part,mat,p=(0,2.26,halfz-.16),parent=t)
        for side in [-1,1]:
            for x in [-halfx+.30,halfx-.30]:
                add(scene,'carved eave joinery '+str(count),'Carved-bracket',mats['wood'],p=(x,2.31,side*(halfz-.25)),parent=t)
        # Alternate original roof materials across the village, not random
        # per-pixel noise. Ammy's existing roof/cutaway stays structurally intact.
        if count%3==1:
            r=scene.component(go,23)
            scene.blocks[r]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mats["indigo"]}, type: 2}}\n',scene.blocks[r],flags=re.S)
        count+=1
    return count


def cliffs(scene,src,mats):
    # Existing simple boundary/triangular distant visuals remain in the scene
    # but are hidden; all physical world boundaries remain exactly as before.
    # Retire the old flat cloud/moon cards as well: the painted sky now supplies
    # continuous brush clouds/ridges/sun for every gameplay camera direction.
    for n in range(752,780):src.hide(n)
    placements=[]
    # Width six metres. Slightly overlapping formations make an unbroken wall;
    # generous margins place them outside the existing playable ground.
    for z,yaw in [(-51,0),(51,180)]:
        for x in range(-61,76,6):
            if -32<x<-14:continue # maintain the existing river's open ends
            placements.append((x,z,yaw))
    for x,yaw in [(-64,90),(74,-90)]:
        for z in range(-45,50,6):placements.append((x,z,yaw))
    for i,(x,z,yaw) in enumerate(placements):
        variant=2 if i%4 not in (1,3) else (i//2)%2
        height=1.30+.22*math.sin(i*1.7)
        for part,mat in [('stone',mats['cliff']),('moss',mats['moss'])]:
            add(scene,'layered boundary cliff '+str(i),'Cliff-'+str(variant)+'-'+part,mat,p=(x,-.7,z),scale=(1.10,height,1.65),yaw=yaw,shadow=part=='stone')
    return len(placements)


def roof_variants(scene,mats):
    for index in [0,3]:
        roof=next(i for i in scene.blocks if scene.kind(i)==1 and scene.name(i).startswith('Village house '+str(index)+' · closed'))
        t=scene.transform(roof)
        scene.set(scene.component(roof,33),'m_Mesh',f'{{fileID: 4300000, guid: {mesh_guid("Roof-House-"+str(index)+"-tiles")}, type: 2}}')
        for part,mat in [('wood',mats['wood']),('paper',mats['plaster'])]:
            add(scene,'high gable '+part+' '+str(index),'Roof-House-'+str(index)+'-'+part,mat,parent=t)
    for go in list(scene.blocks):
        if scene.kind(go)!=1:continue
        # Old small ridge crests now sit inside the taller roof/tower and would
        # poke through an upper window or gable. Keep their objects, hide visuals.
        if any(scene.name(go)=='Ink world · roof sun crest '+str(i) for i in [0,3,8]):
            scene.set(go,'m_IsActive',0)
    hall=next(i for i in scene.blocks if scene.kind(i)==1 and scene.name(i).startswith('Village house 8 · closed'))
    for part,mat in [('timber',mats['wood']),('plaster',mats['plaster']),('tiles',mats['roof'])]:
        add(scene,'hall belfry '+part,'Roof-Tower-'+part,mat,p=(0,3.85,0),parent=scene.transform(hall))


def scenery_details(scene,src,mats):
    # Replace existing five stone-lantern visual groups without moving their
    # established tiny footprint, illumination or physics proxies.
    count=0
    for n in [640,647,654,661,668]:
        ids=list(range(n,n+7));lo,hi=src.bounds(ids);p=(lo+hi)/2;x,z=p[0],p[2]
        for number in ids:src.hide(number)
        for part,mat in [('stone',mats['lanternstone']),('light',mats['gold'])]:
            add(scene,'open garden lantern '+str(count),'Stone-lantern-'+part,mat,p=(x,src.ground(x,z)-.02,z),shadow=part=='stone')
        count+=1
    # Existing sacred tree/garden compositions; no new interactions or obstacles.
    for i,(x,z,yaw) in enumerate([(-42,-20,20),(15,22,-30),(53,20,-45)]):
        for part,mat in [('timber',mats['wood']),('paper',mats['plaster']),('rope',mats['gold'])]:
            add(scene,'shimenawa garden '+str(i),'Prayer-stand-'+part,mat,p=(x,src.ground(x,z)-.015,z),yaw=yaw)
    # Existing laid approach stones retain their shapes/positions and acquire
    # the same painted weathered mineral surface as the other garden stonework.
    for go in list(scene.blocks):
        if scene.kind(go)!=1 or scene.name(go)!='Bridge approach flagstone':continue
        renderer=scene.component(go,23)
        if renderer:
            scene.blocks[renderer]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',
                f'  m_Materials:\n  - {{fileID: 2100000, guid: {mats["lanternstone"]}, type: 2}}\n',scene.blocks[renderer],flags=re.S)
    return count


def landmarks(scene,src,mats):
    # The old side rails are separate from each existing deck. Hide those
    # superseded visual objects, keeping the original solid decks/physics.
    for n in [796,797,798,799,801,802,803,804]:src.hide(n)
    for z in [-8,14]:
        for part,mat in [('vermilion',mats['red']),('ink',mats['ink']),('gold',mats['gold'])]:
            add(scene,'vermilion bridge at '+str(z),'Bridge-'+part,mat,p=(-23,.015,z))
    # Improve the existing working rice mill, rather than adding a second mill.
    # The established X-axis wheel, shaft, gears, millstones, spray, motion script
    # and collision all remain. Only the old wheel renderers are superseded.
    wheel=next(i for i in scene.blocks if scene.kind(i)==1 and scene.name(i)=='Bucket wheel · X axle')
    wheel_t=scene.transform(wheel)
    def is_below(t,parent):
        while t:
            if t==parent:return True
            m=re.search(r'm_Father: \{fileID: (-?\d+)\}',scene.blocks[t])
            t=int(m[1]) if m else 0
        return False
    for go in list(scene.blocks):
        if scene.kind(go)!=1:continue
        renderer=scene.component(go,23);t=scene.transform(go)
        if renderer and t and is_below(t,wheel_t):scene.set(renderer,'m_Enabled',0)
    for part,mat in [('wood',mats['wheelwood']),('iron',mats['ink'])]:
        # Native Blender wheel is local-Z; turn it onto the existing local-X
        # axle. Radius1.59m matches the established paddle envelope and water dip.
        add(scene,'millwheel '+part,'Mill-wheel-'+part,mat,parent=wheel_t,scale=(.76,.76,1),yaw=90)


def shell_mesh(path,cache):
    """Coincident positions share expansion normals: no split-face black spikes."""
    g=guid(path)
    if g in cache:return cache[g]
    raw=path.read_text();n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);data=bytearray.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',raw)[1]);stride=len(data)//n
    positions=np.array([struct.unpack_from('<3f',data,i*stride) for i in range(n)])
    normals=np.array([struct.unpack_from('<3f',data,i*stride+12) for i in range(n)])
    keys=np.round(positions*10000).astype(int);sums=collections.defaultdict(lambda:np.zeros(3))
    for key,normal in zip(keys,normals):sums[tuple(key)]+=normal
    for i,key in enumerate(keys):
        normal=sums[tuple(key)];norm=np.linalg.norm(normal)
        if norm<1e-7:normal=normals[i];norm=max(np.linalg.norm(normal),1e-7)
        struct.pack_into('<3f',data,i*stride+12,*(normal/norm))
    # Shell shader consumes positions/normals only. Strip unused colour/UV data
    # from the duplicate mesh to keep the committed outline assets small.
    compact=b''.join(data[i*stride:i*stride+24] for i in range(n))
    raw=re.sub(r'(?m)^    _typelessdata: .*','    _typelessdata: '+compact.hex(),raw)
    raw=re.sub(r'(?m)^    m_DataSize: .*','    m_DataSize: '+str(len(compact)),raw)
    channel_text=''
    for channel in range(14):
        offset=12 if channel==1 else 0
        dim=3 if channel<2 else 0
        channel_text+=f'    - stream: 0\n      offset: {offset}\n      format: 0\n      dimension: {dim}\n'
    raw=re.sub(r'    m_Channels:\n.*?(?=    m_DataSize:)', '    m_Channels:\n'+channel_text,raw,flags=re.S)
    # Small source river stones have a preserved minimum scale of .153. A .40m
    # local margin covers the .055m world clamp even at that smallest scale.
    raw=re.sub(r'm_Extent: \{[^}]+\}',lambda m:'m_Extent: '+fmt(vec(m[0],'m_Extent')+.40),raw)
    name='Contour-'+path.stem;raw=re.sub(r'm_Name: .*','m_Name: '+name,raw,count=1)
    out=OUT/(name+'.asset');out.write_text(raw);cache[g]=guid(out);return cache[g]


def contours(scene,mat):
    cache={};count=0
    paths={guid(p):p for p in (ASSETS/'Generated').rglob('*.asset') if p.stat().st_size<10_000_000 and 'Contour-' not in p.name}
    for go in list(scene.blocks):
        if scene.kind(go)!=1 or '  m_IsActive: 0\n' in scene.blocks[go]:continue
        name=scene.name(go)
        selected=(name.startswith('Grounded stone ') or
                  (name.startswith('Living tree ') and 'bark' in name) or
                  (name.startswith('Village house ') and ('joined cedar' in name or 'closed supported' in name)) or
                  (name.startswith('Ink world · ') and any(v in name for v in ['cliff','garden lantern','roof sun crest','entrance fascia','millwheel','bridge','high gable','hall belfry'])))
        if not selected:continue
        # Thin gold/inset papers/crowns have internal painted edges rather than
        # closed-hull outlines. Decorative wheel rotation needs matching motion.
        mf=scene.component(go,33);renderer=scene.component(go,23)
        if not mf or not renderer:continue
        if '  m_Enabled: 0\n' in scene.blocks[renderer]:continue
        g=re.search(r'm_Mesh: .*guid: (\w+)',scene.blocks[mf])[1]
        if g not in paths:continue
        path=paths[g]
        if any(v in path.stem for v in ['moss','gold','sun','paper','light','iron','ink']):continue
        shell=shell_mesh(path,cache)
        obj=scene.add('Ink contour · '+name,shell,mat,parent=scene.transform(go))
        r=scene.component(obj,23);scene.set(r,'m_CastShadows',0);scene.set(r,'m_ReceiveShadows',0)
        for field in ['m_LightProbeUsage','m_ReflectionProbeUsage','m_MotionVectors']:
            if field+':' in scene.blocks[r]:scene.set(r,field,0)
        count+=1
    return count,len(cache)


def main():
    OUT.mkdir(exist_ok=True)
    base=subprocess.check_output(['git','show',BASE+':'+str(SCENE.relative_to(ROOT))],cwd=ROOT,text=True)
    scene=Scene(SCENE,text=base);src=Sources(scene)
    material_count=bind_existing_materials()
    river=ASSETS/'Generated/Paint-159.mat'
    river.write_text(color_property(river.read_text(),'_BaseColor',(.13,.40,.36)))
    mats={
        'wood':material('Ink-painted-timber','Timber',.66),
        'wheelwood':material('Ink-wheel-timber','Timber',.66),
        'inkwood':material('Ink-umber-trunk','Timber',.16,tint=(.48,.40,.30)),
        'leaves':material('Ink-living-foliage',wind=.22),
        'moss':material('Ink-cliff-moss',wind=0),
        'cliff':material('Ink-ochre-cliff','Cliff',.88),
        'lanternstone':material('Ink-garden-stone','Cliff',.62,tint=(.78,.81,.72)),
        'plaster':material('Ink-painted-plaster','Plaster',.78),
        'roof':material('Ink-ceramic-crest','Roof',.72),
        'indigo':material('Ink-indigo-roof','RoofIndigo',.87),
        'gold':material('Ink-antique-gold',tint=(.90,.65,.22)),
        'red':material('Ink-vermilion-lacquer','Timber',.05,tint=(1,.72,.48)),
        'ink':material('Ink-iron-and-endcaps',tint=(.19,.16,.12))}
    wheel_material=OUT/'Ink-wheel-timber.mat'
    wheel_material.write_text(float_property(wheel_material.read_text(),'_PaintObjectSpace',1))
    trees=replace_trees(scene,mats);houses=roof_details(scene,mats);roof_variants(scene,mats)
    cliff_count=cliffs(scene,src,mats);lanterns=scenery_details(scene,src,mats)
    landmarks(scene,src,mats)
    # Material for explicit opaque silhouette shells, not a camera filter.
    contour=material('Ink-contour')
    p=OUT/'Ink-contour.mat';s=p.read_text();s=re.sub(r'm_Shader: .*',f'm_Shader: {{fileID: 4800000, guid: {guid(ASSETS/"Shaders/InkContour.shader")}, type: 3}}',s,count=1);p.write_text(s)
    outline_count,outline_meshes=contours(scene,contour)
    # Warm paper atmosphere; strong sun still supports readable wolf silhouettes.
    scene.set(2,'m_FogColor','{r: 0.76, g: 0.68, b: 0.51, a: 1}')
    scene.set(2,'m_FogDensity',.0065)
    scene.set(2,'m_AmbientSkyColor','{r: 0.69, g: 0.71, b: 0.67, a: 1}')
    scene.set(2,'m_AmbientEquatorColor','{r: 0.65, g: 0.59, b: 0.43, a: 1}')
    scene.set(2,'m_AmbientGroundColor','{r: 0.29, g: 0.31, b: 0.24, a: 1}')
    scene.save()
    # Rerunning offline authoring must not leave obsolete duplicate shell meshes
    # behind when the selected tree/cliff variant changes.
    used=set(re.findall(r'guid: ([0-9a-f]{32})',SCENE.read_text()))
    for p in list(OUT.glob('Contour-*.asset'))+list(OUT.glob('Mill-support-*.asset')):
        if guid(p) not in used:
            p.unlink();Path(str(p)+'.meta').unlink()
    report={'baseCommit':BASE,'unityRendered':False,'environmentMaterialsRepainted':material_count,'existingTreeBasesImproved':trees,
            'villageHousesWithRoofDetails':houses,'cliffSections':cliff_count,'existingLanternLocationsImproved':lanterns,
            'highGabledRoofs':2,'tieredHallBelfries':1,
            'redBridges':2,'millwheels':1,'outlineRenderers':outline_count,'sharedOutlineMeshes':outline_meshes,
            'originalObjectsPreserved':all(i in scene.blocks for i in Scene(SCENE,text=base).blocks),
            'collisionChanges':0,'wolfAppearanceChanges':0}
    (ROOT/'tools/ink-world/scene-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
