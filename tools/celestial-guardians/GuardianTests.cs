using System;using System.Linq;using System.IO;using System.Reflection;using System.Collections.Generic;using System.Text.Json;using Unity.Cinemachine;using UnityEngine;using Sunward;using Sunward.Remaster;
class GuardianTests
{
 const BindingFlags F=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
 static object Get(object o,string name)=>o.GetType().GetField(name,F).GetValue(o);
 static void Set(object o,string name,object value)=>o.GetType().GetField(name,F).SetValue(o,value);
 static void Call(object o,string name)=>o.GetType().GetMethod(name,F).Invoke(o,null);
 static float[] V(Vector3 v)=>new[]{v.x,v.y,v.z};static float[] Q(Quaternion q)=>new[]{q.x,q.y,q.z,q.w};
 static float[][] Pose(NativePaintedRig r)=>r.Bones.Select(b=>V(b.localPosition).Concat(Q(b.localRotation)).Concat(V(b.localScale)).ToArray()).ToArray();
 static int n;static void Check(bool v,string why){n++;if(!v)throw new Exception(why);}
 static void Main(string[] args)
 {
  Resources.Root=args[0];
  var p=new ProfileData();Check(!ProgressionRules.DawnReady(p),"Fresh profile gate");Check(ProgressionRules.Validate(p),"Existing save remains valid");
  p.bossWins=1;p.xp=35*19*19;Check(HeavenlyGarden.RiverOpen(p),"Crimson unlocks river");
  foreach(var id in ProgressionRules.Upgrades)while(p.upgrades.Get(id)<ProgressionRules.Cap(id))p.upgrades.Add(id);
  Check(ProgressionRules.DawnReady(p),"Level20 all base paths allows first guardian");p.xp=35*18*18;Check(!ProgressionRules.DawnReady(p),"Level19 blocked");p.xp=35*19*19;
  p.upgrades.vitality--;Check(!ProgressionRules.DawnReady(p),"Missing single rank blocks first");p.upgrades.vitality++;
  p.shiranuiUnlock=1;Check(!ProgressionRules.DawnReady(p),"First guardian cannot farm unlock twice");Check(!ProgressionRules.Advanced(p),"Second form alone does not expand ranks");
  p.xp=35*29*29;Check(ProgressionRules.Advanced(p),"Second form and level30 expand ranks");
  foreach(var id in ProgressionRules.Upgrades){Check(ProgressionRules.Cap(p,id)==ProgressionRules.Cap(id)+5,"Five new ranks per path");while(p.upgrades.Get(id)<ProgressionRules.Cap(p,id))p.upgrades.Add(id);}
  Check(ProgressionRules.EclipseReady(p),"All advanced paths allow second guardian");Check(ProgressionRules.Validate(p),"Advanced ranks survive save validation");p.upgrades.ability--;Check(!ProgressionRules.EclipseReady(p),"One missing advanced rank blocks third form");p.upgrades.ability++;
  p.shiranuiUnlock=2;Check(!ProgressionRules.EclipseReady(p),"Third unlock cannot repeat");Check(ProgressionRules.Validate(p),"Final profile valid");
  Check(CelestialTrialGate.Crosses(new Vector3(0,0,-3),new Vector3(0,0,3)),"Fast walk crossing works");Check(!CelestialTrialGate.Crosses(new Vector3(4,0,-3),new Vector3(4,0,3)),"Outside posts ignored");
  foreach(var c in new[]{CelestialTrials.DawnCentre,CelestialTrials.EclipseCentre}){Check(CelestialTrials.Floor(c,out var y)&&y==c.y,"Independent arena floor");Check(HeavenlyGarden.Inside(c),"Arena is isolated heavenly realm");}
  foreach(int kind in new[]{1,2})
  {
   GameObject.created.Clear();var player=new GameObject("player").AddComponent<WolfMotor>();var game=new GameFlow{Player=player,Panel="",Health=100};player.game=game;game.Combat.allowEquip=true;game.Heaven=new HeavenlyGarden{game=game};game.Transformation.game=game;
   game.Profile.bossWins=1;game.Profile.xp=35*29*29;game.Profile.shiranuiUnlock=kind-1;
   foreach(var id in ProgressionRules.Upgrades)while(game.Profile.upgrades.Get(id)<ProgressionRules.Cap(game.Profile,id))game.Profile.upgrades.Add(id);
   var camera=new OrbitCamera{target=player,virtualCamera=new CinemachineCamera()};camera.virtualCamera.Lens=new LensSettings{FieldOfView=50};MonoBehaviour.CameraInstance=camera;Camera.main.transform=camera.virtualCamera.transform;
   game.Audio=new ValleyAudio();Set(game.Audio,"game",game);Call(game.Audio,"Awake");
   var native=player.gameObject.AddComponent<NativeAmaterasu>();Call(native,"Awake");Check(native.Ready,"Native player loads for earned awakening");
   var trial=new CelestialTrials{game=game};game.Celestial=trial;Call(trial,"Start");Check(trial.Enter(kind),"Eligible passage starts trial");Check(game.InTrial && game.BossTrial && game.Enemies.Count==1,"Actual GameFlow starts single guardian");trial.Skip();Check(!trial.Playing && !player.Locked,"Intro skip returns control");
   var enemy=game.Enemies[0];var actors=enemy.GetComponentsInChildren<OriginalActor>(true);Check(actors.Length==(kind==1?1:2),"Complete guardian body/companion assembly");foreach(var a in actors)Check(a.Ready,"Original model and source bank load");var driver=enemy.GetComponent<CelestialGuardian>();Check(driver!=null,"Guardian driver installed");
   var arena=(GameObject)Get(trial,kind==1?"dawnArena":"eclipseArena");var props=GameObject.created.Where(o=>o.transform.IsChildOf(arena.transform)).Select(o=>o.GetComponent<OriginalVisual>()).Where(v=>v!=null).Select(v=>{var r=(NativePaintedRig)Get(v,"rig");return new{resource=r.Resource,position=V(r.Root.transform.position),rotation=Q(r.Root.transform.rotation),scale=V(r.Root.transform.lossyScale)};}).ToArray();File.WriteAllText(Path.Combine(args[1],"arena-"+kind+".json"),JsonSerializer.Serialize(props));
   game.Health=100000;var frames=new List<object>();var seen=new HashSet<string>();
   for(int i=0;i<720;i++)
   {
    Time.deltaTime=Time.unscaledDeltaTime=1f/30;Time.time=Time.unscaledTime=i/30f;player.transform.position=trial.ArenaCentre+new Vector3(Mathf.Sin(i*.018f)*6,.05f,Mathf.Cos(i*.018f)*5);if(enemy.ActiveMove=="slam" && (enemy.State=="windup" || enemy.State=="strike"))player.transform.position=enemy.transform.position+Vector3.forward*3;Call(driver,"Update");Call(enemy,"Update");foreach(var a in actors)Call(a,"LateUpdate");seen.Add(enemy.State+":"+enemy.ActiveMove);
    Call(camera,"LateUpdate");var rig=(NativePaintedRig)Get(actors[0],"rig");var captured=actors.Select(a=>{var r=(NativePaintedRig)Get(a,"rig");return new{a.resource,position=V(r.Root.transform.position),rotation=Q(r.Root.transform.rotation),scale=V(r.Root.transform.lossyScale),pose=Pose(r),clip=a.CurrentSourceMotion};}).ToArray();
    frames.Add(new{t=i/30f,state=enemy.State,move=enemy.ActiveMove,eye=V(camera.virtualCamera.transform.position),cameraRotation=Q(camera.virtualCamera.transform.rotation),fov=camera.virtualCamera.Lens.FieldOfView,position=V(enemy.transform.position),hero=V(player.transform.position),actors=captured});
   }
   foreach(var move in new[]{"charge","slam","fan"})Check(seen.Contains("strike:"+move),"Native attack cycle reaches "+move);Check(game.shotCount>0,"Fan actually releases ranged attacks");Check(game.hurtCount>0,"Attack contact deals real fixture damage");
   File.WriteAllText(Path.Combine(args[1],"guardian-"+kind+"-runtime.json"),JsonSerializer.Serialize(new{scope="Actual C# guardian/actor driver output; engine API doubles, not Unity",kind,frames}));
   // Put the original attack in a readable windup and exercise the real brush hook.
   Set(driver,"state","windup");Set(driver,"remaining",.8f);Set(driver,"openUntil",0f);float guarded=driver.FilterDamage(100);enemy.BrushCounter();Check(enemy.State=="recover" && driver.FilterDamage(100)>guarded,"Brush counter opens guard without permanent stun");
   enemy.Hp=1;enemy.Damage(100,Vector3.forward,1);Check(enemy.Dead,"Guardian can be defeated");game.GetType().GetMethod("FinishCelestial",F).Invoke(game,new object[]{true});Check(game.Profile.shiranuiUnlock==kind && game.Save.saves>0,"Victory permanently records correct form");trial.Skip();game.Transformation.Skip();Check(native.FormLevel==kind,"Victory reveal applies correct earned skin");Check(HeavenlyGarden.PalaceInside(player.transform.position),"Victory returns to palace");Check(!trial.Enter(kind),"Completed gate cannot award another unlock");
   var sleeper=new GameObject("palace sleeper fixture").AddComponent<OriginalActor>();sleeper.game=game;sleeper.resource="Okami/palace-shiranui";sleeper.idle="pl00_004";Call(sleeper,"Awake");Check(sleeper.Ready,"Sleeping palace actor loads");sleeper.idle="pl00_000";sleeper.EndActivity();Call(sleeper,"LateUpdate");Check(sleeper.CurrentSourceMotion=="pl00_000","Freed palace wolf has an available original standing idle");
   var saved=JsonSerializer.Serialize(game.Profile,new JsonSerializerOptions{IncludeFields=true});var loaded=JsonUtility.FromJson<ProfileData>(saved);Check(ProgressionRules.Validate(loaded) && loaded.shiranuiUnlock==kind,"Unlocked form and upgraded ranks survive serialization");
   native.ApplyPowerForm(0);player.Grounded=true;game.Transformation.BeginEarned(native);game.Transformation.Skip();Check(native.FormLevel==1,"T selects earned second form");player.Grounded=true;game.Transformation.BeginEarned(native);game.Transformation.Skip();Check(native.FormLevel==(kind==1?0:2),"T cannot enter an unearned higher form");
   // A separate attempt loses without granting a form, then can retry.
   game.Profile.shiranuiUnlock=kind-1;game.InTrial=game.BossTrial=false;game.Close();player.Grounded=true;Check(trial.Enter(kind),"Retry enters before guardian defeated");trial.Skip();game.GetType().GetMethod("FinishCelestial",F).Invoke(game,new object[]{false});Check(game.Profile.shiranuiUnlock==kind-1 && !trial.Active,"Defeat grants no unlock");Check(!CelestialTrials.InArena(player.transform.position),"Defeat returns outside the arena");Check(trial.Enter(kind),"Can retry after defeat");trial.Cancel();game.InTrial=false;
   var original=player.transform.position;game.Profile.waterfallVision=false;trial.RevealWaterfall();Check(trial.Playing && game.Profile.waterfallVision,"River reveal records discovery");trial.Skip();Check(Vector3.Distance(original,player.transform.position)<.001f,"Skipping reveal restores prior position");
   game.Profile.waterfallVision=false;trial.RevealWaterfall();trial.Cancel();player.transform.position=new Vector3(-34,0,-24);Time.unscaledDeltaTime=4;Call(trial,"Update");Check(Vector3.Distance(player.transform.position,new Vector3(-34,0,-24))<.001f,"Cancelling reveal cannot later undo a return home");
  }
  Console.WriteLine("PASS "+n+" guardian progression/traversal assertions; API doubles, not Unity Play Mode");
 }
}
