import assert from 'node:assert/strict';
import {createLandform,riverAt,waterAt,resolveRiver,BRIDGES,bridgeAt} from '../../src/environment/landform.js';
const land=createLandform({boxes:[]});
assert.ok(Math.max(...land.grid.heights)-Math.min(...land.grid.heights)>1.5);
for(let z=-32;z<=32;z+=.5){if(BRIDGES.some(b=>Math.abs(b-z)<1.3))continue;const r=riverAt(z);assert.ok(waterAt(r.x,z).deep);assert.ok(land.terrainHeight(r.x,z)<r.waterY-.8);for(const side of[-1,1]){const p={x:r.x+side*.2,z};resolveRiver(p);assert.equal(waterAt(p.x,z).deep,false);assert.equal(Math.sign(p.x-r.x),side);}}
for(const z of BRIDGES)for(let x=-27.8;x<=-18.21;x+=.1){const p={x,z};resolveRiver(p);assert.equal(p.x,x);assert.ok(bridgeAt(x,z));assert.equal(land.groundHeight(x,z),bridgeAt(x,z).y);}
for(const p of land.paths){assert.ok(p.samples.length>50);assert.ok(new Set(p.samples.map(p=>p.width.toFixed(2))).size>10);}
assert.equal(land.groundHeight(-34,16),.105);
console.log('PASS sculpted heights, winding channel depth, both bank guards, both bridge decks, varying spline paths, home floor.');
