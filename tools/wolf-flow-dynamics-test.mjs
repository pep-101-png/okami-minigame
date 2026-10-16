import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:1100,height:800}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(process.env.WOLF_FLOW_URL||'http://127.0.0.1:5291');await page.waitForFunction(()=>wolfStudio?.ready);
 const report=await page.evaluate(()=>{
  const s=wolfStudio;s.externalClock=true;const render=s.renderer.render;s.renderer.render=()=>{};let skin;s.model.traverse(o=>{if(o.isSkinnedMesh&&!skin)skin=o});const bones=Object.fromEntries(skin.skeleton.bones.map(b=>[b.name,b]));const v=()=>s.scene.position.clone(),position=n=>bones[n].getWorldPosition(v());const modes={};let maxTransitionStep=0;
  s.sample('Idle',0);
  for(const clip of ['Idle','Walk','Run','Walk','Idle']){
   s.choose(clip);let previous=s.tail.points.at(-1),maxStep=0,maxLengthError=0,maxBend=0;const samples=[];
   for(let i=0;i<480;i++){
    s.advance(1/120);const points=s.tail.points,tip=points.at(-1);maxStep=Math.max(maxStep,tip.distanceTo(previous));if(i<30)maxTransitionStep=Math.max(maxTransitionStep,tip.distanceTo(previous));previous=tip;
    maxLengthError=Math.max(maxLengthError,...s.tail.lengths.map(l=>Math.abs(l/s.tail.segment-1)));
    for(let j=2;j<points.length;j++)maxBend=Math.max(maxBend,points[j].clone().sub(points[j-1]).angleTo(points[j-1].clone().sub(points[j-2])));
    if(i>240&&i%6===0)samples.push({t:i/120,root:points[0].toArray(),tip:tip.toArray(),earlyDropFraction:(points[0].y-points[3].y)/(3*s.tail.segment),head:position('head').toArray(),back:position('hipsBackA').toArray(),shoulder:position('foreL').toArray()});
   }
   modes[clip]={maxStep,maxLengthError,maxBend,samples};
  }
  const allClips={};for(const c of s.clips){s.choose(c.name);for(let i=0;i<30;i++)s.advance(1/120);allClips[c.name]=s.tail.points.every(p=>p.toArray().every(Number.isFinite));}
  s.renderer.render=render;return {modes,maxTransitionStep,allClips};
 });
 await writeFile('wolf-viewer/review/tail-dynamics-validation.json',JSON.stringify(report,null,2));assert(report.maxTransitionStep<.03);for(const [clip,m] of Object.entries(report.modes)){assert(m.maxStep<.04,`${clip} tail jumped`);assert(m.maxLengthError<.08,`${clip} tail stretches: ${m.maxLengthError}`);assert(m.maxBend<.5,`${clip} tail kink: ${m.maxBend}`)}assert(report.modes.Idle.samples.every(s=>s.earlyDropFraction>.45),'Idle tail keeps a stiff horizontal base');assert(Object.values(report.allClips).every(Boolean));assert.deepEqual(errors,[]);console.log('PASS: passive-tail stability, length constraints, gradual transitions and all 22 clips.');
}finally{await browser.close()}
