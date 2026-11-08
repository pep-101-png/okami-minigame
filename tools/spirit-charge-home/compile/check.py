"""Compile whole camera, cinematic, audio and native drivers with explicit engine doubles."""
from pathlib import Path
import tempfile,subprocess,os,re,argparse
root=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--dotnet',default='dotnet');p.add_argument('--negative-control',action='store_true');p.add_argument('--river-negative-control',action='store_true');p.add_argument('--street-spawn-negative-control',action='store_true');p.add_argument("--charge-negative-control",action="store_true");p.add_argument("--dump-doubles");args=p.parse_args()
s=(root/'tools/spirit-charge-home/tests/RuntimeDoubles.cs').read_text()
s=s.replace('public sealed partial class GameFlow:MonoBehaviour', 'public sealed partial class GameFlow:MonoBehaviour')
s=s.replace('namespace Sunward.Remaster{public class VillagePresentation:UnityEngine.Object{public void Cancel(){}}}','')
s=re.sub(r' public partial class OrbitCamera:Object\n \{[^\n]*\}\n','',s)
s=re.sub(r' public class ShiranuiTransformation:Object\{[^\n]*\}\n','',s)
s=re.sub(r' public sealed partial class ValleyAudio:Object\n \{.*?\n \}\n','',s,flags=re.S)
s=s.replace('public static T FindFirstObjectByType<T>()','public static T[] FindObjectsByType<T>(FindObjectsSortMode mode)=>System.Array.Empty<T>();public static T FindFirstObjectByType<T>()')
s=s.replace('public T GetComponent<T>()where T:new()=>new T();','public T AddComponent<T>()where T:new()=>new T();public T GetComponent<T>()where T:new()=>new T();')
s=s.replace('public bool activeSelf;', 'public bool activeSelf;')
s=s.replace('public float magnitude=>MathF.Sqrt(x*x+y*y+z*z);','public float sqrMagnitude=>x*x+y*y+z*z;public float magnitude=>MathF.Sqrt(sqrMagnitude);public Vector3 normalized=>magnitude>0?this*(1/magnitude):zero;public static Vector3 back=>new Vector3(0,0,-1);public static Vector3 ClampMagnitude(Vector3 v,float max)=>v.magnitude>max?v.normalized*max:v;public static Vector3 operator -(Vector3 v)=>v*(-1);')
s=s.replace('public struct Vector2{','public struct Vector2{public static Vector2 zero=>new Vector2();public static Vector2 operator *(Vector2 v,float x)=>new Vector2(v.x*x,v.y*x);public static Vector2 operator +(Vector2 a,Vector2 b)=>new Vector2(a.x+b.x,a.y+b.y);')
s=s.replace('public static Quaternion Slerp', 'public static Quaternion Euler(float a,float b,float c)=>identity;public static Quaternion LookRotation(Vector3 v)=>identity;public static Vector3 operator *(Quaternion q,Vector3 v)=>v;public static Quaternion Slerp')
s=s.replace('public GameObject gameObject;public Vector3', 'public GameObject gameObject;public Vector3 eulerAngles;public Vector3')
s=s.replace('public static float LerpAngle','public static float Sin(float x)=>MathF.Sin(x);public static float Pow(float x,float y)=>MathF.Pow(x,y);public static float MoveTowards(float a,float b,float t)=>MathF.Abs(a-b)<t?b:a+MathF.Sign(b-a)*t;public static float LerpAngle')
s=s.replace('public class AudioClip:Object{public string name;}','public class AudioClip:Object{public string name;public float length;}')
s=s.replace('public bool isPlaying;public AudioClip clip;', 'public bool isPlaying,loop,playOnAwake;public float spatialBlend,dopplerLevel,minDistance,maxDistance;public AudioRolloffMode rolloffMode;public void PlayOneShot(AudioClip clip,float gain){}public AudioClip clip;')
s=s.replace('public static int syncs;', 'public static bool SphereCast(Vector3 a,float r,Vector3 d,out RaycastHit hit,float n,int mask,QueryTriggerInteraction trigger){hit=new RaycastHit();return false;}public static int syncs;')
s=s.replace('timeScale=1;', 'timeScale=1,unscaledTime,time;')
s=s.replace('public WolfAnimation animationView=new WolfAnimation();', 'public WolfAnimation animationView=new WolfAnimation();public WolfInput input=new WolfInput();public void StopMotion(){}')
s=s.replace('public class Valley:UnityEngine.Object{', 'public class Valley:UnityEngine.Object{public static float RiverX(float z)=>0;')

