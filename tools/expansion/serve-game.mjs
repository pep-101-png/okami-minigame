import http from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {resolve,dirname,extname,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'dist');
const port=Number(process.env.SUNWARD_PORT||5173);
if(!Number.isInteger(port)||port<1||port>65535)throw new Error('SUNWARD_PORT must be a valid port number');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.glb':'model/gltf-binary','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.ogg':'audio/ogg','.wav':'audio/wav','.mp3':'audio/mpeg','.txt':'text/plain; charset=utf-8','.wasm':'application/wasm'};
const server=http.createServer(async(req,res)=>{
 try{let pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);if(pathname==='/')pathname='/index.html';const path=resolve(root,'.'+pathname);if(!path.startsWith(root+sep)){res.writeHead(403);res.end('Forbidden');return;}if(!(await stat(path)).isFile())throw new Error('Missing');const bytes=await readFile(path);res.writeHead(200,{'Content-Type':types[extname(path)]||'application/octet-stream','Cache-Control':'no-cache'});res.end(bytes);}
 catch{res.writeHead(404,{'Content-Type':'text/plain'});res.end('File not found');}
});
server.on('error',error=>{console.error(error.code==='EADDRINUSE'?`Port ${port} is already in use. Close the previous game terminal and start this copy again.`:error.message);process.exitCode=1;});
server.listen(port,'127.0.0.1',()=>{const url=`http://localhost:${port}`;console.log(`Sunward · The Hollow Bell\nOpen ${url}\nKeep this window open. Ctrl+C stops the game.\nProgress is saved in this browser on this address.`);if(process.platform==='win32')spawn('cmd.exe',['/d','/c','start','',url],{detached:true,stdio:'ignore',windowsHide:true}).unref();});
