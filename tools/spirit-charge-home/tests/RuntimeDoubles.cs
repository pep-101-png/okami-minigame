// Explicit engine doubles: these tests are not Unity compilation or playback.
using System;
using System.IO;
using System.Linq;
using N=System.Numerics;
namespace UnityEngine
{
 public class Object
 {public static implicit operator bool(Object x)=>x!=null;public bool wasDestroyed;public static int destroyedObjects;public static void Destroy(Object x){if(x!=null){x.wasDestroyed=true;destroyedObjects++;}}public static T FindFirstObjectByType<T>()where T:class=>MonoBehaviour.CameraInstance as T;}
 [AttributeUsage(AttributeTargets.Class)]public class DefaultExecutionOrder:Attribute{public DefaultExecutionOrder(int n){}}
 public class MonoBehaviour:Object
 {
  public static Sunward.OrbitCamera CameraInstance=new Sunward.OrbitCamera();public GameObject gameObject=new GameObject();public Transform transform=>gameObject.transform;public bool isActiveAndEnabled=true;
  public T GetComponent<T>()where T:class=>null;public T[] GetComponentsInChildren<T>(bool b=false)=>Array.Empty<T>();
 }
 public class GameObject:Object
 {
  public Transform transform;public bool activeSelf;public SkinnedMeshRenderer[] renderers=Array.Empty<SkinnedMeshRenderer>();
  public GameObject(string n=""){transform=new Transform();transform.gameObject=this;}
  public void SetActive(bool b){activeSelf=b;}readonly System.Collections.Generic.Dictionary<Type,object> components=new System.Collections.Generic.Dictionary<Type,object>();public T AddComponent<T>()where T:new(){var c=new T();components[typeof(T)]=c;return c;}public T GetComponent<T>()where T:class=>components.TryGetValue(typeof(T),out var c)?c as T:null;
  public T[] GetComponentsInChildren<T>(bool b=false)=>renderers.Select(x=>(T)(object)x).ToArray();
 }
 public class Renderer:Object{public bool enabled;}
 public class Mesh:Object{public string name;public int vertexCount;}
 public class MeshFilter{public Mesh sharedMesh=new Mesh();}
 public class SkinnedMeshRenderer:Renderer{public Mesh sharedMesh=new Mesh();}
 public struct Vector3
 {
  public float x,y,z;public Vector3(float a,float b,float c){x=a;y=b;z=c;}
  public static Vector3 zero=>new Vector3();public static Vector3 one=>new Vector3(1,1,1);public static Vector3 up=>new Vector3(0,1,0);
  public float magnitude=>MathF.Sqrt(x*x+y*y+z*z);public static Vector3 Lerp(Vector3 a,Vector3 b,float t)=>a+(b-a)*t;
  public static Vector3 operator +(Vector3 a,Vector3 b)=>new Vector3(a.x+b.x,a.y+b.y,a.z+b.z);public static Vector3 operator -(Vector3 a,Vector3 b)=>new Vector3(a.x-b.x,a.y-b.y,a.z-b.z);public static Vector3 operator *(Vector3 a,float t)=>new Vector3(a.x*t,a.y*t,a.z*t);
 }
 public struct Vector2{public float x,y;public Vector2(float a,float b){x=a;y=b;}public float magnitude=>MathF.Sqrt(x*x+y*y);}
 public struct Quaternion
 {
  public float x,y,z,w;public Quaternion(float a,float b,float c,float d){x=a;y=b;z=c;w=d;}public static Quaternion identity=>new Quaternion(0,0,0,1);
  N.Quaternion NQ=>new N.Quaternion(x,y,z,w);static Quaternion Q(N.Quaternion q)=>new Quaternion(q.X,q.Y,q.Z,q.W);
  public static Quaternion Slerp(Quaternion a,Quaternion b,float t)=>Q(N.Quaternion.Slerp(a.NQ,b.NQ,t));public static Quaternion Inverse(Quaternion a)=>Q(N.Quaternion.Inverse(a.NQ));public static Quaternion operator *(Quaternion a,Quaternion b)=>Q(a.NQ*b.NQ);
 }
 public class Transform:Object
 {
  public GameObject gameObject;public Vector3 localPosition,localScale=Vector3.one,position;public Quaternion localRotation=Quaternion.identity,rotation=Quaternion.identity;
  public void SetParent(Transform parent,bool world=false){}public void SetPositionAndRotation(Vector3 p,Quaternion q){position=p;rotation=q;}
  public Vector3 TransformPoint(Vector3 p)=>position+p;public Vector3 InverseTransformPoint(Vector3 p)=>p-position;
 }
 public static class Mathf
 {
  public static float Cos(float x)=>MathF.Cos(x);public const float PI=MathF.PI;public static float Clamp01(float x)=>Math.Clamp(x,0,1);public static float Clamp(float x,float a,float b)=>Math.Clamp(x,a,b);
  public static float Repeat(float t,float n)=>t-MathF.Floor(t/n)*n;public static int FloorToInt(float x)=>(int)MathF.Floor(x);public static int Min(int a,int b)=>Math.Min(a,b);
  public static float Min(float a,float b)=>Math.Min(a,b);public static float Max(float a,float b)=>Math.Max(a,b);public static float Abs(float x)=>Math.Abs(x);
  public static float LerpAngle(float a,float b,float t)=>a+(Repeat(b-a+180,360)-180)*Clamp01(t);public static float Sqrt(float x)=>MathF.Sqrt(x);public static float Exp(float x)=>MathF.Exp(x);public static float Lerp(float a,float b,float t)=>a+(b-a)*t;public static float SmoothStep(float a,float b,float t){t=Clamp01(t);return Lerp(a,b,t*t*(3-2*t));}
 }
 public static class Time{public static float deltaTime=1f/60,unscaledDeltaTime=1f/60,timeScale=1;}
 public static class Debug{public static void LogError(string s,Object context){throw new Exception(s);}}
 public class TextAsset:Object{public byte[] bytes;public string text=>System.Text.Encoding.UTF8.GetString(bytes);}
 public static class JsonUtility{public static T FromJson<T>(string s)=>System.Text.Json.JsonSerializer.Deserialize<T>(s,new System.Text.Json.JsonSerializerOptions{IncludeFields=true});}
 public static class Resources
 {
  public static string Root;
  public static T Load<T>(string name)where T:class
  {foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories))foreach(var ext in new[]{".bytes",".json"}){var p=Path.Combine(dir,name+ext);if(File.Exists(p))return new TextAsset{bytes=File.ReadAllBytes(p)} as T;}return null;}
 }
 public class AudioClip:Object{public string name;}
 public class AudioSource:Object{public bool isPlaying;public AudioClip clip;public float volume;public int plays;public void Play(){isPlaying=true;plays++;}public void Stop(){isPlaying=false;}}
 public class Camera:Object
 {public static Camera main=new Camera();public Unity.Cinemachine.CinemachineBrain brain=new Unity.Cinemachine.CinemachineBrain();public T GetComponent<T>()where T:class=>brain as T;}
 public class CharacterController{public bool enabled=true;}
 public static class Physics{public static int syncs;public static void SyncTransforms(){syncs++;}}
}
namespace UnityEngine.InputSystem
{public class Key{public bool wasPressedThisFrame;}public class Keyboard{public static Keyboard current;public Key pKey=new Key();}}
namespace Sunward
{
 using UnityEngine;
 public class ProfileData{public string equipped="wp2e";public int bossWins,wins,defeats,coins,xp;public Milestones milestones=new Milestones();}public class Milestones{public bool hollowBell;}public class SaveStore{public int saves;public void Save(){saves++;}}
 public sealed partial class WolfMotor:MonoBehaviour
 {
  public const float Gravity=21;public float Vertical,Speed;public bool Grounded,Swimming,Locked,doubleUsed;public Vector3 Velocity,horizontal;
  public float dodgeTimer,landing,jumpBuffer,coyote,airborneTime;public CharacterController controller=new CharacterController();public Valley valley=new Valley();public GameFlow game;public WolfAnimation animationView=new WolfAnimation();
 }
 public class WolfAnimation{public string current;public void Play(string state,float blend=0,float duration=0,bool restart=false){current=state;}}
 public class Valley:UnityEngine.Object{public class Terrain{}public class ValleyData{public Terrain terrain=new Terrain();}public ValleyData Data=new ValleyData();public float Height(Vector3 p)=>.7f;public static float SurfaceHeight(Terrain t,Vector3 p)=>.7f;}
 public class WolfCombat:Object{public int cancels,rests;public void Cancel(){cancels++;}public void Equip(){throw new Exception("Return home attempted a visual reload");}public void Rest(bool rest){rests++;}}
 public sealed partial class ValleyAudio:Object
 {
  public AudioSource tundraSwing=new AudioSource(),tundraImpact=new AudioSource(),transformationVoice=new AudioSource(),transformationBurst=new AudioSource();
  public void VictoryHowl(){}AudioClip Clip(string cue)=>new AudioClip{name=cue};
 }
 public class HomeRest:Object{public int cancels;public void CancelRest(){cancels++;}}
 public partial class OrbitCamera:Object
 {public int snaps;public bool cinematic,savedIgnoreTimeScale;public Unity.Cinemachine.CinemachineBrain brain;public Unity.Cinemachine.CinemachineCamera virtualCamera=new Unity.Cinemachine.CinemachineCamera();public float savedFov,cinematicYaw,cinematicPitch,cinematicDistance,yaw=37,pitch=25,distance=15;public Vector3 cinematicFocus;public WolfMotor target;public void SnapFocus(){snaps++;}}
 public sealed partial class GameFlow:MonoBehaviour
 {
  public ValleyAudio Audio=new ValleyAudio();public Remaster.CrimsonHelmAscension BossTransformation;public bool Blocked,CinematicActive,InTrial,BossTrial,waiting;public ProfileData Profile=new ProfileData();public Remaster.ShiranuiTransformation Transformation=new Remaster.ShiranuiTransformation();
  public WolfMotor Player;public WolfCombat Combat=new WolfCombat();public Valley valley=new Valley();public HomeRest Home=new HomeRest();public Remaster.VillageServices Services=new Remaster.VillageServices();
  public float Health,Stamina,Energy,hitUntil;public int MaxHealth=>120;public float MaxStamina=>100;public float MaxEnergy=>80;public string Panel="result",Dialogue;public GameObject barrier;public int clears,projectiles,runCoins=10,runXp=20;public SaveStore Save=new SaveStore();
  public void ClearProjectiles(){projectiles++;}public void SetPanel(string panel){Panel=panel;}public void ClearEnemies(){clears++;}public void Close(){Panel="";Player.Locked=false;}public void Notify(string s){}
 }
}
namespace Sunward.Remaster
{
 using UnityEngine;
 public class CrimsonHelmAscension:Object{public int cancels;public void Cancel(){cancels++;}}
 public class VillageLife:Object{public void CancelDig(){}}
 public class ShiranuiTransformation:Object{public int cancels;public void Begin(NativeAmaterasu player){}public void Cancel(){cancels++;}}
 public class VillageServices:Object{public int cancels;public void CancelRest(){cancels++;}}
 public static partial class LowerArena{public static void BossDefeated(){}public static int leaves;public static void Leave(){leaves++;}public static void TrialFinished(bool win){}}
 public sealed class NativePaintedRig:IDisposable
 {
  public GameObject Root=new GameObject();public Transform[] Bones;
  public NativePaintedRig(string resource,Transform parent){var bank=new NativePoseBank(resource+"/Poses");Bones=Enumerable.Range(0,bank.BoneCount).Select(_=>new Transform()).ToArray();}
  public void Dispose(){}
 }
}

namespace Unity.Cinemachine
{public struct LensSettings{public float FieldOfView;}public class CinemachineCamera:UnityEngine.Object{public LensSettings Lens=new LensSettings{FieldOfView=50};}public class CinemachineBrain:UnityEngine.Object{public bool IgnoreTimeScale;}}
