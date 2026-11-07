from pathlib import Path
import subprocess,hashlib,json,zipfile,os,tempfile,re
root=Path('/workspace/sunward-tundra-desktop');work=Path('/workspace/work/heaven-gate-trigger');base='1ad16ca739d2a1f2ac3be3faabdedd9e8e00912d'
def git(*args,env=None,data=None):return subprocess.check_output(['git',*args],cwd=root,env=env,input=data)
source=git('rev-parse','HEAD').decode().strip();paths=[p.decode() for p in git('diff','--name-only','-z',base,source,'--','Sunward-Unity/Assets').split(b'\0') if p];assert not git('diff','--name-only','--diff-filter=D',base,source,'--','Sunward-Unity/Assets').strip();files=[];payload=[]
for path in paths:
 data=(root/path).read_bytes();blob=git('show',source+':'+path);assert not data.startswith(b'version https://git-lfs.github.com/spec/v1'),path
 if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
  oid=re.search(rb'oid sha256:(\w+)',blob)[1].decode();size=int(re.search(rb'size (\d+)',blob)[1]);assert hashlib.sha256(data).hexdigest()==oid and len(data)==size,path
 else:assert blob==data,path
 name=str(Path(path).relative_to('Sunward-Unity'));assert name.startswith('Assets/');payload.append((name,data));files.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
p=work/'Sunward-Heaven-Portal-Repair-2026-11-07.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,data in sorted(payload):z.writestr(name,data)
with zipfile.ZipFile(p) as z:assert z.testzip() is None and all(n.startswith('Assets/') for n in z.namelist()) and not any('report' in n.lower() or 'readme' in n.lower() for n in z.namelist())
r=dict(sourceCommit=source,baseline=base,files=len(files),bytes=p.stat().st_size,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest());(work/'package-result.json').write_text(json.dumps(dict(**r,entries=files),indent=2))
tmp=Path(tempfile.mkdtemp(prefix='sunward-spirit-delivery-',dir='/tmp'));env=dict(os.environ,GIT_INDEX_FILE=str(tmp/'index'));git('read-tree',source,env=env);attrs=(root/'.gitattributes').read_text();rule='Downloads/*.zip -filter -diff -merge -text'
if rule not in attrs:attrs+='\n'+rule+'\n'
filename='Downloads/'+p.name
for name,data in [(filename,p.read_bytes()),('.gitattributes',attrs.encode())]:
 sha=git('hash-object','-w','--stdin',env=env,data=data).decode().strip();git('update-index','--add','--cacheinfo','100644,'+sha+','+name,env=env)
tree=git('write-tree',env=env).decode().strip();commit=git('commit-tree',tree,'-p',source,env=env,data=b'Publish cumulative Assets update with gate-owned heaven return repair\n').decode().strip();branch='delivery/heaven-portal-repair-20261107';git('update-ref','refs/heads/'+branch,commit,env=env);r.update(deliveryCommit=commit,deliveryBranch=branch,rawUrl='https://raw.githubusercontent.com/pep-101-png/okami-minigame/'+commit+'/'+filename,downloadUrl='https://github.com/pep-101-png/okami-minigame/blob/'+commit+'/'+filename+'?raw=true');(work/'delivery-result.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
