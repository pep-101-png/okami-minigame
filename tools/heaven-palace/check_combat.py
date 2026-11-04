from pathlib import Path
import re,xml.etree.ElementTree as ET,subprocess,argparse,tempfile,os
parser=argparse.ArgumentParser();parser.add_argument('--dotnet',default='dotnet');parser.add_argument('--doubles',type=Path,required=True);parser.add_argument('--out',type=Path,default=Path(tempfile.gettempdir())/'SunwardHeavenCombat');args=parser.parse_args();R=Path(__file__).resolve().parents[2];W=args.out;W.mkdir(exist_ok=True,parents=True);s=args.doubles.read_text()
def remove(s,label):
 start=s.index(label);b=s.index('{',start);n=1;i=b+1
 while n:
  if s[i]=='{':n+=1
  if s[i]=='}':n-=1
  i+=1
 return s[:start]+s[i:]
s=remove(s,'public class WolfCombat:');s=remove(s,'public static class OriginalWeaponCatalog{')
s=s.replace('public class Object\n {','public class Object\n {public static T Instantiate<T>(T a)where T:Object=>a;')
s+='\nnamespace UnityEngine{public class CreateAssetMenuAttribute:System.Attribute{public string menuName;}}'
s=s.replace('public class VisualFx{', 'public class VisualFx{public void SundialOrbit(UnityEngine.Vector3 p,bool h){}public void Impact(UnityEngine.Vector3 p,UnityEngine.Color c){}')
s=s.replace('public class WolfInput{', 'public class WolfInput{public UnityEngine.InputSystem.InputAction Heavy=new UnityEngine.InputSystem.InputAction(),Bark=new UnityEngine.InputSystem.InputAction(),Switch=new UnityEngine.InputSystem.InputAction();')
s=s.replace('public sealed partial class WolfMotor:MonoBehaviour\n {', 'public sealed partial class WolfMotor:MonoBehaviour\n {public bool Dodging;public void Push(Vector3 p){transform.position+=p;}')
s=s.replace('QueryTriggerInteraction{Ignore}', 'QueryTriggerInteraction{Ignore,Collide}')
s=s.replace('public static class Physics{','public static class Physics{public static int OverlapSphereNonAlloc(Vector3 p,float r,Collider[] c,int mask,QueryTriggerInteraction q)=>0;public static int OverlapCapsuleNonAlloc(Vector3 a,Vector3 b,float r,Collider[] c,int mask,QueryTriggerInteraction q)=>0;public static bool Linecast(Vector3 a,Vector3 b,int mask,QueryTriggerInteraction q)=>false;')
s=s.replace('public class Collider:Object{', 'public class Collider:Object{public T GetComponentInParent<T>()where T:class=>null;')
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {', 'public sealed partial class GameFlow:MonoBehaviour\n {public void HitPause(float t){}')
s=s.replace('public bool IsPressed()=>false;', 'public bool held;public bool IsPressed()=>held;')
s=s.replace('public class TrainingDummy:UnityEngine.MonoBehaviour{', 'public class TrainingDummy:UnityEngine.MonoBehaviour{public void Strike(bool sparks=true){}')
(W/'CombatDoubles.cs').write_text(s)
project=ET.parse(R/'tools/spirit-charge-home/compile/Compile.csproj');root=project.getroot();root.find('PropertyGroup/OutputType').text='Exe'
for group in root.findall('ItemGroup'):
 for c in list(group):
  p=c.get('Include','')
  if p.endswith('Tests.cs') or 'SemanticDoubles' in p:group.remove(c);continue
  p=p.replace('$(NativeBodySource)',str(R/'Sunward-Unity/Assets/OkamiRemaster/Player/NativeAmaterasu.cs')).replace('$(OrbitSource)',str(R/'Sunward-Unity/Assets/Sunward/Scripts/OrbitCamera.cs')).replace('$(StreetSource)',str(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/VillageStreetPlay.cs')).replace('$(WaterSource)',str(R/'Sunward-Unity/Assets/Sunward/Scripts/WaterContact.cs'))
  if not p.startswith('/'):p=str((R/'tools/spirit-charge-home/compile'/p).resolve())
  c.set('Include',p)
group=root.find('ItemGroup');ET.SubElement(group,'Compile',Include=str(W/'CombatDoubles.cs'))
for p in ['Sunward-Unity/Assets/Sunward/Scripts/WolfCombat.cs','Sunward-Unity/Assets/Sunward/Scripts/WeaponDefinition.cs','Sunward-Unity/Assets/Sunward/Scripts/AttackSequence.cs','Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/OriginalWeaponCatalog.cs']:ET.SubElement(group,'Compile',Include=str(R/p))
ET.SubElement(group,'Compile',Include=str(R/'tools/heaven-palace/CombatTests.cs'));project.write(W/'Combat.csproj')
run=subprocess.run([args.dotnet,'run','--project',str(W/'Combat.csproj'),'--',str(R/'Sunward-Unity/Assets')],capture_output=True,text=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'));print(run.stdout);print(run.stderr);run.check_returncode()
