using System;
using System.Reflection;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
public static class GardenPassageTests
{
    static int checks;
    static void Check(bool v,string why){checks++;if(!v)throw new Exception(why);}
    static void Call(object o,string n)=>o.GetType().GetMethod(n,BindingFlags.Instance|BindingFlags.NonPublic).Invoke(o,null);
    public static void Run()
    {
        Check(!HeavenlyGarden.Inside(new Vector3(0,70,0)),"Village classified as heaven");
        Check(HeavenlyGarden.Inside(HeavenlyGarden.Centre),"Garden centre inaccessible");
        Check(!HeavenlyGarden.Inside(new Vector3(230,-250,0)),"Interior classified as heaven");
        var p=HeavenlyGarden.Guard(HeavenlyGarden.Centre+new Vector3(100,2,100));
        Check(Math.Abs(p.y-72)<.01f && Math.Pow((p.x-230)/HeavenlyGarden.WalkRadiusX,2)+Math.Pow(p.z/HeavenlyGarden.WalkRadiusZ,2)<1.001,"Garden guard changes elevation or lets the player leave the island");
        Check(!HeavenlyGarden.RiverLip(new Vector3(35,0,40)),"Dry farm triggers river portal");
        var profile=new ProfileData{xp=6860};Check(ProgressionRules.Level(profile)==15,"Altar threshold is not level fifteen");
        profile.upgrades.vitality=10;profile.upgrades.strength=10;profile.upgrades.stamina=9;Check(!HeavenlyGarden.GrowthReady(profile),"Twenty-nine upgrade ranks satisfy thirty-rank quest");profile.upgrades.stamina=10;Check(HeavenlyGarden.GrowthReady(profile),"Thirty ranks at level fifteen rejected");profile.xp=6859;Check(!HeavenlyGarden.GrowthReady(profile),"Level fourteen accepted");
        var g=new GameFlow{Player=new WolfMotor(),Panel="",Health=100};g.Player.game=g;g.Services.game=g;var presentation=new VillagePresentation{game=g};g.Presentation=presentation;
        var lower=new LowerArena{game=g,cover=new GameObject(),chamber=new GameObject(),fragments=Array.Empty<Transform>()};Call(lower,"Awake");Call(lower,"Start");g.Player.transform.position=new Vector3(35,0,0);
        LowerArena.TrialFinished(true);Check(presentation.Breaking && !LowerArena.Shaft(g.Player.transform.position),"Shaft opens before cinematic anticipation");
        Time.unscaledDeltaTime=1;Call(presentation,"Update");Check(LowerArena.Shaft(g.Player.transform.position),"Cinematic fails to reveal shaft");
        presentation.Cancel();Check(!g.Player.Locked && LowerArena.Shaft(g.Player.transform.position),"Skipping collapse loses access or controls");
        LowerArena.Leave();presentation.ShaftCollapse();presentation.Cancel();Check(LowerArena.Shaft(g.Player.transform.position),"Early cinematic skip leaves floor closed");Call(lower,"OnDestroy");
        var race=new FestivalChallenges{game=g};g.Presentation=null;g.Profile.night=true;race.Begin(1);
        var route=(Vector3[])typeof(FestivalChallenges).GetField("Route",BindingFlags.Static|BindingFlags.NonPublic).GetValue(null);
        Check(route.Length==13,"Race does not have thirteen lights");Time.deltaTime=.01f;
        for(int i=0;i<route.Length-1;i++){g.Player.transform.position=route[i];Call(race,"Update");Check(race.Active,"Race completed before all thirteen checkpoints");}
        g.Player.transform.position=route[route.Length-1];Call(race,"Update");Check(!race.Active && g.Profile.festivalTokens==3,"Thirteen checkpoints did not produce exactly one reward");
        Check(FestivalChallenges.RewardCost(0)==9 && FestivalChallenges.RewardCost(1)==12 && FestivalChallenges.RewardCost(2)==15,"Reward prices failed to increase");
        Console.WriteLine("PASS "+checks+" garden boundary/altar progression, cinematic shaft timing/skip and thirteen-checkpoint race contracts; engine doubles");
    }
}
