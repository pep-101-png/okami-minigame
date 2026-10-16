import {defineConfig} from 'vite';
import {fileURLToPath} from 'node:url';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';

// Model URLs remain stable; each production build requests its exact revision.
// This prevents a cached GLB from being paired with newer face-fit metadata.
const revisions=Object.fromEntries(readdirSync(new URL('./public/models/',import.meta.url)).filter(n=>n.endsWith('.glb')).map(n=>[n,createHash('sha256').update(readFileSync(new URL('./public/models/'+n,import.meta.url))).digest('hex').slice(0,16)]));
export default defineConfig({
  base:'./',
  define:{__WOLF_ASSET_REVISIONS__:JSON.stringify(revisions)},
  build:{rollupOptions:{input:{
    viewer:fileURLToPath(new URL('./index.html',import.meta.url)),
    compare:fileURLToPath(new URL('./compare.html',import.meta.url))
  }}}
});
