import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {writeFile,mkdir} from 'node:fs/promises';
const base=process.env.WOLF_VIEWER_URL||'http://127.0.0.1:5191';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
try{
 await page.goto(base);await page.waitForFunction(()=>window.wolfStudio?.clips?.length>20);
 const report=await page.evaluate(()=>{
  const s=wolfStudio,bones={};s.model.traverse(o=>{if(o.isBone)bones[o.name]=o;});
  const choices=[...document.querySelector('#animation').options].map(o=>o.value),clips=s.clips.map(c=>c.name),finite={},loops={},contacts={},tail={},fur={};
  for(const clip of s.clips){let valid=true;for(const phase of [0,.2,.5,.8,1]){s.sample(clip.name,phase);valid&&=Object.values(bones).every(b=>b.matrixWorld.elements.every(Number.isFinite));}finite[clip.name]=valid;}
  for(const name of ['Idle','Walk','Run','Jump']){s.sample(name,0);const before=Object.fromEntries(Object.values(bones).map(b=>[b.name,b.matrixWorld.elements.slice()]));s.sample(name,1);loops[name]=Math.max(...Object.values(bones).flatMap(b=>b.matrixWorld.elements.map((x,i)=>Math.abs(x-before[b.name][i]))));}
  const offsets={Walk:{foreL:0,hindR:.25,foreR:.5,hindL:.75},Run:{hindL:0,hindR:.09,foreL:.45,foreR:.54}};
  for(const name of ['Walk','Run']){
   const duration=s.clips.find(c=>c.name===name).duration,period=Math.round(duration*24),contact=name==='Walk'?.64:.4,speed=s.motion[name].ground_speed;let slip=0,height=0,count=0,old={},byLeg={};
   for(let frame=0;frame<period;frame++){
    s.sample(name,frame/period);
    for(const [leg,offset] of Object.entries(offsets[name])){
     const phase=(frame/period+offset)%1,bone=bones[`${leg.slice(0,-1)}Paw${leg.slice(-1)}`],m=bone.matrixWorld.elements;
     if(phase>.10&&phase<contact-.05){if(old[leg]&&old[leg].frame===frame-1){slip=Math.max(slip,Math.abs((m[14]-old[leg].z)-speed/24));count++;byLeg[leg]=(byLeg[leg]||0)+1;}height=Math.max(height,Math.abs(m[13]-(leg.startsWith('fore')?.46:.68)*.34));old[leg]={frame,z:m[14]};}else delete old[leg];
    }
   }
   contacts[name]={slip_metres_per_frame:slip,ankle_error_metres:height,samples:count,byLeg};
  }
  for(const clip of ['Idle','Walk','Run']){s.sample(clip,.3);tail[clip]=bones.tailEnd.matrixWorld.elements[13];const before=bones.tailEnd.quaternion.toArray();s.sample(clip,.6);tail[clip+'motion']=bones.tailEnd.quaternion.toArray().reduce((sum,x,i)=>sum+Math.abs(x-before[i]),0);}
  for(const name of ['Idle','Walk','Run','Jump']){s.sample(name,.1);const before=Object.fromEntries(Object.values(bones).filter(b=>/Fur|ruff/.test(b.name)).map(b=>[b.name,b.quaternion.toArray()]));s.sample(name,.45);fur[name]=Object.entries(before).map(([n,q])=>bones[n].quaternion.toArray().reduce((sum,x,i)=>sum+Math.abs(x-q[i]),0));}
  s.sample('Jump',.45);const jumpHeight=bones.head.matrixWorld.elements[13];s.sample('Jump',0);const jumpRise=jumpHeight-bones.head.matrixWorld.elements[13];
  return {choices,clips,finite,loops,contacts,tail,fur,jumpRise};
 });
 await mkdir('wolf-animation-viewer/review',{recursive:true});await writeFile('wolf-animation-viewer/review/browser-validation.json',JSON.stringify(report,null,2));
 assert.deepEqual(report.choices,report.clips);assert(report.clips.includes('Jump'));assert(Object.values(report.finite).every(Boolean));assert(Object.values(report.loops).every(x=>x<.003),JSON.stringify(report.loops));
 for(const [name,data] of Object.entries(report.contacts)){assert(data.samples>=16);assert(Object.values(data.byLeg).length===4&&Object.values(data.byLeg).every(x=>x>=3));assert(data.slip_metres_per_frame<.001,`${name} paw sliding ${data.slip_metres_per_frame}`);assert(data.ankle_error_metres<.006);}
 assert(report.tail.Idle<report.tail.Walk&&report.tail.Walk<report.tail.Run,JSON.stringify(report.tail));
 for(const name of ['Idle','Walk','Run'])assert(report.tail[name+'motion']>.015,'Rigid tail tip');
 for(const [name,motion] of Object.entries(report.fur))assert(motion.length===8&&motion.every(x=>x>.005),`${name} fur is static`);
 assert(report.jumpRise>.7,'Jump has no physical arc');
 await page.selectOption('#animation','Run');await page.waitForTimeout(750);await page.locator('#play').click();const paused=await page.evaluate(()=>wolfStudio.action.time);await page.waitForTimeout(150);assert(Math.abs(await page.evaluate(()=>wolfStudio.action.time)-paused)<.01);
 const box=await page.locator('#scrub').boundingBox();await page.mouse.click(box.x+box.width*.25,box.y+box.height/2);assert(await page.evaluate(()=>wolfStudio.paused));
 await page.locator('[data-view="front"]').click();await page.locator('#bones').check();assert.deepEqual(errors,[]);
 console.log('PASS: all animation selectors, finite poses, seamless locomotion/jump loops, four-paw ground matching, hanging/swaying/raised tail, flowing fur, jump arc, pause/scrub/view controls.');
}finally{await browser.close();}
