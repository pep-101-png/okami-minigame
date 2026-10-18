import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const out=process.env.EXPANSION_OUT||'.test-artifacts/expansion-production';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.addInitScript(()=>{const raf=requestAnimationFrame.bind(window);window.requestAnimationFrame=fn=>raf(function tick(t){if(window.__pauseFrames)return raf(tick);fn(t);});});
await page.goto(process.env.EXPANSION_URL||'http://127.0.0.1:5180');await page.waitForFunction(()=>window.__game,{timeout:60000});await page.click('#start');await page.evaluate(()=>window.__pauseFrames=true);
const result=await page.evaluate(()=>{const g=__game,p=g.player;const tested=[];if(p.actions.ChargedThrust.getClip().duration>.8)throw new Error('Combat export contains idle padding');
 const samples=[];for(const phase of [.03,.52]){p.mixer.stopAllAction();const a=p.actions.ChargedThrust;a.reset().play();a.time=a.getClip().duration*phase;p.mixer.update(0);p.root.updateMatrixWorld(true);samples.push(p.head.getWorldPosition(p.root.position.clone()));}if(samples[0].distanceTo(samples[1])<.01)throw new Error('Combat head does not move');p.mixer.stopAllAction();p.state=null;
 for(const weapon of ['spear','sundial']){p.equip(weapon);for(const clip of ['Thrust','Sweep','Finish','HeavyArc','HeavyReturn','ChargedThrust','ChargedHeavy','AirStrike']){
  for(let i=1;i<20;i++){p.animate({dt:1/60,attack:i/20,combo:clip==='Sweep'?2:clip==='Finish'?3:1,attackClip:clip});let invalid=false;p.body.traverse(o=>{if(!o.matrixWorld.elements.every(Number.isFinite))invalid=true;});if(invalid)throw new Error('Invalid pose '+clip);}
  tested.push(weapon+':'+p.state);
 }}
 for(const kind of ['light','heavy']){p.animate({dt:.2,charge:{kind,ratio:.7}});if(!p.state.startsWith('Charge'))throw new Error('Missing charge pose');tested.push(p.state);}
 p.animate({dt:.2,voice:{clip:'Bark',phase:.4}});if(p.state!=='Bark')throw new Error('Missing bark pose');tested.push(p.state);
 p.equip('spear');p.animate({dt:.2});return{tested,actions:Object.keys(p.actions).length};});
async function shot(name,fn){await page.evaluate(fn);await page.screenshot({path:out+'/'+name+'.png'});}
await shot('home-interior',()=>{const g=__game;g.player.root.position.set(-34,0,16);g.player.root.rotation.y=Math.PI/2;for(let i=0;i<40;i++)g.world.update(.025,i*.025);__camera.position.set(-27,8,27);__camera.lookAt(-34,1,15);__view.painterly.render();});
await shot('market-npc',()=>{const g=__game;g.player.root.position.set(1,0,4);g.player.root.rotation.y=Math.PI/2;for(let i=0;i<40;i++)g.world.update(.025,i*.025);__camera.position.set(8,5,12);__camera.lookAt(3,1,0);__view.painterly.render();});
await shot('native-spear-pose',()=>{const g=__game;g.player.root.position.set(35,0,1);g.player.root.rotation.y=Math.PI/2;for(let i=0;i<20;i++)g.player.animate({dt:.016,attack:.5,attackClip:'ChargedThrust',combo:1});__camera.position.set(40,3,7);__camera.lookAt(35,1,1);__view.painterly.render();});
await shot('hollow-bell-boss',()=>{const g=__game,x=g.expansion;x.startRun();x.wave=3;x.spawnWave();for(let i=0;i<40;i++)g.update(1/60);g.player.root.position.set(35,0,3);__camera.position.set(44,9,18);__camera.lookAt(35,2,-1);g.expansion.renderUi();__view.painterly.render();});
const rendering=await page.evaluate(()=>{const r=__renderer;r.info.autoReset=false;r.info.reset();__view.painterly.render();const stats={drawCallsIncludingShadowsAndPostprocessing:r.info.render.calls,trianglesIncludingPasses:r.info.render.triangles,geometries:r.info.memory.geometries,textures:r.info.memory.textures};r.info.autoReset=true;return stats;});
assert.deepEqual(errors,[]);await writeFile(out+'/visual-check.json',JSON.stringify({...result,rendering,errors},null,2));console.log('PASS native poses, matrices and screenshots',result);await browser.close();
