"""Compile whole camera, cinematic, audio and native drivers with explicit engine doubles."""
from pathlib import Path
import tempfile,subprocess,os,re,argparse
root=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--dotnet',default='dotnet');p.add_argument('--negative-control',action='store_true');args=p.parse_args()
s=(root/'tools/spirit-charge-home/tests/RuntimeDoubles.cs').read_text()
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
s=s.replace('public bool Blocked,CinematicActive,InTrial,BossTrial,waiting;', 'public ValleyAudio Audio;public bool Blocked,CinematicActive,InTrial,BossTrial,waiting;')
s=s.replace('public class VillageServices:Object{', 'public class VillageServices:Object{public static bool InFoodHouse(Vector3 p)=>false;')
s=s.replace('public LensSettings Lens=new LensSettings', 'public UnityEngine.Transform transform=new UnityEngine.Transform();public LensSettings Lens=new LensSettings')
s=s.replace('public class Camera:Object\n {','public class Camera:Object\n {public Transform transform=new Transform();').replace('public bool isPlaying,loop,playOnAwake;','public Transform transform=new Transform();public bool isPlaying,loop,playOnAwake;').replace('public static Vector3 back=>','public static float Distance(Vector3 a,Vector3 b)=>(a-b).magnitude;public static Vector3 back=>')
s+='\n'+(Path(__file__).with_name('ExtraDoubles.cs')).read_text()
# Compile the actual boss, native actor and tendril scripts as well.
s=re.sub(r' public class CrimsonHelmAscension:Object[^\n]*\n','',s)
s=s.replace('public T GetComponent<T>()where T:class=>null;', 'public T GetComponent<T>()where T:class=>gameObject.GetComponent<T>();public T GetComponentInParent<T>()where T:class=>null;public T GetComponentInChildren<T>(bool b=false)where T:class=>null;')
s=s.replace('public static void Destroy(Object x){', 'public static T Instantiate<T>(T x,Transform parent)where T:Object=>x;public static void Destroy(Object x,float delay){Destroy(x);}public static void Destroy(Object x){')
s=s.replace('public Transform transform;public bool activeSelf;', 'public int layer;public Transform transform;public bool activeSelf;')
s=s.replace('public class Renderer:Object{public bool enabled;}', 'public class Renderer:Object{public bool enabled;}')
s=s.replace('public Mesh sharedMesh=new Mesh();}', 'public Bounds localBounds;public bool updateWhenOffscreen;public Mesh sharedMesh=new Mesh();}')
s=s.replace('public void SetParent(Transform parent', 'public T GetComponentInChildren<T>(bool b=false)where T:class=>null;public void Rotate(float x,float y,float z){}public void SetParent(Transform parent')
s=s.replace('public static float Sin(float x)', 'public static float Ceil(float x)=>MathF.Ceiling(x);public static float Cos(float x)=>MathF.Cos(x);public static float Sin(float x)')
s=s.replace('public static float Distance(Vector3 a,Vector3 b)', 'public static float Dot(Vector3 a,Vector3 b)=>a.x*b.x+a.y*b.y+a.z*b.z;public static float Distance(Vector3 a,Vector3 b)')
s=s.replace('public class CharacterController{public bool enabled=true;}', 'public class CharacterController: Object{public bool enabled=true;public float radius,height;public Vector3 center;public void Move(Vector3 delta){}}')
s=s.replace('public void StopMotion(){}','public void StopMotion(){}public void Teleport(Vector3 p){transform.position=p;}')
s=s.replace('public void ClearProjectiles(){', 'public VisualFx Fx=new VisualFx();public void TrackBossTransformation(Remaster.CrimsonHelmAscension c){BossTransformation=c;}public void ReleaseBossTransformation(Remaster.CrimsonHelmAscension c){if(BossTransformation==c)BossTransformation=null;}public void Reward(EnemyBrain b){}public void Hurt(float damage,Vector3 away){}public void Projectile(Vector3 p,Vector3 d,float damage,bool flame=false){}public void ClearProjectiles(){')
s=s.replace('public static int leaves;', 'public static Vector3 Centre=>new Vector3(35,-110,0);public static Vector3 Guard(Vector3 p)=>p;public static bool Height(Vector3 p,out float floor){floor=-110;return true;}public static int leaves;')
s=s.replace('components[typeof(T)]=c;return c;', 'if(c is MonoBehaviour m)m.gameObject=this;components[typeof(T)]=c;return c;')
s=s.replace('public void Reward(EnemyBrain b){}', 'public int rewards;public void Reward(EnemyBrain b){rewards++;}')
s+='\n'+Path(__file__).with_name('RebirthDoubles.cs').read_text()
with tempfile.TemporaryDirectory(prefix='sunward-semantic-') as temp:
 d=Path(temp)/'Doubles.cs';d.write_text(s);cmd=[args.dotnet,'build',str(Path(__file__).with_name('Compile.csproj')),'--nologo','-p:SemanticDoubles='+str(d)]
 if args.negative_control:
  old=Path(temp)/'OrbitCameraBefore.cs';old.write_bytes(subprocess.check_output(['git','show','57ba25ea4d29e73ad80ec562add526909e17da17:Sunward-Unity/Assets/Sunward/Scripts/OrbitCamera.cs'],cwd=root));cmd+=['-p:OrbitSource='+str(old)]
 r=subprocess.run(cmd,cwd=root,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'),capture_output=True,text=True);print(r.stdout);print(r.stderr)
 if args.negative_control:
  assert r.returncode!=0 and 'CS0136' in r.stdout,'Compiler failed to catch original scope regression';print('Negative control caught original CS0136 camera regression')
 else:
  assert r.returncode==0,'Whole-script semantic compilation failed (engine doubles, not Unity)'
  subprocess.run([args.dotnet,str(Path(__file__).with_name('bin')/'Debug/net8.0/Compile.dll'),str(root/'Sunward-Unity/Assets')],check=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'))
