"""Compile the real combat/catalogue plus cinematic and progression code; engine APIs are doubles."""
from pathlib import Path
import re,xml.etree.ElementTree as ET,subprocess,os
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/heaven-gate-trigger');old=R/'tools/spirit-charge-home/compile';s=(W/'Doubles.cs').read_text()
def remove(text,label):
 a=text.index(label);b=text.index('{',a);level=1;c=b+1
 while level:
  if text[c]=='{':level+=1
  elif text[c]=='}':level-=1
  c+=1
 return text[:a]+text[c:]
s=remove(s,'public class WolfCombat:Object');s=remove(s,'public static class OriginalWeaponCatalog');s=remove(s,'public void Reward(EnemyBrain b)')
flow=(R/'Sunward-Unity/Assets/Sunward/Scripts/GameFlow.cs').read_text();a=flow.index('public void Reward(EnemyBrain e)');b=flow.index('{',a);level=1;c=b+1
while level:
 if flow[c]=='{':level+=1
 elif flow[c]=='}':level-=1
 c+=1
s+='\nnamespace Sunward{using UnityEngine;public sealed partial class GameFlow{'+flow[a:c]+'}}'
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {','public sealed partial class GameFlow:MonoBehaviour\n {public Remaster.ShiranuiUltimate Ultimate;')
s=s.replace('cinematicFlag || (Presentation','cinematicFlag || (Ultimate && Ultimate.Playing) || (Presentation')
s=s.replace('public class EnemyDefinition:UnityEngine.Object{','public class EnemyDefinition:UnityEngine.Object{public int reward=1,xp=1;')
s=s.replace('public class WolfInput{','public class WolfInput{public UnityEngine.InputSystem.InputAction Switch=new UnityEngine.InputSystem.InputAction(),Bark=new UnityEngine.InputSystem.InputAction(),Heavy=new UnityEngine.InputSystem.InputAction();')
s=s.replace('public sealed partial class WolfMotor:MonoBehaviour\n {','public sealed partial class WolfMotor:MonoBehaviour\n {public bool Dodging;public void Push(Vector3 d){}')
s=s.replace('public class VisualFx','public class VisualFx')
s=s.replace('public static class Physics{','public static class Physics{public static int OverlapSphereNonAlloc(Vector3 p,float radius,Collider[] c,int layer,QueryTriggerInteraction q)=>0;public static int OverlapCapsuleNonAlloc(Vector3 a,Vector3 b,float radius,Collider[] c,int layer,QueryTriggerInteraction q)=>0;')
s=s.replace('public enum QueryTriggerInteraction{Ignore}','public enum QueryTriggerInteraction{Ignore,Collide}')
s=s.replace('public class Collider:','public class Collider:')
s=s.replace('public class ScriptableObject:Object{','public class CreateAssetMenuAttribute:System.Attribute{public string menuName;}public class ScriptableObject:Object{')
s=s.replace('public static T Instantiate<T>(T x,Transform parent)','public static T Instantiate<T>(T x)where T:Object=>(T)x.GetType().GetMethod("MemberwiseClone",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).Invoke(x,null);public static T Instantiate<T>(T x,Transform parent)')
s=s.replace('public int MaxHealth=>120+(Spa?Spa.Bonus:0);','public int MaxHealth=>ProgressionRules.MaxHp(Profile)+(Spa?Spa.Bonus:0)+Sunward.Remaster.HomeBlessings.HealthBonus(Profile,Sunward.Remaster.HomeBlessings.Now);')
s=s.replace('public class VisualFx{','public class VisualFx{public void SundialOrbit(UnityEngine.Vector3 p,bool h){}public void Impact(UnityEngine.Vector3 p,UnityEngine.Color c){}')

s=s.replace('public static class Physics{','public static class Physics{public static bool Linecast(Vector3 a,Vector3 b,int layer,QueryTriggerInteraction q)=>false;')
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {','public sealed partial class GameFlow:MonoBehaviour\n {public void HitPause(float t){}')
s=s.replace('public class TrainingDummy:','public class TrainingDummy:')
s=s.replace('public class TrainingDummy:UnityEngine.MonoBehaviour{','public class TrainingDummy:UnityEngine.MonoBehaviour{public void Strike(bool sound=true){}')
s=s.replace('public Vector3 WorldToScreenPoint(Vector3 p)=>p;', 'public static System.Func<Vector3,Vector3> Projection=p=>p;public Vector3 WorldToScreenPoint(Vector3 p)=>Projection(p);')
s=s.replace('public void SetPosition(int i,Vector3 p){}','public System.Collections.Generic.Dictionary<int,Vector3> positions=new System.Collections.Generic.Dictionary<int,Vector3>();public void SetPosition(int i,Vector3 p){positions[i]=p;}')
# Run the real transfer and teleport routines, not a return-call counter.
for label in ['public void ReturnHome()','public void ClearEnemies()','public void ClearProjectiles()','public void Close()','public void Teleport(Vector3 p)']:
 s=remove(s,label)
def method(text,label):
 a=text.index(label);b=text.index('{',a);depth=1;c=b+1
 while depth:
  if text[c]=='{':depth+=1
  elif text[c]=='}':depth-=1
  c+=1
 return text[a:c]
for label in ['public void ReturnHome()','void ClearEnemies()','void ClearProjectiles()','public void Close()']:
 s+='\nnamespace Sunward{using UnityEngine;public sealed partial class GameFlow{'+method(flow,label)+'}}'
motor=(R/'Sunward-Unity/Assets/Sunward/Scripts/WolfMotor.cs').read_text()
s+='\nnamespace Sunward{using UnityEngine;public sealed partial class WolfMotor{'+method(motor,'public void Teleport(Vector3 point)')+'}}'
s=s.replace('public int TeleportRevision;','public int TeleportRevision{get;private set;}')
# Model real parent-space transforms for the gate attachment check.
s=remove(s,'public class Transform:Object')
s+='\nnamespace UnityEngine{'+(R/'tools/heaven-gate-trigger/TransformDouble.cs').read_text()+'}'
s=s.replace('public static Quaternion Euler(Vector3 v)=>identity;public static Quaternion Euler(float a,float b,float c)=>identity;', 'public static Quaternion Euler(Vector3 v)=>Euler(v.x,v.y,v.z);public static Quaternion Euler(float a,float b,float c)=>Q(N.Quaternion.CreateFromYawPitchRoll(b*MathF.PI/180,a*MathF.PI/180,c*MathF.PI/180));')
s=s.replace('public static Vector3 operator *(Quaternion q,Vector3 v)=>v;', 'public static Vector3 operator *(Quaternion q,Vector3 v){var a=N.Vector3.Transform(new N.Vector3(v.x,v.y,v.z),q.NQ);return new Vector3(a.X,a.Y,a.Z);}')
(W/'RuntimeDoubles.cs').write_text(s)
x=ET.parse(old/'Compile.csproj').getroot();props={e.tag:e.text for pg in x.findall('PropertyGroup') for e in pg};paths=[]
for el in x.findall('ItemGroup/Compile'):
 path=el.get('Include')
 if path=='$(SemanticDoubles)' or path.endswith('Tests.cs'):continue
 if path.startswith('$('):path=props[path[2:-1]].replace('$(MSBuildThisFileDirectory)',str(old)+'/')
 paths.append(str((old/path).resolve()))
for name in ['WolfCombat','WeaponDefinition','AttackSequence']:paths.append(str(R/'Sunward-Unity/Assets/Sunward/Scripts'/f'{name}.cs'))
paths.append(str(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/OriginalWeaponCatalog.cs'))
paths.extend([str(W/'RuntimeDoubles.cs'),str(R/'tools/heaven-gate-trigger/PortalTests.cs')]);project='<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework><OutputType>Exe</OutputType><EnableDefaultCompileItems>false</EnableDefaultCompileItems><NoWarn>0649;0169;0414</NoWarn></PropertyGroup><ItemGroup>'+''.join('<Compile Include="'+p+'"/>' for p in paths)+'</ItemGroup></Project>';(W/'Runtime.csproj').write_text(project)
exe='/workspace/work/tundra-beads/dotnet/dotnet';env=dict(os.environ,DOTNET_CLI_HOME='/workspace/work/tundra-beads/dotnet-home',DOTNET_CLI_TELEMETRY_OPTOUT='1');subprocess.run([exe,'build',str(W/'Runtime.csproj'),'--nologo'],check=True,env=env);subprocess.run([exe,str(W/'bin/Debug/net8.0/Runtime.dll'),str(R/'Sunward-Unity/Assets')],check=True,env=env)
