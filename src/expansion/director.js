import * as THREE from 'three';
import { Progression,UPGRADES } from './progression.js';
import { expandVillage,BattleBarrier } from './world.js';
import { createSpirit,dangerMark,inkBolt } from './enemies.js';
import { FLAME_ATTACKS,createSundial } from './weapons.js';
import { createDivineSpear } from '../divine-spear.js';
import { brushRibbon } from './painted-forms.js';
const UP=new THREE.Vector3(0,1,0);
const waves=[['wisp','reed','wisp'],['reed','ranged','heavy','wisp','ranged'],['elite','heavy','ranged','wisp','reed','elite'],['boss']];
export class Expansion {
 constructor(game){
  this.game=game;this.flameAttacks=FLAME_ATTACKS;this.profile=new Progression();this.places=expandVillage(game.scene,game.world);this.barrier=new BattleBarrier(game.scene,game.world.arena);this.mode='town';this.wave=0;this.breakTime=0;this.projectiles=[];this.strokes=[];this.shopOpen=false;this.runCoins=0;this.runXp=0;this.runActive=false;this.stamina=this.profile.stats.maxStamina;this.energy=this.profile.stats.maxEnergy;
  for(const e of game.enemies){e.mesh.removeFromParent();e.texture.dispose();}game.enemies=[];
  this.panel=document.createElement('section');this.panel.id='rpg-scroll';this.panel.className='hidden';this.panel.setAttribute('role','dialog');this.panel.setAttribute('aria-modal','true');document.body.append(this.panel);
  const hud=document.createElement('div');hud.id='rpg-hud';hud.innerHTML='<div id="rpg-status"></div><div class="rpg-meters"><span>STAMINA <i id="stamina-fill"></i></span><span>DIVINE INK <i id="ink-fill"></i></span></div><small id="rpg-wave"></small><small id="rpg-save"></small>';document.body.append(hud);
  const boss=document.createElement('div');boss.id='rpg-boss';boss.className='hidden';boss.innerHTML='<strong>KUROGANE · THE HOLLOW BELL</strong><div><i></i></div><small></small>';document.body.append(boss);
  const controls=document.createElement('div');controls.id='rpg-controls';controls.innerHTML='<button id="rpg-journal">JOURNAL · UPGRADES</button><button id="rpg-switch">Q · SWITCH WEAPON</button><button id="rpg-leave" class="hidden">RETREAT · KEEP REWARDS</button>';document.body.append(controls);
  controls.querySelector('#rpg-journal').onclick=()=>{if(this.runActive)game.notify('Visit your home or Taro between trials.');else this.openShop('journal');};controls.querySelector('#rpg-switch').onclick=()=>this.switchWeapon();controls.querySelector('#rpg-leave').onclick=()=>{if(this.runActive)this.finish(false,true);};
  const display=new THREE.Group();display.position.set(-30.7,1.1,14);game.scene.add(display);const flame=createSundial(display);flame.root.scale.setScalar(.62);this.displayFlame=flame;
  const stand=new THREE.Group();stand.position.set(-31.5,1.3,13);stand.rotation.z=-.4;game.scene.add(stand);const displaySpear=createDivineSpear(stand);displaySpear.spear.scale.setScalar(.55);
  this.applyStats(true);game.player.root.position.copy(this.places.homeSpawn);game.notify('Welcome home · E at the resting mat or altar. Follow the bridge east to Taro.',9);this.renderUi();
 }
 get weapon(){return this.profile.data.equipped;}
 applyStats(heal=false){const g=this.game,old=g.maxHp;g.maxHp=this.profile.stats.maxHp;g.hp=heal?g.maxHp:Math.min(g.maxHp,g.hp+Math.max(0,g.maxHp-old));g.player.equip(this.weapon);g.player.power=this.profile.power;g.activities.offered=this.profile.data.shrine;this.stamina=Math.min(this.stamina,this.profile.stats.maxStamina);this.energy=Math.min(this.energy,this.profile.stats.maxEnergy);}
 spendStamina(n){if(this.stamina<n){this.game.notify('Catch your breath · stamina recovers naturally',1.6);return false;}this.stamina-=n;return true;}
 spendEnergy(n){if(this.energy<n){this.game.notify('Your divine ink is recovering',1.6);return false;}this.energy-=n;return true;}
 switchWeapon(){if(this.game.attackTime>0||this.shopOpen)return;const owned=this.profile.data.owned;if(owned.length<2){this.game.notify('Taro sells Sundial Flame for 110 sun coins.');return;}this.profile.equip(this.weapon==='spear'?'sundial':'spear');this.game.cancelAttack();this.applyStats();this.game.audio.play('interact');this.game.notify(this.weapon==='spear'?'Reed spear · precise reach':'Sundial Flame · close-range circular fire');}
 nearby(){const p=this.game.player.root.position;return Object.entries(this.places).filter(([k,v])=>['rest','altar','shop','portal'].includes(k)&&v.distanceTo(p)<2.5).sort((a,b)=>a[1].distanceTo(p)-b[1].distanceTo(p))[0]?.[0];}
 prompt(){if(this.runActive)return '';const key=this.nearby();return{rest:'E · Rest at home · restore vitality and ink',altar:'E · Home altar · permanent blessings',shop:'E · Taro’s weapon & upgrade shop',portal:'E · Enter the Hollow Bell trial · three waves, then boss'}[key]||'';}
 interact(){if(this.runActive)return false;const n=this.nearby();if(!n)return false;if(n==='portal')this.startRun();else if(n==='rest'){this.game.hp=this.game.maxHp;this.energy=this.profile.stats.maxEnergy;this.stamina=this.profile.stats.maxStamina;this.game.audio.play('collect');this.game.notify('A quiet breath · vitality, stamina and divine ink restored');}else this.openShop(n);return true;}
 openShop(kind='shop'){
  if(this.runActive)return;this.shopOpen=true;this.game.input.clear();this.game.cancelAttack();this.game.velocity.set(0,0,0);this.panel.classList.remove('hidden');this.shopKind=kind;this.drawShop();
 }
 closeShop(){this.shopOpen=false;this.panel.classList.add('hidden');this.game.input.clear();}
 drawShop(){
  const p=this.profile,s=p.stats,u=p.data.upgrades;this.panel.innerHTML=`<div class="scroll-heading">${this.shopKind==='shop'?'TARO’S FORGE':'THE GUARDIAN’S RECORD'}</div><h1>Ink remembers.</h1><p>Level ${p.level} · ${p.data.coins} sun coins · Power ${p.power.toFixed(0)}<br>Permanent gains survive every defeat and return home.</p><div class="shop-weapon"><strong>Reed spear</strong><span>Precise three-hit chain · long reach · damage ×${(s.damage*(1+u.spear*.12)).toFixed(2)}</span><button data-equip="spear">${this.weapon==='spear'?'EQUIPPED':'EQUIP SPEAR'}</button></div><div class="shop-weapon"><strong>Sundial Flame</strong><span>Circular fire combo · short-range area strikes · damage ×${(s.damage*(1+u.sundial*.14)).toFixed(2)}</span>${p.data.owned.includes('sundial')?`<button data-equip="sundial">${this.weapon==='sundial'?'EQUIPPED':'EQUIP FLAME'}</button>`:`<button data-buy="unlock-sundial" ${p.data.coins<110?'disabled':''}>UNLOCK · 110 COINS</button>`}</div><div class="upgrade-list">${Object.entries(UPGRADES).map(([key,d])=>`<div><span><b>${d.name}</b><small>${d.detail} · ${u[key]}/${d.max}</small></span><button data-buy="${key}" ${u[key]>=d.max||p.data.coins<p.cost(key)||(key==='sundial'&&!p.data.owned.includes('sundial'))?'disabled':''}>${u[key]>=d.max?'MASTERED':p.cost(key)+' ☀'}</button></div>`).join('')}</div><p class="save-note">${p.status} · This browser stores your progress. Keep its site data.</p><button id="rpg-close">RETURN TO THE VILLAGE →</button>`;
  for(const b of this.panel.querySelectorAll('[data-buy]'))b.onclick=()=>{if(p.buy(b.dataset.buy)){this.applyStats();this.game.audio.play('collect');this.drawShop();}};
  for(const b of this.panel.querySelectorAll('[data-equip]'))b.onclick=()=>{p.equip(b.dataset.equip);this.applyStats();this.drawShop();};this.panel.querySelector('#rpg-close').onclick=()=>this.closeShop();
 }
 disposeEnemies(){for(const e of this.game.enemies){e.tell?.dispose();e.dispose?.();if(!e.dispose)e.mesh.removeFromParent();}this.game.enemies=[];for(const p of this.projectiles)p.dispose();this.projectiles=[];}
 startRun(){const g=this.game;this.closeShop();this.disposeEnemies();this.mode='break';this.runActive=true;this.wave=0;this.breakTime=2.5;this.runCoins=0;this.runXp=0;g.victory=false;g.combatStarted=true;g.active=true;g.hp=g.maxHp;this.stamina=this.profile.stats.maxStamina;this.energy=this.profile.stats.maxEnergy;g.cancelAttack();g.velocity.set(0,0,0);g.player.root.position.set(22,0,0);g.cameraReset?.();g.player.root.rotation.y=-Math.PI/2;this.barrier.target=1;g.notify(`Trial ${this.profile.tier} · three waves, then Kurogane. All rewards are permanent.`,6);g.audio.play('enemyWindup');}
 spawnWave(){this.disposeEnemies();const g=this.game,list=waves[this.wave],scale=1+Math.sqrt(this.profile.tier-1)*.30+(this.profile.level-1)*.04;
  for(let i=0;i<list.length;i++){const a=i/list.length*Math.PI*2,home=new THREE.Vector3(35+Math.sin(a)*9,0,Math.cos(a)*9);const e=createSpirit(g.scene,list[i],i,home,scale);e.damage=e.spec.damage*(1+Math.log2(this.profile.tier)*.08);g.enemies.push(e);g.drawBar(e);}
  this.mode='fight';g.notify(this.wave===3?'Kurogane awakens · jump the shockwave, dodge the charge, avoid the ink fan.':`Wave ${this.wave+1} of 3 · ${list.length} corrupted spirits`,5);g.audio.play(this.wave===3?'heavyHit':'enemyAttack');
 }
 enemyKilled(e){if(e.paid)return;e.paid=true;const coins=Math.round(e.spec.reward*(1+(this.profile.tier-1)*.15));const xp=Math.round(e.spec.xp*Math.sqrt(1+(this.profile.tier-1)*.1));this.profile.reward(coins,xp);this.runCoins+=coins;this.runXp+=xp;this.applyStats();this.game.notify(`+${coins} sun coins · +${e.spec.xp} experience · saved`,1.5);}
 finish(win,retreat=false){if(!this.runActive)return;this.runActive=false;this.mode='result';this.barrier.target=0;this.profile.finish(win);this.applyStats();this.game.victory=win;this.game.active=false;this.game.cancelAttack();this.game.input.clear();for(const p of this.projectiles)p.dispose();this.projectiles=[];this.shopOpen=true;this.panel.classList.remove('hidden');this.panel.innerHTML=`<div class="scroll-heading">${win?'THE BELL FALLS SILENT':retreat?'A WISE RETREAT':'YOUR SPIRIT ENDURES'}</div><h1>${win?'Light returns.':'Rise again.'}</h1><p>${win?'Kurogane’s seal dissolves. Your permanent power grows.':'Your earned coins, experience, weapons and upgrades are safe.'}</p><p>${this.runCoins} combat coins · ${this.runXp} combat XP${win?' · victory bonus awarded':''}<br>Level ${this.profile.level} · ${this.profile.data.coins} coins in your purse</p><button id="rpg-home">RETURN HOME →</button>`;this.panel.querySelector('#rpg-home').onclick=()=>this.returnHome();this.game.audio.play(win?'victory':'playerHit');}
 returnHome(){this.disposeEnemies();this.closeShop();this.mode='town';const g=this.game;g.active=true;g.paused=false;g.dialogue=null;g.hp=g.maxHp;g.velocity.set(0,0,0);g.velocityY=0;g.dashTime=0;g.speed=0;g.hitStop=0;g.invulnerable=0;g.abilities.reset();g.player.root.position.copy(this.places.homeSpawn);g.cameraReset?.();g.player.root.rotation.y=0;this.energy=this.profile.stats.maxEnergy;this.stamina=this.profile.stats.maxStamina;g.notify('Welcome home · visit Taro or the home altar. The next trial grows stronger.',6);}
 collide(position,radius){if(!this.runActive)return;const c=this.game.world.arena.center,d=new THREE.Vector2(position.x-c.x,position.z-c.z),r=17.5-radius;if(d.length()>r){d.setLength(r);position.x=c.x+d.x;position.z=c.z+d.y;}}
 update(dt){const g=this.game;this.barrier.update(dt,g.time,g.input.yaw);this.displayFlame.root.visible=this.profile.data.owned.includes('sundial');this.displayFlame.update(g.time,0);if(!g.active||g.paused||this.shopOpen)return;
  this.stamina=Math.min(this.profile.stats.maxStamina,this.stamina+dt*(g.speed>5?-7:19+this.profile.data.upgrades.stamina));this.stamina=Math.max(0,this.stamina);this.energy=Math.min(this.profile.stats.maxEnergy,this.energy+dt*(this.runActive?5:12));
  if(this.mode==='break'){this.breakTime-=dt;if(this.breakTime<=0)this.spawnWave();}
  if(this.mode==='fight'){for(const e of g.enemies)if(e.hp<=0)this.enemyKilled(e);if(g.enemies.length&&g.enemies.every(e=>e.hp<=0)){this.clearDelay=(this.clearDelay||0)+dt;if(this.clearDelay>2){this.clearDelay=0;if(this.wave===3)this.finish(true);else{this.wave++;this.mode='break';this.breakTime=4;g.hp=Math.min(g.maxHp,g.hp+18);g.notify('The ink thins · breathe, recover and prepare for the next wave',4);}}}}
  for(let i=this.strokes.length-1;i>=0;i--){const p=this.strokes[i];p.time-=dt;p.mesh.material.opacity=Math.max(0,p.time/.32);p.mesh.scale.multiplyScalar(1+dt*2);if(p.time<=0){p.mesh.removeFromParent();p.mesh.geometry.dispose();p.mesh.material.dispose();this.strokes.splice(i,1);}}
 }
 attackEffect(position){if(this.weapon!=='sundial')return;for(let i=0;i<3;i++){const pts=Array.from({length:20},(_,j)=>{let a=j/19*Math.PI*1.8+i*.9;return[Math.sin(a)*1.6,.6+Math.sin(a*2)*.25,Math.cos(a)*1.6];});const m=brushRibbon(pts,.10,i===1?'#e8ba71':'#b95739',.8);m.position.copy(position);this.game.scene.add(m);this.strokes.push({mesh:m,time:.32});}}
 fire(e,count=1){const g=this.game,delta=g.player.root.position.clone().sub(e.mesh.position);delta.y=0;delta.normalize();for(let i=0;i<count;i++){const dir=delta.clone().applyAxisAngle(UP,(i-(count-1)/2)*.24);this.projectiles.push(inkBolt(g.scene,e.mesh.position,dir,e.damage));}g.audio.play('swing');}
 updateEnemies(dt){const g=this.game;if(!this.runActive||this.mode!=='fight')return;
  const player=g.player.root;for(const e of g.enemies){if(e.hp<=0)continue;const old=e.mesh.position.clone(),delta=player.position.clone().sub(e.mesh.position);delta.y=0;const distance=delta.length(),boss=e.kind==='boss';e.bar.visible=!boss;e.cooldown=Math.max(0,e.cooldown-dt);e.stun=Math.max(0,e.stun-dt);e.mesh.rotation.y=Math.atan2(-delta.x,-delta.z);
   if(e.knockback.lengthSq()>.01){g.move(e.mesh.position,e.knockback.clone().multiplyScalar(dt),.5);e.knockback.multiplyScalar(Math.exp(-dt*10));}
   if(e.stun>0){e.tell?.dispose();e.tell=null;e.state='stagger';if(boss)e.stun=Math.min(e.stun,.3);}
   else if(['approach','idle','stagger'].includes(e.state)){
    e.state='approach';const ranged=e.kind==='ranged',reach=ranged?9:boss?4.0:e.kind==='heavy'?2.8:2;
    if(distance>reach){const dir=delta.clone().normalize();if(!g.clearShot(e.mesh.position,player.position))dir.applyAxisAngle(UP,(e.visual.index%2?1:-1)*.85);if(e.kind==='wisp')dir.applyAxisAngle(UP,Math.sin(g.time*2+e.visual.index)*.3);g.move(e.mesh.position,dir.multiplyScalar(dt*e.spec.speed*(e.phase2?1.2:1)),.5);}
    else if(ranged&&distance<5)g.move(e.mesh.position,delta.clone().normalize().multiplyScalar(-dt*1.5),.5);
    if(e.cooldown<=0&&distance<reach+1){e.attacks++;e.attackDirection.copy(delta).normalize();e.hitPlayer=false;e.move=boss?['charge','slam','fan'][e.attacks%3]:ranged?'shot':e.kind==='heavy'?'slam':'charge';e.state='windup';e.timer=e.stateDuration=e.spec.windup*(e.phase2?.8:1);e.tell=dangerMark(g.scene,e.move==='slam'?e.mesh.position:player.position,e.move==='slam'?(boss?5:3):.75);g.audio.play('enemyWindup');}
   }else{
    e.timer=Math.max(0,e.timer-dt);const phase=1-e.timer/e.stateDuration;e.tell?.update(phase);
    if(e.state==='windup'&&e.timer===0){e.tell?.dispose();e.tell=null;e.state='lunge';e.timer=e.stateDuration=e.move==='charge'?(boss?.65:.32):.18;
     if(e.move==='shot'||e.move==='fan'){this.fire(e,e.move==='fan'?(e.phase2?7:5):1);e.hitPlayer=true;}
     if(e.move==='slam'){g.effects.slam(e.mesh.position);g.audio.play('slam');if(distance<(boss?5:3)&&player.position.y<.9&&g.invulnerable===0){g.damagePlayer(e.damage,delta.clone().normalize());e.hitPlayer=true;}}
    }else if(e.state==='lunge'){
     if(e.move==='charge'){
      e.previous.copy(e.mesh.position);g.move(e.mesh.position,e.attackDirection.clone().multiplyScalar(dt*(boss?10:7)),boss?1:.5);
      if(!e.hitPlayer&&g.sweptContact(e.previous,e.mesh.position,player.position,boss?2:1.1)&&player.position.y<.8&&g.invulnerable===0){e.hitPlayer=true;g.damagePlayer(e.damage,e.attackDirection);}
     }
     if(e.timer===0){e.state='recover';e.timer=e.stateDuration=boss?.95:.65;}
    }else if(e.state==='recover'&&e.timer===0){e.state='approach';e.cooldown=boss?.4:.6;}
   }
   if(boss&&e.hp<e.maxHp*.5&&!e.phase2){e.phase2=true;g.notify('The bell cracks · Kurogane’s attacks quicken and its ink fan widens',4);g.effects.barkWave(e.mesh.position,0);}
   for(const other of g.enemies){if(other===e||other.hp<=0)continue;const d=e.mesh.position.clone().sub(other.mesh.position);d.y=0;const l=d.length();if(l>.01&&l<1.1)g.move(e.mesh.position,d.multiplyScalar(dt*(1.1-l)/l*2),.5);}
   this.collide(e.mesh.position,boss?1:.55);e.visual.animate(dt,{state:e.state,phase:e.stateDuration?1-e.timer/e.stateDuration:0,speed:e.mesh.position.distanceTo(old)/Math.max(dt,.001),stun:e.stun});
  }
  for(let i=this.projectiles.length-1;i>=0;i--){const p=this.projectiles[i],old=p.root.position.clone();p.root.position.addScaledVector(p.direction,dt*7.5);p.time-=dt;if(!g.clearShot(old,p.root.position)||g.world.obstacles.some(o=>Math.hypot(o.x-p.root.position.x,o.z-p.root.position.z)<o.r))p.time=0;if(p.time>0&&g.sweptContact(old,p.root.position,player.position,.55)&&player.position.y<1.4&&g.invulnerable===0){g.damagePlayer(p.damage,p.direction);p.time=0;}
   if(p.time<=0||p.root.position.distanceTo(g.world.arena.center)>19){p.dispose();this.projectiles.splice(i,1);}
  }
 }
 renderUi(){const p=this.profile,g=this.game;document.getElementById('rpg-status').textContent=`☀ ${p.data.coins} · LV ${p.level} · ${this.weapon==='spear'?'REED SPEAR':'SUNDIAL FLAME'} · POWER ${p.power.toFixed(0)}`;document.getElementById('rpg-wave').textContent=this.mode==='break'?`Trial ${p.tier} · ${this.wave===3?'BOSS':'Wave '+(this.wave+1)} in ${Math.ceil(this.breakTime)}s`:this.runActive?this.wave===3?'KUROGANE · FINAL SEAL':`Trial ${p.tier} · Wave ${this.wave+1} / 3`:'WESTBANK HOME → MARKET → EASTERN TRIAL';document.getElementById('rpg-save').textContent=p.status==='saved'?`XP ${p.data.xp} / ${p.level*p.level*35} · SAVED LOCALLY`:p.status;document.getElementById('stamina-fill').style.width=`${100*this.stamina/p.stats.maxStamina}%`;document.getElementById('ink-fill').style.width=`${100*this.energy/p.stats.maxEnergy}%`;document.getElementById('rpg-leave').classList.toggle('hidden',!this.runActive);
  const e=g.enemies.find(e=>e.kind==='boss'&&e.hp>0),bar=document.getElementById('rpg-boss');bar.classList.toggle('hidden',!e);if(e){bar.querySelector('i').style.width=`${100*e.hp/e.maxHp}%`;bar.querySelector('small').textContent=e.phase2?'PHASE II · THE BROKEN SEAL':'PHASE I · CHARGE / SHOCK / INK';}
  if(g.active&&!g.paused&&!this.shopOpen&&this.prompt())document.getElementById('talk-prompt').textContent=this.prompt();
  document.getElementById('count').textContent=this.runActive?`${g.enemies.filter(e=>e.hp>0).length} spirits remain · ${this.runCoins} coins earned`:`${p.data.wins} trials cleared · ${p.data.kills} spirits restored`;
 }
}
