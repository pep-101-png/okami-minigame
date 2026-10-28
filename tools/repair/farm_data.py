"""Read converted original ambient-animal geometry and clip bounds for placement."""
import gzip,struct
import numpy as np
from scene_data import A
def read():
    data=gzip.decompress((A/'OkamiRemaster/Village/Resources/Farm/Animals.bytes').read_bytes());off=0
    def unpack(fmt):
        nonlocal off
        values=struct.unpack_from('<'+fmt,data,off);off+=struct.calcsize('<'+fmt);return values
    def text():
        nonlocal off
        n=unpack('i')[0];s=data[off:off+n].decode();off+=n;return s
    magic,version,count=unpack('iii');assert magic==0x314D5246 and version==2;out={}
    for k in range(count):
        name=text();nb=unpack('i')[0];offset=np.asarray(unpack('3f'));parents=[];bind=[]
        for i in range(nb):
            parents.append(unpack('i')[0]);bind.append(unpack('3f'))
        nparts=unpack('i')[0];parts=[]
        for j in range(nparts):
            texture=text();nv,ni=unpack('ii');v=np.frombuffer(data,'<f4',nv*3,off).reshape(-1,3).copy();off+=nv*12
            uv=np.frombuffer(data,'<f4',nv*2,off).reshape(-1,2).copy();off+=nv*8;colors=np.frombuffer(data,'u1',nv*4,off).reshape(-1,4).copy();off+=nv*4
            indices=np.frombuffer(data,'u1',nv*3,off).reshape(-1,3).copy();off+=nv*3
            weights=np.frombuffer(data,'u1',nv*3,off).reshape(-1,3).copy()/255.;off+=nv*3
            faces=np.frombuffer(data,'<i4',ni,off).reshape(-1,3).copy();off+=ni*4
            parts.append(dict(vertices=v,bones=indices,weights=weights,faces=faces,uv=uv,colors=colors,texture=texture))
        clips={}
        for j in range(unpack('i')[0]):
            role=text();source=text();duration,speed,lift=unpack('3f');nf=unpack('i')[0];records=[];ground=[]
            for f in range(nf):
                ground.append(unpack('f')[0]);records.append(np.frombuffer(data,'<f4',nb*10,off).reshape(nb,10).copy());off+=nb*40
            clips[role]=dict(source=source,duration=duration,speed=speed,lift=lift,ground=np.asarray(ground),poses=np.asarray(records))
        points=np.concatenate([p['vertices'] for p in parts])+offset
        radius=max(np.linalg.norm(points[:,[0,2]],axis=1));out[name]=dict(parents=parents,bind=bind,offset=offset,parts=parts,clips=clips,radius=float(radius),bounds=[points.min(0),points.max(0)])
    assert off==len(data);return out
