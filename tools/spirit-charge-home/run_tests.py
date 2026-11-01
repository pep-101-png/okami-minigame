"""Actual native driver and exact return/teleport methods, with explicit engine doubles."""
import argparse,os,re,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--dotnet',default='dotnet');p.add_argument('--legacy-barrier-negative-control',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2];assets=root/'Sunward-Unity/Assets'
def method(path,signature):
    s=(subprocess.check_output(['git','show','8adf22c2d21126ee66f48246bb9308c83cea5368:Sunward-Unity/Assets/'+str(path)],cwd=root).decode() if args.legacy_barrier_negative_control and str(path)=='Sunward/Scripts/GameFlow.cs' and signature!='void ClearBarrier()' else (assets/path).read_text());start=s.index(signature);body=s.index('{',start);depth=1;i=body+1
    while depth:
        if s[i]=='{':depth+=1
        elif s[i]=='}':depth-=1
        i+=1
    return s[start:i]
ret=method(Path('Sunward/Scripts/GameFlow.cs'),'public void ReturnHome()')+'\n'+method(Path('Sunward/Scripts/GameFlow.cs'),'public void Finish(bool win)')+'\n'+method(Path('Sunward/Scripts/GameFlow.cs'),'void ClearBarrier()');teleport=method(Path('Sunward/Scripts/WolfMotor.cs'),'public void Teleport(Vector3 point)')+'\n'+method(Path('Sunward/Scripts/WolfMotor.cs'),'public void StopMotion()')
audio='\n'.join(method(Path('Sunward/Scripts/ValleyAudio.cs'),sig) for sig in ['public void TundraAttack(bool charged,bool heavy)','public void TundraContact()','public void StopTundra()','public void TransformationVoice()','public void TransformationBurst()','public void StopTransformation()'])
camera='\n'.join(method(Path('Sunward/Scripts/OrbitCamera.cs'),sig) for sig in ['public void BeginCinematic()','public void CinematicFrame(Vector3 point,float angle,float elevation,float range,float fov)','public void EndCinematic()','public void ReturnCinematic(float blend)'])
near=re.search(r'bool near=([^;]+);',(assets/'OkamiRemaster/Original/Scripts/LowerArena.cs').read_text())[1]
with tempfile.TemporaryDirectory(prefix='sunward-spirit-tests-') as temp:
    fixture=Path(temp)/'Methods.cs';fixture.write_text('using UnityEngine;using Unity.Cinemachine;\nnamespace Sunward { public sealed partial class GameFlow { '+ret+' } public sealed partial class WolfMotor { '+teleport+' } public sealed partial class ValleyAudio { '+audio+' } public partial class OrbitCamera { '+camera+' }}\nnamespace Sunward.Remaster { public static partial class LowerArena {public static bool Near(Vector3 p,Transform mirror){return '+near+';} }}')
    command=[args.dotnet,'run','--project',str(root/'tools/spirit-charge-home/tests/Tests.csproj'),'-p:MethodFixtures='+str(fixture),'--',str(assets)]
    if args.legacy_barrier_negative_control:
        result=subprocess.run(command,cwd=root,capture_output=True,text=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'))
        assert result.returncode!=0 and 'NullReferenceException' in result.stderr and 'ReturnHome' in result.stderr,result.stdout+result.stderr
        print('Negative control reproduces the original ReturnHome NullReferenceException with a meshless boundary')
    else:subprocess.run(command,cwd=root,check=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'))
