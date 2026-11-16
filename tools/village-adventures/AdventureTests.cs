using System;using Sunward;using Sunward.Remaster;
static class AdventureTests
{
 static int checks;static void Check(bool v,string message){checks++;if(!v)throw new Exception(message);}
 static void Main(string[] args)
 {
  UnityEngine.Resources.Root=args[0];var p=new ProfileData();Check(ProgressionRules.Validate(p),"Existing profile gains safe adventure defaults");
  for(int weapon=0;weapon<15;weapon++)for(int tier=1;tier<=3;tier++){int before=p.coins;Check(VillageAdventureRules.LessonReward(p,weapon,tier),"First mastery completion");Check(p.coins>before,"First reward granted");before=p.coins;Check(!VillageAdventureRules.LessonReward(p,weapon,tier) && p.coins==before,"Replay cannot farm rewards");}
  Check(!VillageAdventureRules.LessonReward(p,0,4),"No invalid mastery tier");var fresh=new ProfileData();Check(!VillageAdventureRules.LessonReward(fresh,0,3),"Cannot skip lesson tiers");
  Check(VillageAdventureRules.FishAvailable(p,0,false),"Carp available without food");Check(!VillageAdventureRules.FishAvailable(p,1,false),"Koi require food");Check(VillageAdventureRules.Catch(p,1,true),"Fed koi caught");p.night=true;Check(!VillageAdventureRules.Catch(p,3,true),"Char wait for restored retreat");Check(!VillageAdventureRules.Catch(p,5,false),"Night salmon require food");Check(VillageAdventureRules.Catch(p,5,true),"Fed night salmon caught");
  p.night=false;p.coins=10000;p.vegetables=30;for(int i=0;i<10;i++)Check(VillageAdventureRules.Catch(p,0,false),"Common catch stored");
  for(int i=0;i<4;i++){Check(VillageAdventureRules.BuildProject(p,i),"Project contribution succeeds");int coins=p.coins;Check(!VillageAdventureRules.BuildProject(p,i) && p.coins==coins,"Project cannot charge twice");}
  p.night=true;Check(VillageAdventureRules.Catch(p,3,true),"Restored retreat unlocks char");int total=p.adventures.caught[0];VillageAdventureRules.SellFish(p,0);Check(p.adventures.caught[0]==total && p.adventures.fish[0]==0,"Selling keeps collection records");
  Check(!VillageAdventureRules.MoonReward(p),"Unsolved trail cannot reward");p.adventures.moonStage=3;Check(!VillageAdventureRules.MoonReward(p),"Encounters must also be completed");p.adventures.moonBattles=6;Check(VillageAdventureRules.MoonReward(p),"Charm awarded");int c=p.coins;Check(!VillageAdventureRules.MoonReward(p) && p.coins==c,"Charm reward once");Check(ProgressionRules.Validate(p),"All completed activity data valid");
  p.adventures.mastery[0]=4;Check(!ProgressionRules.Validate(p),"Bad mastery data rejected");ActivityDriverTests.Run(args[1]);Console.WriteLine("PASS "+checks+" activity persistence and reward assertions; API doubles, not Unity");
 }
}
