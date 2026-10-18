import * as THREE from'three';
export function timberGeometry(size,bevel=.05){
 const axis=size.indexOf(Math.max(...size)),length=size[axis],w=axis===0?size[1]:size[0],d=axis===2?size[1]:size[2],b=Math.min(bevel,w*.18,d*.18),ring=[[-w/2+b,-d/2],[w/2-b,-d/2],[w/2,-d/2+b],[w/2,d/2-b],[w/2-b,d/2],[-w/2+b,d/2],[-w/2,d/2-b],[-w/2,-d/2+b]],v=[],uv=[],ix=[];
 for(let j=0;j<5;j++)for(let i=0;i<8;i++){const t=j/4,[x,z]=ring[i],s=1+.012*Math.sin(t*4.3+i*.1);v.push(x*s,(t-.5)*length,z*s+.006*Math.sin(t*5));uv.push(t,i/8);if(j<4){let k=j*8+i,n=j*8+(i+1)%8;ix.push(k,k+8,n,n,k+8,n+8);}}
 for(const[top,j]of[[false,0],[true,4]]){const c=v.length/3;v.push(0,(j/4-.5)*length,0);uv.push(.5,.5);for(let i=0;i<8;i++)top?ix.push(c,j*8+(i+1)%8,j*8+i):ix.push(c,i,(i+1)%8);}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);if(axis===0)g.rotateZ(-Math.PI/2);if(axis===2)g.rotateX(Math.PI/2);g.computeVertexNormals();return g;
}
export function plasterShell(w,h,d){const g=timberGeometry([w,h,d],.15);g.translate(0,h/2,0);return g;}
