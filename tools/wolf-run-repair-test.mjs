import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
const base=process.env.WOLF_REPAIR_URL||'http://127.0.0.1:5282';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:1000,height:750}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
try{
 await page.goto(base+'/compare.html');await page.waitForFunction(()=>[...document.querySelectorAll('iframe')].every(f=>f.contentWindow.wolfStudio?.ready));
 const report=await page.evaluate(()=>{
  const [before,after]=[...document.querySelectorAll('iframe')].map(f=>f.contentWindow.wolfStudio),skin=s=>{let found;s.model.traverse(o=>{if(o.isSkinnedMesh&&!found)found=o});return found};const old=skin(before),next=skin(after),v=()=>after.scene.position.clone();const renders=[before.renderer.render,after.renderer.render];before.renderer.render=()=>{};after.renderer.render=()=>{};
  const key=p=>[p.x,p.y,p.z].map(n=>Math.round(n*1e5)).join(':'),mapping=new Map();for(let i=0;i<next.geometry.attributes.position.count;i++)mapping.set(key(v().fromBufferAttribute(next.geometry.attributes.position,i)),i);
  const preservation={};for(const clip of ['Idle','Walk']){let maxError=0,count=0;for(const t of [0,.25,.5,.75]){before.sample(clip,t);after.sample(clip,t);for(let i=0;i<old.geometry.attributes.position.count;i++){const index=mapping.get(key(v().fromBufferAttribute(old.geometry.attributes.position,i)));if(index===undefined)continue;maxError=Math.max(maxError,old.getVertexPosition(i,v()).distanceTo(next.getVertexPosition(index,v())));count++;}}preservation[clip]={maxError,count};}
  const positions=next.geometry.attributes.position;let rearPlateVertices=0;for(let i=0;i<positions.count;i++){const x=positions.getX(i),z=positions.getY(i),y=-positions.getZ(i);if(y>2.264&&y<2.2949&&z>2.5863&&z<2.7603&&Math.abs(x)<.31)rearPlateVertices++;}
  const corrections=[];for(let frame=0;frame<48;frame++){const phase=frame/48;after.sample('Run',phase);const influences=next.morphTargetInfluences;corrections.push({phase,weight:influences.reduce((a,b)=>a+b,0),finite:influences.every(Number.isFinite)});}
  after.sample('Run',0);const start=Array.from({length:positions.count},(_,i)=>next.getVertexPosition(i,v()));after.sample('Run',1);let loopError=0;for(let i=0;i<positions.count;i++)loopError=Math.max(loopError,start[i].distanceTo(next.getVertexPosition(i,v())));
  let zeroOutsideRun=true;for(const clip of after.clips){after.sample(clip.name,.4);if(clip.name!=='Run'&&next.morphTargetInfluences.some(w=>Math.abs(w)>1e-6))zeroOutsideRun=false;}
  after.sample('Run',.75);let outlineMatches=true;after.model.traverse(o=>{if(o.isSkinnedMesh&&o!==next&&o.morphTargetInfluences!==next.morphTargetInfluences)outlineMatches=false});
  function folds(s,mesh){
   const g=mesh.geometry,idx=g.index,pos=g.attributes.position,ii=g.attributes.skinIndex,ww=g.attributes.skinWeight;let total=0,peak=0;
   for(let phase=0;phase<96;phase++){
    s.sample('Run',phase/96);const points=Array.from({length:pos.count},(_,i)=>mesh.getVertexPosition(i,v()));const transforms=mesh.skeleton.bones.map((bone,i)=>mesh.bindMatrixInverse.clone().multiply(bone.matrixWorld).multiply(mesh.skeleton.boneInverses[i]).multiply(mesh.bindMatrix).elements);let area=0;
    for(let t=0;t<idx.count;t+=3){const a=idx.getX(t),b=idx.getX(t+1),c=idx.getX(t+2),ra=v().fromBufferAttribute(pos,a),rb=v().fromBufferAttribute(pos,b),rc=v().fromBufferAttribute(pos,c),normal=rb.sub(ra).cross(rc.sub(ra)),restArea=normal.length();if(restArea<.001)continue;const expected=v().set(0,0,0);
     for(const vertex of [a,b,c])for(let j=0;j<4;j++){const weight=ww.array[vertex*4+j];if(!weight)continue;const m=transforms[ii.array[vertex*4+j]],x=normal.x,y=normal.y,z=normal.z;expected.x+=(m[0]*x+m[4]*y+m[8]*z)*weight;expected.y+=(m[1]*x+m[5]*y+m[9]*z)*weight;expected.z+=(m[2]*x+m[6]*y+m[10]*z)*weight;}
     const actual=points[b].clone().sub(points[a]).cross(points[c].clone().sub(points[a]));if(actual.dot(expected)/(actual.length()*expected.length()+1e-12)<-.1)area+=restArea/2;
    }total+=area;peak=Math.max(peak,area);
   }return {totalFoldedArea:total,peakFoldedArea:peak};
  }
  const folding={before:folds(before,old),after:folds(after,next)};before.renderer.render=renders[0];after.renderer.render=renders[1];
  return {folding,preservation,rearPlateVertices,targets:next.morphTargetInfluences.length,corrections,loopError,zeroOutsideRun,outlineMatches,clips:after.clips.length,buildLabel:document.querySelector('#after').contentDocument.querySelector('#status').textContent};
 });
 assert(report.folding.after.totalFoldedArea<report.folding.before.totalFoldedArea*.015,JSON.stringify(report.folding));assert.equal(report.clips,22);assert.equal(report.rearPlateVertices,0);assert.equal(report.targets,24);assert(report.outlineMatches);assert(report.zeroOutsideRun);assert(report.loopError<.0001,`Run pops at loop: ${report.loopError}`);assert(report.corrections.every(s=>s.finite&&Math.abs(s.weight-1)<1e-5));for(const [clip,p] of Object.entries(report.preservation)){assert(p.count>35000);assert(p.maxError<.0001,`${clip} changed: ${p.maxError}`)}
 await page.locator('#play').click();await page.waitForTimeout(300);await page.locator('#play').click();const phase=Number(await page.locator('#phase').inputValue());assert(Math.abs(phase-.75)>.05);await page.locator('#view').selectOption('rear');assert.deepEqual(errors,[]);
 await writeFile('wolf-run-repair/review/browser-validation.json',JSON.stringify(report,null,2));console.log('PASS: plate removed; 24 active run correctives; idle and walk preserved; looping, non-run reset, outline and comparison controls.');
}finally{await browser.close()}
