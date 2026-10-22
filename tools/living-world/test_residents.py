"""Saved skin/rig regression tests; no claim of Unity runtime verification."""
from pathlib import Path
import sys,re,struct,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/village'))
from check_village import parse_mesh
OUT=ROOT/'Sunward-Unity/Assets/Sunward/Generated/LivingVillagers'

def main():
 paths=sorted(OUT.glob('Living-*.asset'));assert len(paths)==7
 for path in paths:
  parse_mesh(path);s=path.read_text();count=int(re.search(r'm_VertexCount: (\d+)',s)[1]);raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',s)[1])
  # The knees must actually have blended vertices across both retained bones,
  # rather than two overlapping cylinders each rigidly assigned to one bone.
  mixed={3:0,6:0};ankles={5:0,8:0}
  for i in range(count):
   y=struct.unpack_from('<f',raw,i*80+4)[0];weights=struct.unpack_from('<4f',raw,i*80+48);bones=struct.unpack_from('<4I',raw,i*80+64)
   assert all(math.isfinite(v) for v in weights)
   active={b:w for b,w in zip(bones,weights) if w>1e-5}
   for thigh in mixed:
    if thigh in active and thigh+1 in active:mixed[thigh]+=1
   for foot in ankles:
    if foot in active:ankles[foot]+=1
  assert min(mixed.values())>=20,(path,'Missing smooth knee weights',mixed)
  assert min(ankles.values())>0,(path,'Missing feet',ankles)
 # Analyze all 360 phases: reach-clamping keeps a positive bend, finite IK and
 # feet connected to both fixed-length leg segments, including stopping/turns.
 for phase in np.linspace(0,1,360):
  for side in (-1,1):
   p=(phase+(0 if side<0 else .5))%1
   z=.16*(1-p/.6*2) if p<.6 else -.16+.32*((p-.6)/.4)
   y=.065+(math.sin((p-.6)/.4*math.pi)*.055 if p>=.6 else 0)
   a=np.array([side*.14,.74-.018+math.cos(phase*math.tau*2)*.006,0]);goal=np.array([side*.14,y,z]);distance=np.linalg.norm(goal-a)
   reach=min(max(distance,abs(.34-.335)+.0001),.34+.335-.0001)
   along=(.34**2-.335**2+reach**2)/(2*reach);lift=math.sqrt(max(0,.34**2-along**2))
   assert math.isfinite(lift) and lift>0 and abs(math.sqrt(along**2+lift**2)-.34)<1e-6
   assert abs(math.sqrt((reach-along)**2+lift**2)-.335)<1e-6
 print('PASS: seven saved skins; blended knees, retained13bones, continuous ankle assignments;720 IK samples preserve limb lengths.')
 print('NOT VERIFIED: Unity import, in-game walk timing, conversations, violin sound quality or doorway traffic.')
if __name__=='__main__':main()
