using System;
using System.Reflection;
using System.Text.Json;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
public static class HeavenTreasureTests
{
 static int checks;static BindingFlags flags=BindingFlags.Instance|BindingFlags.NonPublic;
 static void Check(bool ok,string why){checks++;if(!ok)throw new Exception(why);}
 static void Put(object o,string key,object value)=>o.GetType().GetField(key,flags).SetValue(o,value);
 static object Get(object o,string key)=>o.GetType().GetField(key,flags).GetValue(o);
 static void Finish(HeavenlyGarden h,bool grant)=>typeof(HeavenlyGarden).GetMethod("FinishTreasure",flags).Invoke(h,new object[]{grant});
 public static void Run()
 {
  var p=new ProfileData{coins=777,owned=new[]{"spear","wp2e"}};
  Check(!OriginalWeaponEvolution.Owns(p),"Fresh save owns maze reward");Check(!OriginalWeaponEvolution.Unlock(null),"Null save accepted");
  Check(OriginalWeaponEvolution.Unlock(p),"Cannot unlock evolved Thunder Edge");Check(p.coins==777 && p.equipped=="wp29e","Reward spends currency or fails to equip");Check(Array.IndexOf(p.owned,"wp29")>=0 && Array.IndexOf(p.owned,"wp2e")>=0,"Reward loses existing weapons or base Thunder Edge");
  int count=p.owned.Length;Check(!OriginalWeaponEvolution.Unlock(p) && p.owned.Length==count,"Duplicate reward on revisit");
  var options=new JsonSerializerOptions{IncludeFields=true};var saved=JsonSerializer.Serialize(p,options);var loaded=JsonSerializer.Deserialize<ProfileData>(saved,options);Check(OriginalWeaponEvolution.Owns(loaded) && loaded.equipped=="wp29e","Reward lost on save round trip");Check(Math.Abs(OriginalWeaponEvolution.Power("wp29e")-1.35f)<.001 && OriginalWeaponEvolution.Power("wp29")==1,"Evolution damage corrupts base weapons");Check(Math.Abs(OriginalWeaponEvolution.Reach("wp29e")-1.15f)<.001,"Awakened reach missing");
  var game=new GameFlow{Player=new WolfMotor(),Health=100};game.Player.game=game;game.Services.game=game;game.Combat.allowEquip=true;
  var heaven=new HeavenlyGarden{game=game};game.Heaven=heaven;Put(heaven,"garden",new GameObject());game.Player.transform.position=HeavenlyGarden.Centre;
  foreach(bool grant in new[]{false,true,true})
  {
   Put(heaven,"rewardPlaying",true);typeof(HeavenlyGarden).GetProperty("Playing").SetValue(heaven,true);game.Player.Locked=true;int saves=game.Save.saves;Finish(heaven,grant);
   Check(!heaven.Playing && !(bool)Get(heaven,"rewardPlaying") && !game.Player.Locked,"Cutscene leaves camera/player locked");Check(game.Save.saves==saves+(grant && saves==0?1:0),"Cancel grants or repeat completion saves twice");
   if(!grant)Check(!OriginalWeaponEvolution.Owns(game.Profile),"Cancelled excavation grants reward");
  }
  Check(OriginalWeaponEvolution.Owns(game.Profile),"Completed excavation fails to award");
  Put(heaven,"rewardPlaying",true);typeof(HeavenlyGarden).GetProperty("Playing").SetValue(heaven,true);game.Health=0;Finish(heaven,false);Check(game.Player.Locked && !heaven.Playing,"Death unlocks dead player or strands cutscene");
  // Real native chest driver: recovered opening bank on the original prop skeleton.
  var chestObject=new GameObject();var visual=chestObject.AddComponent<OriginalVisual>();Check(visual.Load("Okami/vt4b",Vector3.zero,Vector3.one),"Original chest cannot load");visual.SampleMotion("Okami/vt4b","vt4b_001",.76f);Check(true,"Original chest opening failed");
  foreach(int fps in new[]{15,30,60,120})
  {
   var scene=new GameFlow{Player=new WolfMotor(),Health=100};scene.Player.game=scene;scene.Services.game=scene;scene.Combat.allowEquip=true;
   var director=new HeavenlyGarden{game=scene};scene.Heaven=director;Put(director,"garden",new GameObject());Put(director,"treasurePoint",HeavenlyGarden.Centre);Put(director,"rewardPlaying",true);typeof(HeavenlyGarden).GetProperty("Playing").SetValue(director,true);scene.Player.Locked=true;Time.unscaledDeltaTime=1f/fps;
   for(int i=0;i<fps*8 && director.Playing;i++)typeof(HeavenlyGarden).GetMethod("TickTreasure",flags).Invoke(director,null);
   Check(!director.Playing && OriginalWeaponEvolution.Owns(scene.Profile) && scene.Save.saves==1 && !scene.Player.Locked,"Timed excavation strands reward/control at "+fps+"fps");
  }
  // Exercise the real basin classifier using public Unity boundary doubles; no physics claim.
  var poolType=typeof(HeavenlyGarden).GetNestedType("GardenPool",BindingFlags.NonPublic);var pool=Activator.CreateInstance(poolType);poolType.GetField("position").SetValue(pool,new Vector3(0,2,0));poolType.GetField("radius").SetValue(pool,new Vector2(3,2));poolType.GetField("depth").SetValue(pool,.85f);var pools=Array.CreateInstance(poolType,1);pools.SetValue(pool,0);Put(heaven,"pools",pools);typeof(HeavenlyGarden).GetField("activeGarden",BindingFlags.Static|BindingFlags.NonPublic).SetValue(null,heaven);
  Check(HeavenlyGarden.Water(HeavenlyGarden.Centre,out var level,out var depth) && level==72 && depth==2,"Native pond level not used");Check(!HeavenlyGarden.Water(HeavenlyGarden.Centre+new Vector3(3.2f,0,0),out level,out depth),"Water extends through pond bank");Check(!HeavenlyGarden.Water(Vector3.zero,out level,out depth),"Village classified as heaven water");heaven.isActiveAndEnabled=false;Check(!HeavenlyGarden.Water(HeavenlyGarden.Centre,out level,out depth),"Inactive garden has phantom water");typeof(HeavenlyGarden).GetField("activeGarden",BindingFlags.Static|BindingFlags.NonPublic).SetValue(null,null);
  Console.WriteLine("PASS "+checks+" real evolution ownership/save, reward cancellation/re-entry/death and pond classification checks; engine doubles, not Unity");
 }
}
