using System;
using System.Reflection;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
public static class FestivalChallengeTests
{
    static int checks;
    static void Check(bool result,string text){checks++;if(!result)throw new Exception(text);}
    public static void Run()
    {
        var game=new GameFlow{Player=new WolfMotor(),Panel=""};game.Profile.night=true;game.Health=100;
        var festival=new FestivalChallenges{game=game};
        festival.Begin(2);Check(festival.Active,"Harvest relay failed to start");
        festival.Deliver(99);Check(festival.Active && game.Profile.festivalTokens==0,"Old pouch produce bypasses fresh harvest requirement");
        festival.Harvest(1);festival.Harvest(1);festival.Deliver(1);Check(festival.Active,"Duplicate crop completed relay");
        festival.Harvest(2);festival.Harvest(3);festival.Deliver(3);
        Check(!festival.Active && game.Profile.festivalTokens==3 && game.Profile.festivalWins==1,"Fresh crops and delivery did not award tokens once");
        festival.Deliver(3);Check(game.Profile.festivalTokens==3,"Repeated delivery duplicates festival reward");
        festival.Buy(0);Check(game.Profile.festivalTokens==3 && game.Profile.festivalRewards==0,"Old cheap price still buys a reward");game.Profile.festivalTokens=9;festival.Buy(0);Check(game.Profile.festivalTokens==0 && game.Profile.festivalRewards==1,"Decoration purchase not persisted");
        festival.Buy(0);festival.Buy(1);Check(game.Profile.festivalTokens==0 && game.Profile.festivalRewards==1,"Duplicate/unaffordable reward mutated profile");
        game.Profile.night=false;festival.Begin(2);Check(!festival.Active,"Daytime festival started");
        game.Profile.night=true;festival.Begin(2);festival.Cancel();Check(!festival.Active && game.Profile.festivalTokens==0,"Cancellation changed reward balance");
        festival.Begin(2);typeof(FestivalChallenges).GetField("remaining",BindingFlags.NonPublic|BindingFlags.Instance).SetValue(festival,.001f);Time.deltaTime=.1f;
        typeof(FestivalChallenges).GetMethod("Update",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(festival,null);
        Check(!festival.Active && game.Profile.festivalTokens==0,"Expired relay granted reward");
        var oldProfile=new ProfileData();Check(ProgressionRules.Validate(oldProfile),"Existing profile without festival fields rejected");
        oldProfile.festivalTokens=-1;Check(!ProgressionRules.Validate(oldProfile),"Negative token balance accepted");
        Console.WriteLine("PASS "+checks+" festival reward/harvest/cancel/time contracts; engine doubles");
    }
}
