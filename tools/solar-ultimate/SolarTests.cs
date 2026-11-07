using System;using System.IO;using System.Linq;using System.Reflection;using System.Collections.Generic;using System.Text.Json;using UnityEngine;using Unity.Cinemachine;using Sunward;using Sunward.Remaster;
static class SolarTests
{
 const BindingFlags F=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;static int checks;
 static void Check(bool b,string msg){checks++;if(!b)throw new Exception(msg);}
 static void Call(object o,string n)=>o.GetType().GetMethod(n,F).Invoke(o,null);
 static object Get(object o,string n)=>o.GetType().GetField(n,F).GetValue(o);
 static void Set(object o,string n,object v)=>o.GetType().GetField(n,F).SetValue(o,v);
 static float[] V(Vector3 v)=>new[]{v.x,v.y,v.z};static float[] Q(Quaternion q)=>new[]{q.x,q.y,q.z,q.w};
 static float[][] Pose(NativePaintedRig rig)=>rig.Bones.Select(b=>V(b.localPosition).Concat(Q(b.localRotation)).Concat(V(b.localScale)).ToArray()).ToArray();
 static bool Alive(GameObject go){for(var t=go.transform;t!=null;t=t.parent)if(t.gameObject!=null && t.gameObject.wasDestroyed)return false;return true;}
 static GameFlow Game()
 {
  GameObject.created.Clear();CannonFixture.Reset();AudioSource.All.Clear();AudioSource.Events.Clear();Time.time=Time.unscaledTime=0;Time.deltaTime=Time.unscaledDeltaTime=1f/30;
  var root=new GameObject("Actual player pose fixture");var p=root.AddComponent<WolfMotor>();var g=new GameFlow{InTrial=true,Panel="",Player=p,Health=100};p.game=g;p.Grounded=true;p.transform.position=new Vector3(35,0,0);CharacterController.Target=p.transform;
  var native=root.AddComponent<NativeAmaterasu>();Call(native,"Awake");Check(native.Ready,"Native player did not load");Check(native.ApplyPowerForm(2),"ES3A did not load");
  g.Audio=new ValleyAudio();Set(g.Audio,"game",g);Call(g.Audio,"Awake");
  var camera=new OrbitCamera{target=p,virtualCamera=new CinemachineCamera()};camera.virtualCamera.Lens=new LensSettings{FieldOfView=50};MonoBehaviour.CameraInstance=camera;Camera.main.transform=camera.virtualCamera.transform;
  g.Ultimate=new ShiranuiUltimate{game=g};return g;
 }
 static string Field(string s,string name)=>System.Text.RegularExpressions.Regex.Match(s,@"^  "+name+@": (.*)",System.Text.RegularExpressions.RegexOptions.Multiline).Groups[1].Value.Trim();
 static EnemyBrain Enemy(GameFlow g,string role,int index)
 {
  var go=new GameObject(role);go.transform.position=new Vector3(35+Mathf.Sin(index*1.2566f)*8,0,Mathf.Cos(index*1.2566f)*8);var e=go.AddComponent<EnemyBrain>();
  var prefab=new GameObject("native imp prefab");var a=prefab.AddComponent<OriginalActor>();string text=File.ReadAllText(Path.Combine(Resources.Root,"Sunward/Generated/Enemy-"+role+".prefab"));
  foreach(string n in new[]{"resource","idle","walk","run","windup","strike","recover","death"})typeof(OriginalActor).GetField(n).SetValue(a,Field(text,n));a.modelScale=float.Parse(Field(text,"modelScale"));var o=System.Text.RegularExpressions.Regex.Match(text,@"modelOffset: \{x: ([^,]+), y: ([^,]+), z: ([^}]+)\}");a.modelOffset=new Vector3(float.Parse(o.Groups[1].Value),float.Parse(o.Groups[2].Value),float.Parse(o.Groups[3].Value));
  string def=File.ReadAllText(Path.Combine(Resources.Root,"Sunward/Generated/Spirit-"+role+".asset"));e.Init(g,new EnemyDefinition{id=role,hp=400,damage=20,scale=float.Parse(Field(def,"scale")),speed=float.Parse(Field(def,"speed")),visual=prefab});g.Enemies.Add(e);return e;
 }
 static object[] Paint()
 {
  var result=new List<object>();foreach(var go in GameObject.created){if(!Alive(go))continue;var p=go.GetComponent<SolarPaint>();if(p==null)continue;var layers=(Array)Get(p,"layers");if(layers==null)continue;foreach(var l in layers){var mesh=(Mesh)Get(l,"mesh");result.Add(new{sprite=(string)Get(l,"sprite"),position=V(p.transform.position),vertices=mesh.vertices.Select(V).ToArray(),colors=mesh.colors.Select(c=>new[]{c.r,c.g,c.b,c.a}).ToArray(),uv=mesh.uv.Select(v=>new[]{v.x,v.y}).ToArray(),triangles=mesh.triangles});}}
  return result.ToArray();
 }
 static void Effects()
 {
  foreach(var go in GameObject.created.ToArray()){if(!Alive(go))continue;var p=go.GetComponent<SolarPaint>();if(p!=null){Call(p,"Update");if(Alive(go))Call(p,"LateUpdate");}}
 }
 static void Main(string[] args)
 {
  Resources.Root=args[0];var output=args[1];StreetActorLifecycle.Enabled=false;
  foreach(int fps in new[]{15,30,60,120})
  {
   var g=Game();var e=Enemy(g,"wisp",0);Check(g.Ultimate.Begin(),"Third form ultimate failed");Check(!g.Ultimate.Begin(),"Reentrant ultimate");
   Time.unscaledDeltaTime=1f/fps;Time.deltaTime=0;
   for(int i=0;i<fps*7;i++){Time.unscaledTime=i/(float)fps;Call(g.Ultimate,"Update");if(g.Ultimate.Playing)Call(g.Player.GetComponent<NativeAmaterasu>(),"LateUpdate");if(g.Ultimate.Playing && g.Ultimate.Detonated)Check(e.Dead,"Damage did not land on flash");}
   Check(!g.Ultimate.Playing && !g.Player.Locked && e.Dead,"Ultimate did not finish/restore");Check(!g.Ultimate.Begin(),"Second use in same fight");Check(Vector3.Distance(g.Player.transform.position,new Vector3(35,0,0))<.0001f,"Player failed exact return");
   g.Ultimate.ResetFight();g.Enemies.Clear();Enemy(g,"reed",1);Check(g.Ultimate.Begin(),"Next fight reuse failed");g.Ultimate.Skip();Check(g.Enemies.All(x=>x.Dead)&&!g.Player.Locked,"Skip lost damage or control");
   g.Ultimate.ResetFight();g.Enemies.Clear();e=Enemy(g,"ranged",2);Check(g.Ultimate.Begin(),"Cancel begin failed");g.Ultimate.Cancel();Check(!e.Dead&&!g.Player.Locked&&!g.Ultimate.Playing,"Cancel inflicted damage/locked control");
   g.Ultimate.ResetFight();g.Player.GetComponent<NativeAmaterasu>().ApplyPowerForm(1);Check(!g.Ultimate.Begin(),"Second form ultimate allowed");
  }
  {
   var g=Game();var roles=new[]{"wisp","reed","ranged","heavy","elite"};for(int i=0;i<roles.Length;i++)Enemy(g,roles[i],i);var body=g.Player.GetComponent<NativeAmaterasu>();var camera=(OrbitCamera)MonoBehaviour.CameraInstance;Check(g.Ultimate.Begin(),"Capture begin failed");var frames=new List<object>();
   for(int i=0;i<222;i++)
   {
    Time.unscaledTime=i/30f;Time.unscaledDeltaTime=1f/30;Time.deltaTime=g.Ultimate.Playing?0:1f/30;Time.time+=Time.deltaTime;CannonFixture.Advance();Call(g.Ultimate,"Update");Call(body,"LateUpdate");
    foreach(var e in g.Enemies){if(!Alive(e.gameObject))continue;var a=(OriginalActor)Get(e,"nativeActor");Call(a,"LateUpdate");}
    Call(camera,"LateUpdate");Effects();var rig=(NativePaintedRig)Get(body,"rig");
    if(g.Ultimate.Playing)Check(Vector3.Distance(body.Torso.position,g.Ultimate.SunCentre)<.001f,"Wolf not centered in sun");
    frames.Add(new{t=i/30f,playing=g.Ultimate.Playing,detonated=g.Ultimate.Detonated,centre=V(g.Ultimate.SunCentre),hero=V(g.Player.transform.position),rotation=Q(g.Player.transform.rotation),bodyPosition=V(rig.Root.transform.position),bodyRotation=Q(rig.Root.transform.rotation),bodyScale=V(rig.Root.transform.lossyScale),pose=Pose(rig),eye=V(camera.virtualCamera.transform.position),cameraRotation=Q(camera.virtualCamera.transform.rotation),fov=camera.virtualCamera.Lens.FieldOfView,charge=Get(g.Audio,"solarCharge") is AudioSource audio?new{playing=audio.isPlaying,gain=audio.volume,pitch=audio.pitch}:null,paint=Paint(),enemies=g.Enemies.Select(e=>{var a=(OriginalActor)Get(e,"nativeActor");var er=(NativePaintedRig)Get(a,"rig");return new{resource=a.resource,visible=Alive(e.gameObject),position=V(e.transform.position),rotation=Q(e.transform.rotation),scale=a.ImpWorldScale,offset=V(a.modelOffset*e.definition.scale),pose=Pose(er),hp=e.Hp,dead=e.Dead};}).ToArray()});
   }
   File.WriteAllText(Path.Combine(output,"ultimate-runtime.json"),JsonSerializer.Serialize(new{fps=30,frames,audio=AudioSource.Events}));
  }
  {
   var g=Game();var camera=(OrbitCamera)MonoBehaviour.CameraInstance;FallingDivineSword.Begin(g,new Vector3(35,0,0));var sword=GameObject.created.Last(o=>o.GetComponent<FallingDivineSword>()!=null);var driver=sword.GetComponent<FallingDivineSword>();var blade=(GameObject)Get(driver,"blade");var visual=blade.GetComponent<OriginalVisual>();var rig=(NativePaintedRig)Get(visual,"rig");var frames=new List<object>();
   for(int i=0;i<54;i++){Time.unscaledTime=Time.time=i/30f;Time.deltaTime=Time.unscaledDeltaTime=1f/30;CannonFixture.Advance();if(Alive(sword)){Call(driver,"Update");Call(blade.GetComponent<EighthWonderMotion>(),"Update");}Call(camera,"LateUpdate");Effects();if(i==11)Check((bool)Get(driver,"landed"),"Sword slower than requested .36s impact");frames.Add(new{t=i/30f,visible=Alive(sword),position=V(rig.Root.transform.position),rotation=Q(rig.Root.transform.rotation),scale=V(rig.Root.transform.lossyScale),pose=Pose(rig),paint=Paint(),eye=V(camera.virtualCamera.transform.position),cameraRotation=Q(camera.virtualCamera.transform.rotation),fov=camera.virtualCamera.Lens.FieldOfView});}
   File.WriteAllText(Path.Combine(output,"sword-runtime.json"),JsonSerializer.Serialize(new{fps=30,frames,audio=AudioSource.Events}));
  }
  Console.WriteLine("Reviewed fixture: "+checks+" actual source state, centered pose, flash-time damage, once/fight, skip/cancel, second-form rejection and fast sword-impact assertions. API doubles, not Unity.");
 }
}

