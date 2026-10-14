/** Keep the approved idle bindings; blend into repaired locomotion bindings. */
export function createIdleBinding(mesh){
 const g=mesh.geometry,oldI=g.getAttribute('_idle_skin_index'),oldW=g.getAttribute('_idle_skin_weight');
 if(!oldI||!oldW)throw new Error('Approved idle bindings are missing.');
 const index=g.getAttribute('skinIndex'),weight=g.getAttribute('skinWeight'),newI=index.array.slice(),newW=weight.array.slice(),unions=[];
 for(let v=0;v<index.count;v++){
  const entries=new Map();for(let j=0;j<4;j++){const n=oldI.array[v*4+j];if(oldW.array[v*4+j]>0)entries.set(n,{n,old:oldW.array[v*4+j],next:0});}
  for(let j=0;j<4;j++){const n=newI[v*4+j],w=newW[v*4+j];if(w<=0)continue;const e=entries.get(n)||{n,old:0,next:0};e.next+=w;entries.set(n,e);}
  unions.push([...entries.values()]);
 }
 let previous=-1;
 return {set(blend){
  if(Math.abs(blend-previous)<1e-5)return;previous=blend;
  if(blend===0){index.array.set(newI);weight.array.set(newW);}
  else if(blend===1){index.array.set(oldI.array);weight.array.set(oldW.array);}
  else for(let v=0;v<index.count;v++){
   const top=unions[v].map(e=>({n:e.n,w:e.old*blend+e.next*(1-blend)})).sort((a,b)=>b.w-a.w).slice(0,4);const sum=top.reduce((s,e)=>s+e.w,0);
   for(let j=0;j<4;j++){index.array[v*4+j]=top[j]?.n||0;weight.array[v*4+j]=(top[j]?.w||0)/sum;}
  }
  index.needsUpdate=true;weight.needsUpdate=true;
 },approvedIndices:oldI,approvedWeights:oldW};
}
