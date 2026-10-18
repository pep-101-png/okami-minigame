import * as THREE from 'three';
// An authored asymmetrical stack of broad rock planes, softened at the joints.
export function rockGeometry(radius=1){
 const rings=[[0,.84,0,0],[.18,1,.04,-.02],[.62,.86,-.10,.06],[.98,.60,.08,-.02],[1.12,.26,.18,.05]],v=[],uv=[],ix=[],n=9;
 rings.forEach(([y,r,cx,cz],j)=>{for(let i=0;i<=n;i++){let a=i/n*Math.PI*2,f=1+.09*Math.sin(i*3.1+j*.6);v.push((Math.cos(a)*r*f+cx)*radius,y*radius,(Math.sin(a)*r*f+cz)*radius);uv.push(i/n,j/4);}});
 for(let j=0;j<4;j++)for(let i=0;i<n;i++){let a=j*(n+1)+i;ix.push(a,a+1,a+n+1,a+1,a+n+2,a+n+1);}const top=v.length/3;v.push(.18*radius,1.16*radius,.05*radius);uv.push(.5,1);for(let i=0;i<n;i++)ix.push(top,4*(n+1)+i,4*(n+1)+i+1);
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));for(let i=0;i<ix.length;i+=3)[ix[i+1],ix[i+2]]=[ix[i+2],ix[i+1]];g.setIndex(ix);g.computeVertexNormals();g.userData.sumiRock=true;return g;
}
