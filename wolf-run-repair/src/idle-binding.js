/** Retain approved idle and walk deformation while repairing the run skin. */
export function createIdleBinding(mesh){
 const g=mesh.geometry,index=g.getAttribute('skinIndex'),weight=g.getAttribute('skinWeight');
 const idleI=g.getAttribute('_idle_skin_index'),idleW=g.getAttribute('_idle_skin_weight'),walkI=g.getAttribute('_walk_skin_index')||index.clone(),walkW=g.getAttribute('_walk_skin_weight')||weight.clone();
 if(!idleI||!idleW||!walkI||!walkW)throw new Error('Preserved animation bindings are missing.');
 const nextI=index.array.slice(),nextW=weight.array.slice(),unions=[];
 for(let v=0;v<index.count;v++){
  const entries=new Map();
  for(const [channel,ii,ww] of [['idle',idleI.array,idleW.array],['walk',walkI.array,walkW.array],['next',nextI,nextW]])for(let j=0;j<4;j++){
   const n=ii[v*4+j],w=ww[v*4+j];if(w<=0)continue;const e=entries.get(n)||{n,idle:0,walk:0,next:0};e[channel]+=w;entries.set(n,e);
  }
  unions.push([...entries.values()]);
 }
 let previous='';return {set(idle,walk=0){
  const key=`${idle}:${walk}`;if(previous===key)return;previous=key;
  if(idle===1){index.array.set(idleI.array);weight.array.set(idleW.array);}
  else if(walk===1){index.array.set(walkI.array);weight.array.set(walkW.array);}
  else if(idle===0&&walk===0){index.array.set(nextI);weight.array.set(nextW);}
  else for(let v=0;v<index.count;v++){
   const top=unions[v].map(e=>({n:e.n,w:e.idle*idle+e.walk*walk+e.next*Math.max(0,1-idle-walk)})).sort((a,b)=>b.w-a.w).slice(0,4),sum=top.reduce((s,e)=>s+e.w,0);
   for(let j=0;j<4;j++){index.array[v*4+j]=top[j]?.n||0;weight.array[v*4+j]=(top[j]?.w||0)/sum;}
  }
  index.needsUpdate=true;weight.needsUpdate=true;
 }};
}
