using System;
using System.Reflection;
using System.Collections.Generic;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
public static class VillageCompleteTests
{
    static int count;static BindingFlags flags=BindingFlags.NonPublic|BindingFlags.Instance;
    static void Check(bool b,string s){count++;if(!b)throw new Exception(s);}
    static void Call(object a,string method)=>a.GetType().GetMethod(method,flags).Invoke(a,null);
    static void Set(object a,string field,object value)=>a.GetType().GetField(field,flags).SetValue(a,value);
    public static void Run()
    {
        var profile=new ProfileData();HomeBlessings.FireBonus(profile,1000);Check(HomeBlessings.StaminaBonus(profile,1299)==50 && HomeBlessings.StaminaBonus(profile,1300)==0,"Fire bonus is not exactly five minutes");Check(HomeBlessings.HealthBonus(profile,1001)==0,"Fire grants unrequested health");HomeBlessings.BedBonus(profile,1100);Check(HomeBlessings.HealthBonus(profile,1999)==50 && HomeBlessings.StaminaBonus(profile,1999)==50,"Bed grants wrong bonuses");Check(HomeBlessings.HealthBonus(profile,2000)==0 && HomeBlessings.StaminaBonus(profile,2000)==0,"Bed bonus outlasts fifteen minutes");Check(HomeBlessings.StaminaBonus(profile,1150)==50,"Fire and bed stack twice");
        foreach(int fps in new[]{15,30,60,120})
        {
            var p=new ProfileData();for(int i=0;i<fps*899;i++)VillageDayCycle.Tick(p,1f/fps);Check(!p.night,"Day ended early");for(int i=0;i<fps*2;i++)VillageDayCycle.Tick(p,1f/fps);Check(p.night,"Night did not begin at fifteen minutes");VillageDayCycle.Tick(p,900);Check(!p.night,"Night did not end at fifteen minutes");
            p.night=true;p.dayElapsed=400;Check(VillageDayCycle.SleepTime(p,3),"NPCs do not sleep during night");p.dayElapsed=0;Check(!VillageDayCycle.SleepTime(p,3),"NPCs instantly disappear at dusk");p.dayElapsed=850;Check(!VillageDayCycle.SleepTime(p,3),"NPCs never wake during late night");
            var g=new GameFlow{Player=new WolfMotor(),Panel="",Health=100,InTrial=true,BossTrial=true};g.Player.game=g;g.Player.transform.position=LowerArena.Centre;g.Presentation=new VillagePresentation{game=g};g.Audio=new ValleyAudio();var voice=new AudioSource();Set(g.Audio,"transformationVoice",voice);var clips=(Dictionary<string,List<AudioClip>>)typeof(ValleyAudio).GetField("bank",flags).GetValue(g.Audio);clips["transformation-voice"]=new List<AudioClip>{new AudioClip()};
            g.Finish(true);Check(g.Profile.bossWins==1 && g.Presentation.Playing && g.Player.Locked,"Final boss death does not start a locked victory cinematic");Time.unscaledDeltaTime=1f/fps;for(int i=0;i<fps*7;i++)Call(g.Presentation,"Update");Check(voice.plays==1,"Victory howl did not play exactly once");Check(!g.Presentation.Playing && !g.Player.Locked,"Victory cinematic strands player");
            g.Presentation.SkyTransition(true);Check(g.Presentation.Playing && g.Player.Locked,"Sun/moon cinematic does not start");Time.frameCount++;g.Presentation.Skip();Check(!g.Presentation.Playing && !g.Player.Locked && g.Presentation.SkipHandledFrame==Time.frameCount,"Skipping sky cinematic does not restore control or consume Escape");
        }
        Console.WriteLine("PASS "+count+" actual time-cycle, home buff, final-boss victory/howl and cinematic skip checks at 15/30/60/120fps; engine doubles, not Unity");
    }
}
