"""Independent repair gates. No successful Unity run or compile is implied."""
import json,re,subprocess,hashlib,sys,collections,math,shutil
from pathlib import Path
import numpy as np
from tree_sitter import Parser,Language
import tree_sitter_c_sharp
from scene_data import A,ROOT,World,Scene,Terrain,ref,vec
from placements import water,road,intersects,circle_box
from farm_data import read as animals
BASE='be9f4a045125750e187b6b58e49c65d3ba92cb80';w=World();s=w.scene;rows=list(w.renderers());terrain=Terrain(w,rows)
def old(path):return subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT)
baseline=Scene(s.path,text=old(s.path).decode());assert set(baseline.blocks)<=set(s.blocks)
for i,b in baseline.blocks.items():
    if baseline.kind(i) in [114,95,143,20]:assert s.blocks[i]==b,('Changed functional scene component',i)
parser=Parser(Language(tree_sitter_c_sharp.language()))
for path in A.rglob('*.cs'):assert not parser.parse(path.read_bytes()).root_node.has_error,path
def methods(data):
    out={}
    def visit(n):
        if n.type=='method_declaration':out[n.child_by_field_name('name').text.decode()]=n.text
        for c in n.children:visit(c)
    visit(parser.parse(data).root_node);return out
p=A/'Sunward/Scripts/WolfCombat.cs';a=methods(old(p));b=methods(p.read_bytes())
for name in ['Equip','Rest','Cancel','Begin','Update','Hit']:assert a[name]==b[name],('Changed combat mechanics',name)
p=A/'Sunward/Scripts/WolfMotor.cs';new=p.read_text().replace('        public const float Gravity = 21f;\n','').replace('Vertical -= Gravity * dt;','Vertical -= 21 * dt;');assert new==old(p).decode(),'Changed motor physics beyond naming the same gravity constant'
protected=['GameFlow.cs','WolfInput.cs','AttackSequence.cs','SaveStore.cs','ProgressionData.cs','HomeRest.cs','VillageNavigation.cs','Valley.cs','EnemyBrain.cs','VillageResident.cs','ResidentLocomotion.cs','HomeCutaway.cs']
for name in protected:
    p=A/'Sunward/Scripts'/name;assert p.read_bytes()==old(p),name
data=json.loads((A/'Sunward/Data/Valley.json').read_text());before=json.loads(old(A/'Sunward/Data/Valley.json'))
assert data['assets']==before['assets'] and data['materials']==before['materials']
for key in set(before['world'])-{'obstacles'}:assert data['world'][key]==before['world'][key],key
assert len(list(A.rglob('*.unity')))==1
for p in A.rglob('*.meta'):
    text=p.read_text();assert len(re.findall(r'^guid: (\w+)',text,re.M))==1,p
assert len(w.assets)==sum(1 for _ in A.rglob('*.meta')),'Duplicate asset GUID'
for i,b in s.blocks.items():
    for g in re.findall(r'guid: ([a-f0-9]{32})',b):
        if g.startswith('0000000000000000'):continue
        # Package/built-in references may predate this repair.
        assert g in w.assets or g in baseline.blocks.get(i,''),(i,g)
colliders=[]
for r in rows:
    if not re.match(r'Native Windflower · original ST2 rock \d+$',r['name']):continue
    mc=s.component(r['go'],64);assert mc and '  m_Convex: 1\n' in s.blocks[mc] and '  m_Layer: 6\n' in s.blocks[r['go']]
    assert ref(s.blocks[mc],'m_Mesh')==(r['meshID'],r['meshGUID']);mesh=w.mesh(r['meshGUID'],r['meshID']);v=mesh['vertices'];ix=mesh['triangles'];assert np.isfinite(v).all() and ix.max()<len(v)
    unique=np.unique(v.round(6),axis=0);assert len(unique)<255 and np.linalg.det(np.cov(unique.T))>1e-8
    colliders.append(r)
assert len(colliders)==122
# Validate final geometry independently of the placement ledger. The visual
# boulder's world axis lengths must preserve its actual recovered source ratio.
pieces=json.loads((ROOT/'tools/remaster/live/authoring-report.json').read_text())['originalRocks']['pieces']
for r in colliders:
    number=int(r['name'].split()[-1]);piece=pieces[number%len(pieces)]
    source=np.asarray(piece['sourceBoundsMax'])-piece['sourceBoundsMin']
    ratios=np.linalg.norm(r['matrix'][:3,:3],axis=0)/source
    assert np.max(ratios)/np.min(ratios)<1.00001,('Stretched original boulder',r['name'])
buildings=[]
for n in range(14):
    group=[r for r in rows if r['lo'] is not None and re.search(r'Native Windflower · .* house '+str(n)+r'$',r['name'])]
    assert group,('Missing existing house group',n)
    buildings.append((np.min([r['lo'] for r in group],0),np.max([r['hi'] for r in group],0)))
home=[r for r in rows if r['lo'] is not None and r['name'].startswith('Home ·')]
assert len(home)==2,'Missing real playable home exterior'
buildings.append((np.min([r['lo'] for r in home],0),np.max([r['hi'] for r in home],0)))
approaches=[(np.array([-35.4,0,-25]),np.array([-32.6,3,-19.4]))]
for instance,prefab in w.prefabs.items():
    if not prefab.path.name.startswith('NPC-'):continue
    root=next(i for i in prefab.blocks if prefab.kind(i)==4 and ref(prefab.blocks[i],'m_Father')[0]==0)
    p=w.matrix(instance,root)[:3,3];approaches.append((p-np.array([1.2,1,1.2]),p+np.array([1.2,2,1.2])))
