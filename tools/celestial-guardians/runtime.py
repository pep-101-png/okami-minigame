"""Compile and exercise actual guardian/progression code with engine API doubles."""
from pathlib import Path
import xml.etree.ElementTree as ET,re,subprocess,os
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/celestial-guardians');old=R/'tools/spirit-charge-home/compile'
s=(R/'tools/celestial-guardians/EngineApiBase.cs.txt').read_text()
s=s.replace('public class EnemyDefinition:UnityEngine.Object{public string id;','public class EnemyDefinition:UnityEngine.Object{public string id,title;public int reward,xp;')
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {','public sealed partial class GameFlow:MonoBehaviour\n {public Remaster.CelestialTrials Celestial;public int Wave;')
s=s.replace('public class WolfInput{','public class WolfInput{public UnityEngine.InputSystem.InputAction TransformForm=new UnityEngine.InputSystem.InputAction();')
s=s.replace('public VisualFx Fx=new VisualFx();','public VisualFx Fx=new VisualFx();')
s=s.replace('public class VisualFx{','public class VisualFx{public UnityEngine.GameObject Boundary(UnityEngine.Vector3 c,float r)=>new UnityEngine.GameObject();')

def remove(text,label):
 a=text.index(label);b=text.index('{',a);level=1;c=b+1
 while level:
  if text[c]=='{':level+=1
  elif text[c]=='}':level-=1
  c+=1
 return text[:a]+text[c:]
s=s.replace('public class Material:Object{','public class Material:Object{public void SetVector(string name,Vector3 v){}')
s=s.replace('public class ParticleSystem:Object','public enum ParticleSystemStopBehavior{StopEmittingAndClear}public class ParticleSystem:Object')
s=s.replace('public void Emit(int count){}','public void Emit(int count){}public void Stop(bool child,ParticleSystemStopBehavior mode){}public void Play(){}')
s=s.replace('public struct MainModule{','public struct MainModule{public float startLifetime;')
s=s.replace('public struct VelocityOverLifetimeModule{','public struct ColorOverLifetimeModule{public bool enabled;}public ColorOverLifetimeModule colorOverLifetime=>new ColorOverLifetimeModule();public struct VelocityOverLifetimeModule{')
s=remove(s,'public class Transform:Object');s+='\nnamespace UnityEngine{'+(R/'tools/heaven-gate-trigger/TransformDouble.cs').read_text().replace('gameObject.GetComponent<T>();public T[] GetComponentsInChildren','gameObject.GetComponentInChildren<T>(b);public T[] GetComponentsInChildren')+'}'
s=s.replace('public static Quaternion Euler(Vector3 v)=>identity;public static Quaternion Euler(float a,float b,float c)=>identity;', 'public static Quaternion Euler(Vector3 v)=>Euler(v.x,v.y,v.z);public static Quaternion Euler(float a,float b,float c)=>Q(N.Quaternion.CreateFromYawPitchRoll(b*MathF.PI/180,a*MathF.PI/180,c*MathF.PI/180));')
s=s.replace('public static Quaternion LookRotation(Vector3 v)=>identity;', 'public static Quaternion LookRotation(Vector3 v)=>Euler(0,MathF.Atan2(v.x,v.z)*180/MathF.PI,0);')
s=s.replace('public static Quaternion LookRotation(Vector3 v)=>Euler(0,MathF.Atan2(v.x,v.z)*180/MathF.PI,0);','public static Quaternion LookRotation(Vector3 v)=>Euler(-MathF.Atan2(v.y,MathF.Sqrt(v.x*v.x+v.z*v.z))*180/MathF.PI,MathF.Atan2(v.x,v.z)*180/MathF.PI,0);')
s=s.replace('public static Vector3 operator *(Quaternion q,Vector3 v)=>v;', 'public static Vector3 operator *(Quaternion q,Vector3 v){var a=N.Vector3.Transform(new N.Vector3(v.x,v.y,v.z),q.NQ);return new Vector3(a.X,a.Y,a.Z);}')
s=s.replace('public T GetComponentInParent<T>()where T:class=>null;', 'public T GetComponentInParent<T>()where T:class{for(var p=transform;p!=null;p=p.parent){var c=p.gameObject?.GetComponent<T>();if(c!=null)return c;}return null;}')
s=s.replace('public T GetComponentInChildren<T>(bool b=false)where T:class=>null;', 'public T GetComponentInChildren<T>(bool b=false)where T:class=>gameObject.GetComponentInChildren<T>(b);')
s=s.replace('public T[] GetComponentsInChildren<T>(bool b=false)=>Array.Empty<T>();', 'public T[] GetComponentsInChildren<T>(bool b=false)=>gameObject.GetComponentsInChildren<T>(b);')
s=s.replace('public T GetComponentInChildren<T>(bool include=false)where T:class=>GetComponent<T>();', 'public T GetComponentInChildren<T>(bool include=false)where T:class{foreach(var o in created)if(o.transform.IsChildOf(transform)){var c=o.GetComponent<T>();if(c!=null)return c;}return null;}')
s=s.replace('public T[] GetComponentsInChildren<T>(bool b=false)=>renderers.Select(x=>(T)(object)x).ToArray();','public T[] GetComponentsInChildren<T>(bool b=false)=>created.Where(o=>o.transform.IsChildOf(transform)).SelectMany(o=>o.components.Values.Concat(o.renderers.Cast<object>())).OfType<T>().ToArray();')
s=s.replace('public static T Instantiate<T>(T x,Transform parent)where T:Object=>x;', 'public static T Instantiate<T>(T x,Transform parent)where T:Object=>GuardianEngine.Clone(x as GameObject,parent) as T;')
s=s.replace('public class CharacterController: Object{public bool enabled=true;public float radius,height;public Vector3 center;public void Move(Vector3 delta){}}', 'public class CharacterController: Object{public Transform transform;public bool enabled=true;public float radius,height;public Vector3 center;public void Move(Vector3 delta){if(enabled)transform.position+=delta;}}')
s=s.replace('components[typeof(T)]=c;StreetActorLifecycle.Added', 'if(c is CharacterController cc)cc.transform=transform;components[typeof(T)]=c;StreetActorLifecycle.Added')
s=remove(s,'public sealed class NativePaintedRig:IDisposable')
s+='\n'+(R/'tools/celestial-guardians/EngineModels.cs').read_text()
s=s.replace('public void Hurt(float damage,Vector3 away){}','public int hurtCount;public void Hurt(float damage,Vector3 away){hurtCount++;Health=MathF.Max(0,Health-damage);}')
s=s.replace('public void Projectile(Vector3 p,Vector3 d,float damage,bool flame=false){}','public int shotCount;public void Projectile(Vector3 p,Vector3 d,float damage,bool flame=false){shotCount++;}')
s=s.replace('public void Notify(string s){}','public string notice;public void Notify(string s){notice=s;}')
s=s.replace('public void ClearEnemies(){clears++;}','public void ClearEnemies(){clears++;Enemies.Clear();}')
s=s.replace('public bool Blocked,InTrial,BossTrial,waiting;', 'public bool InTrial,BossTrial,waiting;public bool Blocked=>CinematicActive || Panel!="";')
s=s.replace('cinematicFlag || (Presentation', 'cinematicFlag || (Celestial && Celestial.Playing) || (Transformation && Transformation.Playing) || (Presentation')

s=s.replace('{foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories)){if(typeof(T)==typeof(Material)', '{if(typeof(T)==typeof(AudioClip)){foreach(var folder in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories))foreach(var ext in new[]{".wav",".ogg"}){var path=Path.Combine(folder,name+ext);if(File.Exists(path)){var b=File.ReadAllBytes(path);float length=ext==".wav"?(b.Length-44f)/Math.Max(1,BitConverter.ToInt32(b,28)):60;return new AudioClip{name=name,length=length} as T;}}return null;}foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories)){if(typeof(T)==typeof(Material)')
(W/'RuntimeDoubles.cs').write_text(s)
x=ET.parse(old/'Compile.csproj').getroot();props={e.tag:e.text for pg in x.findall('PropertyGroup') for e in pg};paths=[]
for el in x.findall('ItemGroup/Compile'):
 p=el.get('Include')
 if p=='$(SemanticDoubles)' or p.endswith('Tests.cs'):continue
 if p.startswith('$('):p=props[p[2:-1]].replace('$(MSBuildThisFileDirectory)',str(old)+'/')
 paths.append(str((old/p).resolve()))
paths.extend(str(p) for p in (R/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts').glob('Celestial*.cs') if str(p) not in paths)
paths += [str(R/'Sunward-Unity/Assets/Sunward/Scripts/GameFlow.Celestial.cs'),str(W/'RuntimeDoubles.cs'),str(R/'tools/celestial-guardians/GuardianTests.cs')]
(W/'Runtime.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework><OutputType>Exe</OutputType><EnableDefaultCompileItems>false</EnableDefaultCompileItems><NoWarn>0649;0169;0414</NoWarn></PropertyGroup><ItemGroup>'+''.join('<Compile Include="'+p+'"/>' for p in dict.fromkeys(paths))+'</ItemGroup></Project>')
exe='/workspace/work/tundra-beads/dotnet/dotnet';env=dict(os.environ,DOTNET_CLI_HOME='/workspace/work/tundra-beads/dotnet-home');subprocess.run([exe,'build',str(W/'Runtime.csproj'),'--nologo'],env=env,check=True)
subprocess.run([exe,str(W/'bin/Debug/net8.0/Runtime.dll'),str(R/'Sunward-Unity/Assets'),str(W)],env=env,check=True)

import hashlib,json,datetime
inputs=list((R/'Sunward-Unity/Assets/Sunward/Scripts').glob('*.cs'))+list((R/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts').glob('*.cs'))+list((R/'Sunward-Unity/Assets/OkamiRemaster/Player').glob('*.cs'))
inputs += [p for p in (R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami').glob('guardian-*/*') if p.is_file()]
inputs += [R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/palace-shiranui/Poses.bytes',R/'Sunward-Unity/Assets/OkamiRemaster/Original/Shaders/OriginalCelestialCourt.shader',R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/Effects/CelestialCourt.mat']
receipt=dict(scope='Actual guardian/OriginalActor, native player transformation and progression drivers with Unity API doubles. Scripted target and flat collision floor; not Unity Play Mode.',createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceHashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},captureHashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in W.glob('*runtime.json')})
(W/'runtime-receipt.json').write_text(json.dumps(receipt,indent=2))
