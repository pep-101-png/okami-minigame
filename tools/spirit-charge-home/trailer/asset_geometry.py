"""Original MD skinning in the same coordinate convention as the Unity adapter."""
import numpy as np
def rotation(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def skin(model,pose):
    matrices=[];bind=[]
    for i,record in enumerate(pose):
        p,q,s=record[:3],record[3:7],record[7:];m=np.eye(4);m[:3,:3]=rotation(q)@np.diag(s);m[:3,3]=p
        parent=model['bones'][i-1]['parent']+1 if i else -1
        matrices.append(m if parent<0 else matrices[parent]@m)
        bind.append(np.zeros(3) if not i else bind[parent]+np.asarray(model['bones'][i-1]['position']))
    matrices=np.asarray(matrices);bind=np.asarray(bind);out=[]
    for part in model['parts']:
        v=np.asarray(part['positions']).reshape(-1,3);indices=np.asarray(part['boneIndices']).reshape(-1,3)+1;weights=np.asarray(part['weights']).reshape(-1,3);weights/=weights.sum(1,keepdims=True);posed=np.zeros_like(v)
        for k in range(3):posed+=weights[:,k,None]*(np.einsum('nij,nj->ni',matrices[indices[:,k],:3,:3],v-bind[indices[:,k]])+matrices[indices[:,k],:3,3])
        out.append(posed)
    return out
