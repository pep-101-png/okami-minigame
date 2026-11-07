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
 static T Get<T>(object x,string n)=>(T)x.GetType().GetField(n,BindingFlags.NonPublic|BindingFlags.Instance).GetValue(x);
 static void Call(object x,string n)=>x.GetType().GetMethod(n,BindingFlags.NonPublic|BindingFlags.Instance).Invoke(x,null);
 static void Main(string[] args)
 {
  Resources.Root=args[0];FullPowerTests.Run();HeavenAudioPolishTests.Run();TrailingRibbonTests.Run();
  foreach(int fps in new[]{15,30,60,120})foreach(int mode in new[]{0,1,2,3,4})
  {
   var player=new WolfMotor();var game=new GameFlow{Player=player,Audio=new ValleyAudio(),InTrial=true,BossTrial=true,Panel="",Health=100};player.game=game;
   Set(game.Audio,"transformationVoice",new AudioSource());Set(game.Audio,"transformationBurst",new AudioSource());
   MonoBehaviour.CameraInstance=new OrbitCamera{target=player,virtualCamera=new Unity.Cinemachine.CinemachineCamera()};
   var prefab=new GameObject();var actor=prefab.AddComponent<OriginalActor>();actor.resource="Okami/em11";actor.idle="em65_000";actor.game=game;
   var rig=new NativePaintedRig(actor.resource,actor.transform);var bank=new NativePoseBank(actor.resource+"/Poses");Set(actor,"rig",rig);Set(actor,"bank",bank);Set(actor,"fromPosition",new Vector3[bank.BoneCount]);Set(actor,"fromScale",new Vector3[bank.BoneCount]);Set(actor,"fromRotation",Enumerable.Repeat(Quaternion.identity,bank.BoneCount).ToArray());
   typeof(OriginalActor).GetMethod("Change",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(actor,new object[]{actor.idle});Set(actor,"<Ready>k__BackingField",true);
   var boss=new EnemyBrain();Set(actor,"enemy",boss);boss.Init(game,new EnemyDefinition{id="boss",hp=145,damage=28,scale=2.75f,visual=prefab});boss.transform.position=new Vector3(35,-110,0);player.transform.position=boss.transform.position+Vector3.back*10;
   Check(boss.BossPhase==1&&boss.AttackDamage==28&&Get<NativePaintedRig>(actor,"crimsonArmour").Root.activeSelf&&rig.Root.activeSelf,"First phase is missing the real body/armour assembly");
   var director=boss.gameObject.GetComponent<CrimsonHelmAscension>();Check(Get<ParticleSystem>(director,"flames")!=null,"Full armour has no fire");
   // Repeated contacts must never turn one short flinch into a permanent stun.
   Time.time=0;int stunned=0;
   for(int i=0;i<400;i++){Time.time=i*.02f;Time.deltaTime=.02f;boss.Stun(1);if(boss.VisualStunned)stunned++;Call(boss,"Update");}
   Check(stunned<40,"Boss permanently stun-locked by repeated hits");Set(boss,"stun",0f);Set(boss,"<State>k__BackingField","windup");boss.Stun(1);Check(!boss.VisualStunned,"Boss windup interrupted by ordinary hit");Set(boss,"<State>k__BackingField","approach");
   bool cancelled=false;
   for(int phase=2;phase<=3;phase++)
   {
    int cancels=game.Combat.cancels;game.Blocked=game.CinematicActive=false;boss.Damage(9999,Vector3.zero,0);var sequence=game.BossTransformation;
    Check(!boss.Dead&&boss.BossRising&&boss.Hp==boss.MaxHp&&game.rewards==0&&sequence.Playing,"Intermediate death grants victory/rewards");
    Check(game.Combat.cancels==cancels,"Combat cancelled re-entrantly in hit iteration");boss.Damage(9999,Vector3.zero,0);Check(boss.Hp==boss.MaxHp,"Transition accepts damage");
    Time.unscaledDeltaTime=1f/fps;Time.deltaTime=0;game.Blocked=game.CinematicActive=true;
    if(mode==1)sequence.Skip();
    else if(mode==2 || mode==3){int frames=mode==2?1:fps*2;for(int f=0;f<frames;f++)Call(sequence,"Update");game.InTrial=game.BossTrial=false;Call(sequence,"Update");cancelled=true;}
    else if(mode==4){Call(sequence,"Update");sequence.Skip();}
    else for(int frame=0;frame<fps*4&&sequence.Playing;frame++){Call(sequence,"Update");if(sequence.Playing){Call(actor,"LateUpdate");if(frame==1)Check(actor.CurrentSourceMotion=="em65_032"&&Get<float>(actor,"time")>0,"Paused cinematic freezes its native motion");}}
    Check(!sequence.Playing&&game.BossTransformation==null&&!player.Locked&&Time.timeScale==1,"Cinematic leaves time/input/ownership locked");
    if(cancelled){Check(game.rewards==0,"Cancelled phase grants a reward");break;}
    float scale=phase==2?2:4;var motor=boss.gameObject.GetComponent<CharacterController>();
    Check(boss.BossPhase==phase&&!boss.BossRising&&!boss.Dead&&boss.AttackDamage==28*scale,"Phase damage/health incorrect");Check(motor.height==3.6f*scale&&motor.radius==scale,"Phase size is not 1x/2x/4x");
    Check(!Get<NativePaintedRig>(actor,"crimsonArmour").Root.activeSelf&&rig.Root.activeSelf,"Armour and exposed body render together");
    Check(rig.Root.renderers.Where(r=>r.enabled).All(r=>phase==3?r.sharedMesh.name.StartsWith("Native-1-"):!r.sharedMesh.name.StartsWith("Native-1-")),"Wrong native body group visible");
    Check((Get<ParticleSystem>(sequence,"flames")!=null)==(phase==3),"Fire is missing from skeleton or remains on middle phase");
    sequence.Skip();sequence.Cancel();Check(boss.BossPhase==phase&&game.rewards==0,"Repeated cleanup changes completed phase");
   }
   if(cancelled)continue;
   game.Blocked=game.CinematicActive=false;boss.Damage(9999,Vector3.zero,0);Check(boss.Dead&&game.rewards==1&&boss.State=="dead","Third death fails to award once");boss.Damage(9999,Vector3.zero,0);Check(game.rewards==1,"Final death duplicates rewards");
  }
  {
   var player=new WolfMotor();var game=new GameFlow{Player=player,Panel="",Health=100};player.game=game;game.Profile.wins=1;
   var lower=new LowerArena{game=game,cover=new GameObject(),chamber=new GameObject(),fragments=Array.Empty<Transform>(),mirror=new GameObject().transform};Call(lower,"Awake");Call(lower,"Start");
   Check(!lower.mirror.gameObject.activeSelf,"Return mirror is present before victory");LowerArena.TrialFinished(true);player.transform.position=new Vector3(35,0,0);Time.deltaTime=3.1f;Call(lower,"Update");player.transform.position=LowerArena.Centre+Vector3.up*.05f;Call(lower,"Update");Check(game.bossStarts==1,"Entering lower chamber fails to start one boss");
   game.InTrial=game.BossTrial=false;LowerArena.BossDefeated();var beacon=Get<GameObject>(lower,"victoryBeacon");
   Check(lower.mirror.gameObject.activeSelf&&(lower.mirror.position-(LowerArena.Centre+Vector3.up*.3f)).magnitude<.001f&&beacon!=null,"Victory mirror/beacon did not appear in centre");
   LowerArena.BossDefeated();Check(Get<GameObject>(lower,"victoryBeacon")==beacon,"Victory beacon duplicates");Call(lower,"Update");Check(game.bossStarts==1,"Closing victory screen respawns boss");
   player.input.Interact.pressedThisFrame=true;Call(lower,"Update");Check(game.homeReturns==1,"Centre mirror interaction cannot call home return");
   LowerArena.Leave();Check(!lower.mirror.gameObject.activeSelf&&beacon.wasDestroyed,"Home exit leaves victory effects/return mirror active");Call(lower,"OnDestroy");
  }
  checks+=VillageTests.Run()+FestivalTests.Run();FestivalChallengeTests.Run();VillageRefinementTests.Run();GardenPassageTests.Run();HeavenFollowupTests.Run();HeavenTreasureTests.Run();HeavenPalaceTests.Run();TextBoundsTests.Run(args[0]);VillageCompleteTests.Run();
  Console.WriteLine("PASS "+checks+" actual three-phase boss/native director checks, stun resistance, first/middle/final deaths, 1x/2x/4x scaling, fire/armour visibility, skip/cancel and paused motion at 15/30/60/120fps. Engine doubles, NOT Unity.");
 }
}
