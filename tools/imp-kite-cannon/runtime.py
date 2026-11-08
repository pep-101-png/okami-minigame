"""Exercise actual imp state machine/pose driver. Engine API doubles, not Unity Play Mode."""
from pathlib import Path
import re,xml.etree.ElementTree as ET,subprocess,os,json,hashlib,datetime
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/imp-kite-cannon');old=R/'tools/spirit-charge-home/compile'
for stale in W.glob('*-runtime.json'):stale.unlink()
(W/'runtime-receipt.json').unlink(missing_ok=True)
s=(W/'Doubles.cs').read_text()
def remove(text,label):
 a=text.index(label);b=text.index('{',a);level=1;c=b+1
 while level:
  if text[c]=='{':level+=1
  elif text[c]=='}':level-=1
  c+=1
 return text[:a]+text[c:]
s=remove(s,'public class Transform:Object');s+='\nnamespace UnityEngine{'+(R/'tools/heaven-gate-trigger/TransformDouble.cs').read_text()+'}'
s=s.replace('public static Quaternion Euler(Vector3 v)=>identity;public static Quaternion Euler(float a,float b,float c)=>identity;', 'public static Quaternion Euler(Vector3 v)=>Euler(v.x,v.y,v.z);public static Quaternion Euler(float a,float b,float c)=>Q(N.Quaternion.CreateFromYawPitchRoll(b*MathF.PI/180,a*MathF.PI/180,c*MathF.PI/180));')
s=s.replace('public static Quaternion LookRotation(Vector3 v)=>identity;', 'public static Quaternion LookRotation(Vector3 v)=>Euler(0,MathF.Atan2(v.x,v.z)*180/MathF.PI,0);')
s=s.replace('public static Vector3 operator *(Quaternion q,Vector3 v)=>v;', 'public static Vector3 operator *(Quaternion q,Vector3 v){var a=N.Vector3.Transform(new N.Vector3(v.x,v.y,v.z),q.NQ);return new Vector3(a.X,a.Y,a.Z);}')
s=s.replace('public T GetComponentInParent<T>()where T:class=>null;', 'public T GetComponentInParent<T>()where T:class{for(var p=transform;p!=null;p=p.parent){var c=p.gameObject?.GetComponent<T>();if(c!=null)return c;}return null;}')
s=s.replace('public float radius,height;public Vector3 center;public void Move(Vector3 delta){}', 'public static Transform Target;public Transform transform;public float radius,height;public Vector3 center;public void Move(Vector3 delta){if(!enabled || !transform)return;var p=transform.position+delta;if(Target && center.y-height*.5f<1.15f){var away=p-Target.position;away.y=0;if(away.magnitude<radius+.35f && away.magnitude>.0001f){var fit=Target.position+away.normalized*(radius+.35f);p.x=fit.x;p.z=fit.z;}}transform.position=p;}')
s=s.replace('public void Hurt(float damage,Vector3 away){}','public int hurtCount;public void Hurt(float damage,Vector3 away){hurtCount++;}')
s=s.replace('public void Projectile(Vector3 p,Vector3 d,float damage,bool flame=false){}','public int shots;public void Projectile(Vector3 p,Vector3 d,float damage,bool flame=false){shots++;}')
# Exercise actual Init, including immediate prefab Awake, rather than manually
# installing a native actor or mirroring the production capsule dimensions.
s=s.replace('public static T Instantiate<T>(T x,Transform parent)where T:Object=>x;', 'public static T Instantiate<T>(T x,Transform parent)where T:Object{if(x is GameObject source){var copy=new GameObject(source.name);copy.transform.SetParent(parent,false);var old=source.GetComponent<Sunward.Remaster.OriginalActor>();if(old!=null){var actor=copy.AddComponent<Sunward.Remaster.OriginalActor>();foreach(var f in typeof(Sunward.Remaster.OriginalActor).GetFields(System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.DeclaredOnly))f.SetValue(actor,f.GetValue(old));typeof(Sunward.Remaster.OriginalActor).GetMethod("Awake",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance).Invoke(actor,null);}return copy as T;}return x;}')
s=s.replace('if(c is MonoBehaviour m)m.gameObject=this;', 'if(c is MonoBehaviour m)m.gameObject=this;if(c is CharacterController controller)controller.transform=transform;')
# Recreate only the source bone hierarchy and inspected mesh mask. No mesh rendering here.
s=remove(s,'public sealed class NativePaintedRig:IDisposable')
s+='''
namespace Sunward.Remaster{using UnityEngine;public sealed class NativePaintedRig:IDisposable{
 public GameObject Root=new GameObject();public Transform[] Bones;
 public NativePaintedRig(string resource,Transform parent){Root.transform.SetParent(parent,false);using var doc=System.Text.Json.JsonDocument.Parse(Resources.Load<TextAsset>(resource+"/Model").text);var j=doc.RootElement;var b=j.GetProperty("bones");Bones=new Transform[b.GetArrayLength()+1];Bones[0]=new GameObject().transform;Bones[0].SetParent(Root.transform,false);for(int i=0;i<b.GetArrayLength();i++){var t=new GameObject().transform;Bones[i+1]=t;t.SetParent(Bones[b[i].GetProperty("parent").GetInt32()+1],false);var p=b[i].GetProperty("position");t.localPosition=new Vector3(p[0].GetSingle(),p[1].GetSingle(),p[2].GetSingle());}var groups=j.GetProperty("visibleGroups").EnumerateArray().Select(x=>x.GetInt32()).ToArray();Root.renderers=j.GetProperty("parts").EnumerateArray().Where(p=>groups.Contains(int.Parse(p.GetProperty("name").GetString().Split('-')[1]))).Select(p=>new SkinnedMeshRenderer{enabled=true,sharedMaterial=new Material((Material)null),sharedMesh=new Mesh{name=p.GetProperty("name").GetString(),vertexCount=p.GetProperty("positions").GetArrayLength()/3}}).ToArray();}
 public void Dispose(){}
}}
'''
# Audio API stand-in records scheduling of real World calls and releases finished voices.
s=s.replace('public class AudioSource:Object{','public class AudioSource:Object{public static System.Collections.Generic.List<AudioSource> All=new();public static System.Collections.Generic.List<object> Events=new();public float started;public AudioSource(){All.Add(this);}')
s=s.replace('public void Play(){isPlaying=true;plays++;}', 'public void Play(){isPlaying=true;plays++;started=Time.time;if(clip!=null)Events.Add(new{time=Time.time,cue=clip.name,gain=volume,position=new[]{transform.position.x,transform.position.y,transform.position.z}});}')
s=s.replace('{foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories)){if(typeof(T)==typeof(Material)', '{if(typeof(T)==typeof(AudioClip)){foreach(var folder in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories))foreach(var ext in new[]{".wav",".ogg"}){var path=Path.Combine(folder,name+ext);if(File.Exists(path)){var b=File.ReadAllBytes(path);float length=ext==".wav"?(b.Length-44f)/Math.Max(1,BitConverter.ToInt32(b,28)):60;return new AudioClip{name=name,length=length} as T;}}return null;}foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories)){if(typeof(T)==typeof(Material)')
s=s.replace('hit=new RaycastHit();return false;}public static int syncs;', 'return CannonFixture.Cast(a,r,d,out hit,n,mask);}public static int syncs;')
s=s.replace('gain=volume,position=', 'gain=volume,pitch=pitch,range=maxDistance,minDistance=minDistance,listener=new[]{CharacterController.Target.position.x,CharacterController.Target.position.y,CharacterController.Target.position.z},position=')
s=s.replace('public static void Destroy(Object x,float delay){Destroy(x);}', 'public static void Destroy(Object x,float delay){CannonFixture.Delay(x,delay);}')
s=remove(s,'public void ClearProjectiles()')
flow=(R/'Sunward-Unity/Assets/Sunward/Scripts/GameFlow.cs').read_text();a=flow.index('        void ClearProjectiles()');b=flow.index('\n        public void Reward',a)
s+='\nnamespace Sunward{using UnityEngine;public sealed partial class GameFlow{'+flow[a:b]+'}}'
(W/'RuntimeDoubles.cs').write_text(s)
x=ET.parse(old/'Compile.csproj').getroot();props={e.tag:e.text for pg in x.findall('PropertyGroup') for e in pg};paths=[]
for el in x.findall('ItemGroup/Compile'):
 p=el.get('Include')
 if p=='$(SemanticDoubles)' or p.endswith('Tests.cs'):continue
 if p.startswith('$('):p=props[p[2:-1]].replace('$(MSBuildThisFileDirectory)',str(old)+'/')
 paths.append(str((old/p).resolve()))
