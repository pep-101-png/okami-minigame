using System;
using System.Collections;
using System.Reflection;
using Sunward;
using Sunward.Remaster;
using UnityEngine;
static class FestivalTests
{
 static object Call(object target,string method)=>target.GetType().GetMethod(method,BindingFlags.NonPublic|BindingFlags.Instance).Invoke(target,null);
 static int checks;
 static void Check(bool yes,string why){checks++;if(!yes)throw new Exception(why);}
 public static int Run()
 {
  var dialogue=new GameFlow();dialogue.ShowDialogue("Tea invitation","elder");Check(dialogue.Dialogue=="Tea invitation"&&dialogue.Panel=="elder","Public dialogue API loses invitation text/panel");
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
  foreach(string id in ProgressionRules.Upgrades)Check(ProgressionRules.Explain(id).Length>8&&ProgressionRules.Explain(id).Length<75&&ProgressionRules.Cap(id)>0,"Missing shop effect or cap");
  foreach(string room in new[]{"home","food","dojo"})
  {
   player.transform.position=Vector3.zero;VillageInteriors.Enter(game,room);var inside=player.transform.position;
   Check(VillageInteriors.Inside(inside),"Door teleport does not reach its room");
   Check(VillageInteriors.Height(inside,out var floor)&&floor<-240,"Indoor height falls through to the outdoor terrain");
   Check(!LowerArena.Inside(inside)&&!LowerArena.Shaft(inside),"House interior triggers lower arena recovery");
   var guarded=VillageInteriors.Guard(inside,new Vector3(1000,inside.y,1000));Check(VillageInteriors.Inside(guarded),"Player can leave an isolated room's bounds");
   VillageInteriors.Enter(game,room);Check(!VillageInteriors.Inside(player.transform.position)&&player.transform.position.y>-.1f,"Room exit cannot return outdoors");
  }
  // Walk real portal code, then run the actual river-recovery component.
  // This catches the previous update's immediate y<-6 river recovery indoors.
  var waterContact=new WaterContact{game=game};
  foreach(string room in new[]{"home","food","dojo"})
  {
   player.transform.position=Vector3.zero;
   var doorways=new VillageDoorways{game=game};
   Vector3 threshold=room=="home"?VillageInteriors.HomeDoor:room=="food"?VillageInteriors.FoodDoor:VillageInteriors.DojoDoor;
   Vector3 inward=room=="food"?Vector3.right:Vector3.forward;
   Vector3 from=threshold-inward*3.4f,to=threshold-inward*1.4f;
   player.transform.position=from;Call(doorways,"Update");player.transform.position=to;Call(doorways,"Update");
   var arrival=player.transform.position;Check(VillageInteriors.Inside(arrival),"Walking into "+room+" does not enter");
   int cancels=game.Combat.cancels;
   for(int frame=0;frame<120;frame++)Call(waterContact,"Update");
   Check(game.Combat.cancels==cancels && (player.transform.position-arrival).magnitude<.001f,"River recovery ejects player from "+room);
   var camera=VillageInteriors.CameraPosition(arrival,arrival+new Vector3(100,30,-100));
   Check(VillageInteriors.Inside(camera) && camera.y<arrival.y+6,"Room camera exposes a floating floor from outside");
   var outside=arrival+new Vector3(80,0,0);Check(!VillageInteriors.AnyRoom(outside),"Interior bounds include unrelated world");
   Time.deltaTime=1f/60;Call(doorways,"Update");
   player.transform.position=room=="home"?new Vector3(-34,-249.865f,-19.4f):room=="food"?new Vector3(4.3f,-249.57f,-15):new Vector3(0,-249.47f,14.2f);
   Call(doorways,"Update");Check(player.transform.position.y>-1,"Immediate walk-back exit is blocked by a portal timer");
  }
  Check(!VillageDoorways.Crossed(new Vector3(-38,.1f,-23),new Vector3(-38,.1f,-20),VillageInteriors.HomeDoor,Vector3.forward),"Walking beside house triggers its portal");
  Check(!VillageDoorways.Crossed(new Vector3(-34,.1f,-21),new Vector3(-34,.1f,-23),VillageInteriors.HomeDoor,Vector3.forward),"Walking away from doorway enters house");
  Check(!VillageDoorways.Crossed(new Vector3(-34,8,-23),new Vector3(-34,8,-20),VillageInteriors.HomeDoor,Vector3.forward),"Jumping above door enters house");
  var home=new NativeHomeRoom{number=2,game=game,door=new Vector3(-5.56f,0,-6.06f),doorInward=Vector3.left,doorHalfWidth=.83f,exitPoint=new Vector3(-2.96f,0,-6.06f),entrance=new Vector3(-9,-54.97f,-8.2f)};home.transform.position=new Vector3(-9,-55,-6);Call(home,"OnEnable");
  var teaDoors=new VillageDoorways{game=game};player.transform.position=new Vector3(-2,0,-6.06f);Call(teaDoors,"Update");player.transform.position=new Vector3(-4,0,-6.06f);Call(teaDoors,"Update");
  Check(home.Contains(player.transform.position),"Tea home still requires a glow/E hotspot");
  int teaCancels=game.Combat.cancels;for(int i=0;i<30;i++)Call(waterContact,"Update");Check(game.Combat.cancels==teaCancels,"Tea room is treated as river");
  Time.deltaTime=.7f;Call(teaDoors,"Update");player.transform.position=new Vector3(-9,-54.97f,-7.8f);Call(teaDoors,"Update");Check(player.transform.position.y>-1,"Tea home exit cannot walk back to village");Call(home,"OnDisable");
  foreach(var inward in new[]{Vector3.forward,Vector3.back,Vector3.right,Vector3.left})
  {
   var threshold=new Vector3(5,0,7);
   Check(VillageDoorways.Crossed(threshold-inward*1.4f,threshold-inward*1.2f,threshold,inward),"Player already in approach zone cannot enter");
   Check(VillageDoorways.Crossed(threshold-inward*3,threshold-inward*.4f,threshold,inward),"Low-frame step skips doorway");
   Check(!VillageDoorways.Crossed(threshold-inward*1.2f,threshold-inward*1.4f,threshold,inward),"Walking away activates portal");
  }
  for(int i=0;i<=200;i++)foreach(bool forward in new[]{true,false})
  {var p=VillageStreetPlay.BallPosition(i/200f,forward);Check(p.x>=-1.81f&&p.x<=1.81f&&p.z>=-5.21f&&p.z<=-1.29f&&p.y>=.17f&&p.y<=.25f,"Street ball leaves its safe play area");}
  var audio=new ValleyAudio();var audioType=typeof(ValleyAudio);var flags=BindingFlags.Instance|BindingFlags.NonPublic;
  foreach(string field in new[]{"music","wind","river","houseMusic","gardenMusic","palaceMusic","presentationMusic"})audioType.GetField(field,flags).SetValue(audio,new AudioSource());
  audioType.GetField("game",flags).SetValue(audio,game);
  var sounds=(System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<AudioClip>>)audioType.GetField("bank",flags).GetValue(audio);
  sounds["housemusic"]=new System.Collections.Generic.List<AudioClip>{new AudioClip{length=34.7f,name="original melody"}};
  var houseAudio=(AudioSource)audioType.GetField("houseMusic",flags).GetValue(audio);var update=audioType.GetMethod("Update",flags);
  player.transform.position=VillageInteriors.FoodCentre;Time.unscaledDeltaTime=.1f;update.Invoke(audio,null);
  Check(houseAudio.isPlaying&&houseAudio.volume>0&&houseAudio.volume<.01f,"Music enters at full volume");
  for(int i=0;i<45;i++)update.Invoke(audio,null);Check(Math.Abs(houseAudio.volume-.035f)<.001f,"House music never reaches quiet target");
  player.transform.position=Vector3.zero;update.Invoke(audio,null);Check(houseAudio.volume>0&&houseAudio.volume<.035f&&houseAudio.isPlaying,"Leaving music house stops abruptly");
  for(int i=0;i<45;i++)update.Invoke(audio,null);Check(!houseAudio.isPlaying&&houseAudio.volume==0,"House music leaks outside indefinitely");
  sounds["gardenmusic"]=new System.Collections.Generic.List<AudioClip>{new AudioClip{length=34.7f,name="original garden melody"}};
  sounds["palacemusic"]=new System.Collections.Generic.List<AudioClip>{new AudioClip{length=62f,name="separate native palace melody"}};
  var gardenAudio=(AudioSource)audioType.GetField("gardenMusic",flags).GetValue(audio);var palaceAudio=(AudioSource)audioType.GetField("palaceMusic",flags).GetValue(audio);
  player.transform.position=HeavenlyGarden.Centre;for(int i=0;i<45;i++)update.Invoke(audio,null);
  Check(gardenAudio.isPlaying&&Math.Abs(gardenAudio.volume-.012f)<.001f&&!houseAudio.isPlaying&&!palaceAudio.isPlaying,"Garden reuses indoor house source or starts palace music");
  player.transform.position=HeavenlyGarden.PalaceCentre;for(int i=0;i<45;i++)update.Invoke(audio,null);
  Check(palaceAudio.isPlaying&&Math.Abs(palaceAudio.volume-.004f)<.001f&&!gardenAudio.isPlaying,"Palace lacks its own quiet exclusive music");
  player.transform.position=VillageInteriors.FoodCentre;for(int i=0;i<45;i++)update.Invoke(audio,null);
  Check(!palaceAudio.isPlaying&&houseAudio.isPlaying&&!gardenAudio.isPlaying,"Room music leaks across realms");
  var life=new VillageLife{game=game};game.Profile.vegetables=2;int coins=game.Profile.coins;life.GiveProduce();Check(game.Profile.vegetables==1&&game.Profile.coins==coins+5,"Farmer cannot receive one carried/pouch vegetable");
  var tea=new VillageTeaVisit{game=game};string first=tea.Story;tea.NextStory();Check(tea.Story!=first&&first.Contains("Shiranui"),"Tea stories do not advance or lack original lore");
  StreetActorLifecycle.Enabled=true;
  try
  {
   int streetObjectStart=GameObject.created.Count;var street=new VillageStreetPlay{game=game};Call(street,"Start");
   var children=(OriginalActor[])typeof(VillageStreetPlay).GetField("children",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(street);
   var puppies=(OriginalActor[])typeof(VillageStreetPlay).GetField("puppies",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(street);
   Check(street.Ready && children.Length==2 && puppies.Length==3,"Street actor population missing");
   foreach(var actor in children)Check(actor!=null && actor.Ready && actor.CurrentSourceMotion=="hm1c_000","Child failed Awake after runtime creation");
   foreach(var actor in puppies)Check(actor!=null && actor.Ready && actor.CurrentSourceMotion=="an18_000","Puppy failed Awake after runtime creation");
   Check(System.Linq.Enumerable.Count(System.Linq.Enumerable.Distinct(System.Linq.Enumerable.Select(puppies,p=>p.resource)))==3,"Puppy variants share one appearance");
   Check(GameObject.created.Count>streetObjectStart,"Street did not instantiate its original actors");
  }
  finally{StreetActorLifecycle.Enabled=false;}
  return checks;
 }
}
