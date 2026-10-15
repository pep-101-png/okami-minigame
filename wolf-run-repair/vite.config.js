import {defineConfig} from 'vite';
import {fileURLToPath} from 'node:url';
export default defineConfig({build:{rollupOptions:{input:{viewer:fileURLToPath(new URL('./index.html',import.meta.url)),compare:fileURLToPath(new URL('./compare.html',import.meta.url))}}}});
