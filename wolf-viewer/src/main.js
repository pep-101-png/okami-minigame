import * as THREE from 'three';
import {createFurDynamics} from './fur-dynamics.js';
import {createInkOutlines} from './ink-outlines.js';
import {applyWatercolorMaterial,createPaperBackground} from './watercolor.js';
import {createTailDynamics} from './tail-dynamics.js';
import {createFaceDynamics} from './face-dynamics.js';
import {createIdleBinding} from './idle-binding.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const parameters=new URLSearchParams(location.search);const baseline=parameters.has('baseline');
const version=parameters.get('version')||'head-study';
const versionModel={'head-study':'head-study.glb','jaw-repair':'jaw-repair.glb','neck-approved':'neck-approved.glb','baseline-2ba1f2b':'baseline-2ba1f2b.glb'}[version]||'wolf.glb';
const assetRevision=__WOLF_ASSET_REVISIONS__[versionModel];
const neckReview=parameters.get('review');
const reviewModel={baseline:'baseline.glb',candidate:'wolf.glb'}[neckReview];
const reviewRoot=`${import.meta.env.BASE_URL}review/drafts/neck-repair/`;
if(parameters.has('compare'))document.querySelector('main').style.display='none';
const scene=new THREE.Scene();scene.background=createPaperBackground();scene.fog=new THREE.Fog('#e8dfc8',16,35);
scene.add(new THREE.HemisphereLight('#fff8e9','#85847c',.9));
const key=new THREE.DirectionalLight('#fff2d7',2.6);key.position.set(4,6,-3);key.castShadow=true;key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-6;key.shadow.camera.right=6;key.shadow.camera.top=6;key.shadow.camera.bottom=-6;key.shadow.normalBias=.018;scene.add(key);
const fill=new THREE.DirectionalLight('#dce8ed',.7);fill.position.set(-4,3,2);scene.add(fill);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;key.shadow.radius=3.5;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.02;document.body.append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(34,innerWidth/innerHeight,.1,80);camera.position.set(-7.5,3.1,-.1);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,1,-.45);controls.enableDamping=true;controls.minDistance=1.2;controls.maxDistance=12;controls.maxPolarAngle=Math.PI*.48;
const floorPaper=createPaperBackground();floorPaper.wrapS=floorPaper.wrapT=THREE.RepeatWrapping;floorPaper.repeat.set(24,24);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(80,80),new THREE.MeshBasicMaterial({map:floorPaper,toneMapped:false}));floor.rotation.x=-Math.PI/2;floor.position.y=-.008;floor.receiveShadow=false;floor.renderOrder=-2;scene.add(floor);
const washShadow=new THREE.Mesh(new THREE.PlaneGeometry(80,80),new THREE.ShadowMaterial({color:'#685d4b',opacity:.20,depthWrite:false}));washShadow.rotation.x=-Math.PI/2;washShadow.position.y=-.006;washShadow.receiveShadow=true;scene.add(washShadow);
const markers=new THREE.Group();scene.add(markers);for(let i=0;i<40;i++){const line=new THREE.Mesh(new THREE.PlaneGeometry(8,.012),new THREE.MeshBasicMaterial({color:'#aa9e83',transparent:true,opacity:.16,depthWrite:false}));line.rotation.x=-Math.PI/2;line.position.set(0,.001,(i-20)*.35);markers.add(line);}
const status=document.querySelector('#status'),select=document.querySelector('#animation'),scrub=document.querySelector('#scrub');
let face,model,mixer,action,clips=[],motion={},skeleton,paused=false,rate=1,groundDistance=0,fade=0,groundSpeed=0,last=performance.now(),idleBindings=[],idleBlend=1,walkBlend=0,tail,fur;
const descriptions={Jump:'Squat, head and shoulder lead, body lift and staggered landing.',AirStrike:'A slow downward lead, forepaw contact and impact compression.',Bark:'Wide, low front stance and a stronger opening jaw.',Idle:'Relaxed breathing, a hanging tail and gentle fur movement.',Walk:'Four-beat walk. Planted paw travel and ground speed are matched.',Run:'Coordinated head, scapular glide and back flexion. Passive tail follows momentum.',JumpRise:'Upward jump pose.',JumpFall:'Falling pose with reaching legs.',Land:'Landing compression and recovery.'};
const studio={scene,camera,renderer,controls,get model(){return model},get mixer(){return mixer},get clips(){return clips},get action(){return action},get motion(){return motion},get groundSpeed(){return groundSpeed},get paused(){return paused},get idleBlend(){return idleBlend},get tail(){return tail},get fur(){return fur},get face(){return face},externalClock:parameters.has('capture'),reviewMode:reviewModel?neckReview:null,version};window.wolfStudio=studio;
function choose(name){const clip=clips.find(c=>c.name===name);if(!clip)return;const next=mixer.clipAction(clip);next.setLoop(THREE.LoopRepeat,Infinity);next.clampWhenFinished=false;next.reset().setEffectiveWeight(1).setEffectiveTimeScale(1).play();if(action&&action!==next)action.crossFadeTo(next,.65,false);for(const existing of clips){const a=mixer.clipAction(existing);if(a!==next&&a!==action)a.stop();}action=next;if(!studio.ready)idleBindings.forEach(b=>b.set(name==='Idle'?1:0,name==='Walk'?1:0));fade=.65;select.value=name;paused=false;document.querySelector('#play').textContent='Pause';document.querySelector('#play').setAttribute('aria-pressed','false');document.querySelector('#description').textContent=descriptions[name]||'Attack unchanged in this pass · deferred for later review.';}
studio.choose=choose;
studio.play=()=>{action.paused=false;action.enabled=true;action.clampWhenFinished=false;action.setLoop(THREE.LoopRepeat,Infinity).play();paused=false;};
studio.sample=(name,phase,options={})=>{
 face?.reset();mixer.stopAllAction();action=mixer.clipAction(clips.find(c=>c.name===name));action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.reset().setEffectiveWeight(1).play();
 idleBlend=name==='Idle'?1:0;walkBlend=name==='Walk'?1:0;idleBindings.forEach(b=>b.set(idleBlend,walkBlend));
 const duration=action.getClip().duration,speed=motion[name]?.ground_speed||0;
 if(tail&&options.tail!==false){
  action.time=0;mixer.update(0);model.updateMatrixWorld(true);tail.reset(speed);
  const h=1/120,total=Math.ceil(2/duration)*duration+duration*phase;
  for(let t=0;t<total;t+=h){action.time=(t%duration);mixer.update(0);model.updateMatrixWorld(true);tail.step(h,speed);}
 }
 action.time=duration*phase;mixer.update(0);model.updateMatrixWorld(true);tail?.apply();paused=true;select.value=name;renderer.render(scene,camera);
};
select.addEventListener('change',()=>choose(select.value));
document.querySelector('#play').onclick=()=>{if(paused&&action){if(action.time>=action.getClip().duration-.001)action.reset();action.paused=false;action.enabled=true;action.setLoop(THREE.LoopRepeat,Infinity);action.clampWhenFinished=false;action.play();}paused=!paused;document.querySelector('#play').textContent=paused?'Play':'Pause';document.querySelector('#play').setAttribute('aria-pressed',String(paused));};
document.querySelector('#restart').onclick=()=>{if(action){choose(action.getClip().name);groundDistance=0;}};
document.querySelector('#rate').oninput=e=>{rate=Number(e.target.value);document.querySelector('#rate-value').textContent=`${rate.toFixed(2).replace(/0+$/,'').replace(/\.$/,'')}×`;};
scrub.oninput=e=>{if(!action)return;studio.sample(action.getClip().name,Number(e.target.value));document.querySelector('#play').textContent='Play';document.querySelector('#play').setAttribute('aria-pressed','true');};
document.querySelector('#bones').onchange=e=>{if(skeleton)skeleton.visible=e.target.checked;};
for(const button of document.querySelectorAll('[data-view]'))button.onclick=()=>{const p={side:[-7.5,2.55,0],front:[0,2.7,-7.5],three:[-6,3.1,-4],face:[0,1.65,-3.5]}[button.dataset.view];camera.position.set(...p);controls.target.set(...(button.dataset.view==='face'?[0,1.48,-1.15]:[0,1,-.5]));controls.update();};
try{
 const [asset,metadata,tailMetadata,faceMetadata]=await Promise.all([new GLTFLoader().loadAsync(reviewModel?reviewRoot+reviewModel:`${import.meta.env.BASE_URL}models/${baseline?'before.glb':versionModel}?v=${assetRevision}`),fetch(`${import.meta.env.BASE_URL}${baseline?'before-motion':'motion'}.json`).then(r=>r.json()),fetch(`${import.meta.env.BASE_URL}tail.json`).then(r=>r.json()),fetch(reviewModel?reviewRoot+'face.json':`${import.meta.env.BASE_URL}${version==='jaw-repair'?'face-jaw-repair.json':version==='head-study'?'face-head-study.json':'face-neck-approved.json'}?v=${assetRevision}`).then(r=>r.json())]);
 model=asset.scene;model.scale.setScalar(.34);model.rotation.y=Math.PI;scene.add(model);motion=metadata;clips=asset.animations;mixer=new THREE.AnimationMixer(model);
 if(!baseline)face=createFaceDynamics(faceMetadata);
 const skins=[];model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;if(!baseline)for(const material of (Array.isArray(o.material)?o.material:[o.material]))applyWatercolorMaterial(material,face);}if(o.isSkinnedMesh)skins.push(o);});
 for(const mesh of skins){idleBindings.push(createIdleBinding(mesh));for(const ink of createInkOutlines(mesh))mesh.parent.add(ink);}
 if(!baseline){tail=createTailDynamics(model,tailMetadata);fur=createFurDynamics(model);}
 skeleton=new THREE.SkeletonHelper(model);skeleton.visible=false;scene.add(skeleton);
 const order=['Idle','Walk','Run','Jump','JumpRise','JumpFall','Land'];clips.sort((a,b)=>(order.includes(a.name)?order.indexOf(a.name):99)-(order.includes(b.name)?order.indexOf(b.name):99)||a.name.localeCompare(b.name));
 select.replaceChildren(...clips.map(c=>{const option=document.createElement('option');option.value=c.name;option.textContent=c.name.replace(/([a-z])([A-Z])/g,'$1 $2');return option;}));select.disabled=false;idleBlend=0;choose(baseline?'Run':'Idle');studio.ready=true;if(!parameters.has('compare'))document.querySelector('[data-view=face]').click();status.textContent=reviewModel?(neckReview==='baseline'?'ACCEPTED · 2ba1f2b':'APPROVED NECK CHECKPOINT'):baseline?'PREVIOUS BUILD · before repair':version==='neck-approved'?'APPROVED NECK CHECKPOINT':version==='baseline-2ba1f2b'?'ORIGINAL ACCEPTED · 2ba1f2b':version==='jaw-repair'?'JAW & FACE REPAIR · AWAITING REVIEW':'HEAD ANATOMY · AWAITING REVIEW';
}catch(error){status.textContent=`Could not load the viewer: ${error.message}`;console.error(error);}
function advance(dt){
 if(!mixer)return;mixer.update(dt*rate);const targetBinding=action.getClip().name==='Idle'?1:0;
 idleBlend=THREE.MathUtils.damp(idleBlend,targetBinding,10,dt);if(Math.abs(idleBlend-targetBinding)<.001)idleBlend=targetBinding;
 const targetWalk=action.getClip().name==='Walk'?1:0;walkBlend=THREE.MathUtils.damp(walkBlend,targetWalk,10,dt);if(Math.abs(walkBlend-targetWalk)<.001)walkBlend=targetWalk;
 idleBindings.forEach(b=>b.set(idleBlend,walkBlend));fade=Math.max(0,fade-dt);const target=motion[action.getClip().name]?.ground_speed||0;
 groundSpeed=THREE.MathUtils.damp(groundSpeed,target,fade>0?6:25,dt);groundDistance+=groundSpeed*dt*rate;
 model.updateMatrixWorld(true);tail?.step(dt*rate,groundSpeed);fur?.step(dt*rate,groundSpeed);face?.step(dt*rate);scrub.value=(action.time/action.getClip().duration)%1;
}
studio.advance=advance;
function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;if(mixer&&!paused&&!studio.externalClock)advance(dt);markers.visible=document.querySelector('#ground').checked;markers.position.z=markers.visible?groundDistance%.35:0;controls.update();renderer.render(scene,camera);requestAnimationFrame(frame);}requestAnimationFrame(frame);
window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
