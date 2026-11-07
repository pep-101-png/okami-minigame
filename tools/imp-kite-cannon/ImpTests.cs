using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
using System.Text.Json;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
static class ImpTests
{
 const BindingFlags flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
 static void Set(object o,string n,object v)=>o.GetType().GetField(n,flags).SetValue(o,v);
 static object Get(object o,string n)=>o.GetType().GetField(n,flags).GetValue(o);
 static void Call(object o,string n)=>o.GetType().GetMethod(n,flags).Invoke(o,null);
 static void Check(bool yes,string msg){if(!yes)throw new Exception(msg);}
 static float[] V(Vector3 v)=>new[]{v.x,v.y,v.z};
 static float[] Q(Quaternion q)=>new[]{q.x,q.y,q.z,q.w};
 static float[][] Pose(OriginalActor a){var rig=(NativePaintedRig)Get(a,"rig");return rig.Bones.Select(b=>V(b.localPosition).Concat(Q(b.localRotation)).Concat(V(b.localScale)).ToArray()).ToArray();}
 static string Field(string text,string n)=>System.Text.RegularExpressions.Regex.Match(text,@"^  "+n+@": (.*)",System.Text.RegularExpressions.RegexOptions.Multiline).Groups[1].Value.Trim();
 static bool Alive(GameObject go){for(var t=go.transform;t!=null;t=t.parent)if(t.gameObject!=null && t.gameObject.wasDestroyed)return false;return true;}
 static object[] PaintFrames()
 {
  var result=new List<object>();foreach(var go in GameObject.created){if(!Alive(go))continue;var p=go.GetComponent<ImpCannonPaint>();if(p==null)continue;var layers=(Array)Get(p,"layers");if(layers==null)continue;foreach(var layer in layers){int count=(int)Get(layer,"count");if(count==0)continue;var mesh=(Mesh)Get(layer,"mesh");result.Add(new{sprite=(string)Get(layer,"sprite"),position=V(p.transform.position),vertices=mesh.vertices.Select(V).ToArray(),colors=mesh.colors.Select(c=>new[]{c.r,c.g,c.b,c.a}).ToArray(),uv=mesh.uv.Select(u=>new[]{u.x,u.y}).ToArray(),triangles=mesh.triangles});}}
  return result.ToArray();
 }
 static void CannonChecks(GameFlow game,OriginalActor actor)
 {
  game.Blocked=false;game.InTrial=true;CannonFixture.Player=game.Player;var data=actor.Imp.cannon;
  foreach(float dt in new[]{1f/15,1f/30,1f/60,1f/120})
  {
   Time.deltaTime=Time.unscaledDeltaTime=dt;game.Player.transform.position=new Vector3(35,0,7);int hits=game.hurtCount;
   var shell=ImpCannonProjectile.Spawn(game,new Vector3(35,1.7f,0),new Vector3(35,.55f,7),20,data);
   var p=shell.transform.position;game.Blocked=true;Call(shell,"Update");Check(Vector3.Distance(p,shell.transform.position)<.00001f,"Paused shell moved");game.Blocked=false;
   for(int j=0;j<300 && !shell.gameObject.wasDestroyed;j++){Time.time+=dt;Time.unscaledTime=Time.time;Call(shell,"Update");}
   Check(shell.gameObject.wasDestroyed && game.hurtCount==hits+1,"Swept cannon hit/explosion failed or damaged twice at "+dt);Call(shell,"Update");Check(game.hurtCount==hits+1,"Destroyed shell detonated again");
  }
  var clean=ImpCannonProjectile.Spawn(game,new Vector3(35,2,0),new Vector3(35,.55f,7),20,data);var legacy=new InkProjectile();SceneQuery.objects=new UnityEngine.Object[]{clean,legacy};Call(game,"ClearProjectiles");Check(clean.gameObject.wasDestroyed && legacy.gameObject.wasDestroyed,"Real cleanup left a cannon shell behind");SceneQuery.objects=Array.Empty<UnityEngine.Object>();
 }
 static void Main(string[] args)
 {
  Resources.Root=args[0];StreetActorLifecycle.Enabled=false;var root=args[1];
  foreach(var role in new[]{"wisp","reed","ranged","heavy","elite"})
  {
   GameObject.created.Clear();CannonFixture.Reset();Time.time=Time.unscaledTime=0;Time.deltaTime=Time.unscaledDeltaTime=1f/30;AudioSource.All.Clear();AudioSource.Events.Clear();
   var game=new GameFlow{InTrial=true,Panel="",Player=new WolfMotor(),Health=9999};game.Audio=new ValleyAudio();Set(game.Audio,"game",game);Call(game.Audio,"Awake");
   string def=File.ReadAllText(Path.Combine(Resources.Root,"Sunward/Generated/Spirit-"+role+".asset"));
   var spec=new EnemyDefinition{id=role,hp=100,damage=20,scale=float.Parse(Field(def,"scale")),speed=float.Parse(Field(def,"speed")),windup=float.Parse(Field(def,"windup"))};
   var go=new GameObject(role);var enemy=go.AddComponent<EnemyBrain>();enemy.game=game;enemy.definition=spec;enemy.Hp=enemy.MaxHp=100;
   enemy.transform.position=new Vector3(35,0,0);game.Player.transform.position=new Vector3(35,0,role=="ranged"?7:4.8f);
   var visual=new GameObject("original imp prefab");
   var actor=visual.AddComponent<OriginalActor>();string prefab=File.ReadAllText(Path.Combine(Resources.Root,"Sunward/Generated/Enemy-"+role+".prefab"));
   foreach(string f in new[]{"resource","idle","walk","run","windup","strike","recover","death"})typeof(OriginalActor).GetField(f).SetValue(actor,Field(prefab,f));
   actor.game=null;actor.modelScale=float.Parse(Field(prefab,"modelScale"));var off=System.Text.RegularExpressions.Regex.Match(prefab,@"modelOffset: \{x: ([^,]+), y: ([^,]+), z: ([^}]+)\}");actor.modelOffset=new Vector3(float.Parse(off.Groups[1].Value),float.Parse(off.Groups[2].Value),float.Parse(off.Groups[3].Value));actor.splitAttackClip=true;
   CharacterController.Target=game.Player.transform;spec.visual=visual;enemy.Init(game,spec);actor=(OriginalActor)Get(enemy,"nativeActor");
   Check(actor.Ready && actor.Imp!=null,role+" original prefab actor missing");var capsule=(CharacterController)Get(enemy,"motor");Check(Math.Abs(capsule.height-Math.Max(.85f,1.7f*actor.ImpWorldScale))<.001f,"Init capsule does not match native body scale");game.Enemies.Add(enemy);
   var released=new HashSet<ImpCannonProjectile>();var launches=new List<object>();var trace=new List<object>();var moves=new HashSet<string>();CannonFixture.Player=game.Player;var states=new HashSet<string>();float[][] frozen=null;bool firstAttack=false,contact=false;float lastPhase=-1;string previousState="";bool freezeApplied=false,stunApplied=false,deathApplied=false;int beforeShots=0;float nativeMaxY=0;
   for(int i=0;i<720;i++)
   {
    Time.time=Time.unscaledTime=i/30f;CannonFixture.Advance();
    foreach(var s in AudioSource.All)if(s.isPlaying && !s.loop && s.clip!=null && Time.time-s.started>s.clip.length)s.Stop();
    if(i==450){enemy.Freeze(.8f);frozen=Pose(actor);freezeApplied=true;}
    if(i==516){enemy.Stun(.2f);stunApplied=true;Check(enemy.State=="stagger","Hit must interrupt pending attack");enemy.Stun(.2f);Check(enemy.VisualStateProgress==0,"Repeated hit extended flinch");}
    if(i==660){enemy.Freeze(.8f);Check(enemy.Frozen,"Frozen defeat fixture missing");enemy.Damage(999,Vector3.zero,0);Check(!enemy.Frozen,"Defeat must release freeze before the fall");deathApplied=true;Check(enemy.Dead && game.rewards==1,"Death must reward once");}
    if(role=="ranged"){if(i>=210 && i<420)game.Player.transform.position=enemy.transform.position+new Vector3(0,0,2);else if(i>=420)game.Player.transform.position=new Vector3(35,0,7);}
    float mid=(enemy.transform.position.z+game.Player.transform.position.z)/2;Vector3 eye=new Vector3(41.4f,4.8f,mid+7.8f),target=new Vector3(35,1,mid),aim=target-eye;Camera.main.transform.rotation=Quaternion.Euler(-MathF.Atan2(aim.y,MathF.Sqrt(aim.x*aim.x+aim.z*aim.z))*Mathf.Rad2Deg,MathF.Atan2(aim.x,aim.z)*Mathf.Rad2Deg,0);
    if(Alive(go)){Call(enemy,"Update");Call(actor,"LateUpdate");}
    foreach(var node in GameObject.created.ToArray()){var shell=node.GetComponent<ImpCannonProjectile>();if(shell==null || released.Contains(shell))continue;released.Add(shell);Check(enemy.State=="strike" && actor.Imp.IsCannon(enemy.ActiveMove) && enemy.VisualStateProgress>=actor.Imp.Contact(enemy.ActiveMove),"Shell released outside its firing event");Check(Vector3.Distance(shell.transform.position,actor.CannonMuzzle)<.001f,"Shell did not use this frame's muzzle");launches.Add(new{time=Time.time,muzzle=V(actor.CannonMuzzle),source=actor.CurrentSourceTime,clip=actor.CurrentSourceMotion});}
    foreach(var go2 in GameObject.created.ToArray()){if(!Alive(go2))continue;var shell=go2.GetComponent<ImpCannonProjectile>();if(shell!=null)Call(shell,"Update");}
    foreach(var go2 in GameObject.created.ToArray()){if(!Alive(go2))continue;var paint=go2.GetComponent<ImpCannonPaint>();if(paint!=null){Call(paint,"Update");if(Alive(go2))Call(paint,"LateUpdate");}}
    if(enemy.ActiveMove!=null)moves.Add(enemy.ActiveMove);
    if(i>450 && i<471)Check(JsonSerializer.Serialize(frozen)==JsonSerializer.Serialize(Pose(actor)),"Freeze pose moved");
    states.Add(enemy.State);nativeMaxY=Math.Max(nativeMaxY,Pose(actor)[0][1]);
    if(enemy.State=="windup")firstAttack=true;
    if(enemy.State=="strike" && firstAttack && enemy.VisualStateProgress>=actor.Imp.Contact(enemy.ActiveMove))contact=true;
    if(previousState=="strike" && enemy.State=="recover"){beforeShots=game.shots;}
    if(!(actor.Imp.Action(enemy.ActiveMove)?.separate??actor.Imp.separate) && (enemy.State=="windup" || enemy.State=="strike" || enemy.State=="recover")){
     if(previousState=="windup" && enemy.State=="strike" || previousState=="strike" && enemy.State=="recover")Check(actor.CurrentSourceTime>=lastPhase-.002f,"Attack jumped backwards between states");
     lastPhase=actor.CurrentSourceTime;
    }
    previousState=enemy.State;
    trace.Add(new{t=Time.time,state=enemy.State,clip=actor.CurrentSourceMotion,sourceTime=actor.CurrentSourceTime,visible=Alive(go),position=V(enemy.transform.position),rotation=Q(enemy.transform.rotation),modelScale=actor.modelScale,scale=spec.scale,offset=V(actor.modelOffset),pose=Pose(actor),frozen=enemy.Frozen,move=enemy.ActiveMove,hero=V(game.Player.transform.position),eye=V(eye),target=V(target),shells=GameObject.created.Where(o=>Alive(o) && o.GetComponent<ImpCannonProjectile>()!=null).Select(o=>new{position=V(o.transform.position),velocity=V(o.GetComponent<ImpCannonProjectile>().Velocity)}).ToArray(),paint=PaintFrames(),hits=game.hurtCount});
   }
   Check(firstAttack && contact && states.Contains("recover") && states.Contains("stagger") && states.Contains("dead"),role+" coverage missing");Check(freezeApplied && stunApplied && deathApplied,"Missing transitions");Check(actor.CurrentSourceMotion==actor.Imp.Clip("dead"),"Dead imp returned upright");Check(moves.Count>=2,role+" never varied its native attack");
   if(role=="wisp")Check(nativeMaxY>1,"Authored jumping attack lost original root height");
   File.WriteAllText(Path.Combine(root,role+"-runtime.json"),JsonSerializer.Serialize(new{role,resource=actor.resource,scope="Actual C# state/pose/audio drivers; API doubles and flat floor; offline render, not Unity Play Mode",launches=launches,fps=30,frames=trace,audio=AudioSource.Events,actions=moves.ToArray()}));
   if(role=="ranged"){Check(released.Count>=2,"Cannon never fired multiple shots");Check(moves.Contains("kick-left") && moves.Contains("kick-right"),"Close-range original kick variants missing");CannonChecks(game,actor);}
   Console.WriteLine(role+": attack/contact/recovery, interrupted attack, exact frozen pose and held defeat captured");
  }
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