s=s.replace('public class VillageServices:Object{', 'public class VillageServices:Object{public static bool InFoodHouse(Vector3 p)=>false;')
s=s.replace('public LensSettings Lens=new LensSettings', 'public UnityEngine.Transform transform=new UnityEngine.Transform();public LensSettings Lens=new LensSettings')
s=s.replace('public class Camera:Object\n {','public class Camera:Object\n {public Transform transform=new Transform();').replace('public bool isPlaying,loop,playOnAwake;','public Transform transform=new Transform();public bool isPlaying,loop,playOnAwake;').replace('public static Vector3 back=>','public static float Distance(Vector3 a,Vector3 b)=>(a-b).magnitude;public static Vector3 back=>')
s=s.replace('Bones=Enumerable.Range(0,bank.BoneCount).Select(_=>new Transform()).ToArray();','Bones=Enumerable.Range(0,bank.BoneCount).Select(_=>new Transform()).ToArray();var model=Resources.Load<TextAsset>(resource+"/Model");if(model!=null){using var json=System.Text.Json.JsonDocument.Parse(model.text);Root.renderers=json.RootElement.GetProperty("parts").EnumerateArray().Select(p=>new SkinnedMeshRenderer{sharedMesh=new Mesh{name=p.GetProperty("name").GetString(),vertexCount=p.GetProperty("positions").GetArrayLength()/3}}).ToArray();}')
s+='\n'+(Path(__file__).with_name('ExtraDoubles.cs')).read_text()
# Compile the actual boss, native actor and tendril scripts as well.
s=re.sub(r' public class CrimsonHelmAscension:Object[^\n]*\n','',s)
s=s.replace('public T GetComponent<T>()where T:class=>null;', 'public T GetComponent<T>()where T:class=>gameObject.GetComponent<T>();public T GetComponentInParent<T>()where T:class=>null;public T GetComponentInChildren<T>(bool b=false)where T:class=>null;')
s=s.replace('public static void Destroy(Object x){', 'public static T Instantiate<T>(T x,Transform parent)where T:Object=>x;public static void Destroy(Object x,float delay){Destroy(x);}public static void Destroy(Object x){')
s=s.replace('public Transform transform;public bool activeSelf;', 'public int layer;public Transform transform;public bool activeSelf;')
s=s.replace('public class Renderer:Object{public bool enabled;}', 'public class Renderer:Object{public bool enabled;public Material sharedMaterial;}')
s=s.replace('public Mesh sharedMesh=new Mesh();}', 'public Bounds localBounds;public bool updateWhenOffscreen;public Mesh sharedMesh=new Mesh();}')
s=s.replace('public void SetParent(Transform parent', 'public T GetComponentInChildren<T>(bool b=false)where T:class=>gameObject.GetComponent<T>();public void Rotate(float x,float y,float z){}public void SetParent(Transform parent')
s=s.replace('public static float Sin(float x)', 'public static float Ceil(float x)=>MathF.Ceiling(x);public static float Sin(float x)')
s=s.replace('public static float Distance(Vector3 a,Vector3 b)', 'public static float Dot(Vector3 a,Vector3 b)=>a.x*b.x+a.y*b.y+a.z*b.z;public static float Distance(Vector3 a,Vector3 b)')
s=s.replace('public class CharacterController{public bool enabled=true;}', 'public class CharacterController: Object{public bool enabled=true;public float radius,height;public Vector3 center;public void Move(Vector3 delta){}}')
s=s.replace('public void StopMotion(){}','public void StopMotion(){}public void Teleport(Vector3 p){transform.position=p;}')
s=s.replace('public void ClearProjectiles(){', 'public VisualFx Fx=new VisualFx();public void TrackBossTransformation(Remaster.CrimsonHelmAscension c){BossTransformation=c;}public void ReleaseBossTransformation(Remaster.CrimsonHelmAscension c){if(BossTransformation==c)BossTransformation=null;}public void Reward(EnemyBrain b){}public void Hurt(float damage,Vector3 away){}public void Projectile(Vector3 p,Vector3 d,float damage,bool flame=false){}public void ClearProjectiles(){')
s=s.replace('public static int leaves;', 'public static Vector3 Centre=>new Vector3(35,-110,0);public static Vector3 Guard(Vector3 p)=>p;public static bool Height(Vector3 p,out float floor){floor=-110;return true;}public static int leaves;')
s=s.replace('components[typeof(T)]=c;return c;', 'if(c is MonoBehaviour m)m.gameObject=this;components[typeof(T)]=c;return c;')
s=s.replace('public void Reward(EnemyBrain b){}', 'public int rewards;public void Reward(EnemyBrain b){rewards++;}')
s+='\n'+Path(__file__).with_name('RebirthDoubles.cs').read_text()
s=re.sub(r' public class VillageLife:Object[^\n]*\n','',s)
s=s.replace('public void StopMotion(){}','public bool Locked;public void StopMotion(){}') if False else s
s=s.replace('public GameObject gameObject=new GameObject();public Transform transform=>', 'public Coroutine StartCoroutine(System.Collections.IEnumerator routine)=>new Coroutine();public void StopCoroutine(Coroutine routine){}public GameObject gameObject=new GameObject();public Transform transform=>')
s=s.replace('public GameObject(string n=""){','public T GetComponentInChildren<T>(bool include=false)where T:class=>GetComponent<T>();public GameObject(string n=""){')
s=s.replace('public static class Resources', 'public class Coroutine{}public class WaitForSeconds{public WaitForSeconds(float t){}}public static class Cursor{public static bool visible=true;}public static class Resources')
s=s.replace('public float x,y;public Vector2(float a,float b)', 'public float x,y;public float sqrMagnitude=>x*x+y*y;public static float Dot(Vector2 a,Vector2 b)=>a.x*b.x+a.y*b.y;public static float Distance(Vector2 a,Vector2 b)=>(a-b).magnitude;public static Vector2 Min(Vector2 a,Vector2 b)=>new Vector2(MathF.Min(a.x,b.x),MathF.Min(a.y,b.y));public static Vector2 Max(Vector2 a,Vector2 b)=>new Vector2(MathF.Max(a.x,b.x),MathF.Max(a.y,b.y));public static Vector2 Lerp(Vector2 a,Vector2 b,float t)=>a+(b-a)*t;public static Vector2 operator -(Vector2 a,Vector2 b)=>new Vector2(a.x-b.x,a.y-b.y);public float xUnused;public Vector2(float a,float b)')
s=s.replace('public static Vector3 operator -(Vector3 v)', 'public static Vector3 operator /(Vector3 v,float t)=>v*(1/t);public static implicit operator Vector2(Vector3 v)=>new Vector2(v.x,v.y);public static Vector3 operator -(Vector3 v)')
s=s.replace('public Vector3 eulerAngles;','public Vector3 forward=Vector3.up;public Vector3 eulerAngles;') if False else s.replace('public Transform transform;','public Transform transform;')
s=s.replace('public GameObject gameObject;public Vector3 eulerAngles;', 'public GameObject gameObject;public Vector3 forward=Vector3.up;public Vector3 eulerAngles;')
s=s.replace('public static int FloorToInt', 'public static int CeilToInt(float v)=>(int)MathF.Ceiling(v);public static int Max(int a,int b)=>Math.Max(a,b);public static int FloorToInt')
s=s.replace('public bool isActiveAndEnabled=true;', 'public bool isActiveAndEnabled=true;')
s=s.replace('public Transform transform=new Transform();public bool isPlaying', 'public Transform transform=new Transform();public bool isPlaying')
s=s.replace('public static class Physics{', 'public static class Physics{public static bool Raycast(Ray r,out RaycastHit hit,float range,int mask,QueryTriggerInteraction q){hit=new RaycastHit();return false;}')
s=s.replace('public struct RaycastHit{public float distance;}', 'public struct RaycastHit{public float distance;public Vector3 point;}')
s=s.replace('public class Camera:Object\n {', 'public class Camera:Object\n {public Ray ScreenPointToRay(Vector2 p)=>new Ray();public Vector3 WorldToScreenPoint(Vector3 p)=>p;')
s=s.replace('public static Color color;', 'public static Matrix4x4 matrix;public static Color color;public static void Label(Rect r,string text){}')
s=s.replace('public class Mouse{public static Mouse current;public VectorControl delta', 'public class Mouse{public VectorControl position=new VectorControl();public static Mouse current;public VectorControl delta')
s=s.replace('public class Gamepad{public static Gamepad current;', 'public class PadDirection{public UnityEngine.InputSystem.Key up=new UnityEngine.InputSystem.Key();}public class Gamepad{public PadDirection dpad=new PadDirection();public static Gamepad current;')
s=s.replace('public bool wasPressedThisFrame;', 'public bool wasPressedThisFrame,isPressed;')
s=s.replace('public bool IsPressed()=>false;', 'public bool WasPressedThisFrame()=>false;public bool IsPressed()=>false;')
s=s.replace('public UnityEngine.InputSystem.InputAction Orbit=', 'public UnityEngine.InputSystem.InputAction Brush=new UnityEngine.InputSystem.InputAction(),Light=new UnityEngine.InputSystem.InputAction(),Pause=new UnityEngine.InputSystem.InputAction(),Dig=new UnityEngine.InputSystem.InputAction(),Eat=new UnityEngine.InputSystem.InputAction(),Carry=new UnityEngine.InputSystem.InputAction(),Interact=new UnityEngine.InputSystem.InputAction();public UnityEngine.InputSystem.InputAction Orbit=')
s=s.replace('public int bossWins,wins,defeats,coins,xp;', 'public int vegetables,farmVitality,cropsSold,praise,restorationStage,kills;public int bossWins,wins,defeats,coins,xp;')
s=s.replace('public int cancels,rests;', 'public float FormMultiplier=>1;public int cancels,rests;')
s=s.replace('public float Health,Stamina,Energy,hitUntil;', 'public GameObject[] npcObjects=System.Array.Empty<GameObject>();public System.Collections.Generic.List<EnemyBrain> Enemies=new System.Collections.Generic.List<EnemyBrain>();public void WorldPrompt(string text){}public float Health,Stamina,Energy,hitUntil;')
s=s.replace('public class VillageResident:UnityEngine.Object{public GameFlow game;}', 'public class VillageResident:UnityEngine.Object{public GameFlow game;public int index;public bool stallkeeper;}')
s=s.replace('public class VillageServices:Object{', 'public class VillageServices:Object{public static Vector3 Farmer=>Vector3.zero;public static bool InDojo(Vector3 p)=>false;public int restRequests;public Vector3 restPoint;public void RestAt(Vector3 p,float yaw){restRequests++;restPoint=p;}')
s+='\n'+Path(__file__).with_name('VillageBrushDoubles.cs').read_text()
s=re.sub(r' public static partial class LowerArena[^\n]*\n','',s)
s=s.replace('public static Vector3 zero=>','public static Vector3 down=>new Vector3(0,-1,0);public static Vector3 zero=>')
s=s.replace('public float sqrMagnitude=>x*x+y*y;', 'public Vector2 normalized=>magnitude>0?this*(1/magnitude):zero;public float sqrMagnitude=>x*x+y*y;')
s=s.replace('public Vector3 point;}', 'public Collider collider;public Vector3 point;}')
s=s.replace('public static class Physics{','public static class Physics{public static int RaycastNonAlloc(Vector3 p,Vector3 dir,RaycastHit[] hits,float d,int mask,QueryTriggerInteraction q)=>0;')
s=s.replace('public T GetComponentInChildren<T>(bool b=false)where T:class=>gameObject.GetComponent<T>();public void Rotate', 'public T[] GetComponentsInChildren<T>(bool b=false)=>gameObject.GetComponentsInChildren<T>(b);public T GetComponentInChildren<T>(bool b=false)where T:class=>gameObject.GetComponent<T>();public void Rotate')
s=s.replace('public void WorldPrompt(string text){}','public int bossStarts;public void StartBossTrial(){bossStarts++;}public void WorldPrompt(string text){}')
s=s.replace('public void Teleport(Vector3 p){transform.position=p;}','public void Recover(Vector3 p){transform.position=p;}public void Teleport(Vector3 p){transform.position=p;}')
s=s.replace('public bool isGlobal;', 'public bool isGlobal;')
s=s.replace('public int bossStarts;public void StartBossTrial(){bossStarts++;}', 'public int bossStarts,homeReturns;public void ReturnHome(){homeReturns++;InTrial=BossTrial=false;}public void StartBossTrial(){bossStarts++;InTrial=BossTrial=true;}')
s=s.replace('public bool WasPressedThisFrame()=>false;', 'public bool pressedThisFrame;public bool WasPressedThisFrame()=>pressedThisFrame;')
s=s.replace('public GameObject(string n=""){', 'public static System.Collections.Generic.List<GameObject> created=new System.Collections.Generic.List<GameObject>();public GameObject(string n=""){created.Add(this);')
s=re.sub(r' public class HomeRest:Object[^\n]*\n','',s)
s=s.replace('public int bossWins,wins,defeats,coins,xp;', 'public bool night;public int bossWins,wins,defeats,coins,xp;')
s=s.replace('public bool hollowBell;', 'public bool hollowBell,sleptAtHome;')
s=s.replace('public int cancels,rests;', 'public Transform transform=new Transform();public void TundraBeadContacts(Vector3[] p,int count){}public int cancels,rests;')
s=s.replace('public void StopCoroutine(Coroutine routine){}', 'public void StopAllCoroutines(){}public void StopCoroutine(Coroutine routine){}')
s=s.replace('public Vector3 forward=Vector3.up;', 'public Vector3 right=new Vector3(1,0,0),forward=new Vector3(0,0,1);public Transform parent;public Matrix4x4 worldToLocalMatrix=>Matrix4x4.identity;public Matrix4x4 localToWorldMatrix=>Matrix4x4.identity;')
s=s.replace('public class Mesh:Object{public string name;public int vertexCount;}', 'public class Mesh:Object{public string name;public int vertexCount;public Bounds bounds;public void GetVertices(System.Collections.Generic.List<Vector3> v){}}')
s=s.replace('public class Renderer:Object{', 'public class Renderer:Object{public Transform transform=new Transform();public string name;')
s=s.replace('public class SkinnedMeshRenderer:Renderer{', 'public class SkinnedMeshRenderer:Renderer{public void BakeMesh(Mesh mesh){}')
s=s.replace('public static Vector3 Lerp(Vector3 a', 'public static Vector3 Scale(Vector3 a,Vector3 b)=>new Vector3(a.x*b.x,a.y*b.y,a.z*b.z);public static Vector3 Min(Vector3 a,Vector3 b)=>new Vector3(MathF.Min(a.x,b.x),MathF.Min(a.y,b.y),MathF.Min(a.z,b.z));public static Vector3 Max(Vector3 a,Vector3 b)=>new Vector3(MathF.Max(a.x,b.x),MathF.Max(a.y,b.y),MathF.Max(a.z,b.z));public static Vector3 ProjectOnPlane(Vector3 a,Vector3 normal)=>a-normal*Dot(a,normal);public static Vector3 Lerp(Vector3 a')
s=s.replace('public static Quaternion Euler(float a', 'public static Quaternion FromToRotation(Vector3 a,Vector3 b)=>identity;public static Quaternion Euler(Vector3 v)=>identity;public static Quaternion Euler(float a')
s=s.replace('public string current;public void Play', 'public string current;public float ClipLength(string state)=>1;public void Play')
s=s.replace('public Vector3 center,size;', 'public Vector3 center,size;public Vector3 min=>center-size*.5f;')
s=s.replace('public static class GardenPond{', 'public static class GardenPond{public const float Water=-.23f,RadiusX=3.05f,RadiusZ=2.05f;')
s+='\nnamespace UnityEngine{public class BoxCollider:Object{public Vector3 center,size;}}'
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {','public sealed partial class GameFlow:MonoBehaviour\n {public Sunward.Remaster.SpaRest Spa;')
s=s.replace('public class VillageServices:Object{','public partial class VillageServices:Object{public bool Resting;')
s=s.replace('public int MaxHealth=>120;', 'public int MaxHealth=>120+(Spa?Spa.Bonus:0);')
s=s.replace('public class Keyboard{public static Keyboard current;', 'public class Keyboard{public Key anyKey=new Key();public static Keyboard current;')
s=s.replace('public class Mouse{', 'public class Mouse{public Key leftButton=new Key();')
s=s.replace('public class Gamepad{', 'public class Gamepad{public UnityEngine.InputSystem.Key startButton=new UnityEngine.InputSystem.Key();')
s=s.replace('public struct Rect{public Rect(float x,float y,float w,float h){}}','public struct Rect{public float x,y,width,height;public Rect(float x,float y,float w,float h){this.x=x;this.y=y;width=w;height=h;}}')
s=s.replace('public static class GUI{','public static partial class GUI{')
s=s.replace('public class Gamepad{','public class Gamepad{public UnityEngine.InputSystem.Key buttonSouth=new UnityEngine.InputSystem.Key();')
service=(root/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/VillageServices.cs').read_text();start=service.index('        IEnumerator SitAt(');end=service.index('\n        }',start)+10
s+='\nnamespace Sunward.Remaster{using UnityEngine;using System.Collections;public partial class VillageServices{public Sunward.GameFlow game;'+service[start:end]+'}}\n'
s=s.replace('public class Gamepad{', 'public class Gamepad{public object[] allControls=System.Array.Empty<object>();')
s=s.replace('public class Mouse{', 'public class Mouse{public Key rightButton=new Key(),middleButton=new Key();')
s=s.replace('public class Material:Object{', 'public class Material:Object{public void SetColor(string name,Color value){}')
s=s.replace('public bool CinematicActive;', 'bool cinematicFlag;public bool CinematicActive{get=>cinematicFlag || (Presentation && Presentation.Playing);set=>cinematicFlag=value;}')
s=s.replace('BossTrial,waiting,InTrial,CinematicActive;', 'BossTrial,waiting,InTrial;bool cinematicFlag;public bool CinematicActive{get=>cinematicFlag || (Presentation && Presentation.Playing);set=>cinematicFlag=value;}')
s=s.replace('public bool Blocked,CinematicActive,InTrial,BossTrial,waiting;', 'public bool Blocked,InTrial,BossTrial,waiting;bool cinematicFlag;public bool CinematicActive{get=>cinematicFlag || (Presentation && Presentation.Playing);set=>cinematicFlag=value;}')
s=s.replace('public class Shader:','public class Shader:')
s=s.replace('public static class Shader{','public class Shader{public static Shader Find(string n)=>new Shader();')
s=s.replace('public class Material:Object{','public class Material:Object{public void SetTexture(string n,Texture2D t){}public Shader shader;')
s=s.replace('namespace Sunward.Remaster{public class HeavenlyGarden:UnityEngine.Object{public bool Playing;public void Cancel(){Playing=false;}}}', '')
s=s.replace('public class BoxCollider:Collider{','public class MeshCollider:Collider{public Mesh sharedMesh;}public class BoxCollider:Collider{')
s=s.replace('public static float Height(', 'public static float Height(')
s=s.replace('public static class OriginalWeaponCatalog{', 'public static class OriginalWeaponCatalog{public class Entry{public string family,resource;public int cost;}')
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {','public sealed partial class GameFlow:MonoBehaviour\n {public void OfferWindflowers(){}')
s+='\n'+Path(__file__).with_name('VillagePresentationDoubles.cs').read_text()
s+='\n'+Path(__file__).with_name('FestivalDoubles.cs').read_text()
s=s.replace('public bool HoldingCharge;', 'public GameFlow game;public bool HoldingCharge;')
s=s.replace('public class Light:Object{', 'public class Light:Object{public Transform transform=new Transform();')
s=s.replace('public UnityEngine.InputSystem.InputAction Brush=', 'public UnityEngine.InputSystem.InputAction Jump=new UnityEngine.InputSystem.InputAction(),Move=new UnityEngine.InputSystem.InputAction();public UnityEngine.InputSystem.InputAction Brush=')
s=re.sub(r' public class ProfileData.*?(?=public class SaveStore)',' ',s,flags=re.S)
s=re.sub(r' public static class ProgressionRules[^\n]*\n','',s)
s=s.replace('public static Vector3 Farmer=>Vector3.zero;', 'public static Vector3 Farmer=>Vector3.zero;public static Vector3 FarmerPosition=>Farmer;')
s=s.replace('public void BakeMesh(Mesh mesh){}', 'public void BakeMesh(Mesh mesh,bool scale=false){}')
s=s.replace('public static Vector3 Lerp(Vector3 a', 'public static Vector3 MoveTowards(Vector3 a,Vector3 b,float step)=>(b-a).magnitude<=step?b:a+(b-a).normalized*step;public static Vector3 Lerp(Vector3 a')
s=s.replace('public static Quaternion FromToRotation', 'public static Quaternion RotateTowards(Quaternion a,Quaternion b,float t)=>b;public static Quaternion FromToRotation')
s=s.replace('public class MonoBehaviour:Object', 'public class MonoBehaviour:Object')
s=s.replace('public bool isActiveAndEnabled=true;', 'public bool enabled=true;public bool isActiveAndEnabled=true;')
s=s.replace('public static float Sin(float x)', 'public static float Sign(float x)=>MathF.Sign(x);public static float Sin(float x)')
s=s.replace('public static Vector3 up=>', 'public static Vector3 right=>new Vector3(1,0,0);public static Vector3 up=>')
s=re.sub(r' public class NativeDailyRoutine:[^\n]*\n','',s)
s=re.sub(r' public class NativeHomeRoom:[^\n]*\n','',s)
s=s.replace('public class VillageResident:UnityEngine.Object{','public class VillageResident:UnityEngine.Object{public bool enabled=true;')
s=s.replace('public static float Sign(float x)', 'public const float Deg2Rad=MathF.PI/180;public static int Abs(int x)=>Math.Abs(x);public static int RoundToInt(float x)=>(int)MathF.Round(x);public static int Clamp(int x,int a,int b)=>Math.Max(a,Math.Min(b,x));public static float Sign(float x)')
s=s.replace('public static bool InFoodHouse(Vector3 p)=>false;', 'public static bool InFoodHouse(Vector3 p)=>Sunward.Remaster.VillageInteriors.Food(p);')
# Match the actual GameFlow access boundary instead of a writable fake field.
flow=(root/'Sunward-Unity/Assets/Sunward/Scripts/GameFlow.cs').read_text();start=flow.index('public void ShowDialogue(');at=flow.index('{',start);depth=1;end=at+1
while depth:
 if flow[end]=='{':depth+=1
 elif flow[end]=='}':depth-=1
 end+=1
s+='\nnamespace Sunward {public sealed partial class GameFlow {'+flow[start:end]+'}}\n'
s=s.replace('public class Camera:Object\n {','public enum CameraClearFlags{Skybox,SolidColor}public class Camera:Object\n {public int cullingMask=-1;public CameraClearFlags clearFlags;public Color backgroundColor;')
s=s.replace('public static class ObjectUnused', 'public static class ObjectUnused')
s=s.replace('public enum FindObjectsSortMode{None}', 'public enum FindObjectsInactive{Include,Exclude}public enum FindObjectsSortMode{None}')
s=s.replace('public static T[] FindObjectsByType<T>(FindObjectsSortMode mode)', 'public static T[] FindObjectsByType<T>(FindObjectsInactive inactive,FindObjectsSortMode mode)=>System.Array.Empty<T>();public static T[] FindObjectsByType<T>(FindObjectsSortMode mode)')
s=s.replace('public static Vector3 zero=>','public static Vector3 forward=>new Vector3(0,0,1);public static Vector3 left=>new Vector3(-1,0,0);public static Vector3 zero=>')
s=s.replace('public class Renderer:Object{','public class Renderer:Object{public bool forceRenderingOff;public GameObject gameObject=new GameObject();')
s=s.replace('public static void LogError(string s,Object context)', 'public static void LogError(string s,Object context=null)')
s=s.replace('public class Valley:UnityEngine.Object{', 'public class Valley:UnityEngine.Object{public static float Depth(Vector3 p)=>0;')
s=s.replace('float radius,float distance){goal=p;', 'float radius=.5f,float distance=16){goal=p;')
s+='\nnamespace Sunward{public static class MeshSafety{public static bool Finite(UnityEngine.Vector3 p)=>float.IsFinite(p.x)&&float.IsFinite(p.y)&&float.IsFinite(p.z);}}'
s=s.replace('public const float PI=', 'public const float Rad2Deg=57.2957795f;public static float Atan2(float y,float x)=>MathF.Atan2(y,x);public const float PI=')
s=s.replace('components[typeof(T)]=c;return c;', 'components[typeof(T)]=c;StreetActorLifecycle.Added(c,activeSelf);return c;')
s=s.replace('public void SetActive(bool b){activeSelf=b;}', 'public void SetActive(bool b){activeSelf=b;if(b)StreetActorLifecycle.Activated(this);}')
s=s.replace('created.Add(this);', 'activeSelf=StreetActorLifecycle.Enabled;created.Add(this);')
s=s.replace('public static class Shader{','public class Shader{public static Shader Find(string n)=>new Shader();')
s=s.replace('public static class OriginalWeaponCatalog{', 'public static class OriginalWeaponCatalog{public class Entry{public string family,resource;public int cost;}')
s=s.replace('public class GameObject:Object', 'public class GameObject:Object')
s=s.replace('public GameObject(string n="")', 'public string name;public GameObject(string n="")')
s=s.replace('public Material(Material source){}', 'public Material(Material source){}public Material(Shader shader){}')
s+='\nnamespace UnityEngine{public class MeshCollider:Collider{public Mesh sharedMesh;}}'
s=s.replace('public class ValleyData{', 'public class ValleyData{public BoxData[] boxes=System.Array.Empty<BoxData>();')
s+='\nnamespace Sunward{public class BoxData{public float x,z,halfX,halfZ;}}'
s=s.replace('public class Material:Object{','public class Material:Object{public void SetFloat(string n,float v){}')
s=s.replace('public Transform parent;', 'public Transform parent;public bool IsChildOf(Transform root){for(Transform t=this;t!=null;t=t.parent)if(System.Object.ReferenceEquals(t,root))return true;return false;}')
s=s.replace('public class Renderer:Object{', 'public class Renderer:Object{public Bounds bounds;')
s=s.replace('public static T[] FindObjectsByType<T>(FindObjectsSortMode mode)=>System.Array.Empty<T>();', 'public static T[] FindObjectsByType<T>(FindObjectsSortMode mode)=>SceneQuery.Find<T>();')
s=s.replace('public static T[] FindObjectsByType<T>(FindObjectsInactive inactive,FindObjectsSortMode mode)=>System.Array.Empty<T>();','public static T[] FindObjectsByType<T>(FindObjectsInactive inactive,FindObjectsSortMode mode)=>SceneQuery.Find<T>();')
s+='\nnamespace UnityEngine{public static class SceneQuery{public static Object[] objects=System.Array.Empty<Object>();public static T[] Find<T>(){var result=new System.Collections.Generic.List<T>();foreach(var o in objects)if(o is T t)result.Add(t);return result.ToArray();}}}'
s=s.replace('public void Equip(){throw new Exception("Return home attempted a visual reload");}','public bool allowEquip;public int equips;public void Equip(){if(!allowEquip)throw new Exception("Return home attempted a visual reload");equips++;}')
s=re.sub(r' public class OriginalVisual:UnityEngine.MonoBehaviour\{[^\n]*\}\n','',s)
# NativePaintedRig loads static models without requiring a motion bank, as the real engine adapter does.
s=s.replace('var bank=new NativePoseBank(resource+"/Poses");Bones=', 'var motion=Resources.Load<TextAsset>(resource+"/Poses");var bank=new {BoneCount=motion==null?1:new NativePoseBank(resource+"/Poses").BoneCount};Bones=')
s=s.replace('public static int RaycastNonAlloc(Vector3 p,Vector3 dir,RaycastHit[] hits,float d,int mask,QueryTriggerInteraction q)=>0;', 'public static int RaycastNonAlloc(Vector3 p,Vector3 dir,RaycastHit[] hits,float d,int mask,QueryTriggerInteraction q){int n=System.Math.Min(hits.Length,HeavenPhysicsFixture.hits.Length);System.Array.Copy(HeavenPhysicsFixture.hits,hits,n);return n;}')
s+='\nnamespace UnityEngine{public static class HeavenPhysicsFixture{public static RaycastHit[] hits=System.Array.Empty<RaycastHit>();}}'
# Static native ES3A has no motion bank: read the original model's bone count.
s=s.replace('motion==null?1:new NativePoseBank(resource+"/Poses").BoneCount', 'motion==null?System.Text.Json.JsonDocument.Parse(Resources.Load<TextAsset>(resource+"/Model").text).RootElement.GetProperty("bones").GetArrayLength()+1:new NativePoseBank(resource+"/Poses").BoneCount')
s=s.replace('new SkinnedMeshRenderer{sharedMesh=new Mesh{name=p.GetProperty', 'new SkinnedMeshRenderer{sharedMaterial=new Material((Material)null),sharedMesh=new Mesh{name=p.GetProperty')
# Public Unity APIs used by the real native shrine floor and veil adapters.
s=s.replace('public class Mesh:Object{', 'public class Mesh:Object{public Vector3[] vertices=System.Array.Empty<Vector3>();public int[] triangles=System.Array.Empty<int>();public void RecalculateBounds(){}')
s=s.replace('public static Vector3 Lerp(', 'public static Vector3 Cross(Vector3 a,Vector3 b)=>new Vector3(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);public static Vector3 Lerp(')
s=s.replace('public class ParticleSystem:Object{', 'public class ParticleSystem:Object{public class VelocityModule{public float y;}public VelocityModule velocityOverLifetime=new VelocityModule();')
s=s.replace('public class LineRenderer:', 'public class LineRenderer:')
s=s.replace('public int positionCount;', 'public bool loop;public int positionCount;')
s=s.replace('public GameObject(string n=""){', 'public GameObject(string n=""){name=n;')
s=s.replace('{foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories))foreach(var ext', '{foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories)){if(typeof(T)==typeof(Material) && File.Exists(Path.Combine(dir,name+".mat")))return new Material((Material)null){shader=new Shader()} as T;}foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories))foreach(var ext')
# API doubles for the native home, time and save-menu additions. These do not
# model Unity rendering, real save I/O or the player's PC.
s=s.replace('public class SaveStore{public int saves;public void Save(){saves++;}}','public class SaveStore{public int saves;public string Status="";public void Save(){saves++;}public ProfileData ReadSlot(int i)=>null;public bool SaveSlot(int i)=>true;public bool LoadSlot(int i)=>false;}')
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {','public sealed partial class GameFlow:MonoBehaviour\n {public CollectibleShelf Shelf=new CollectibleShelf();public void RefreshQuest(){}')
s+='\nnamespace Sunward{public class CollectibleShelf{public void Refresh(){}}}'
s=s.replace('public bool Sleeping;', 'public bool Active;public bool Sleeping;')
s=s.replace('public struct Matrix4x4{','public struct Matrix4x4{public static Matrix4x4 Scale(Vector3 p)=>identity;')
s=s.replace('public enum ParticleSystemRenderMode{','public enum ParticleSystemRenderMode{VerticalBillboard,')
s+='\nnamespace UnityEngine{public enum LineAlignment{View,TransformZ}}'
s=s.replace('public class LineRenderer:Renderer{','public class LineRenderer:Renderer{public LineAlignment alignment;')
s=s.replace('public bool useUnscaledTime;', 'public bool useUnscaledTime,startSize3D;public float startSizeX,startSizeY,startSizeZ;')
s=s.replace('public class Transform:Object\n {','public class Transform:Object\n {public string name=>gameObject!=null?gameObject.name:"";')
s=s.replace('public class WolfCombat:Object{','public class WolfCombat:Object{public T GetComponent<T>()where T:new()=>new T();')
s=s.replace('public string family,resource;public int cost;}public static object Find(string id)=>new object();','public string id,title,family,resource;public int cost;}public static Entry Find(string id)=>new Entry();')
s=s.replace('public struct MainModule{public bool useUnscaledTime,startSize3D;', 'public struct MainModule{public ParticleSystemSimulationSpace simulationSpace;public float startRotation;public bool useUnscaledTime,startSize3D;')
s=s.replace('public class ParticleSystem:Object\n {','public class ParticleSystem:Object\n {public T GetComponent<T>()where T:new()=>new T();public struct TextureSheetAnimationModule{public bool enabled;public int numTilesX,numTilesY;public MinMaxCurve startFrame;public float frameOverTime;}public TextureSheetAnimationModule textureSheetAnimation=>new TextureSheetAnimationModule();')
s+='\nnamespace UnityEngine{public enum ParticleSystemSimulationSpace{Local,World}public enum ParticleSystemRenderMode{Billboard,HorizontalBillboard,VerticalBillboard}public class ParticleSystemRenderer:Renderer{public ParticleSystemRenderMode renderMode;}}'
s=s.replace('public static class Time{','public static class Time{public static int frameCount;')
s=s.replace('public class Keyboard{','public class Keyboard{public Controls.ButtonControl upArrowKey=new Controls.ButtonControl(),downArrowKey=new Controls.ButtonControl(),leftArrowKey=new Controls.ButtonControl(),rightArrowKey=new Controls.ButtonControl();')
# Execute the real GameFlow.Finish implementation so victory coverage cannot
# pass against a mock callback that never starts the actual sequence.
start=flow.index('public void Finish(bool win)');pos=flow.index('{',start);level=1;end=pos+1
while level:
 if flow[end]=='{':level+=1
 elif flow[end]=='}':level-=1
 end+=1
s+='\nnamespace Sunward {public sealed partial class GameFlow {'+flow[start:end]+'}}\n'
start=flow.index('void ClearBarrier()');pos=flow.index('{',start);level=1;end=pos+1
while level:
 if flow[end]=='{':level+=1
 elif flow[end]=='}':level-=1
 end+=1
s+='\nnamespace Sunward {public sealed partial class GameFlow {'+flow[start:end]+'}}\n'
s+='\nnamespace UnityEngine{public static class PlayerPrefs{static System.Collections.Generic.Dictionary<string,float> values=new System.Collections.Generic.Dictionary<string,float>();public static float GetFloat(string k,float d)=>values.TryGetValue(k,out var v)?v:d;public static void SetFloat(string k,float v){values[k]=v;}public static void Save(){}}}'
s=s.replace('public bool isPlaying,loop,playOnAwake;', 'public float time;public bool isPlaying,loop,playOnAwake;')
s=s.replace('public class Material:Object{', 'public class Material:Object{public void SetVectorArray(string n,Vector4[] v){}')
# API doubles for the awakening expansion; these do not validate Unity playback.
s=s.replace('public class WolfCombat:Object{','public class WolfCombat:Object{public void QueueAwakeningEquip(){}public Vector3 LightningSource=>transform.position+Vector3.up;')
s=s.replace('public static bool Buy(Sunward.ProfileData p,string id)=>false;','public static bool Owns(Sunward.ProfileData p,string id)=>p.owned!=null && System.Array.IndexOf(p.owned,id)>=0;public static bool Buy(Sunward.ProfileData p,string id)=>false;')
s=s.replace('public class Mesh:Object{','public class Mesh:Object{public Vector2[] uv;')
s=s.replace('public struct Vector3{','public struct Vector3{public void Normalize(){this=normalized;}')
s=s.replace('public class WolfInput{','public class WolfInput{public UnityEngine.InputSystem.InputAction Ultimate=new UnityEngine.InputSystem.InputAction();')
s=s.replace('public float MaxStamina=>100;', 'public float MaxStamina=>100+Profile.upgrades.stamina*15+Sunward.Remaster.HomeBlessings.StaminaBonus(Profile,Sunward.Remaster.HomeBlessings.Now);')
s=s.replace('public sealed class Rigidbody:Object{','public sealed class Rigidbody:Object{public bool useGravity;')
s=s.replace('public class BoxCollider:Object{','public class BoxCollider:Collider{public bool isTrigger;')
s=s.replace('public class Collider:Object{','public class Collider:Object{public Sunward.WolfMotor owner;public T GetComponentInParent<T>()where T:class=>owner as T;')
s=s.replace('public sealed partial class WolfMotor:MonoBehaviour\n {','public sealed partial class WolfMotor:MonoBehaviour\n {public int TeleportRevision;')
s=s.replace('public class Mesh:Object{','public class Mesh:Object{public Color[] colors;')
s=s.replace('public class AudioSource:Object{','public class AudioSource:Object{public float pitch=1;')
s=s.replace('public struct RaycastHit{','public struct RaycastHit{public Vector3 normal;')
s=s.replace('public sealed partial class GameFlow:MonoBehaviour\n {','public sealed partial class GameFlow:MonoBehaviour\n {public Remaster.ShiranuiUltimate Ultimate;')
if args.dump_doubles:Path(args.dump_doubles).write_text(s)
with tempfile.TemporaryDirectory(prefix='sunward-semantic-') as temp:
 d=Path(temp)/'Doubles.cs';d.write_text(s);cmd=[args.dotnet,'build',str(Path(__file__).with_name('Compile.csproj')),'--nologo','-p:SemanticDoubles='+str(d)]
 if args.negative_control:
  old=Path(temp)/'OrbitCameraBefore.cs';old.write_bytes(subprocess.check_output(['git','show','57ba25ea4d29e73ad80ec562add526909e17da17:Sunward-Unity/Assets/Sunward/Scripts/OrbitCamera.cs'],cwd=root));cmd+=['-p:OrbitSource='+str(old)]
 if args.river_negative_control:
  old=Path(temp)/'WaterContactBefore.cs';old.write_bytes(subprocess.check_output(['git','show','d70906a28725bcd7fabc17103b87039b3fc44b91:Sunward-Unity/Assets/Sunward/Scripts/WaterContact.cs'],cwd=root));cmd+=['-p:WaterSource='+str(old)]
 if args.street_spawn_negative_control:
  old=Path(temp)/'StreetBefore.cs';old.write_bytes(subprocess.check_output(['git','show','66029d8a8411860d47d3cc760a90c98b9951f88b:Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/VillageStreetPlay.cs'],cwd=root));cmd+=['-p:StreetSource='+str(old)]
 if args.charge_negative_control:
  old=Path(temp)/'NativeBefore.cs';old.write_bytes(subprocess.check_output(['git','show','4bb8a7409797ff8408d0284d989a526c061bf657:Sunward-Unity/Assets/OkamiRemaster/Player/NativeAmaterasu.cs'],cwd=root));cmd+=['-p:NativeBodySource='+str(old)]
 r=subprocess.run(cmd,cwd=root,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'),capture_output=True,text=True);print(r.stdout);print(r.stderr)
 if args.negative_control:
  assert r.returncode!=0 and 'CS0136' in r.stdout,'Compiler failed to catch original scope regression';print('Negative control caught original CS0136 camera regression')
 else:
  assert r.returncode==0,'Whole-script semantic compilation failed (engine doubles, not Unity)'
  command=[args.dotnet,str(Path(__file__).with_name('bin')/'Debug/net8.0/Compile.dll'),str(root/'Sunward-Unity/Assets')]
  if args.charge_negative_control:
   result=subprocess.run(command,capture_output=True,text=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'));assert result.returncode!=0 and 'Glaive release holds displaced final pose' in result.stderr,result.stdout+result.stderr;print('PASS negative control: old charged release fails the native recovery assertion')
  elif args.street_spawn_negative_control:
   result=subprocess.run(command,capture_output=True,text=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'));assert result.returncode!=0 and 'Original Okami actor could not load' in result.stderr,result.stdout+result.stderr;print('PASS negative control: original active-add order runs Awake before actor resources are assigned')
  elif args.river_negative_control:
   result=subprocess.run(command,capture_output=True,text=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'));assert result.returncode!=0 and 'River recovery ejects player' in result.stderr,result.stdout+result.stderr;print('PASS negative control: previous river code ejects player immediately after walking into a house')
  else:subprocess.run(command,check=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'))
