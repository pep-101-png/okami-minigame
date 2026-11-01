using System;
using System.Linq;
using System.Reflection;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
static class RebirthTests
{
 static int checks;
 static void Check(bool yes,string why){checks++;if(!yes)throw new Exception(why);}
 static void Set(object x,string n,object v)=>x.GetType().GetField(n,BindingFlags.NonPublic|BindingFlags.Instance).SetValue(x,v);
 static void Call(object x,string n)=>x.GetType().GetMethod(n,BindingFlags.NonPublic|BindingFlags.Instance).Invoke(x,null);
 static void Main(string[] args)
 {
  Resources.Root=args[0];
  foreach(int fps in new[]{15,30,60,120})foreach(int mode in new[]{0,1,2,3,4})
  {
   var player=new WolfMotor();var game=new GameFlow{Player=player,Audio=new ValleyAudio(),InTrial=true,BossTrial=true,Panel="",Health=100};player.game=game;
   Set(game.Audio,"transformationVoice",new AudioSource());Set(game.Audio,"transformationBurst",new AudioSource());
   MonoBehaviour.CameraInstance=new OrbitCamera{target=player,virtualCamera=new Unity.Cinemachine.CinemachineCamera()};
   var boss=new EnemyBrain();boss.Init(game,new EnemyDefinition{id="boss",hp=145,damage=28,scale=2.75f,visual=new GameObject()});boss.transform.position=new Vector3(35,-110,0);player.transform.position=boss.transform.position+Vector3.back*2;
   var actor=new OriginalActor{resource="Okami/em11",idle="em65_000"};var rig=new NativePaintedRig(actor.resource,actor.transform);rig.Root.renderers=new[]{0,1,2}.Select(i=>new SkinnedMeshRenderer{sharedMesh=new Mesh{name="Native-"+i+"-0"}}).ToArray();
   Set(actor,"rig",rig);Set(boss,"nativeActor",actor);actor.game=game;Set(actor,"enemy",boss);
   var bank=new NativePoseBank(actor.resource+"/Poses");Set(actor,"bank",bank);Set(actor,"fromPosition",new Vector3[bank.BoneCount]);Set(actor,"fromScale",new Vector3[bank.BoneCount]);Set(actor,"fromRotation",Enumerable.Repeat(Quaternion.identity,bank.BoneCount).ToArray());
   typeof(OriginalActor).GetMethod("Change",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(actor,new object[]{actor.idle});Set(actor,"<Ready>k__BackingField",true);Check(actor.SetCrimsonFlame(false)&&rig.Root.renderers[0].enabled&&!rig.Root.renderers[1].enabled&&rig.Root.renderers[2].enabled,"Armoured form leaks skeleton");
   boss.Damage(999,Vector3.zero,0);var sequence=game.BossTransformation;
   Check(!boss.Dead&&boss.BossRising&&boss.Hp==boss.MaxHp&&game.rewards==0&&sequence.Playing,"First death rewards/finishes instead of rebirth");
   Check(game.Combat.cancels==0,"Synchronous combat cancellation inside contact iteration");
   boss.Damage(999,Vector3.zero,0);Check(boss.Hp==boss.MaxHp,"Rising boss accepts damage");
   Time.unscaledDeltaTime=1f/fps;Time.deltaTime=0;game.Blocked=true;game.CinematicActive=true;
   if(mode==1)sequence.Skip();
   else if(mode==2 || mode==3){int frames=mode==2?1:fps*2;for(int f=0;f<frames;f++)Call(sequence,"Update");game.InTrial=game.BossTrial=false;Call(sequence,"Update");}
   else if(mode==4){Call(sequence,"Update");sequence.Skip();}
   else
   {for(int frame=0;frame<fps*4&&sequence.Playing;frame++){Call(sequence,"Update");if(sequence.Playing){Call(actor,"LateUpdate");if(frame==1)Check(actor.CurrentSourceMotion=="em65_032"&&(float)typeof(OriginalActor).GetField("time",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(actor)>0,"Rebirth motion freezes under paused world time");}}}
   Check(!sequence.Playing&&game.BossTransformation==null&&!player.Locked&&Time.timeScale==1,"Cinematic leaves locks/time/ownership behind");
   if(mode==2 || mode==3){Check(!boss.FlamePhase&&game.rewards==0,"Cancelled encounter ignites or rewards");continue;}
   Check(boss.FlamePhase&&!boss.BossRising&&!boss.Dead&&boss.AttackDamage==56,"Flame phase damage/health incorrect");
   Check(!rig.Root.renderers[0].enabled&&rig.Root.renderers[1].enabled&&!rig.Root.renderers[2].enabled,"Flame reveal doubles visible bodies");
   var motor=boss.gameObject.GetComponent<CharacterController>();Check(motor.height==7.2f&&motor.radius==2,"Boss collision did not grow twice");
   sequence.Skip();sequence.Cancel();Check(boss.FlamePhase&&game.rewards==0,"Repeated skip/cancel alters finished phase");
   game.Blocked=game.CinematicActive=false;boss.Damage(999,Vector3.zero,0);Check(boss.Dead&&game.rewards==1&&boss.State=="dead","Second death does not award exactly once");
   boss.Damage(999,Vector3.zero,0);Check(game.rewards==1,"Dead boss duplicates rewards");
  }
  Console.WriteLine("PASS "+checks+" actual EnemyBrain/rebirth director checks: first/final death, doubled damage/capsule, native form visibility, skip/cancel, deferred combat cancellation at 15/30/60/120fps. Engine doubles, NOT Unity.");
 }
}
