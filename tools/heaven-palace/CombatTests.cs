using System;using System.Linq;using System.Reflection;using Sunward;using Sunward.Remaster;using UnityEngine;
class CombatTests
{
 static int n;static BindingFlags flags=BindingFlags.Instance|BindingFlags.NonPublic;
 static void Check(bool b,string s){n++;if(!b)throw new Exception(s);}
 static void Set(object o,string f,object value)=>o.GetType().GetField(f,flags).SetValue(o,value);
 static void Call(object o,string f,params object[] args)=>o.GetType().GetMethod(f,flags).Invoke(o,args);
 static void Main(string[] args)
 {
  Resources.Root=args[0];
  foreach(int fps in new[]{15,30,60,120})foreach(bool heavy in new[]{false,true})
  {
   var game=new GameFlow{Player=new WolfMotor(),InTrial=true,Panel="",Health=100};var combat=new WolfCombat{game=game,motor=game.Player};game.Combat=combat;game.Player.game=game;game.Player.Grounded=true;
   var entry=OriginalWeaponCatalog.Find("wp29e");Set(combat,"originalWeapon",entry);var definition=OriginalWeaponCatalog.Definition(entry,new WeaponDefinition(),new WeaponDefinition());Set(combat,"weapon",definition);
   var button=heavy?game.Player.input.Heavy:game.Player.input.Light;button.held=true;button.pressedThisFrame=true;Time.deltaTime=1f/fps;Call(combat,"Update");button.pressedThisFrame=false;
   for(int i=0;i<fps;i++)Call(combat,"Update");Check(combat.HoldingCharge && game.Player.animationView.current=="NativeCharge_glaive","Held glaive does not use charge preparation");button.held=false;Call(combat,"Update");Check(combat.Attacking && game.Player.animationView.current=="NativeAttack_524","Released normal/heavy charge does not play original release");
   int before=GameObject.created.Count(o=>o.name=="Original Thunder Edge · charged thunderstrike");Call(combat,"ThunderContact",Vector3.zero);Call(combat,"ThunderContact",Vector3.one);Check(GameObject.created.Count(o=>o.name=="Original Thunder Edge · charged thunderstrike")==before+1,"Charged explosion is missing or repeats for every target");
   for(int i=0;i<fps*2 && combat.Attacking;i++)Call(combat,"Update");Check(!combat.Busy && game.Player.animationView.current=="Idle_Natural","Release leaves Ammy frozen at "+fps+" fps");
   Call(combat,"Begin",definition.charged);game.InTrial=false;Call(combat,"Update");Check(!combat.Busy,"Leaving combat leaves charge locked");
  }
  foreach(var entry in OriginalWeaponCatalog.All)
  {
   var game=new GameFlow{Player=new WolfMotor(),InTrial=true,Panel="",Health=100,Energy=80};var combat=new WolfCombat{game=game,motor=game.Player};game.Combat=combat;game.Player.game=game;Set(combat,"originalWeapon",entry);game.Player.input.Bark.pressedThisFrame=true;Time.deltaTime=.016f;Call(combat,"Update");Check(game.Energy==65 && game.Player.animationView.current=="Bark","Elemental bark loses its original animation or energy cost");
  }
  {
   var game=new GameFlow{Player=new WolfMotor(),InTrial=true,Panel="",Health=100};var combat=new WolfCombat{game=game,motor=game.Player};game.Combat=combat;game.Player.game=game;game.Profile.equipped="wp29e";var view=new OriginalWeaponView();view.Load("wp29","glaive");Set(view,"combat",combat);
   void Guard(int expected){Call(view,"LateUpdate");var renderers=(SkinnedMeshRenderer[])view.GetType().GetField("renderers",flags).GetValue(view);Check(renderers.Where(r=>r.enabled).All(r=>int.Parse(r.sharedMesh.name.Split('_')[0].Split('-')[1])==1 || int.Parse(r.sharedMesh.name.Split('-')[1])==expected) && renderers.Any(r=>r.enabled && r.sharedMesh.name.StartsWith("Native-"+expected+"-")),"Native Thunder Edge side pieces missing or overlapping");}
   Guard(4);game.Profile.equipped="wp29";Guard(2);Set(combat,"charging",true);Set(combat,"hold",1f);Guard(3);
  }
  Console.WriteLine("PASS "+n+" actual WolfCombat normal/heavy hold, release recovery, charged explosion and interrupt checks at 15/30/60/120fps; engine doubles, not Unity");
 }
}
