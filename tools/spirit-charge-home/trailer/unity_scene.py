"""Read Unity text serialization; changes remain in memory for rendering only."""
import re,json,numpy as np
def vec(s,key):return np.array([float(v) for v in re.search(r"\b"+key+r": \{x: ([^,]+), y: ([^,]+), z: ([^}]+)",s).groups()])
class Scene:
 def __init__(self,path,text=None):
  self.path=path;s=path.read_text() if text is None else text;self.header=s.split('--- !u!')[0];self.blocks={}
  for b in re.split(r'(?=--- !u!)',s):
   if b.startswith('--- !u!'):self.blocks[int(re.search(r'&(-?\d+)',b)[1])]=b
  self.next=8000000000000000000
 def alloc(self):
  self.next+=1
  while self.next in self.blocks:self.next+=1
  return self.next
 def kind(self,id):return int(re.match(r'--- !u!(\d+)',self.blocks[id])[1])
 def name(self,id):
  m=re.search(r'^  m_Name: (.*)',self.blocks.get(id,''),re.M)
  if not m:return ''
  value=m[1]
  if value.startswith('"'):return bytes(value[1:-1],'utf8').decode('unicode_escape')
  return value
 def refs(self,id):return [int(x) for x in re.findall(r'component: \{fileID: (-?\d+)\}',self.blocks[id])]
 def owner(self,id):
  match=re.search(r'm_GameObject: \{fileID: (-?\d+)\}',self.blocks[id])
  return int(match[1]) if match else 0
 def component(self,id,kind):return next((r for r in self.refs(id) if self.kind(r)==kind),None)
 def transform(self,id):return self.component(id,4)
 def set(self,id,key,value):
  s,count=re.subn(r'(?m)^  '+key+r': .*',lambda _:'  '+key+': '+str(value),self.blocks[id]);assert count==1,(id,key);self.blocks[id]=s
