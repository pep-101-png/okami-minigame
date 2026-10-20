from pathlib import Path
import json,zipfile,hashlib
r=Path(__file__).resolve().parents[1]
code=['Assets/Editor/MarketTreeCleanup.cs','Assets/Editor/VisualRemakeBuilder.cs','Assets/Sunward/Scripts/MarketTreeRules.cs','Assets/Sunward/Scripts/EnvironmentReviewState.cs']
names=code+[p+'.meta'for p in code]+['Review/MARKET-TREE-FIX.md','Review/market-tree-portable-tests.txt']
out=r/'Releases/Sunward-Unity-Market-Tree-Fix.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for name in names:z.write(r/name,name)
 z.writestr('START-HERE.txt',(r/'Review/MARKET-TREE-FIX.md').read_text())
with zipfile.ZipFile(out)as z:
 assert z.testzip()is None
 for name in names:assert z.read(name)==(r/name).read_bytes()
 assert not any(name.endswith(('.fbx','.png','.unity','.anim','.controller'))for name in z.namelist())
report={'file':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':names,'target':'Scene-root Cherry_A / Cherry_A(Clone) / Cherry_A_Mesh / Cherry_A_Mesh_MeshPart0 and MeshPart1','native_unity_tested':False}
(r/'Releases/market-tree-fix.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))
