import * as THREE from 'three';
import {createTerrain} from './terrain.js';
import {paintedTree,grassMeadows,driftingPetals} from './vegetation.js';
import {paintedSky,mountainScrolls,valleyBoundaries,bambooGrove,paintedWater} from './scenery.js';
import {enrichHome,paintedRoof} from './architecture.js';
import {paintingTime,restorePigments} from './pigment.js';
import {paint,stroke} from '../art.js';
import {batchDecoration} from '../town.js';

export function installEnvironment(game,camera){
 const {scene,world}=game;camera.far=280;camera.updateProjectionMatrix();
 scene.background=new THREE.Color('#e8e4d6');
 for(const light of scene.children){if(light.isHemisphereLight){light.color.set('#fcf9ed');light.groundColor.set('#93a6a0');light.intensity=1.55;}if(light.isDirectionalLight){light.color.set('#fff7ea');light.intensity=1.35;}}scene.fog=new THREE.FogExp2('#dce2d5',.0043);
 const retired=[];scene.traverse(o=>{if(o.userData.groundLayer||o.userData.legacyLandscape){o.visible=false;retired.push(o);}if(o.isMesh&&o.material?.color?.getHexString()==='56b3b3')o.visible=false;});
 createTerrain(scene);paintedSky(scene);mountainScrolls(scene);valleyBoundaries(scene,world);paintedWater(scene);
 // Retain tree positions, scale, trunk collision and camera fading contracts.
 for(const [i,tree]of world.trees.entries()){for(const child of [...tree.children])child.visible=false;paintedTree(tree,i%5===3?'maple':'cherry',i*13);}
 const newTrees=[[-46,23,'pine'],[-42,-29,'pine'],[-14,-26,'maple'],[15,-23,'pine'],[-16,27,'maple'],[15,25,'cherry'],[55,-22,'pine'],[54,24,'maple'],[-28,29,'cherry']];
 for(const [x,z,kind]of newTrees){if(world.boxes.some(b=>Math.abs(x-b.x)<b.halfX+1&&Math.abs(z-b.z)<b.halfZ+1))continue;const tree=new THREE.Group();tree.position.set(x,0,z);scene.add(tree);paintedTree(tree,kind,Math.round(x*z));world.trees.push(tree);world.obstacles.push({x,z,r:.43});}
 for(const [x,z]of[[-48,-22],[-48,7],[-47,31],[55,-31],[56,30],[-10,-34],[14,-34]])bambooGrove(scene,x,z,Math.round(x*z));
 const grassCount=grassMeadows(scene,world),petals=driftingPetals(scene,world.trees);petals(0);
 const oldHomeParts=new Set(game.expansion.places.home.children);enrichHome(game.expansion.places.home);for(const child of game.expansion.places.home.children)if(child.isGroup&&!oldHomeParts.has(child))batchDecoration(child);
 // Taro's shop becomes a deep-timber pavilion with a recognisable indigo canopy.
 const shop=new THREE.Group();shop.name='Taro · painted weapons pavilion';shop.position.set(4.8,0,0);scene.add(shop);
 paintedRoof(shop,3.7,2.2,2.3,'#5c7588',.52);
 const ornaments=new THREE.Group();shop.add(ornaments);
 stroke(scene,[[-31,3.7,7],[-24,3.48,7],[-17,3.65,7],[-10,3.48,7],[-3,3.7,7]],'#827c66',.018);
 for(const sign of[-1,1]){
  stroke(ornaments,[[sign*1.45,0,.55],[sign*1.43,2.27,.55]],'#665a51',.055);
  stroke(ornaments,[[sign*1.43,1.88,.55],[sign*1.12,2.17,.55],[sign*.92,2.2,.55]],'#9a8a70',.025);
 }
 for(let i=0;i<5;i++){const m=new THREE.Mesh(new THREE.PlaneGeometry(.49,.58,1,5),paint(i%2?'#7895a0':'#526e7b','wash'));m.position.set(-1.05+i*.53,2.05,1.05);m.material.side=THREE.DoubleSide;ornaments.add(m);stroke(ornaments,[[-1.2+i*.53,1.87,1.07],[-.93+i*.53,1.9,1.07]],'#d8d9bd',.015);}
 batchDecoration(ornaments);
 // Home roof extensions join the existing cutaway, keeping the interior readable.
 const home=game.expansion.places.home;const roofExtension=home.children.find(o=>o.isGroup&&o.position.z===4.4);
 const oldUpdate=world.update;
 const foliage=[];for(const t of world.trees)t.traverse(o=>{if(o.userData.foliage)foliage.push({mesh:o,tree:t});});
 const clouds=scene.children.filter(o=>o.material?.map&&o.renderOrder===-20);
 world.update=(dt,t)=>{
  oldUpdate(dt,t);paintingTime.value=t;petals(t);
  const p=game.player.root.position,inside=Math.abs(p.x+34)<5.6&&Math.abs(p.z-16)<5;
  if(roofExtension)roofExtension.visible=!inside;
  for(const tree of world.trees)for(const child of tree.children)if(child.userData.windBranch)child.rotation.z=Math.sin(t*.65+tree.position.x)*.004;
  for(const {mesh,tree}of foliage){const c=camera.position,dx=c.x-p.x,dz=c.z-p.z,vx=tree.position.x-p.x,vz=tree.position.z-p.z,l=Math.hypot(dx,dz)||1,u=(vx*dx+vz*dz)/(l*l),side=Math.abs(vx*dz-vz*dx)/l;const block=u>0&&u<1&&side<2.6;mesh.material.opacity=THREE.MathUtils.damp(mesh.material.opacity,block?.025:1,8,dt);}
  for(let i=0;i<clouds.length;i++)clouds[i].position.x+=Math.sin(t*.07+i)*dt*.04;
  for(const petal of world.petals.children){petal.position.x+=Math.sin(t*.9+petal.id)*dt*.11;petal.rotation.y+=dt*.25;}
 };
 restorePigments(scene);
 world.environment={version:1,name:'The painted valley',retiredSurfaces:retired.length,trees:world.trees.length,grassCount,atlas:'2048 × 1536, one nonrepeating world atlas',materials:'object/UV-space pigment; variable ink; no repaint of the original wolf'};
 return world.environment;
}