paths.extend([str(W/'RuntimeDoubles.cs'),str(R/'tools/imp-kite-cannon/ImpTests.cs')]);(W/'Runtime.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework><OutputType>Exe</OutputType><EnableDefaultCompileItems>false</EnableDefaultCompileItems><NoWarn>0649;0169;0414</NoWarn></PropertyGroup><ItemGroup>'+''.join('<Compile Include="'+p+'"/>' for p in paths)+'</ItemGroup></Project>')
exe='/workspace/work/tundra-beads/dotnet/dotnet';env=dict(os.environ,DOTNET_CLI_HOME='/workspace/work/tundra-beads/dotnet-home',DOTNET_CLI_TELEMETRY_OPTOUT='1');subprocess.run([exe,'build',str(W/'Runtime.csproj'),'--nologo'],check=True,env=env);subprocess.run([exe,str(W/'bin/Debug/net8.0/Runtime.dll'),str(R/'Sunward-Unity/Assets'),str(W)],check=True,env=env)

inputs=[Path(p) for p in paths if str(p).startswith(str(R))]
D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami'
inputs += [D/'ImpMotions.json']+[p for i in range(5) for p in (D/f'em0{i}').glob('*') if p.suffix in ['.json','.png','.bytes']]
inputs += list((D/'Effects').glob('Cannon*.png'))
inputs += [D/'NativeAudio.json',*list((D/'ImpAudio').glob('*.wav')),*list((R/'Sunward-Unity/Assets/Sunward/Generated').glob('Enemy-*.prefab')),*list((R/'Sunward-Unity/Assets/Sunward/Generated').glob('Spirit-*.asset'))]
receipt=dict(engineDoublesSHA256=hashlib.sha256((W/'RuntimeDoubles.cs').read_bytes()).hexdigest(),scope='Actual source Init/state/pose/audio drivers; simulated API lifecycle, flat floor and approximate player capsule. Not Unity Play Mode.',createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceHashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
(W/'runtime-receipt.json').write_text(json.dumps(receipt,indent=2))
