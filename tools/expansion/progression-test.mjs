import assert from 'node:assert/strict';
import {Progression,SAVE_KEY,sanitizeSave} from '../../src/expansion/progression.js';
const map=new Map();const storage={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v)};
const p=new Progression(storage);assert.equal(p.data.coins,35);assert.equal(p.buy('vitality'),true);assert.equal(p.stats.maxHp,112);assert.equal(p.data.coins,5);assert.equal(p.buy('strength'),false);
p.reward(180,100);assert.equal(p.buy('unlock-sundial'),true);assert.equal(p.data.equipped,'sundial');const power=p.power;p.finish(false);const loaded=new Progression(storage);assert.equal(loaded.data.equipped,'sundial');assert.equal(loaded.stats.maxHp,p.stats.maxHp);assert.equal(loaded.power,power);assert.equal(loaded.data.defeats,1);
loaded.finish(true);assert.equal(new Progression(storage).data.wins,1);map.set(SAVE_KEY,'{BROKEN');const recovered=new Progression(storage);assert.ok(recovered.data.owned.includes('sundial'));assert.equal(recovered.data.upgrades.vitality,1);
const s=sanitizeSave({version:1,currency:75,upgrades:{vitality:999,strength:-4},owned:['evil'],xp:NaN});assert.equal(s.coins,75);assert.equal(s.upgrades.vitality,8);assert.equal(s.upgrades.strength,0);assert.deepEqual(s.owned,['spear']);
const unavailable=new Progression({getItem(){throw new Error('blocked')},setItem(){throw new Error('blocked')}});assert.match(unavailable.status,/SESSION ONLY/);
console.log('PASS: upgrades, affordability, weapon ownership, defeat/victory persistence, corruption recovery, migration and storage failure.');
