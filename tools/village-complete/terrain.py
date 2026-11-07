"""Sculpt only the existing valley terrain around the river mouth; preserve UVs/topology."""
from pathlib import Path
import sys,json,re,numpy as np,struct,subprocess
sys.path.insert(0,'/workspace/sunward-remaster/tools/repair');import scene_data as d
d.A=Path('/workspace/sunward-tundra-desktop/Sunward-Unity/Assets');w=d.World();from native import Mesh
r=next(r for r in w.renderers() if r['go']==8000000000000011394);m=w.mesh(r['meshGUID'],r['meshID']);raw=subprocess.check_output(['git','show','e17c75d275d0fb2fa2f4dd09cb99dd8af57c54a6:'+str(m['path'].relative_to(d.A.parent.parent))],cwd=d.A.parent.parent).decode();buf=bytes.fromhex(re.search('_typelessdata: ([a-f0-9]+)',raw)[1]);stride=m['stride'];v=np.ndarray((len(m['vertices']),3),'<f4',buffer=buf,strides=(stride,4)).copy();colors=np.ndarray((len(v),4),'<f4',buffer=buf,offset=24,strides=(stride,4)).copy();uv=np.ndarray((len(v),2),'<f4',buffer=buf,offset=40,strides=(stride,4)).copy()
def smooth(a,b,x):q=np.clip((x-a)/(b-a),0,1);return q*q*(3-2*q)
def river(z):
 def raw(q):return 1.1*np.sin(q*.13)+.45*np.sin(q*.31)+2*np.exp(-((q+8)/4)**2)
 cross=np.exp(-(26/4)**2);a=(raw(12)-raw(-14)*cross)/(1-cross*cross);b=raw(-14)-a*cross
 return -23+raw(z)-a*np.exp(-((z-12)/4)**2)-b*np.exp(-((z+14)/4)**2)
def sculpt(p):
 result=p.copy();x,y,z=p.T;spread=smooth(36,38,z);weight=smooth(35.95,36.9,z)*(1-smooth(42,47.5,z))*(1-smooth(2.7+spread*.9,5.8+spread*1.3,abs(x-river(-z))));result[:,1]=y*(1-weight)+(-7.15+.06*np.sin(x*.4))*weight;rear=smooth(43,48,z)*(1-smooth(7,14,abs(x+22)));result[:,1]+=rear*7;return result
new=sculpt(v);mesh=Mesh();mesh.v=new.tolist();mesh.c=colors[:,:3].tolist();mesh.uv=uv.tolist();mesh.bones=[0]*len(v);mesh.tri=m['triangles'].tolist();mesh.write(m['path'],template=raw)
p=d.A/'Sunward/Data/Valley.json';j=json.loads(p.read_text());t=j['world']['terrain'];original=json.loads(subprocess.check_output(['git','show','e17c75d275d0fb2fa2f4dd09cb99dd8af57c54a6:Sunward-Unity/Assets/Sunward/Data/Valley.json'],cwd=d.A.parent.parent));t['heights']=original['world']['terrain']['heights'];points=np.array([[t['minX']+x*t['step'],t['heights'][z*t['nx']+x],-(t['minZ']+z*t['step'])] for z in range(t['nz']) for x in range(t['nx'])]);t['heights']=sculpt(points)[:,1].tolist();p.write_text(json.dumps(j,separators=(',',':'))+'\n')
report=dict(changedVertices=int(np.sum(abs(v[:,1]-new[:,1])>1e-5)),preservedVertices=len(v),preservedTriangles=len(m['triangles']),minRiverBed=float(new[:,1].min()),operation='Existing valley terrain vertices lowered into continuous river gorge; topology/UV/pigment retained; hardcoded shader hole removed')
Path('/workspace/work/village-complete/terrain.json').write_text(json.dumps(report,indent=2));print(report)
