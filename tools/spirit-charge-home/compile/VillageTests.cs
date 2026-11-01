using System;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
static class VillageTests
{
 static int checks;
 static void Check(bool yes,string why){checks++;if(!yes)throw new Exception(why);}
 static void Set(object x,string n,object v)=>x.GetType().GetField(n,BindingFlags.NonPublic|BindingFlags.Instance).SetValue(x,v);
 static T Get<T>(object x,string n)=>(T)x.GetType().GetField(n,BindingFlags.NonPublic|BindingFlags.Instance).GetValue(x);
 static object Call(object x,string n,params object[] args)=>x.GetType().GetMethod(n,BindingFlags.NonPublic|BindingFlags.Instance).Invoke(x,args);
 static OriginalActor Actor(string resource,string idle,GameFlow game)
 {
  var actor=new OriginalActor{resource=resource,idle=idle,game=game};var bank=new NativePoseBank(resource+"/Poses");var rig=new NativePaintedRig(resource,actor.transform);
  Set(actor,"rig",rig);Set(actor,"bank",bank);Set(actor,"fromPosition",new Vector3[bank.BoneCount]);Set(actor,"fromScale",new Vector3[bank.BoneCount]);Set(actor,"fromRotation",Enumerable.Repeat(Quaternion.identity,bank.BoneCount).ToArray());Call(actor,"Change",idle);Set(actor,"<Ready>k__BackingField",true);return actor;
 }
 public static int Run()
 {
  var player=new WolfMotor{Grounded=true};var game=new GameFlow{Player=player,Audio=new ValleyAudio(),Panel="",Health=100,Energy=80};player.game=game;player.transform.position=new Vector3(250,100,0);
  var enemy=new EnemyBrain();enemy.Init(game,new EnemyDefinition{id="imp",hp=100,damage=10,visual=new GameObject(),scale=1});enemy.transform.position=player.transform.position+new Vector3(5,0,1);game.Enemies.Add(enemy);
  var brush=new CelestialBrush{game=game};var stroke=Get<List<Vector2>>(brush,"stroke");var world=Get<List<Vector3>>(brush,"world");
  for(int i=0;i<15;i++){stroke.Add(new Vector2(100+i*20,101));world.Add(enemy.transform.position);}
  Call(brush,"Resolve");Check(game.Energy==60&&enemy.Hp==72,"Power Slash fails to consume ink and damage a crossed target");
  stroke.Clear();world.Clear();for(int i=0;i<=32;i++){float t=i*Mathf.PI/16;stroke.Add(new Vector2(250+100*Mathf.Cos(t),100+100*Mathf.Sin(t)));world.Add(player.transform.position+Vector3.up);}
  Call(brush,"Resolve");Check(game.Energy==45&&enemy.Hp==72,"Bloom is misclassified as a slash or has wrong ink cost");
  game.Energy=0;Call(brush,"Resolve");Check(game.Energy==0&&enemy.Hp==72,"Brush spends unavailable ink");
  Set(brush,"<Drawing>k__BackingField",true);Set(brush,"savedCursor",true);Cursor.visible=false;Call(brush,"OnDisable");Check(Cursor.visible&&!brush.Drawing&&stroke.Count==0&&world.Count==0,"Interrupted brush leaves cursor hidden or a stale stroke");
  foreach(bool harvest in new[]{false,true})
  {
   var life=new VillageLife{game=game};FarmCrop crop=harvest?new FarmCrop():null;if(crop!=null)Call(crop,"Awake");int before=game.Profile.vegetables;
   var routine=(IEnumerator)Call(life,"Dig",crop);Check(routine.MoveNext()&&player.Locked&&player.animationView.current=="Dig","Dig does not lock and animate");Check(routine.MoveNext(),"Dig ends before its recovery");Check(!routine.MoveNext()&&!player.Locked,"Dig does not restore movement");
   Check(game.Profile.vegetables==before+(harvest?1:0)&&(!harvest||crop.Harvested),"Ordinary ground creates produce or crop digging fails");
  }
  foreach(string resource in new[]{"dojo-hm08","dojo-hm2d","dojo-hm2e"})
  {
   bool archer=resource!="dojo-hm08";string idle=resource=="dojo-hm08"?"hm08_000":resource=="dojo-hm2d"?"hm2d_000":"hm00_000";string motion=resource=="dojo-hm08"?"hm08_088":resource=="dojo-hm2d"?"hm2d_080":"dojo_bow_080";
   var actor=Actor("Okami/"+resource,idle,game);actor.transform.position=Vector3.zero;var dummy=new TrainingDummy{game=game};dummy.transform.position=Vector3.back*(archer?10:2);
   var venue=new NativeVenueActor{actor=actor,dummy=dummy,role="training",motion=motion,archer=archer,contactEnabled=true,releasePhase=.16f};Set(venue,"game",game);Time.deltaTime=1f/60;bool sampledAttack=false;int spawned=0;
   for(int frame=0;frame<360;frame++)
   {
    Call(venue,"Update");Call(actor,"LateUpdate");sampledAttack|=actor.CurrentSourceMotion==motion;
    foreach(var root in GameObject.created.ToArray())
    {var arrow=root.GetComponent<PracticeArrow>();if(arrow && !root.wasDestroyed){if(Get<TrainingDummy>(arrow,"target")==dummy){Call(arrow,"Update");spawned++;}}}
   }
   Check(archer?actor.CurrentSourceMotion==idle:sampledAttack,"Dojo actor does not use its correct native body action");Check(dummy.contacts>=2,"Training actions never reach their dummy");Check(!archer||spawned>0,"Ranged trainees never launch arrows");
  }
  return checks;
 }
}
