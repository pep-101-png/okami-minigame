"""Original supported gable roofs and Japanese hall cupola. Offline native meshes.
No scene, colliders or existing geometry is edited. Units are Unity metres.
"""
from pathlib import Path
import sys,re,json,math,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
import native
from native import Mesh,ASSETS,Scene,vec,guid
OUT=ASSETS/'Generated/InkWorld'
WOOD=(.43,.26,.13);DARK=(.22,.16,.105);PAPER=(.89,.79,.58)
TILE=(.48,.47,.35);GOLD=(.84,.61,.23)


def beam(m,a,b,r=.06,color=WOOD):
 m.tube([a,b],[r,r],color,n=6)


def tile_slab(m,pts,thick,color):
 """Closed quad prism; caller supplies top corners counterclockwise from above."""
 top=np.array(pts);bottom=top-np.array([0,thick,0])
 m.face(top,color);m.face(list(reversed(bottom)),np.array(color)*.76)
 for j in range(4):m.face([top[j],bottom[j],bottom[(j+1)%4],top[(j+1)%4]],np.array(color)*.88)


def gabled(hx,hz,ridge=4.75,eave=2.65,small=False):
 wood,paper,tiles=Mesh(),Mesh(),Mesh()
 def height(x):
  t=abs(x)/hx
  return eave+(ridge-eave)*max(0,1-t)**1.7+.24*t**10
 rows=6 if small else 13;cols=5 if small else 8
 # Individual closed courses with slight painted lip relief, continuous underside.
 for side in [-1,1]:
  for c in range(cols):
   x0=side*hx*c/cols;x1=side*hx*(c+1)/cols;xa,xb=sorted((x0,x1))
   for row in range(rows):
    z0=-hz+2*hz*row/rows;z1=min(hz,-hz+2*hz*(row+1)/rows+.012)
    lip=.018+(row%2)*.004
    pts=[(xa,height(xa)+lip,z0),(xa,height(xa)+lip,z1),(xb,height(xb)+lip,z1),(xb,height(xb)+lip,z0)]
    col=np.array(TILE)*(1+.055*math.sin(row*1.9+c*.7))
    tile_slab(tiles,pts,.095 if not small else .065,col)
 # Closed structural gable infill lies inside the existing wall's footprint.
 wallx=max(.55,hx-.72) if not small else hx*.76
 wallz=hz-.62 if not small else hz*.76
 for sign in [-1,1]:
  z=sign*wallz;xs=np.linspace(-wallx,wallx,13)
  outline=[(x,eave,z) for x in [wallx,-wallx]]+[(x,height(x)-.12,z) for x in xs]
  # Per-segment closed panels avoid triangulating a concave fan.
  for xa,xb in zip(xs,xs[1:]):
   yy0=max(eave+.03,height(xa)-.12);yy1=max(eave+.03,height(xb)-.12)
   verts=[(xa,eave,z-.045),(xb,eave,z-.045),(xb,yy1,z-.045),(xa,yy0,z-.045)]
   # Front and rear walls of this gable infill.
   paper.face(list(reversed(verts)),PAPER)
   back=[(x,y,z+.09) for x,y,z in verts];paper.face(back,PAPER)
   for j in range(4):paper.face([verts[j],verts[(j+1)%4],back[(j+1)%4],back[j]],PAPER)
  beam(wood,(-wallx,eave,z),(wallx,eave,z),.09 if not small else .055)
  beam(wood,(0,eave,z),(0,ridge-.09,z),.085 if not small else .05)
  for side in [-1,1]:
   beam(wood,(0,eave+.11,z),(side*wallx*.78,height(wallx*.78)-.20,z),.065 if not small else .035)
  # Curved bargeboards and a slim parallel gold edge actually trace the roof.
  path=[(x,height(x)-.045,z+sign*(.13 if not small else .08)) for x in np.linspace(-hx,hx,17)]
  wood.tube(path,[.075 if not small else .05]*17,WOOD,n=8)
  tiles.tube([(x,y+.075,zz) for x,y,zz in path],[.020 if not small else .013]*17,GOLD,n=5)
 # Eave timbers and actual uprights connect curved roof underside to wall-top ring.
 for side in [-1,1]:
  x=side*wallx
  beam(wood,(x,eave,-wallz),(x,eave,wallz),.085 if not small else .05)
  for zz in np.linspace(-wallz,wallz,5 if not small else 3):
   beam(wood,(x,eave,zz),(x,height(x)-.12,zz),.065 if not small else .04)
 for zz in np.linspace(-hz,hz,rows+1):
  # Rounded individual ridge caps repeat along the true ridge line.
  tiles.tube([(0,ridge+.025,max(-hz,zz-.10)),(0,ridge+.045,min(hz,zz+.10))],[.10 if not small else .07]*2,TILE,n=8)
 # Restrained upward-curling ridge terminals, recognisable at a distance.
 for side in [-1,1]:
  path=[(0,ridge+.05,side*(hz-.35)),(0,ridge+.09,side*(hz-.18)),
        (0,ridge+.24,side*(hz-.10)),(0,ridge+.40,side*(hz-.12))]
  tiles.tube(path,[.10,.10,.065,.018],TILE,n=8)
 return wood,paper,tiles


