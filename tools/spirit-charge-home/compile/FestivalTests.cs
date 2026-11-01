using System;
using System.Collections;
using System.Reflection;
using Sunward;
using Sunward.Remaster;
using UnityEngine;
static class FestivalTests
{
 static int checks;
 static void Check(bool yes,string why){checks++;if(!yes)throw new Exception(why);}
 public static int Run()
 {
  var player=new WolfMotor();var game=new GameFlow{Player=player,Panel="",Health=1};player.game=game;
  var festival=game.gameObject.AddComponent<VillageFestival>();festival.game=game;var bed=new HomeRest{game=game};Time.deltaTime=.2f;
  for(int cycle=0;cycle<2;cycle++)
  {
   bool before=game.Profile.night;player.input.Interact.pressedThisFrame=false;
   var sleep=(IEnumerator)typeof(HomeRest).GetMethod("Rest",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(bed,null);
   int budget=30;while(!bed.Sleeping&&budget-->0)Check(sleep.MoveNext(),"Sleep ended before its rest state");
   Check(bed.Sleeping&&game.Profile.night!=before&&player.Locked,"Sleep does not toggle the saved time of day");
   bool night=game.Profile.night;int saves=game.Save.saves;for(int i=0;i<5;i++)sleep.MoveNext();Check(game.Profile.night==night&&game.Save.saves==saves,"Remaining asleep toggles day/night repeatedly");
   Check(game.Health==game.MaxHealth&&game.Stamina==game.MaxStamina&&game.Energy==game.MaxEnergy,"Sleep lost its existing healing mechanics");
   player.input.Interact.pressedThisFrame=true;while(sleep.MoveNext()){}Check(!bed.Active&&!player.Locked,"Waking leaves the player locked");
  }
  var profile=new ProfileData{coins=1000000};Check(ProgressionRules.Explain("vitality").Contains("12")&&ProgressionRules.Explain("strength").Contains("18%")&&ProgressionRules.Explain("movement").Contains("Rank 2"),"Upgrade explanations lack actual effects");
  int hp=ProgressionRules.MaxHp(profile);Check(ProgressionRules.Buy(profile,"vitality")&&ProgressionRules.MaxHp(profile)==hp+12,"Vitality explanation differs from gameplay");
  foreach(string id in ProgressionRules.Upgrades)Check(ProgressionRules.Explain(id).Length>25&&ProgressionRules.Cap(id)>0,"Missing shop effect or cap");
  return checks;
 }
}
