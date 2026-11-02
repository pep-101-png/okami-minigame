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
  foreach(string room in new[]{"home","food","dojo"})
  {
   player.transform.position=Vector3.zero;VillageInteriors.Enter(game,room);var inside=player.transform.position;
   Check(VillageInteriors.Inside(inside),"Door teleport does not reach its room");
   Check(VillageInteriors.Height(inside,out var floor)&&floor<-240,"Indoor height falls through to the outdoor terrain");
   Check(!LowerArena.Inside(inside)&&!LowerArena.Shaft(inside),"House interior triggers lower arena recovery");
   var guarded=VillageInteriors.Guard(inside,new Vector3(1000,inside.y,1000));Check(VillageInteriors.Inside(guarded),"Player can leave an isolated room's bounds");
   VillageInteriors.Enter(game,room);Check(!VillageInteriors.Inside(player.transform.position)&&player.transform.position.y>-.1f,"Room exit cannot return outdoors");
  }
  var audio=new ValleyAudio();var audioType=typeof(ValleyAudio);var flags=BindingFlags.Instance|BindingFlags.NonPublic;
  foreach(string field in new[]{"music","wind","river","houseMusic"})audioType.GetField(field,flags).SetValue(audio,new AudioSource());
  audioType.GetField("game",flags).SetValue(audio,game);
  var sounds=(System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<AudioClip>>)audioType.GetField("bank",flags).GetValue(audio);
  sounds["housemusic"]=new System.Collections.Generic.List<AudioClip>{new AudioClip{length=34.7f,name="original melody"}};
  var houseAudio=(AudioSource)audioType.GetField("houseMusic",flags).GetValue(audio);var update=audioType.GetMethod("Update",flags);
  player.transform.position=VillageInteriors.FoodCentre;Time.unscaledDeltaTime=.1f;update.Invoke(audio,null);
  Check(houseAudio.isPlaying&&houseAudio.volume>0&&houseAudio.volume<.01f,"Music enters at full volume");
  for(int i=0;i<35;i++)update.Invoke(audio,null);Check(Math.Abs(houseAudio.volume-.1f)<.001f,"House music never reaches quiet target");
  player.transform.position=Vector3.zero;update.Invoke(audio,null);Check(houseAudio.volume>0&&houseAudio.volume<.1f&&houseAudio.isPlaying,"Leaving music house stops abruptly");
  for(int i=0;i<35;i++)update.Invoke(audio,null);Check(!houseAudio.isPlaying&&houseAudio.volume==0,"House music leaks outside indefinitely");
  var life=new VillageLife{game=game};game.Profile.vegetables=2;int coins=game.Profile.coins;life.GiveProduce();Check(game.Profile.vegetables==1&&game.Profile.coins==coins+5,"Farmer cannot receive one carried/pouch vegetable");
  var tea=new VillageTeaVisit{game=game};string first=tea.Story;tea.NextStory();Check(tea.Story!=first&&first.Contains("Shiranui"),"Tea stories do not advance or lack original lore");
  return checks;
 }
}
