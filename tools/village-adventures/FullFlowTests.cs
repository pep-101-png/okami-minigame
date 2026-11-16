using System;using System.Reflection;using Sunward;using Sunward.Remaster;using UnityEngine;
static class FullFlowTests
{
 const BindingFlags F=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
 static void Set(object o,string n,object v)=>o.GetType().GetProperty(n,F).SetValue(o,v);static void Call(object o,string n)=>o.GetType().GetMethod(n,F).Invoke(o,null);static int n;static void Check(bool b,string why){n++;if(!b)throw new Exception(why);}
 static void Main(string[] args)
 {
  Resources.Root=args[0];StreetActorLifecycle.Enabled=false;var player=new GameObject().AddComponent<WolfMotor>();var g=new GameFlow{Player=player,Combat=new WolfCombat{allowEquip=true},Fx=new PaintedEffects(),Audio=new ValleyAudio(),Home=new HomeRest(),valley=new Valley()};player.game=g;Set(g,"Save",new SaveStore());g.Health=100;g.Stamina=80;g.Energy=40;g.Profile.owned=new[]{"wp2be","spear"};g.Profile.equipped="spear";g.Audio.GetType().GetField("game",F).SetValue(g.Audio,g);Call(g.Audio,"Awake");
  var a=new GameObject().AddComponent<VillageAdventures>();a.game=g;Set(g,"Adventures",a);Call(a,"Start");Call(a.Mastery,"Start");player.Teleport(WeaponMasteryTrials.Scroll);
  Check(a.Mastery.Begin(11,1),"Life practice starts in actual GameFlow");g.Health=50;int coins=g.Profile.coins,xp=g.Profile.xp,kills=g.Profile.kills;var enemy=new EnemyBrain{definition=new EnemyDefinition{id="reed",reward=10,xp=15}};
  g.Reward(enemy);Check(g.Health==55 && a.Mastery.Count("life")==1,"Actual practice kill restores Life health and records art");Check(g.Profile.coins==coins && g.Profile.xp==xp && g.Profile.kills==kills,"Practice kills cannot farm normal rewards");
  g.Player.Invulnerable=0;g.Hurt(1,Vector3.zero);g.Hurt(1,Vector3.zero);var hurt=(int)typeof(WeaponMasteryTrials).GetField("hurt",F).GetValue(a.Mastery);Check(hurt==1,"Invulnerable contacts do not count twice against mastery");
  g.Finish(false);Check(!g.InTrial && !a.Mastery.Active && Vector3.Distance(player.transform.position,WeaponMasteryTrials.Scroll)<.01f,"Actual Finish dispatch exits mastery correctly");
  Set(g,"InTrial",true);g.Profile.equipped="wp2be";AwakeningProgress.Get(g.Profile,"wp2be").rank=5;g.Health=50;g.Reward(enemy);Check(g.Health==58,"Awakened rank strengthens Life recovery");Check(g.Profile.coins>coins && g.Profile.xp>xp && g.Profile.kills==kills+1,"Actual arena kills preserve normal rewards");
  Console.WriteLine("PASS "+n+" actual GameFlow reward, hurt and exit integration assertions; engine API doubles");
 }
}
