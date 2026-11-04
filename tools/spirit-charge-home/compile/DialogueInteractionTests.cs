using System;
using System.Reflection;
using System.Collections.Generic;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
public static class DialogueInteractionTests
{
    static BindingFlags instance=BindingFlags.Instance|BindingFlags.NonPublic;
    static int checks;
    static void Check(bool ok,string why){checks++;if(!ok)throw new Exception(why);}
    static object Get(object o,string n)=>o.GetType().GetField(n,instance).GetValue(o);
    static void Set(object o,string n,object v)=>o.GetType().GetField(n,instance).SetValue(o,v);
    static void Call(object o,string n)=>o.GetType().GetMethod(n,instance).Invoke(o,null);
    public static void Run(string message)
    {
        int oldWidth=Screen.width,oldHeight=Screen.height;Screen.width=800;Screen.height=600;
        var game=new GameFlow{Player=new WolfMotor(),Panel="dialogue"};game.ShowDialogue(message+"\n\n"+message);var p=new VillagePresentation{game=game};
        Time.unscaledDeltaTime=.01f;Call(p,"Update");var pages=(List<string>)Get(p,"dialoguePages");Check(pages.Count>1,"Long dialogue not split");
        for(int i=0;i<pages.Count;i++)
        {
            Set(p,"dialogueTime",0f);Call(p,"Advance");Check(game.Panel=="dialogue" && (int)Get(p,"page")==i,"First input skips unseen words or closes dialogue");
            Call(p,"Advance");Check(i==pages.Count-1?game.Panel=="":game.Panel=="dialogue" && (int)Get(p,"page")==i+1,"Page input closes early or strands final page");
        }
        game.ShowDialogue(message);Set(p,"dialogueWasOpen",false);Call(p,"Update");Check((int)Get(p,"page")==0,"Reopening dialogue keeps old page");
        Screen.width=1920;Screen.height=1080;Call(p,"Update");Check(Get(p,"lastDialogue").Equals(message),"Resize loses current dialogue");Screen.width=oldWidth;Screen.height=oldHeight;
        // Exercise the actual audio router with a range large enough that distance
        // alone would otherwise allow farm/rooster recordings across realms.
        var audio=new ValleyAudio();Set(audio,"game",game);var bank=(Dictionary<string,List<AudioClip>>)Get(audio,"bank");bank["rooster"]=new List<AudioClip>{new AudioClip()};bank["heaven-gong"]=new List<AudioClip>{new AudioClip()};Time.unscaledTime=100;game.Player.transform.position=HeavenlyGarden.Centre;
        Check(!audio.World("rooster",Vector3.zero,500),"Farm call leaks into heavens");Check(audio.World("heaven-gong",HeavenlyGarden.Centre+Vector3.right,20),"Realm guard silences garden gong");
        Time.unscaledTime=102;game.Player.transform.position=HeavenlyGarden.PalaceCentre;Check(!audio.World("heaven-gong",HeavenlyGarden.Centre,500),"Garden sound leaks into palace");
        game.Player.transform.position=Vector3.zero;Check(audio.World("rooster",Vector3.right,20),"Farm voice broken in village");
        Console.WriteLine("PASS "+checks+" real dialogue advance/reopen/resize and audio realm routing checks; engine doubles, not Unity");
    }
}
