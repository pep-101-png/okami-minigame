"""Match repaired native boulders and moved trees with their real collision."""
import re,json,subprocess
import numpy as np
from scene_data import A,ROOT,World,Scene,ref,vec
def run():
    w=World();s=w.scene;path=s.path
    base=Scene(path,text=subprocess.check_output(['git','show','be9f4a0:'+str(path.relative_to(ROOT))],cwd=ROOT,text=True))
    rocks=[];trees=[];stats=dict(nativeRockConvexColliders=0,newRockCollidersAdded=0,obsoleteRockCapsulesDisabled=0,treeCapsulesMoved=0)
    for i in base.blocks:
        if base.kind(i)!=1:continue
        if base.name(i).startswith('Grounded stone '):rocks.append((vec(base.blocks[base.transform(i)],'m_LocalPosition'),i))
        if re.match(r'Living tree \d+ · bark',base.name(i)):
            old=vec(base.blocks[base.transform(i)],'m_LocalPosition');new=vec(s.blocks[s.transform(i)],'m_LocalPosition');trees.append((old,new))
    for i in s.blocks:
        if s.kind(i)!=136 or s.name(s.owner(i))!='Trunk / rock collider':continue
        t=s.transform(s.owner(i));p=vec(base.blocks[t],'m_LocalPosition')
        closest=min([(float(np.linalg.norm((old-p)[[0,2]])),old,new) for old,new in trees],key=lambda x:x[0])
        distance,old,new=closest
        rockdistance=min(float(np.linalg.norm((old-p)[[0,2]])) for old,_ in rocks)
        if distance<.12 and distance<=rockdistance:
            delta=new-old;position=p+delta
            if np.linalg.norm(delta)>.025:s.set(t,'m_LocalPosition','{x: %.8g, y: %.8g, z: %.8g}'%tuple(position));stats['treeCapsulesMoved']+=1
        elif rockdistance<.12:
            s.set(i,'m_Enabled',0);stats['obsoleteRockCapsulesDisabled']+=1
    template=next(s.blocks[i] for i in s.blocks if s.kind(i)==64)
    for row in list(w.renderers()):
        if not re.match(r'Native Windflower · original ST2 rock \d+$',row['name']):continue
        stats['nativeRockConvexColliders']+=1
        go=row['go']
        if any(s.kind(i)==64 for i in s.refs(go)):continue
        cid=s.alloc();raw=re.sub(r'^--- !u!64 &-?\d+',f'--- !u!64 &{cid}',template)
        raw=re.sub(r'm_GameObject: \{fileID: -?\d+\}','m_GameObject: {fileID: '+str(go)+'}',raw)
        raw=re.sub(r'(?m)^  m_Mesh: .*','  m_Mesh: {fileID: '+str(row['meshID'])+', guid: '+row['meshGUID']+', type: 2}',raw)
        raw=re.sub(r'(?m)^  m_Convex: .*','  m_Convex: 1',raw)
        raw=re.sub(r'(?m)^  m_IsTrigger: .*','  m_IsTrigger: 0',raw)
        raw=re.sub(r'(?m)^  m_Enabled: .*','  m_Enabled: 1',raw)
        s.blocks[cid]=raw;s.blocks[go]=s.blocks[go].replace('  m_Layer:',f'  - component: {{fileID: {cid}}}\n  m_Layer:',1);s.set(go,'m_Layer',6);stats['newRockCollidersAdded']+=1
    s.save();return stats
if __name__=='__main__':
    result=run();(ROOT/'tools/repair/collision-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
