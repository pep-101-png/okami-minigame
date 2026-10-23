"""Read-only inspection of the user's supplied Okami HD archive; no Unity import."""
from pathlib import Path
import zipfile,struct,re,json,collections,hashlib,sys
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
KEY=b'YaKiNiKuM2rrVrPJpGMkfe3EK4RbpbHw' # Documented game-format key, not an account credential.
def swap32(b):return np.frombuffer(b,dtype='<u4').byteswap().tobytes()
def decrypt(b):
 assert len(b)%8==0
 c=Cipher(algorithms.Blowfish(KEY),modes.ECB())
 d=swap32(c.decryptor().update(swap32(b)))
 assert swap32(c.encryptor().update(swap32(d)))==b
 return d

def entries(b):
 if len(b)<12:return []
 n=struct.unpack_from('<I',b)[0]
 if not 0<n<1024 or 4+n*8>len(b):return []
 offsets=struct.unpack_from('<'+'I'*n,b,4);types=[b[4+n*4+i*4:8+n*4+i*4].rstrip(b'\0') for i in range(n)]
 if any(x and (x<4+n*8 or x>=len(b)) for x in offsets) or any(not re.fullmatch(rb'[A-Z0-9]{0,4}',x) for x in types):return []
 nonzero=[x for x in offsets if x]
 if nonzero!=sorted(nonzero):return []
 result=[]
 for i,(offset,kind) in enumerate(zip(offsets,types)):
  if not offset:continue
  following=[x for x in offsets[i+1:] if x>offset];end=following[0] if following else len(b)
  result.append((i,kind.decode(),offset,b[offset:end]))
 return result

def inspect(source,out):
 out.mkdir(parents=True,exist_ok=True);rows=[];textures=[];models=[]
 def recurse(b,label,depth=0):
  if depth>12:return
  for i,kind,offset,data in entries(b):
   path=label+'/'+str(i)+'.'+kind
   rows.append({'path':path,'type':kind,'bytes':len(data)})
   if kind in ('MD','SCR','MEH','MDB'):models.append({'path':path,'bytes':len(data),'header':data[:16].hex()})
   recurse(data,path,depth+1)
 with zipfile.ZipFile(source) as z:
  for member in z.infolist():
   if member.is_dir():continue
   data=decrypt(z.read(member));recurse(data,member.filename)
   # Standard DDS headers inside nested packages can be independently identified.
   for match in re.finditer(rb'DDS ',data):
    i=match.start()
    if i+128>len(data) or struct.unpack_from('<I',data,i+4)[0]!=124:continue
    h,w=struct.unpack_from('<II',data,i+12);mips=max(1,struct.unpack_from('<I',data,i+28)[0]);fourcc=data[i+84:i+88]
    if not(0<w<=8192 and 0<h<=8192):continue
    item={'file':member.filename,'offset':i,'width':w,'height':h,'fourcc':fourcc.decode('ascii',errors='replace'),'mips':mips}
    if fourcc in [b'DXT1',b'DXT3',b'DXT5']:
     size=128+sum(max(1,(max(1,w>>j)+3)//4)*max(1,(max(1,h>>j)+3)//4)*(8 if fourcc==b'DXT1' else 16) for j in range(mips))
     if i+size<=len(data):
      payload=data[i:i+size];digest=hashlib.sha256(payload).hexdigest();item['sha256']=digest
      p=out/(digest[:16]+'.dds')
      if not p.exists():p.write_bytes(payload)
    textures.append(item)
 counts=collections.Counter(r['type'] for r in rows)
 report={'archive':Path(source).name,'zipEntries':len(zipfile.ZipFile(source).infolist()),'decryption':'Blowfish ECB with 32-bit word swapping; every member round-trip verified','nestedTypes':dict(counts),'modelEntries':models,'ddsTextures':textures,'uniqueExtractedDDS':len(list(out.glob('*.dds'))),'houseIdentification':'Not established by filenames; visual texture/model inspection required','sourceFormatReference':'https://github.com/allogic/Nippon/blob/main/Common/Archive/Archive.cpp','importedIntoUnity':False}
 (out/'inspection.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('modelEntries','ddsTextures')},indent=2))
if __name__=='__main__':inspect(Path(sys.argv[1]),Path(sys.argv[2]))
