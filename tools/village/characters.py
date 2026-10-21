"""Seven original Japanese fantasy village costumes on Sunward's existing 13-bone skeleton."""
import math
from native import Mesh
SKIN=(.78,.58,.43);HAIR=(.065,.045,.045);INK=(.035,.055,.065);IVORY=(.88,.84,.71);GOLD=(.66,.43,.15)
ROLES=['Elder','Merchant','ShrineMaiden','Samurai','Chef','Geisha','Gardener']

def resident(role):
 m=Mesh();female=role in ('ShrineMaiden','Geisha');stocky=role in ('Chef','Merchant');width=.23 if stocky else .185 if female else .205
 robe={'Elder':(.32,.40,.36),'Merchant':(.23,.29,.43),'ShrineMaiden':(.89,.86,.75),'Samurai':(.16,.23,.27),'Chef':(.86,.85,.75),'Geisha':(.39,.17,.29),'Gardener':(.32,.39,.23)}[role]
 # Zori, tabi, separate trouser legs and calves. Joint assignments match existing rig.
 for side in (-1,1):
  leg=3 if side<0 else 6
  m.box((side*.14,.055,.035),(.18,.07,.29),(.24,.16,.09),leg+2,.025)
  m.ellipsoid((side*.14,.115,.065),(.074,.047,.12),IVORY,leg+2,n=12,rows=5)
  m.loft([(side*.14,.13,0,.064,.067),(side*.14,.36,0,.079,.071),(side*.14,.67,0,.095,.095)],robe,leg+1,n=16,flute=.04)
  m.loft([(side*.14,.38,0,.085,.075),(side*.14,.62,0,.12,.105),(side*.14,.79,0,.115,.1)],robe,leg,n=16,flute=.055)
 # Curved cloth panels, overlapping lapels and a raised woven obi.
 m.loft([(0,.72,0,width*1.1,.14),(0,.91,0,width,.135),(0,1.20,0,width*1.12,.15),(0,1.41,0,width*1.13,.115)],robe,1,n=24,flute=.027)
 obi=(.67,.39,.13) if role=='Geisha' else (.66,.16,.13) if role=='ShrineMaiden' else (.26,.17,.12)
 m.loft([(0,.86,0,width*1.10,.147),(0,.99,0,width*1.12,.15)],obi,0,n=24)
 # V-shaped collar in front; raised geometry makes the wrap read in silhouette.
 m.tube([(-.13,1.40,.105),(-.035,1.22,.158),(.10,1.04,.15)],[.025,.027,.024],IVORY,1,n=6)
 m.tube([(.13,1.40,.105),(.035,1.22,.16),(-.01,1.17,.15)],[.026,.027,.024],IVORY,1,n=6)
 m.loft([(0,1.39,0,.061,.062),(0,1.58,0,.065,.06)],SKIN,2,n=16)
 # Shaped faces with chin, cheeks, separate nose, lips, eyelids, ears and eyebrows.
 headwidth=.127 if female else .142 if stocky else .134
 m.loft([(0,1.58,.018,.068,.074),(0,1.65,.018,headwidth*.83,.105),(0,1.76,0,headwidth,.113),(0,1.86,-.006,headwidth*.88,.10),(0,1.91,-.012,.055,.052)],SKIN,2,n=24)
 for side in (-1,1):
  m.ellipsoid((side*(headwidth-.004),1.75,0),(.025,.045,.025),SKIN,2,n=10,rows=6)
  m.ellipsoid((side*.052,1.776,.107),(.027,.012,.009),IVORY,2,n=12,rows=5)
  m.ellipsoid((side*.052,1.777,.115),(.009,.011,.005),INK,2,n=10,rows=5)
  m.tube([(side*.025,1.808,.112),(side*.06,1.816,.108),(side*.086,1.80,.095)],[.006,.006,.004],HAIR,2,n=6)
 m.ellipsoid((0,1.735,.12),(.019,.030,.027),SKIN,2,n=10,rows=6)
 m.tube([(-.027,1.68,.11),(0,1.675,.118),(.027,1.68,.11)],[.003,.004,.003],(.44,.20,.18),2,n=6)
 m.loft([(0,1.82,-.018,headwidth*1.03,.105),(0,1.91,-.02,headwidth*.86,.085),(0,1.94,-.02,.045,.04)],HAIR,2,n=24)
 # Separate hanging sleeves follow the existing arm/forearm bones.
 for side in (-1,1):
  arm=9 if side<0 else 11
  m.tube([(side*.23,1.39,0),(side*.34,1.20,0),(side*.43,1.10,0)],[.104,.112,.09],robe,arm,n=16,groove=.025)
  m.tube([(side*.43,1.17,0),(side*.48,.99,.025),(side*.51,.89,.04)],[.08,.072,.058],robe,arm+1,n=16)
  m.ellipsoid((side*.52,.87,.05),(.058,.08,.045),SKIN,arm+1,n=12,rows=6)
  if female:
   m.loft([(side*.33,.83,-.015,.14,.14),(side*.32,1.22,0,.125,.115)],robe,arm,n=16,flute=.025)
 if role in ('Geisha','ShrineMaiden','Elder'):
  skirt=(.68,.17,.12) if role=='ShrineMaiden' else robe
  m.loft([(0,.17,0,.30,.20),(0,.48,0,.285,.19),(0,.74,0,.25,.17),(0,.87,0,width*1.12,.15)],skirt,0,n=32,flute=.045)
  # Narrow hand-painted floral appliqué, not random full-surface dots.
  if role=='Geisha':
   m.box((0,.93,-.21),(.33,.20,.13),obi,0,.025)
   for j in range(7):
    a=j*.7;cx=.20*math.sin(a);cy=.28+j*.065;zz=.195
    for k in range(5):
     b=k*math.tau/5;m.ellipsoid((cx+.014*math.cos(b),cy+.014*math.sin(b),zz),(.012,.012,.004),(.88,.67,.56),0,n=6,rows=3)
 if role=='Chef':
  m.loft([(0,1.88,0,.145,.12),(0,2.03,0,.16,.13),(0,2.10,0,.10,.09)],IVORY,2,n=20,flute=.035)
  m.box((0,.86,.17),(.32,.58,.022),(.92,.88,.74),0,.008)
  m.tube([(-.16,.95,.18),(.16,.95,.18)],[.012,.012],(.37,.31,.21),0,n=6)
  m.box((-.15,.80,.19),(.05,.22,.04),(.29,.21,.13),0,.01)
 elif role=='Samurai':
  for j in range(5):
   m.loft([(0,1.04+j*.067,0,.245,.171),(0,1.09+j*.067,0,.245,.169)],INK,1,n=24)
   m.tube([(-.18,1.06+j*.067,.16),(.18,1.06+j*.067,.16)],[.008,.008],(.59,.22,.15),1,n=6)
  for side in (-1,1):
   for j in range(3):m.box((side*.29,1.40-j*.05,0),(.20,.045,.32),INK,9 if side<0 else 11,.012)
  m.loft([(0,1.85,-.01,.18,.15),(0,1.94,-.01,.14,.12),(0,2.01,-.01,.06,.05)],INK,2,n=20)
  for side in (-1,1):m.tube([(side*.04,1.94,.115),(side*.10,2.02,.12),(side*.16,2.05,.10)],[.015,.012,.006],GOLD,2,n=8)
  # Sheathed paired swords, angled at the belt, with carved guards.
  for j in range(2):
   m.tube([(-.24,.93,-.01),(-.38,.70,-.05),(-.57,.30,-.10)],[.027,.025,.013],INK,0,n=8)
   m.tube([(-.24,.93,-.01),(-.16,1.08,.01)],[.027,.022],(.43,.22,.13),0,n=8)
 elif female:
  m.ellipsoid((0,1.92,-.09),(.14,.11,.09),HAIR,2,n=20,rows=8)
  if role=='ShrineMaiden':m.loft([(0,1.02,-.135,.11,.035),(0,1.60,-.13,.10,.05),(0,1.84,-.11,.11,.06)],HAIR,2,n=16)
  else:
   for j in range(3):m.tube([(-.15,1.92+j*.025,-.03),(.18,1.96+j*.025,-.05)],[.009,.009],GOLD,2,n=6)
 elif role in ('Elder','Gardener'):
  m.loft([(0,1.86,0,.30,.27),(0,1.91,0,.29,.26),(0,2.04,0,.06,.06)],(.60,.46,.24),2,n=32,flute=.018)
  if role=='Elder':
   m.loft([(0,1.53,.077,.015,.02),(0,1.69,.09,.078,.04)],(.68,.67,.57),2,n=16)
   m.tube([(.55,.04,.12),(.56,.66,.1),(.51,.92,.05)],[.017,.021,.023],(.29,.18,.10),12,n=10,groove=.05)
  else:
   m.loft([(0,.87,-.28,.20,.13),(0,1.33,-.28,.25,.17)],(.50,.33,.15),1,n=20,flute=.035)
   for j in range(6):m.tube([(-.20,1.08+j*.037,-.41),(.20,1.08+j*.037,-.41)],[.008,.008],(.68,.48,.23),1,n=6)
 elif role=='Merchant':
  m.box((.18,.82,.12),(.18,.22,.12),(.43,.25,.12),0,.035)
  m.loft([(0,1.88,0,.14,.12),(0,2.01,-.03,.11,.10),(0,2.08,-.04,.02,.03)],(.18,.22,.30),2,n=20)
 return m
