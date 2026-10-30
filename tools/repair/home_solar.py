"""Replace the actual home wall display's old disc, not only its unused prefab."""
import ast,json,re,struct,itertools
import numpy as np
from scene_data import A,ROOT,World
def run():
    w=World();s=w.scene;go=1679395475;t=s.transform(go);parent=w.matrix(0,t);inverse=np.linalg.inv(parent)
    rows=[r for r in w.renderers() if r['name'].startswith('Sundial-') and not r['instance']]
    points=[]
    for r in rows:
        m=inverse@r['matrix'];v=w.mesh(r['meshGUID'],r['meshID'])['vertices'];points.append(v@m[:3,:3].T+m[:3,3])
    points=np.concatenate(points);lo=points.min(0);hi=points.max(0)
    # Reuse the independent quaternion/skinning checker functions without
    # executing its top-level validation or changing any reference snapshots.
    file=ROOT/'tools/remaster/live/check_player.py';scope={'np':np,'struct':struct}
    for node in ast.parse(file.read_text()).body:
        if isinstance(node,ast.FunctionDef) and node.name in ['read_bank','matrices','skin']:exec(compile(ast.Module([node],[]),str(file),'exec'),scope)
    resource=A/'OkamiRemaster/Player/Resources/NativePlayer/wp24';model=json.loads((resource/'Model.json').read_text());pose=scope['read_bank'](resource/'Poses.bytes')['wp24_000'][0][0];native=np.concatenate(scope['skin'](model,pose))
    best=None
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product([-1,1],repeat=3):
            matrix=np.eye(3)[list(perm)]*np.asarray(signs)[:,None]
            if np.linalg.det(matrix)<.99:continue
            q=native@matrix.T;size=q.max(0)-q.min(0);scale=float(np.min((hi-lo+.03)/np.maximum(size,.01)))
            # Prefer a useful wall silhouette while fitting entirely inside
            # the existing cradle. The active player's mount remains unscaled.
            score=scale-.001*np.linalg.norm(matrix-np.eye(3))
            if best is None or score>best[0]:best=(score,matrix,q,scale)
    _,matrix,q,scale=best;offset=(lo+hi)/2-(q.min(0)+q.max(0))/2*scale
    # Convert a proper orthogonal 90-degree rotation to a quaternion.
    k=np.array([[matrix[0,0]-matrix[1,1]-matrix[2,2],matrix[1,0]+matrix[0,1],matrix[2,0]+matrix[0,2],matrix[2,1]-matrix[1,2]],
                [matrix[1,0]+matrix[0,1],matrix[1,1]-matrix[0,0]-matrix[2,2],matrix[2,1]+matrix[1,2],matrix[0,2]-matrix[2,0]],
                [matrix[2,0]+matrix[0,2],matrix[2,1]+matrix[1,2],matrix[2,2]-matrix[0,0]-matrix[1,1],matrix[1,0]-matrix[0,1]],
                [matrix[2,1]-matrix[1,2],matrix[0,2]-matrix[2,0],matrix[1,0]-matrix[0,1],np.trace(matrix)]])/3
    vals,vectors=np.linalg.eigh(k);quat=vectors[:,np.argmax(vals)]
    cid=8100000000000011001;script=re.search(r'^guid: (\w+)',(A/'OkamiRemaster/Player/NativeSolarFlare.cs.meta').read_text(),re.M)[1]
    if cid not in s.blocks:s.blocks[go]=s.blocks[go].replace('  m_Layer:',f'  - component: {{fileID: {cid}}}\n  m_Layer:',1)
    s.blocks[cid]=f'''--- !u!114 &{cid}
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
  m_EditorClassIdentifier: Assembly-CSharp::Sunward.Remaster.NativeSolarFlare
  visualScale: {scale:.9g}
  visualOffset: {{x: {offset[0]:.9g}, y: {offset[1]:.9g}, z: {offset[2]:.9g}}}
  visualRotation: {{x: {quat[0]:.9g}, y: {quat[1]:.9g}, z: {quat[2]:.9g}, w: {quat[3]:.9g}}}
  freezePose: 1
''';s.save();return dict(component=cid,oldDisplayRenderersReplacedAtRuntime=len(rows),cradleBounds=[lo.tolist(),hi.tolist()],nativeScale=scale,nativeOffset=offset.tolist(),nativeRotation=quat.tolist(),UnityVerified=False)
if __name__=='__main__':
    result=run();(ROOT/'tools/repair/home-solar-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
