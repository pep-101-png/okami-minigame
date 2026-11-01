using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
static class Program
{
 static int checks;
 static void Check(bool yes,string why){checks++;if(!yes)throw new Exception(why);}
 static void Set(object x,string name,object value)=>x.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic).SetValue(x,value);
 static void Tick(NativeAmaterasu body)=>typeof(NativeAmaterasu).GetMethod("LateUpdate",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(body,null);
 static float Delta(Vector3 a,Vector3 b)=>(a-b).magnitude;
 static void Main(string[] args)
 {
  var crimsonPhase=new CrimsonPhaseState();Check(crimsonPhase.Stage==CrimsonStage.ArmouredFlame,"Wrong first form");
  Check(crimsonPhase.TryRise()&&!crimsonPhase.TryRise(),"First transition re-enters");crimsonPhase.Ignite();Check(crimsonPhase.Phase==2&&crimsonPhase.ScaleMultiplier==2,"Second form scale incorrect");
  Check(crimsonPhase.TryRise()&&!crimsonPhase.TryRise(),"Second transition re-enters");crimsonPhase.Ignite();Check(crimsonPhase.Phase==3&&crimsonPhase.DamageMultiplier==4&&!crimsonPhase.TryRise(),"Final form incorrect");crimsonPhase.Defeat();Check(crimsonPhase.Stage==CrimsonStage.Defeated&&!crimsonPhase.TryRise(),"Final death restarts fight");
  Resources.Root=args[0];var bank=new NativePoseBank("NativePlayer/pl00/Poses");
  using var json=JsonDocument.Parse(File.ReadAllText(Path.Combine(args[0],"OkamiRemaster/Player/Resources/NativePlayer/Bindings.json")));
  var bindings=json.RootElement.GetProperty("bindings").EnumerateArray().Select(x=>new NativeAmaterasu.Binding{state=x.GetProperty("state").GetString(),clip=x.GetProperty("clip").GetString(),loop=x.TryGetProperty("loop",out var loop)&&loop.GetBoolean(),intro=x.TryGetProperty("intro",out var intro)?intro.GetString():null}).ToArray();
  Check(bindings.Single(x=>x.state==TundraAttackRules.Charge).clip!="pl00_540","Charge still uses the static pose");
  foreach(int fps in new[]{30,60,120})foreach(float speed in new[]{1f,2f})
  {
   Time.deltaTime=Time.unscaledDeltaTime=1f/fps;var body=new NativeAmaterasu();var rig=new NativePaintedRig("NativePlayer/pl00",body.transform);var motor=new WolfMotor();var game=new GameFlow{Player=motor};motor.game=game;
   Set(body,"bank",bank);Set(body,"rig",rig);Set(body,"amaterasuRig",rig);Set(body,"motor",motor);Set(body,"bindings",bindings);Set(body,"fromPosition",new Vector3[bank.BoneCount]);Set(body,"fromScale",new Vector3[bank.BoneCount]);Set(body,"fromRotation",Enumerable.Repeat(Quaternion.identity,bank.BoneCount).ToArray());Set(body,"<Ready>k__BackingField",true);
   body.Play("Idle_Natural",0,0,true,false);
   foreach(var charge in bindings.Where(b=>b.state.StartsWith("NativeCharge_")))
   {
    Check(charge.loop,"Held charge binding is not looping");body.Play(charge.state,.08f,0,true,false);var first=rig.Bones.Select(b=>b.localPosition).ToArray();float motion=0;
    for(int frame=0;frame<fps*3;frame++){body.HoldChargePose();Tick(body);motion=Math.Max(motion,rig.Bones.Select((b,i)=>Delta(b.localPosition,first[i])).Max());}
    Check(body.PlaybackRate>0&&motion>.1f,"A held weapon-family charge remains frozen");
   }
   foreach(bool heavy in new[]{false,true})
   {
    body.Play(TundraAttackRules.Charge,.08f,0,true,false);var start=rig.Bones.Select(b=>b.localPosition).ToArray();float moved=0;
    for(int f=0;f<fps*2;f++){body.HoldChargePose();Tick(body);moved=Math.Max(moved,rig.Bones.Select((b,i)=>Delta(b.localPosition,start[i])).Max());}
    Check(body.PlaybackRate>0 && moved>.1f,"Held charge freezes the actual native driver");
    body.Play(TundraAttackRules.Cast,.08f,1.3333333f/speed,true,false);moved=0;start=rig.Bones.Select(b=>b.localPosition).ToArray();
    int frames=(int)Math.Ceiling(1.3333333f/speed*fps);
    for(int f=0;f<=frames;f++){body.SetTundraPhase(Math.Min(1,f/(float)frames),1.3333333f);Tick(body);moved=Math.Max(moved,rig.Bones.Select((b,i)=>Delta(b.localPosition,start[i])).Max());}
    Check(moved>.1f,"Released cast freezes the actual native driver");
    body.EndTundraAction();for(int f=0;f<fps/2;f++)Tick(body);float phase=body.Phase;Tick(body);Check(body.Phase>phase,"Cast release retains an external stopped clock");
    game.Blocked=true;var frozen=rig.Bones.Select(b=>b.localPosition).ToArray();Tick(body);Check(rig.Bones.Select((b,i)=>Delta(b.localPosition,frozen[i])).All(x=>x<1e-7),"Menu pause changes body pose");game.Blocked=false;
   }
  }
  // The cinematic freezes world time, but its native body animation must run.
  {
   var body=new NativeAmaterasu();var rig=new NativePaintedRig("NativePlayer/pl00",body.transform);var motor=new WolfMotor();var game=new GameFlow{Player=motor,Blocked=true,CinematicActive=true};motor.game=game;
   Set(body,"bank",bank);Set(body,"rig",rig);Set(body,"amaterasuRig",rig);Set(body,"motor",motor);Set(body,"bindings",bindings);Set(body,"fromPosition",new Vector3[bank.BoneCount]);Set(body,"fromScale",new Vector3[bank.BoneCount]);Set(body,"fromRotation",Enumerable.Repeat(Quaternion.identity,bank.BoneCount).ToArray());Set(body,"<Ready>k__BackingField",true);
   Time.deltaTime=0;Time.unscaledDeltaTime=1f/60;body.Play("Bark",0,1.9333333f,true,false);float before=body.Phase;Tick(body);Check(body.Phase>before,"Cinematic freezes its own native animation");
   Check(body.PrepareShiranui()&&body.ApplyShiranuiForm()&&body.Shiranui,"Original Shiranui form cannot be prepared/switched");
   Check(body.ApplyShiranuiForm()&&!body.Shiranui,"Transformation cannot return to Amaterasu");Time.deltaTime=Time.unscaledDeltaTime;
  }
  foreach(int fps in new[]{15,30,60,120})
  {
   var clock=new TransformationTimeline();Check(clock.Begin()&&!clock.Begin(),"Transformation can re-enter");var counts=new int[4];
   for(int i=0;i<fps*5;i++){var cue=clock.Tick(1f/fps);for(int k=0;k<4;k++)if((((int)cue)&(1<<k))!=0)counts[k]++;}
   Check(counts.All(n=>n==1)&&!clock.Playing,"Transformation events duplicate or never finish");
   foreach(float before in new[]{0f,.5f,1.8f,3f})
   {
    clock.Begin();var first=clock.Tick(before);var skipped=clock.Skip();Check(((first|skipped)&TransformationCue.Reveal)!=0,"Skipping loses the form switch");Check((first&skipped&TransformationCue.Reveal)==0,"Skipping switches the form twice");Check(!clock.Playing && clock.Skip()==TransformationCue.None,"Skip leaves input locked");
   }
   clock.Begin();clock.Cancel();Check(!clock.Playing && clock.Tick(100)==TransformationCue.None,"Cancelled transformation emits later events");
  }
  foreach(string panel in new[]{"pause","result",""})foreach(float hp in new[]{0f,50f})
  {
   var player=new WolfMotor{Locked=true,Swimming=true,Vertical=-12,Speed=8,horizontal=Vector3.one,Velocity=Vector3.one,dodgeTimer=1,landing=1,jumpBuffer=1,coyote=1,airborneTime=9,doubleUsed=true};player.transform.position=new Vector3(35,-110,0);
   var game=new GameFlow{Player=player,Panel=panel,InTrial=true,BossTrial=true,Health=hp,hitUntil=999,barrier=new GameObject()};player.game=game;var exitBoundary=game.barrier;Check(exitBoundary.GetComponent<MeshFilter>()==null,"Test incorrectly invents a mesh component on the particle boundary");exitBoundary.SetActive(true);Time.timeScale=0;int leaves=LowerArena.leaves,snaps=MonoBehaviour.CameraInstance.snaps,syncs=Physics.syncs;
   game.ReturnHome();
   Check(game.barrier==null&&exitBoundary.wasDestroyed&&!exitBoundary.activeSelf,"Return does not safely destroy the meshless boundary");
   Check(Delta(player.transform.position,new Vector3(-34,.82f,-24))<1e-5,"Home transfer did not leave the chamber");
   Check(!game.InTrial&&!game.BossTrial&&!player.Locked&&!player.Swimming&&game.Panel=="","Return retains encounter/menu/lock state");
   Check(game.Health==120&&game.Stamina==100&&game.Energy==80&&Time.timeScale==1&&game.hitUntil==0,"Return does not restore playable state");
   Check(player.Vertical==0&&player.Speed==0&&player.Velocity.magnitude==0&&player.dodgeTimer==0&&player.airborneTime==0&&player.controller.enabled,"Teleport retains falling/movement state");
   Check(LowerArena.leaves==leaves+1&&MonoBehaviour.CameraInstance.snaps==snaps+1&&Physics.syncs==syncs+1,"Return does not release floor/camera/physics state");
   Check(game.Home.cancels==1&&game.Services.cancels==1&&game.Transformation.cancels==1,"Background animation can overwrite home transfer");
  }
  var stopped=new WolfMotor{Grounded=true,horizontal=Vector3.one,Velocity=Vector3.one,Vertical=-2,Speed=6,dodgeTimer=.2f,jumpBuffer=.1f};stopped.StopMotion();
  Check(stopped.Velocity.magnitude==0&&stopped.Speed==0&&stopped.dodgeTimer==0&&stopped.jumpBuffer==0,"Cinematic resumes old movement/dodge inputs");
  Check(stopped.Grounded&&stopped.controller.enabled,"Stopping for a cinematic changes floor/controller state");
  foreach(bool win in new[]{false,true})foreach(bool boss in new[]{false,true})
  {
   var player=new WolfMotor();var game=new GameFlow{Player=player,InTrial=true,BossTrial=boss,Health=win?45:0,Panel="",barrier=new GameObject()};player.game=game;var resultBoundary=game.barrier;game.Finish(win);
   Check(game.barrier==null&&resultBoundary.wasDestroyed,"Victory/defeat cleanup cannot handle a meshless boundary");
   Check(!game.InTrial&&!game.BossTrial&&game.Panel==(win?(boss?"bossVictory":""):"result"),"Victory modal must close automatically; defeat must retain recovery menu");
   Check(game.Save.saves==1&&player.Locked==!win,"Result did not save or release/lock control correctly");
   Check(win?game.Profile.coins==(boss?150:75)&&game.Profile.xp==100&&game.Profile.bossWins==(boss?1:0)&&game.Profile.wins==(boss?0:1):game.Profile.defeats==1,"Result changed earned rewards");
   Check(game.projectiles>0&&game.Dialogue.Contains("10 combat coins"),"End of trial keeps stray projectiles or loses result text");
   game.Finish(win);Check(game.Save.saves==1,"Finishing twice duplicates progress");
  }
  var sharedMesh=new Mesh();var meshBoundary=new GameObject();meshBoundary.AddComponent<MeshFilter>().sharedMesh=sharedMesh;
  var exitPlayer=new WolfMotor();var completed=new GameFlow{Player=exitPlayer,InTrial=true,BossTrial=true,Health=45,barrier=meshBoundary};exitPlayer.game=completed;
  completed.Finish(true);Check(!sharedMesh.wasDestroyed&&meshBoundary.wasDestroyed,"Boundary cleanup destroys a borrowed mesh asset");
  completed.ReturnHome();completed.ReturnHome();Check(completed.barrier==null&&completed.Panel==""&&completed.Profile.bossWins==1,"Repeated home return after boss victory fails or duplicates rewards");
  foreach(bool originalIgnore in new[]{false,true})
  {
   var camera=new OrbitCamera{target=new WolfMotor()};UnityEngine.Camera.main.brain.IgnoreTimeScale=originalIgnore;camera.BeginCinematic();Check(UnityEngine.Camera.main.brain.IgnoreTimeScale,"Cinematic camera obeys paused world time");
   camera.CinematicFrame(new Vector3(0,.95f,0),5,12,5.4f,37);Check(camera.virtualCamera.Lens.FieldOfView==37,"Cinematic lens is not applied");
   camera.ReturnCinematic(1);Check(camera.virtualCamera.Lens.FieldOfView==50&&camera.cinematicDistance==15,"Camera cannot ease back to its prior gameplay framing");
   camera.EndCinematic();Check(camera.virtualCamera.Lens.FieldOfView==50&&UnityEngine.Camera.main.brain.IgnoreTimeScale==originalIgnore&&camera.snaps==1,"Cinematic changes camera settings permanently");
   camera.EndCinematic();Check(camera.snaps==1,"Repeated cleanup changes camera state twice");
  }
  var audio=new ValleyAudio();audio.TundraAttack(false,false);Check(audio.tundraSwing.clip.name=="weapon-wp2e"&&audio.tundraSwing.plays==1,"Primary attack selects wrong sound");
  audio.TundraAttack(false,true);Check(audio.tundraSwing.clip.name=="weapon-wp2e"&&audio.tundraSwing.volume<=.30f,"Heavy swing uses generic impact or unbounded volume");
  audio.TundraAttack(true,true);Check(audio.tundraSwing.clip.name=="weapon-wp2e-heavy"&&audio.tundraSwing.volume==.22f,"Charged cast selects wrong original cue");
  audio.TundraContact();audio.TundraContact();Check(audio.tundraImpact.plays==1&&audio.tundraImpact.volume==.15f,"Contact sound stacks repeatedly");
  audio.StopTundra();Check(!audio.tundraSwing.isPlaying,"Cancelled swing continues playing");
  audio.TransformationVoice();audio.TransformationBurst();Check(audio.transformationVoice.clip.name=="transformation-voice"&&audio.transformationBurst.volume==.28f,"Transformation bypasses bounded source channels");
  audio.StopTransformation();Check(!audio.transformationVoice.isPlaying&&!audio.transformationBurst.isPlaying,"Skipped cinematic keeps its sounds playing");
  var mirror=new Transform{position=new Vector3(15,-109.7f,-18)};
  Check(LowerArena.Near(new Vector3(17,-105,-18),mirror),"Raised decorative pivot prevents mirror use from floor");
  Check(!LowerArena.Near(new Vector3(15,0,-18),mirror)&&!LowerArena.Near(new Vector3(35,-110,0),mirror)&&!LowerArena.Near(Vector3.zero,null),"Mirror reaches wrong floor or distant players");
  Console.WriteLine("PASS "+checks+" checks: actual NativeAmaterasu held/released charge driver; actual extracted ReturnHome/Teleport/mirror/audio/camera methods; timeline at 15/30/60/120 fps, skip/cancel/re-entry. Engine doubles, NOT Unity compilation or playback.");
 }
}
