import * as THREE from 'three';

/** Material overrides only; original geometry, normals, textures and clips stay intact. */
export function archiveMaterials(model){
 const entries=[],outlines=[];
 model.traverse(object=>{
  if(!object.isMesh)return;
  if(object.userData.archiveInk){outlines.push(object);return;}
  const saved=object.material;
  const clay=material=>new THREE.MeshStandardMaterial({color:'#b9b9b9',roughness:1,metalness:0,side:material.side});
  entries.push({object,saved,sides:(Array.isArray(saved)?saved:[saved]).map(m=>m.side),neutral:Array.isArray(saved)?saved.map(clay):clay(saved)});
 });
 const apply=mode=>{for(const ink of outlines)ink.visible=mode==='saved';for(const {object,saved,neutral} of entries)object.material=mode==='saved'?saved:neutral;};
 apply.cull=frontOnly=>{for(const {saved,neutral,sides} of entries)for(const group of [saved,neutral])for(const [i,m] of (Array.isArray(group)?group:[group]).entries()){m.side=frontOnly?THREE.FrontSide:sides[i];m.needsUpdate=true;}};
 return apply;
}