static class CannonFixture
{
 static readonly List<(UnityEngine.Object target,float when)> delayed=new();
 public static void Reset(){delayed.Clear();SceneQuery.objects=Array.Empty<UnityEngine.Object>();}
 public static void Delay(UnityEngine.Object target,float delay){if(delay<=0)UnityEngine.Object.Destroy(target);else delayed.Add((target,Time.time+delay));}
 public static void Advance(){for(int i=delayed.Count-1;i>=0;i--)if(Time.time>=delayed[i].when){UnityEngine.Object.Destroy(delayed[i].target);delayed.RemoveAt(i);}}
 public static WolfMotor Player;static readonly Collider ground=new Collider();static readonly Collider body=new Collider();
 public static bool Cast(Vector3 p,float radius,Vector3 dir,out RaycastHit hit,float distance,int mask)
 {
  hit=new RaycastHit();float nearest=distance+1;
  if((mask&(1<<6))!=0 && dir.y<-.00001f){float t=(radius-p.y)/dir.y;if(t>=0 && t<=distance){nearest=t;hit=new RaycastHit{collider=ground,distance=t,normal=Vector3.up,point=p+dir*t-Vector3.up*radius};}}
  if(Player!=null && (mask&(1<<7))!=0){Vector3 center=Player.transform.position+Vector3.up*.55f,q=p-center;float r=radius+.35f,b=Vector3.Dot(q,dir),c=q.sqrMagnitude-r*r,d=b*b-c;if(d>=0){float t=-b-MathF.Sqrt(d);if(t>=0 && t<=distance && t<nearest){body.owner=Player;Vector3 pos=p+dir*t;var normal=(pos-center).normalized;nearest=t;hit=new RaycastHit{collider=body,distance=t,normal=normal,point=pos-normal*radius};}}}
  return nearest<=distance;
 }
}
