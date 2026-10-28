"""Remove contradictory duplicate visual overrides, retaining the final value."""
import re,json
from scene_data import World,ROOT
def run():
    w=World();count=0
    for inst,prefab in w.prefabs.items():
        raw=w.scene.blocks[inst];pattern=r'    - target: \{fileID: (-?\d+),[^\n]+\}\n      propertyPath: ([^\n]+)\n      value:[ \t]*[^\n]*\n      objectReference: [^\n]*\n';matches=list(re.finditer(pattern,raw));last={}
        for i,m in enumerate(matches):
            target=int(m[1]);prop=m[2].strip("'\"")
            if target in prefab.blocks and prefab.kind(target) in [23,33,137] and prop.startswith(('m_Materials.','m_Mesh','m_Enabled')):last[target,prop]=i
        index=-1
        def replace(m):
            nonlocal index,count
            index+=1;key=(int(m[1]),m[2].strip("'\""))
            if key in last and index!=last[key]:count+=1;return ''
            return m[0]
        w.scene.blocks[inst]=re.sub(pattern,replace,raw)
    w.scene.save();return count
if __name__=='__main__':print('Redundant visual overrides removed:',run())