treeids=sorted({int(re.search(r'^Living tree (\d+)',s.name(i))[1]) for i in s.blocks if s.kind(i)==1 and re.search(r'^Living tree (\d+)',s.name(i))})
checkedtrees=0
for n in treeids:
    group=[r for r in rows if r['lo'] is not None and (re.match(r'Living tree '+str(n)+r'\b',r['name']) or re.match(r'Native Windflower · village cherry '+str(n)+r'$',r['name']))]
    if not group:continue
    box=(np.min([r['lo'] for r in group],0),np.max([r['hi'] for r in group],0))
    assert not any(intersects(box,b,.39) for b in buildings+approaches),('Canopy intersects building/approach',n)
    checkedtrees+=1
assert checkedtrees==21
for r in colliders:
    assert not any(intersects((r['lo'],r['hi']),b,.19) for b in buildings+approaches),('Rock intersects building/approach',r['name'])
# Every animal's entire planned route must have body clearance, including
# subsegments, world limits, actual rocks/buildings/rails and rendered slopes.
layout=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json').read_text());blocks=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/PlacementBounds.json').read_text())['blockers'];assets=animals();issues=[]
for actor in layout['actors']:
    radius=assets[actor['asset']]['radius']+.12;path=actor['path']
    for i,a in enumerate(path):
        b=path[(i+1)%len(path)]
        for u in np.linspace(0,1,9):
            x=a['x']*(1-u)+b['x']*u;z=a['y']*(1-u)+b['y']*u
            if not(-48+radius<x<57-radius and -32+radius<z<33-radius):issues.append((actor['name'],'world-bounds'))
            if water(x,z,radius):issues.append((actor['name'],'water'))
            h=terrain.height(x,z)
            if any(abs(terrain.height(x+dx*radius,z+dz*radius)-h)>.28 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):issues.append((actor['name'],'slope'))
            for block in blocks:
                dx=max(0,abs(x-block['center']['x'])-block['half']['x']);dz=max(0,abs(z-block['center']['y'])-block['half']['y'])
                if dx*dx+dz*dz<(radius+.08)**2:issues.append((actor['name'],block['kind']))
assert not issues,issues[:10]
modeljson=A/'OkamiRemaster/Player/Resources/NativePlayer/Bindings.json';bindings=json.loads(modeljson.read_text())['bindings'];states=set(re.findall(r'm_Name: (\S+)\n',(A/'Sunward/Generated/Amaterasu-SourceClips.controller').read_text()))-{'Amaterasu-SourceClips'};assert states<=set(x['state'] for x in bindings)
for clip,speed in [('pl00_010',2.07000732421875),('pl00_011',8.80321796123798),('pl00_012',16.540216619318183)]:assert all(abs(x['referenceSpeed']-speed)<1e-7 for x in bindings if x['clip']==clip)
for p in (A/'OkamiRemaster/Player/Resources/NativePlayer').glob('*/Poses.bytes'):assert p.read_bytes()==old(p),'Changed authentic motion data'
code=(A/'Sunward/Scripts/WolfCombat.cs').read_text();assert 'CreateBackSocket()' in code
native=(A/'OkamiRemaster/Player/NativeAmaterasu.cs').read_text();mount=native[native.index('public Transform CreateBackSocket'):native.index('void Awake()')];assert 'offset = Vector3.zero' in mount and 'original.position' not in mount
ground=next(r for r in rows if r['hi'] is not None and r['hi'][0]-r['lo'][0]>120 and r['hi'][1]<2);mat=w.assets[ground['materials'][0]];shader=w.assets[ref(mat.read_text(),'m_Shader')[1]];assert shader.name=='ContinuousGround.shader'
shadertext=shader.read_text();assert '_PathMap' not in shadertext and '_BaseMap' not in shadertext and 'Noise(' not in shadertext and 'frac(' not in shadertext
check=dict(sourceBaseline=BASE,sceneSHA256=hashlib.sha256(s.path.read_bytes()).hexdigest(),existingSceneObjectsPreserved=len(baseline.blocks),originalGameplayComponentsUnchanged=sum(baseline.kind(i)==114 for i in baseline.blocks),activeCSharpSyntaxFiles=sum(1 for _ in A.rglob('*.cs')),protectedGameplayScriptFiles=len(protected),combatMechanicsBytePreserved=True,motorGravityNumericallyUnchanged=True,nativeMotionBankBytesUnchanged=True,controllerStatesCovered=len(states),nativeBoulderConvexColliders=len(colliders),nativeBoulderWorldProportionsPreserved=True,fullCanopiesClearOfBuildingsAndApproaches=checkedtrees,protectedHomeAndNPCApproaches=len(approaches),fullFootprintAnimalRoutesPassed=len(layout['actors']),groundMaterialActuallyBound=str(mat.relative_to(A)),UnityLaunched=False,UnityCompiled=False,UnityGameplayVerified=False)
(ROOT/'tools/repair/checks.json').write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check,indent=2))
