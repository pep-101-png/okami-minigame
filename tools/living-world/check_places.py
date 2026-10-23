"""Geometry and layout regressions; does not claim Unity play-mode validation."""
from pathlib import Path
import importlib.util,sys,re,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('places_test_subject',ROOT/'tools/living-world/places.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
for w,d in [(9.0,7.2),(10.2,12.0)]:
 wood,panels,floor,front,roof=p.room_mesh(w,d)
 for m in [wood,panels,floor,front,roof]:
  v=np.array(m.v);assert np.isfinite(v).all();assert min(min(t) for t in m.tri)>=0;assert max(max(t) for t in m.tri)<len(v)
 # The entire 3.2m door clearance is actual empty geometry below the lintel.
 for triangle in front.tri:
  points=np.array(front.v)[list(triangle)]
  assert points[:,0].min()>=1.599 or points[:,0].max()<=-1.599
 v=np.array(floor.v);assert v[:,0].min()>=-w/2-.001 and v[:,0].max()<=w/2+.001
 # Floor boards cover a substantial real surface, not a painted plane.
 assert v[:,1].max()-v[:,1].min()>.07
for seed in range(4):
 wood,cloth,goods,ornament=p.stall(seed)
 assert ornament.v and goods.v
 assert ornament.v and np.ptp(np.array(goods.v)[:,1])>.10
 assert len(set(tuple(c) for c in cloth.c))>5
bed=p.dog_bed();v=np.array(bed[0].v);assert np.ptp(v[:,2])>2.8 and np.ptp(v[:,0])>1.5
shader=(p.ASSETS/'Shaders/NightLantern.shader').read_text();assert '_SunwardNight' in shader and 'saturate' in shader
sky=(p.ASSETS/'Shaders/PaintedSky.shader').read_text();assert 'moonDot' in sky and 'float stars=' in sky
print('PASS: 2 room door openings/floors, finite indexed geometry, 4 decorated stalls, wolf-sized bed, night shader contracts')
