import {recoveryCatalog as catalog} from './recovery-catalog.js';
const frames=[document.querySelector('#before'),document.querySelector('#after')];
const picks=[document.querySelector('#left'),document.querySelector('#right')];
const notes=[document.querySelector('#left-note'),document.querySelector('#right-note')];
const view=document.querySelector('#view'),surface=document.querySelector('#surface'),clip=document.querySelector('#clip'),slider=document.querySelector('#phase'),play=document.querySelector('#play'),linked=document.querySelector('#linked'),state=document.querySelector('#state');
const query=new URLSearchParams(location.search);let driver=0,ready=false,playing=false,phase=0,last=performance.now();
for(const [i,pick] of picks.entries()){
 pick.replaceChildren(...Object.entries(catalog).map(([key,item])=>{const o=document.createElement('option');o.value=key;o.textContent=item.label;return o}));
 pick.value=query.get(i?'right':'left') in catalog?query.get(i?'right':'left'):(i?'current':'original');
 pick.onchange=()=>load(i);load(i);
}
function studios(){return frames.map(f=>f.contentWindow.wolfStudio)}
function loaded(){return studios().every((s,i)=>s?.ready&&s.archive===picks[i].value)}
function load(i){const next='./?compare=1&capture=1&archive='+picks[i].value;if(frames[i].getAttribute('src')===next)return;ready=false;playing=false;play.textContent='Play';state.textContent='Loading preserved models…';notes[i].textContent=catalog[picks[i].value].note;frames[i].src=next;}
function cameras(){
 const positions={three:[1.25,1.67,-2.55],profile:[1.65,1.68,-1.20],other:[-1.25,1.67,-2.55],front:[0,1.68,-3.1],body:[-4.8,2.45,-4.3],bodySide:[-6,2.3,.05]};
 const target=view.value.startsWith('body')?[0,.95,-.05]:[0,1.55,-1.17];
 for(const s of studios()){s.controls.enableDamping=false;s.camera.position.set(...positions[view.value]);s.controls.target.set(...target);s.controls.update();s.renderer.render(s.scene,s.camera)}driver=0;
}
function material(){for(const s of studios()){s.setArchiveMaterial(surface.value);s.setArchiveCulling(document.querySelector('#culling').checked);s.setArchiveShadows(document.querySelector('#shadows').checked)}}
document.querySelector('#culling').onchange=()=>{if(ready)material()};
document.querySelector('#shadows').onchange=()=>{if(ready)material()};
function sample(){
 if(!ready)return;playing=false;play.textContent='Play';const name=clip.value;
 for(const s of studios()){if(name!=='Rest'&&s.clips.some(c=>c.name===name))s.sample(name,phase,{tail:false});else s.rest();}
 slider.disabled=name==='Rest';play.disabled=name==='Rest';
 state.textContent=name==='Rest'?'Rest geometry · matching scale and lighting':studios().some(s=>!s.clips.some(c=>c.name===name))?'Matched phase · unavailable clips stay at rest':'Matched animation phase';
}
view.onchange=()=>{if(ready)cameras()};surface.onchange=()=>{if(ready)material()};
clip.onchange=()=>{phase=0;slider.value=0;sample()};slider.oninput=()=>{phase=Number(slider.value);sample()};
play.onclick=()=>{if(!ready||clip.value==='Rest')return;playing=!playing;play.textContent=playing?'Pause':'Play'};
function initialize(){
 if(ready||!loaded())return;ready=true;
 const previous=clip.value;const names=[...new Set(['Rest','Idle','Walk','Run',...studios().flatMap(s=>s.clips.map(c=>c.name))])].filter(n=>n==='Rest'||studios().some(s=>s.clips.some(c=>c.name===n)));
 clip.replaceChildren(...names.map(name=>{const o=document.createElement('option');o.value=name;o.textContent=name;return o}));clip.value=names.includes(previous)?previous:'Rest';
 for(const [i,f] of frames.entries()){const canvas=f.contentDocument.querySelector('canvas');canvas.onpointerdown=()=>driver=i;canvas.addEventListener('wheel',()=>driver=i,{passive:true});}
 material();sample();cameras();
}
function sync(){if(!linked.checked)return;const ss=studios(),a=ss[driver],b=ss[1-driver];b.camera.position.copy(a.camera.position);b.camera.quaternion.copy(a.camera.quaternion);b.camera.zoom=a.camera.zoom;b.camera.updateProjectionMatrix();b.controls.target.copy(a.controls.target);b.controls.update();}
function tick(now){const dt=Math.min(.05,(now-last)/1000);last=now;initialize();if(ready){
 if(playing){const reference=studios().find(s=>s.action);phase=(phase+dt/(reference?.action?.getClip().duration||1))%1;slider.value=phase;for(const s of studios())if(s.action){s.action.time=s.action.getClip().duration*phase;s.mixer.update(0);s.model.updateMatrixWorld(true);}}
 sync();
 }requestAnimationFrame(tick)}requestAnimationFrame(tick);
window.wolfRecovery={get ready(){return ready},studios,catalog};
