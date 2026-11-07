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
 static void Main(string[] args)
 {
  Resources.Root=args[0];StreetActorLifecycle.Enabled=false;var root=args[1];
  foreach(var role in new[]{"wisp","reed","ranged","heavy","elite"})
  {
   Time.time=Time.unscaledTime=0;Time.deltaTime=Time.unscaledDeltaTime=1f/60;AudioSource.All.Clear();AudioSource.Events.Clear();
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
   var trace=new List<object>();var states=new HashSet<string>();float[][] frozen=null;bool firstAttack=false,contact=false;float lastPhase=-1;string previousState="";bool freezeApplied=false,stunApplied=false,deathApplied=false;int beforeShots=0;float nativeMaxY=0;
   for(int i=0;i<720;i++)
   {
    Time.time=Time.unscaledTime=i/60f;
    foreach(var s in AudioSource.All)if(s.isPlaying && !s.loop && s.clip!=null && Time.time-s.started>s.clip.length)s.Stop();
    if(i==300){enemy.Freeze(.8f);frozen=Pose(actor);freezeApplied=true;}
    if(i==420){enemy.Stun(.2f);stunApplied=true;Check(enemy.State=="stagger","Hit must interrupt pending attack");enemy.Stun(.2f);Check(enemy.VisualStateProgress==0,"Repeated hit extended flinch");}
    if(i==610){enemy.Freeze(.8f);Check(enemy.Frozen,"Frozen defeat fixture missing");enemy.Damage(999,Vector3.zero,0);Check(!enemy.Frozen,"Defeat must release freeze before the fall");deathApplied=true;Check(enemy.Dead && game.rewards==1,"Death must reward once");}
    Call(enemy,"Update");Call(actor,"LateUpdate");
    if(i>300 && i<346)Check(JsonSerializer.Serialize(frozen)==JsonSerializer.Serialize(Pose(actor)),"Freeze pose moved");
    states.Add(enemy.State);nativeMaxY=Math.Max(nativeMaxY,Pose(actor)[0][1]);
    if(enemy.State=="windup")firstAttack=true;
    if(enemy.State=="strike" && firstAttack){if(enemy.VisualStateProgress<actor.Imp.StrikeContact)Check(game.shots==beforeShots,"Projectile released before native contact");if(enemy.VisualStateProgress>=actor.Imp.StrikeContact)contact=true;}
    if(previousState=="strike" && enemy.State=="recover"){if(role=="ranged")Check(game.shots==beforeShots+1,"One projectile per shot animation");beforeShots=game.shots;}
    if(!actor.Imp.separate && (enemy.State=="windup" || enemy.State=="strike" || enemy.State=="recover")){
     if(previousState=="windup" && enemy.State=="strike" || previousState=="strike" && enemy.State=="recover")Check(actor.CurrentSourceTime>=lastPhase-.002f,"Attack jumped backwards between states");
     lastPhase=actor.CurrentSourceTime;
    }
    previousState=enemy.State;
    trace.Add(new{t=Time.time,state=enemy.State,clip=actor.CurrentSourceMotion,sourceTime=actor.CurrentSourceTime,position=V(enemy.transform.position),rotation=Q(enemy.transform.rotation),modelScale=actor.modelScale,scale=spec.scale,offset=V(actor.modelOffset),pose=Pose(actor),frozen=enemy.Frozen,shots=game.shots,hits=game.hurtCount});
   }
   Check(firstAttack && contact && states.Contains("recover") && states.Contains("stagger") && states.Contains("dead"),role+" coverage missing");Check(freezeApplied && stunApplied && deathApplied,"Missing transitions");Check(actor.CurrentSourceMotion=="em00_032","Dead imp returned upright");
   if(role=="wisp")Check(nativeMaxY>1,"Authored jumping attack lost original root height");
   File.WriteAllText(Path.Combine(root,role+"-runtime.json"),JsonSerializer.Serialize(new{role,resource=actor.resource,scope="Actual C# state/pose/audio drivers; API doubles and flat floor; offline render, not Unity Play Mode",frames=trace,audio=AudioSource.Events}));
   Console.WriteLine(role+": attack/contact/recovery, interrupted attack, exact frozen pose and held defeat captured");
  }
 }
}