def cupola():
 wood,paper,tiles=Mesh(),Mesh(),Mesh()
 # Local Y=0 sits on hall ridge; beams cradle the old hip roof without replacing it.
 for x in [-.84,.84]:
  for z in [-.57,.57]:
   wood.box((x,.54,z),(.14,1.20,.14),WOOD,bevel=.025)
   # Saddle feet reach the sloping existing hip roof below its central ridge.
   # A plinth that merely touches the ridge would leave its corners floating.
   wood.box((x,-.20,z),(.18,.42,.18),WOOD,bevel=.025)
 for y in [.08,1.03]:
  wood.box((0,y,0),(2.02,.17,1.43),WOOD,bevel=.035)
 # Louvre slats on four sides, open spacing and darker backing create actual depth.
 for side in [-1,1]:
  z=side*.60
  paper.box((0,.59,z), (1.52,.72,.045),PAPER,bevel=.012)
  for row in range(5):wood.box((0,.28+row*.135,z+side*.045),(1.69,.068,.09),DARK,bevel=.012)
  for x in [-.84,0,.84]:wood.box((x,.61,z+side*.08),(.055,.80,.07),WOOD,bevel=.01)
  x=side*.88
  paper.box((x,.59,0),(.045,.72,1.0),PAPER,bevel=.012)
  for row in range(5):wood.box((x+side*.045,.28+row*.135,0),(.09,.068,1.14),DARK,bevel=.012)
 # Two supported, strongly curved tiers on a 2.6 x 2.05m maximum roof footprint.
 for eave,ridge,hx,hz in [(1.07,1.73,1.28,.98),(1.73,2.15,.86,.70)]:
  w,p,t=gabled(hx,hz,ridge,eave,small=True);wood.merge(w);paper.merge(p);tiles.merge(t)
 # Slim central finial reinforces the hall silhouette without a large primitive cap.
 tiles.loft([(0,2.15,0,.07,.07),(0,2.28,0,.11,.11),(0,2.40,0,.025,.025)],GOLD,n=8)
 return wood,paper,tiles


def dimensions(index):
 s=Scene(ASSETS/'Scenes/Windflower.unity',text=subprocess.check_output(['git','show','ce07e12:Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'],cwd=ROOT,text=True))
 go=next(i for i in s.blocks if s.kind(i)==1 and s.name(i).startswith('Village house '+str(index)+' · closed'))
 mf=s.component(go,33);g=re.search(r'm_Mesh: .*guid: (\w+)',s.blocks[mf])[1]
 p=next(p.with_suffix('') for p in (ASSETS/'Generated/VillageFinish').glob('*.asset.meta') if 'guid: '+g in p.read_text())
 extent=vec(p.read_text(),'m_Extent');return extent[0],extent[2],p.name


def main():
 native.OUT=OUT;OUT.mkdir(exist_ok=True);rows=[]
 for index in [0,3]:
  hx,hz,source=dimensions(index)
  for part,mesh in zip(['wood','paper','tiles'],gabled(hx,hz)):
   name='Roof-House-'+str(index)+'-'+part;g=mesh.save(name)
   rows.append({'name':name,'guid':g,'triangles':len(mesh.tri),'houseIndex':index,'localPosition':[0,0,0],'sourceRoof':source,'eaveY':2.65,'ridgeY':4.75})
 for part,mesh in zip(['timber','plaster','tiles'],cupola()):
  name='Roof-Tower-'+part;g=mesh.save(name)
  rows.append({'name':name,'guid':g,'triangles':len(mesh.tri),'houseIndex':8,'localPosition':[0,3.85,0],'keepExistingRoof':True})
 assert sum(x['triangles'] for x in rows)<20000,rows
 (ROOT/'tools/ink-world/roof-manifest.json').write_text(json.dumps({'assets':rows,'triangles':sum(x['triangles'] for x in rows),'unityRendered':False},indent=2)+'\n')
 print(json.dumps({'assets':len(rows),'triangles':sum(x['triangles'] for x in rows)},indent=2))
if __name__=='__main__':main()
