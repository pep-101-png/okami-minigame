export const SAVE_KEY = 'sunward.rpg.v2';
export const UPGRADES = {
  vitality: { name: 'Heart of the mountain', detail: '+12 permanent vitality', base: 30, max: 8 },
  strength: { name: 'Crimson resolve', detail: '+18% permanent weapon damage', base: 40, max: 8 },
  movement: { name: 'Windwalker', detail: '+3% movement speed; level 2 unlocks double jump', base: 35, max: 6 },
  stamina: { name: 'Enduring stride', detail: '+15 stamina; stronger recovery', base: 30, max: 8 },
  energy: { name: 'Wellspring of ink', detail: '+15 divine energy', base: 35, max: 8 },
  ability: { name: 'Voice of the guardian', detail: 'Faster, wider bark; stronger charged attacks', base: 45, max: 6 },
  spear: { name: 'Temper the reed spear', detail: '+12% spear damage', base: 30, max: 10 },
  sundial: { name: 'Stoke Sundial Flame', detail: '+14% flame damage', base: 35, max: 10 },
};
const cleanInt = (v, cap = 1e8) => Number.isFinite(v) ? Math.max(0, Math.min(cap, Math.floor(v))) : 0;
export function freshSave() { return { version: 2, revision: 0, coins: 35, xp: 0, wins: 0, defeats: 0, kills: 0, equipped: 'spear', owned: ['spear'], upgrades: Object.fromEntries(Object.keys(UPGRADES).map(k=>[k,0])), shrine: false, collectibles: [], windflowers: [], milestones: {} }; }
export function sanitizeSave(raw) {
  if (!raw || typeof raw !== 'object' || ![1,2].includes(raw.version)) throw new Error('Unsupported save version');
  const s=freshSave();
  for(const key of ['revision','coins','xp','wins','defeats','kills']) s[key]=cleanInt(raw[key]);
  s.coins=cleanInt(raw.coins ?? raw.currency);
  s.owned=raw.owned?.includes('sundial')?['spear','sundial']:['spear'];
  s.equipped=s.owned.includes(raw.equipped)?raw.equipped:'spear';s.shrine=raw.shrine===true;
  for(const [k,d]of Object.entries(UPGRADES))s.upgrades[k]=cleanInt(raw.upgrades?.[k],d.max);
  s.collectibles=Array.isArray(raw.collectibles)?[...new Set(raw.collectibles.filter(v=>typeof v==='string'&&/^[-a-zA-Z0-9_]{1,64}$/.test(v)))].slice(0,64):[];
  s.windflowers=Array.isArray(raw.windflowers)?[...new Set(raw.windflowers.filter(v=>['garden','mill','shrine'].includes(v)))]:[];
  if(raw.milestones&&typeof raw.milestones==='object')for(const[k,v]of Object.entries(raw.milestones))if(/^[-a-zA-Z0-9_]{1,64}$/.test(k)&&v===true)s.milestones[k]=true;
  if(s.wins)s.milestones.hollowBell=true;
  return s;
}
export class Progression {
  constructor(storage) {
    if(arguments.length===0){try{storage=globalThis.localStorage;}catch{storage=null;}}
    this.storage=storage;this.status='saved';let candidates=[];
    for(const key of [SAVE_KEY,SAVE_KEY+'.backup'])try{const value=storage?.getItem(key);if(value)candidates.push(sanitizeSave(JSON.parse(value)));}catch{this.status='recovered';}
    this.data=candidates.sort((a,b)=>b.revision-a.revision)[0]||freshSave();
    if(this.status==='recovered'&&candidates.length===0)this.status='new save · damaged data ignored';
    this.save();
  }
  reload(){const candidates=[];for(const key of[SAVE_KEY,SAVE_KEY+'.backup'])try{const v=this.storage?.getItem(key);if(v)candidates.push(sanitizeSave(JSON.parse(v)));}catch{}if(!candidates.length)return false;this.data=candidates.sort((a,b)=>b.revision-a.revision)[0];this.status='loaded';return true;}
  save() {
    this.data.revision++;const text=JSON.stringify(this.data);
    try {
      if(!this.storage)throw new Error('Unavailable');
      const old=this.storage.getItem(SAVE_KEY);
      if(old){try{sanitizeSave(JSON.parse(old));this.storage.setItem(SAVE_KEY+'.backup',old);}catch{ /* Keep the last valid backup. */ }}
      this.storage.setItem(SAVE_KEY,text);
      if(this.storage.getItem(SAVE_KEY)!==text)throw new Error('Write was not retained');
      this.status='saved';return true;
    }catch{this.status='SESSION ONLY · browser storage unavailable';return false;}
  }
  get level(){return 1+Math.floor(Math.sqrt(this.data.xp/35));}
  get power(){return (this.level-1)*2+Object.values(this.data.upgrades).reduce((a,b)=>a+b,0)*1.6+this.data.wins*2;}
  get stats(){const u=this.data.upgrades;return { maxHp:100+(this.level-1)*4+u.vitality*12+(this.data.shrine?20:0),damage:1+(this.level-1)*.045+u.strength*.18,movement:1+u.movement*.03,maxStamina:100+u.stamina*15,maxEnergy:80+u.energy*15,barkCooldown:Math.max(2.5,6-u.ability*.45),barkRadius:5.5+u.ability*.3,charge:1+u.ability*.08 };}
  get tier(){return 1+this.data.wins;}
  cost(key){const d=UPGRADES[key];return d?Math.round(d.base*Math.pow(1.48,this.data.upgrades[key])):Infinity;}
  buy(key){
    if(key==='unlock-sundial'){
      if(this.data.owned.includes('sundial')||this.data.coins<110)return false;
      this.data.coins-=110;this.data.owned.push('sundial');this.data.equipped='sundial';
    }else{
      const d=UPGRADES[key];if(!d||this.data.upgrades[key]>=d.max||(key==='sundial'&&!this.data.owned.includes('sundial'))||this.data.coins<this.cost(key))return false;
      this.data.coins-=this.cost(key);this.data.upgrades[key]++;
    }
    this.save();return true;
  }
  equip(weapon){if(!this.data.owned.includes(weapon))return false;this.data.equipped=weapon;this.save();return true;}
  reward(coins,xp){this.data.coins+=cleanInt(coins);this.data.xp+=cleanInt(xp);this.data.kills++;this.save();}
  finish(win){this.data[win?'wins':'defeats']++;if(win){this.data.coins+=65+this.data.wins*10;this.data.xp+=100;}this.save();}
  weaponDamage(){return this.stats.damage*(1+this.data.upgrades[this.data.equipped]*(this.data.equipped==='spear'?.12:.14));}
}
