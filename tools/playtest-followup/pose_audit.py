"""Offline native pose inspection; no Unity playback is implied."""
from pathlib import Path
import sys,json,struct,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/original-remake'));from export_assets import skin
sys.path.insert(0,'/workspace/work/full-asset-inspection');import visual_catalog as c
OUT=Path('/workspace/work/playtest-followup');OUT.mkdir(exist_ok=True)
def bank(path):
 d=path.read_bytes();_,_,bones,count=struct.unpack_from('<4sIII',d);off=16;clips={}
 for _ in range(count):
  n=struct.unpack_from('<I',d,off)[0];off+=4;name=d[off:off+n].decode();off+=n;frames,duration,loop=struct.unpack_from('<IfI',d,off);off+=12;a=np.frombuffer(d,'<f4',frames*bones*10,off).reshape(frames,bones,10);off+=a.nbytes;clips[name]=(a,duration,loop)
 return clips

def render(folder,name,phase,width=240,height=190):
 model=json.loads((folder/'Model.json').read_text());data=bank(folder/'Poses.bytes')[name][0];pose=data[round(phase*(len(data)-1))];parts=skin(model,pose);records=[]
 for part,v in zip(model['parts'],parts):
  if model.get('visibleGroups') and int(part['name'].split('-')[1]) not in model['visibleGroups']:continue
  colors=np.asarray(part['colors']).reshape(-1,4)
  if colors[:,:3].mean()<.04:continue
  tex=next(t for t in model['textures'] if t['index']==part['texture'])
  if tex.get('vertexOnly'):texture=np.full((2,2,4),255,'u1')
  else:texture=np.asarray(Image.open(folder/tex['path']).convert('RGBA'))
  records.append((part,v,colors,texture))
 points=np.concatenate([r[1] for r in records]);angle=1.40;right=np.array([math.cos(angle),0,-math.sin(angle)]);forward=np.array([math.sin(angle)*.98,.18,math.cos(angle)*.98]);forward/=np.linalg.norm(forward);up=np.cross(forward,right);basis=np.array([right,up,forward]);proj=points@basis.T;lo=proj.min(0);hi=proj.max(0);scale=min((width-25)/max(.001,hi[0]-lo[0]),(height-30)/max(.001,hi[1]-lo[1]));center=(lo+hi)/2
 pixels=np.full((height,width,3),[235,231,218],'u1');depth=np.full((height,width),-1e30,'f4')
 for part,points,colors,texture in records:
  v=points@basis.T;v[:,0]=(v[:,0]-center[0])*scale+width/2;v[:,1]=height/2-(v[:,1]-center[1])*scale;v=np.ascontiguousarray(v,dtype='f4');uv=np.asarray(part['uv']).reshape(-1,2).copy();uv[:,1]=1-uv[:,1];uv=np.ascontiguousarray(uv,dtype='f4');colors=np.ascontiguousarray(colors*128,dtype='f4');faces=np.ascontiguousarray(np.asarray(part['indices']).reshape(-1,3),dtype='i4');texture=np.ascontiguousarray(texture)
  c.lib.draw(width,height,pixels.ctypes.data,depth.ctypes.data,v.ctypes.data,uv.ctypes.data,colors.ctypes.data,len(v),faces.ctypes.data,len(faces),texture.ctypes.data,texture.shape[1],texture.shape[0],-1)
 im=Image.fromarray(pixels);ImageDraw.Draw(im).text((5,5),name+' '+str(phase),fill='black');return im
if __name__=='__main__':
 folder=ROOT/'Sunward-Unity/Assets/OkamiRemaster/Player/Resources/NativePlayer/pl00';clips=bank(folder/'Poses.bytes');names=[n for n in clips if int(n.split('_')[-1],16)<0x150]
 for offset in range(0,len(names),12):
  page=names[offset:offset+12];sheet=Image.new('RGB',(240*3,190*len(page)),(235,231,218))
  for i,name in enumerate(page):
   for j,phase in enumerate([.05,.4,.75]):sheet.paste(render(folder,name,phase),(j*240,i*190))
  p=OUT/('player-cycles-'+str(offset//12)+'.jpg');sheet.save(p);print(p.name,','.join(page),flush=True)
