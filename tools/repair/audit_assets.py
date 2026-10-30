"""Enumerate resolved active visuals; keep the full working CSV outside the repo.

Runtime adapters are explicitly separate from editor-visible fallback renderers.
An OkamiRemaster directory alone never proves original game provenance.
"""
import collections,csv,hashlib,json,re,sys
from pathlib import Path
from scene_data import World,Scene,A,ROOT,ref

def run(destination):
    w=World();report=json.loads((ROOT/'tools/remaster/live/authoring-report.json').read_text())
    original={x['mesh']:report['originalRocks']['source'] for x in report['originalRocks']['pieces']}
    for x in report['trialBellFrame']['meshes']:original[x['mesh']]='Original r200/35.SCR torii; approved coordinate conversion'
    bridge={x['mesh'] for x in report['bridges']['meshes']}
    paint={str(A.parent/x['output']):x for x in report['paintSourceProvenance'].values()}
    entries=[]
    def classify(path,guid,kind):
        if path is None:return 'old Sunward artwork','Unity primitive/built-in visual retained'
        rel=str(path.relative_to(A))
        if guid in original:return 'approved original conversion',original[guid]
        if guid in bridge:return 'mixed original and authored','Original r200/3.SCR bridge plus separately authored planks/ink'
        if kind=='model' and rel.startswith('OkamiRemaster/Windflower/Meshes/'):
            return 'temporary/composite artwork','Converted village prototype; not a verified exact original model'
        if rel.startswith('OkamiRemaster/Player/Resources/NativePlayer/'):
            return 'approved original conversion','pl00/wp24 native model, original pose banks and decoded paint; retained raw source files'
        if kind=='material' and rel.startswith('OkamiRemaster/'):
            return 'approved material conversion','Unity shader/material port; texture provenance classified separately'
        if str(path) in paint:
            p=paint[str(path)];return 'retained paint conversion',p['path']+'; copy/crop verified; raw game-archive identity not established for every painting'
        if rel.endswith('Existing-Road-Bank-Mask.png'):return 'authored layout mask','Existing Sunward paths/riverbanks; not original game artwork'
        if rel.endswith('Continuous-Grass.png'):return 'retained paint conversion','Byte-identical Recovered-Meadow; no synthetic noise'
        if rel.endswith('Continuous-Earth.png'):return 'retained paint conversion','Byte-identical retained 91b5ed75723a7cc7 painting; raw archive identity unverified'
        if '/FarmTextures/' in rel:return 'approved original conversion','Recovered native animal texture; original packed farm model/motion bank retained'
        if rel.startswith('OkamiRemaster/Village/Demo/Textures/'):
            return 'retained source paint; provenance incomplete','Retained village library paint; original-versus-authored identity requires per-source recovery'
        if rel.startswith('Sunward/'):
            return 'old Sunward artwork','Existing geometry/paint retained; native source equivalent not verified'
        return 'unverified','No verified per-asset provenance assigned'
    def append(actor,context,kind,path,guid='',fileid=''):
        category,evidence=classify(path,guid,kind)
        entries.append(dict(actor=actor,context=context,kind=kind,path=str(path.relative_to(A)) if path else 'Unity built-in',guid=guid or '',fileID=fileid,category=category,evidence=evidence))
    rows=list(w.renderers())
    for r in rows:
        context='saved scene; runtime visibility unverified'
        if r['kind']==137 and r['mesh'] and r['mesh'].name=='Amaterasu.fbx':context='legacy player fallback; native adapter hides after successful load'
        if r['go'] in [1103,1104,1105,1106,1107,1108,1109,1110]:context='legacy home weapon display; native adapter hides after successful load'
        actor=f"{r['instance']}:{r['go']} {r['name']}"
        append(actor,context,'model',r['mesh'],r['meshGUID'],r['meshID'])
        for g in r['materials']:
            mat=w.assets.get(g);append(actor,context,'material',mat,g)
            if mat:
                for tex in re.findall(r'm_Texture: \{[^}]*guid: (\w+)',mat.read_text()):append(actor,context,'texture',w.assets.get(tex),tex)
    # Follow serialized runtime prefab references (enemy/weapon definitions),
    # rather than silently excluding every visual instantiated during play.
    stack=[w.scene.path];seen=set();runtime_prefabs=[]
    while stack:
        path=stack.pop()
        if path in seen:continue
        seen.add(path)
        if path.suffix not in ['.unity','.prefab','.asset','.mat']:continue
        raw=path.read_text(errors='replace')
        for g in set(re.findall(r'guid: (\w+)',raw)):
            p=w.assets.get(g)
            if p and p not in seen and p.suffix in ['.prefab','.asset','.mat']:stack.append(p)
        if path.suffix!='.prefab' or path in {p.path for p in w.prefabs.values()}:continue
        runtime_prefabs.append(str(path.relative_to(A)));prefab=Scene(path)
        for i,b in prefab.blocks.items():
            if prefab.kind(i) not in [23,137] or '  m_Enabled: 0\n' in b:continue
            go=prefab.owner(i);mf=prefab.component(go,33)
            mesh=ref(b,'m_Mesh') if prefab.kind(i)==137 else ref(prefab.blocks.get(mf,''),'m_Mesh')
            actor=path.stem+':'+prefab.name(go);context='scene-reachable runtime prefab; spawning/visibility Unity unverified'
            append(actor,context,'model',w.assets.get(mesh[1]),mesh[1],mesh[0])
            material_section=re.search(r'  m_Materials:\n(.*?)(?=  m_StaticBatchInfo:|  m_StaticBatchRoot:)',b,re.S)
            for g in re.findall(r'guid: (\w+)',material_section[1] if material_section else ''):
                mat=w.assets.get(g);append(actor,context,'material',mat,g)
                if mat:
                    for tex in re.findall(r'm_Texture: \{[^}]*guid: (\w+)',mat.read_text()):append(actor,context,'texture',w.assets.get(tex),tex)
    # Dynamic native models do not exist in the saved editor mesh hierarchy.
    for name in ['pl00','wp24']:
        p=A/'OkamiRemaster/Player/Resources/NativePlayer'/name/'Model.json'
        append(p.parent.name,'runtime native adapter; Unity unverified','model',p)
        for t in p.parent.glob('Texture-*.png'):append(p.parent.name,'runtime native adapter; Unity unverified','texture',t)
    for p in (A/'OkamiRemaster/Village/Resources/FarmTextures').glob('*.png'):append('native ambient animals','runtime native adapter; Unity unverified','texture',p)
    for name in ['pl00','wp24']:
        p=A/'OkamiRemaster/Player/Resources/NativePlayer'/name/'Poses.bytes';append(name,'runtime native adapter; Unity unverified','motion bank',p)
    # Retained procedural visual effects are also artwork and remain incomplete.
    for name in ['PaintedEffects.cs','DivineGrowth.cs','VillageBreeze.cs']:
        for p in A.rglob(name):
            append(name,'runtime generated effects/props; implementation retained','visual-effect code',p)
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('w',newline='') as f:
        writer=csv.DictWriter(f,entries[0].keys());writer.writeheader();writer.writerows(entries)
    unique={(e['kind'],e['path']):e for e in entries}
    summary=dict(scene='Assets/Sunward/Scenes/Windflower.unity',activeEditorRenderers=len(rows),resolvedPrefabInstances=len(w.prefabs),activeVisualReferences=len(entries),distinctVisualAssets=len(unique),distinctAssetCategories=dict(collections.Counter(e['category'] for e in unique.values())),completeOriginalArtReplacement=False,mainHomeExactOriginalFound=False,originalPLModels=16,originalWPModels=96,rawSourceArchives=['pl.zip','wp.zip'],additionalAvailableSourcesInspected=['12 available ZIPs including prior Sunward projects/updates','retained native environmental mesh divisions and source bindings','WindflowerRemake.fbx','Amaterasu.fbx','sunward-wolf.blend','sunward-wolf.glb','fox-reference.glb'],unavailableSources=['Two Nippon example Tree.blend files are LFS pointers; remote server denied access'],limitations=['Editor renderer list includes fallbacks that runtime adapters hide after loading','Dynamic gameplay effect visibility and instantiated enemy prefabs require Unity verification','Retained village paint is not automatically proof of original archive provenance'],UnityVerified=False)
    (ROOT/'tools/repair/asset-audit-checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else '/workspace/work/repair/active-assets.csv')
