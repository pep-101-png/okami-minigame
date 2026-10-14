import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
const base=process.env.WOLF_POLISH_URL||'http://127.0.0.1:5247';
const binary=await readFile('wolf-animation-viewer/public/models/wolf.glb'),length=binary.readUInt32LE(12),doc=JSON.parse(binary.subarray(20,20+length)),start=28+length;
function accessor(index){const a=doc.accessors[index],view=doc.bufferViews[a.bufferView],count={VEC3:3,VEC4:4,MAT4:16}[a.type],size={5126:4,5123:2,5121:1}[a.componentType],stride=view.byteStride||count*size,out=[];for(let i=0;i<a.count;i++)for(let j=0;j<count;j++){const offset=start+(view.byteOffset||0)+(a.byteOffset||0)+i*stride+j*size;let v=a.componentType===5126?binary.readFloatLE(offset):a.componentType===5123?binary.readUInt16LE(offset):binary.readUInt8(offset);if(a.normalized)v/=a.componentType===5121?255:65535;out.push(v);}return out;}
const old=doc.meshes[0].primitives[0],approved={positions:accessor(old.attributes.POSITION),indices:accessor(old.attributes.JOINTS_0),weights:accessor(old.attributes.WEIGHTS_0),inverses:accessor(doc.skins[0].inverseBindMatrices),names:doc.skins[0].joints.map(i=>doc.nodes[i].name)};
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:1440,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
try{
 await page.goto(base);await page.waitForFunction(()=>wolfStudio?.clips?.length===22);
 const report=await page.evaluate(approved=>{
  const s=wolfStudio;let skin;s.model.traverse(o=>{if(o.isSkinnedMesh&&!skin)skin=o;});const bones=Object.fromEntries(skin.skeleton.bones.map(b=>[b.name,b]));const vector=()=>s.scene.position.clone(),matrix=()=>skin.matrixWorld.clone();
  const vertexMap=new Map(),positions=skin.geometry.attributes.position,key=(x,y,z)=>[x,y,z].map(n=>Math.round(n*1e5)).join(':');for(let i=0;i<positions.count;i++)vertexMap.set(key(positions.getX(i),positions.getY(i),positions.getZ(i)),i);
  let idleError=0,matched=0;const bindError=Math.max(...approved.names.flatMap((name,i)=>skin.skeleton.boneInverses[skin.skeleton.bones.indexOf(bones[name])].elements.map((v,j)=>Math.abs(v-approved.inverses[i*16+j]))));
  for(const phase of [0,.25,.5,.75]){
   s.sample('Idle',phase);
   for(let i=0;i<approved.positions.length/3;i++){
    const index=vertexMap.get(key(...approved.positions.slice(i*3,i*3+3)));if(index===undefined)continue;matched++;
    const p=vector().fromArray(approved.positions,i*3).applyMatrix4(skin.bindMatrix),expected=vector().set(0,0,0);
    for(let j=0;j<4;j++){const w=approved.weights[i*4+j];if(!w)continue;const oldIndex=approved.indices[i*4+j],bone=bones[approved.names[oldIndex]],inverse=matrix().fromArray(approved.inverses,oldIndex*16),transform=matrix().multiplyMatrices(bone.matrixWorld,inverse);expected.addScaledVector(p.clone().applyMatrix4(transform),w);}
    expected.applyMatrix4(skin.bindMatrixInverse).applyMatrix4(skin.matrixWorld);const actual=skin.getVertexPosition(index,vector()).applyMatrix4(skin.matrixWorld);idleError=Math.max(idleError,expected.distanceTo(actual));
   }
  }
  const position=(name)=>bones[name].getWorldPosition(vector()),samples={};
  for(const t of [.07,.14,.22,.5,.9]){s.sample('Jump',t);samples[t]={head:position('head').y,body:position('body').y,fore:position('forePawL').y};}
  const air=[];for(const t of [.05,.25,.45,.65,.85]){s.sample('AirStrike',t);const forward=vector().setFromMatrixColumn(bones.head.matrixWorld,1).normalize();air.push({t,head:position('head').y,forwardY:forward.y,body:position('body').y});}
  s.sample('Bark',0);const jawStart=bones.jaw.quaternion.clone(),startBody=position('body').y;s.sample('Bark',.46);const bark={jawAngle:jawStart.angleTo(bones.jaw.quaternion),bodyDrop:startBody-position('body').y,frontWidth:position('forePawL').distanceTo(position('forePawR'))};
  let walkClearance=0;for(let i=0;i<36;i++){s.sample('Walk',i/36);for(const name of ['forePawL','forePawR','hindPawL','hindPawR'])walkClearance=Math.max(walkClearance,position(name).y-(name.startsWith('fore')?.46:.68)*.34);}
  const maxStretch={};const index=skin.geometry.index,edges=new Map(),p=positions;
  for(let i=0;i<index.count;i+=3)for(const [a,b] of [[index.getX(i),index.getX(i+1)],[index.getX(i+1),index.getX(i+2)],[index.getX(i+2),index.getX(i)]]){const label=Math.min(a,b)+':'+Math.max(a,b);if(edges.has(label))continue;const length=vector().fromBufferAttribute(p,a).distanceTo(vector().fromBufferAttribute(p,b));if(length>.015)edges.set(label,{a,b,length});}
  for(const name of ['Run','Walk','Jump','AirStrike','Bark']){
   let peak=0;for(const phase of Array.from({length:25},(_,i)=>i/25)){s.sample(name,phase);const deformed=Array.from({length:p.count},(_,i)=>skin.getVertexPosition(i,vector()));for(const edge of edges.values())peak=Math.max(peak,deformed[edge.a].distanceTo(deformed[edge.b])/edge.length);}maxStretch[name]=peak;
  }
  const fur=bones.shoulderFurLTip&&bones.foreFurRTip&&bones.hindFurLTip;const tailCounts=['tail','tailMid','tailTip','tailEnd',...['tail','tailMid','tailTip','tailEnd'].flatMap(n=>[n+'Flow',n+'Silk'])].filter(n=>bones[n]).length;
  const skinIndex=skin.geometry.attributes.skinIndex,skinWeight=skin.geometry.attributes.skinWeight,usage={};for(let i=0;i<skinIndex.count;i++)for(let j=0;j<4;j++){const n=skin.skeleton.bones[skinIndex.array[i*4+j]].name,w=skinWeight.array[i*4+j];usage[n]=(usage[n]||0)+w;}
  const finite={};for(const clip of s.clips){s.sample(clip.name,.35);finite[clip.name]=skin.skeleton.bones.every(b=>b.matrixWorld.elements.every(Number.isFinite));}
  return {idleError,matched,bindError,jump:samples,air,bark,walkClearance,maxStretch,segmentedFur:!!fur,tailCounts,spineCount:['chestBackA','chestBackB','hipsBackA','hipsBackB'].filter(n=>bones[n]&&usage[n]>1).length,tailUsage:Object.fromEntries(Object.entries(usage).filter(([n])=>n.startsWith('tail')&&(n.endsWith('Flow')||n.endsWith('Silk')))),finite};
 },approved);
 await mkdir('wolf-motion-refinement/review',{recursive:true});await writeFile('wolf-motion-refinement/review/animation-validation.json',JSON.stringify(report,null,2));
 assert(report.matched>approved.positions.length/3*3.9);assert(report.bindError<.00002);assert(report.idleError<.00005,`Idle changed: ${report.idleError}`);
 assert(report.jump['0.14'].head>report.jump['0.07'].head+.065,'Head does not lead takeoff');assert(Math.abs(report.jump['0.14'].body-report.jump['0.07'].body)<.035,'Body lifts before the head');assert(report.jump['0.22'].body>report.jump['0.14'].body+.12,'Body does not follow lift-off');
 assert(report.air.find(p=>p.t===.45).forwardY<-.35,'Air strike points upward');assert(report.air[0].body>report.air[3].body+.35,'Air strike has no downward travel');
 assert(report.bark.jawAngle>.20&&report.bark.bodyDrop>.20,'Bark is not braced with an opening jaw');
 assert(report.walkClearance<.115,'Walking feet are too high');
 for(const [clip,ratio] of Object.entries(report.maxStretch))assert(ratio<3,`${clip} exploding geometry: ${ratio}`);
 assert(report.spineCount===4);assert(report.bark.frontWidth>.48);assert(report.segmentedFur&&report.tailCounts===12);assert(Object.values(report.tailUsage).length===8&&Object.values(report.tailUsage).every(w=>w>1));assert(Object.values(report.finite).every(Boolean));
 await page.selectOption('#animation','Walk');await page.waitForTimeout(750);const playBox=await page.locator('#play').boundingBox();await page.mouse.click(playBox.x+playBox.width/2,playBox.y+playBox.height/2);const time=await page.evaluate(()=>wolfStudio.action.time);await page.waitForTimeout(100);assert(Math.abs(await page.evaluate(()=>wolfStudio.action.time)-time)<.01);const box=await page.locator('#scrub').boundingBox();await page.mouse.click(box.x+box.width*.65,box.y+box.height/2);assert(await page.evaluate(()=>wolfStudio.paused));const faceBox=await page.locator('[data-view=face]').boundingBox();await page.mouse.click(faceBox.x+faceBox.width/2,faceBox.y+faceBox.height/2);assert.deepEqual(errors,[]);
 console.log('PASS: approved idle bindings, staged jump, downward air slam, crouched/open-jaw bark, bounded deformations, segmented fur and twelve weighted tail joints, all clips and viewer controls.');
}finally{await browser.close();}
