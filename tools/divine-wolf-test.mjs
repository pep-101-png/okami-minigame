import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {writeFile,mkdir} from 'node:fs/promises';
const base=process.env.SMOKE_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(`${base}/wolf-review.html`);await page.waitForFunction(()=>window.review?.model?.actions?.HeavyReturn);
 const report=await page.evaluate(()=>{
  review.paused=true;const p=review.model;p.spear.visible=true;
  const ends=p.weaponEndpoints();const forwardWeapon=ends.tip.z<ends.heel.z;
  const fur=p.fur.bones.map(b=>b.name);const tail={},furMotion={};
  for(const clip of ['Idle','Walk','Run']){
   review.sample(clip,0);p.root.updateMatrixWorld(true);const a=p.body.getObjectByName('tailTip');tail[clip]=a.localToWorld(p.root.position.clone().set(0,1.23,0)).y;
   const before=p.fur.bones.map(b=>b.quaternion.toArray());review.sample(clip,p.actions[clip].getClip().duration*.37);
   furMotion[clip]=p.fur.bones.map((b,i)=>b.quaternion.toArray().reduce((v,x,j)=>v+Math.abs(x-before[i][j]),0));
  }
  p.animate({dt:.1,speed:2,charge:{kind:'light',ratio:.7}});const leg=p.body.getObjectByName('foreShinL');const legStart=leg.quaternion.toArray();
  for(let i=0;i<20;i++)p.animate({dt:.025,speed:2,charge:{kind:'light',ratio:.7}});
  const chargeStrideMotion=leg.quaternion.toArray().reduce((sum,x,i)=>sum+Math.abs(x-legStart[i]),0);
  const combat=[];
  for(const name of ['Thrust','Sweep','Finish','HeavyArc','HeavyReturn','ChargedThrust','ChargedHeavy','AirStrike']){
   const poses=[];let floorError=0,maxLift=0;
   for(let i=1;i<=40;i++){
    p.animate({dt:1/120,speed:0,air:name==='AirStrike',attack:i/41,attackClip:name});p.root.updateMatrixWorld(true);
    poses.push(p.head.matrixWorld.elements.slice());maxLift=Math.max(maxLift,p.groundLift);
    if(name!=='AirStrike'){const ends=p.weaponEndpoints();floorError=Math.max(floorError,.02-Math.min(ends.tip.y,ends.heel.y));}
   }
   const range=Math.max(...poses.map(m=>m[13]))-Math.min(...poses.map(m=>m[13]));
   combat.push({name,range,floorError,maxLift,finite:poses.every(m=>m.every(Number.isFinite))});
  }
  return {chargeStrideMotion,forwardWeapon,fur,furMotion,tail,combat,modelSource:performance.getEntriesByType('resource').filter(e=>e.name.endsWith('divine-wolf.glb')).map(e=>e.name)};
 });
 await mkdir('.test-artifacts/divine-wolf',{recursive:true});await writeFile('.test-artifacts/divine-wolf/report.json',JSON.stringify(report,null,2));
 assert(report.chargeStrideMotion>.01,'Charging while moving froze the legs');assert(report.forwardWeapon,'Spear points against gameplay forward direction');assert.equal(report.fur.length,8);assert(report.modelSource.length);
 for(const movement of Object.values(report.furMotion))assert(movement.every(x=>x>.005),'Fur did not deform through the loop');
 assert(report.tail.Idle<report.tail.Walk&&report.tail.Walk<report.tail.Run,'Tail height does not follow movement state');
 for(const attack of report.combat){assert(attack.finite,attack.name);assert(attack.range>.03,`${attack.name} has no body/head motion`);assert(attack.floorError<.035,`${attack.name} weapon below floor: ${attack.floorError}`);assert(attack.maxLift<.8,`${attack.name} excessive ground lift`);}
 assert.deepEqual(errors,[]);await mkdir('.test-artifacts/divine-wolf',{recursive:true});await writeFile('.test-artifacts/divine-wolf/report.json',JSON.stringify(report,null,2));console.log('PASS 8 fur controls in all locomotion loops, state-dependent tail height, 8 distinct body/head attacks and weapon floor clearance');
}finally{await browser.close();}
