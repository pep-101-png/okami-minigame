using System;
using System.Reflection;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
public static class HeavenFollowupTests
{
    static int checks;
    static void Check(bool ok,string why){checks++;if(!ok)throw new Exception(why);}
    static void Call(object o,string n)=>o.GetType().GetMethod(n,BindingFlags.Instance|BindingFlags.NonPublic).Invoke(o,null);
    public static void Run()
    {
        var game=new GameFlow{Player=new WolfMotor(),Panel="",Health=100};game.Player.game=game;game.Services.game=game;
        var garden=new GameObject();var heaven=new HeavenlyGarden{game=game};game.Heaven=heaven;
        typeof(HeavenlyGarden).GetField("garden",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(heaven,garden);
        var village=new Renderer{bounds=new Bounds(Vector3.zero,Vector3.one)};
        var alreadyHidden=new Renderer{forceRenderingOff=true,bounds=new Bounds(Vector3.zero,Vector3.one)};
        var gardenPainting=new Renderer{bounds=new Bounds(HeavenlyGarden.Centre,Vector3.one)};gardenPainting.transform.parent=garden.transform;
        var playerPainting=new Renderer{bounds=new Bounds(Vector3.zero,Vector3.one)};playerPainting.transform.parent=game.Player.transform;
        var worldEffect=new Renderer{bounds=new Bounds(Vector3.zero,Vector3.one)};
        var dressing=new NativeInteriorDressing{game=game};
        SceneQuery.objects=new UnityEngine.Object[]{village,alreadyHidden,gardenPainting,playerPainting,worldEffect};
        game.Player.transform.position=HeavenlyGarden.Centre+new Vector3(0,0,17);Time.unscaledDeltaTime=.016f;Call(heaven,"Update");Call(dressing,"LateUpdate");
        Check(village.forceRenderingOff && alreadyHidden.forceRenderingOff,"Village remains visible from the garden");
        Check(!gardenPainting.forceRenderingOff && !playerPainting.forceRenderingOff,"Garden or player hidden with village");
        Check(worldEffect.forceRenderingOff,"Pooled effect at village origin remains visible");worldEffect.bounds=new Bounds(HeavenlyGarden.Centre,Vector3.one);Call(dressing,"LateUpdate");Check(!worldEffect.forceRenderingOff,"World-space player effect is hidden by village isolation");
        var presentation=new VillagePresentation{game=game};game.Presentation=presentation;
        game.Player.input.Interact.pressedThisFrame=true;Call(heaven,"Update");Check(game.Panel=="dialogue","Keeper does not begin talking");
        Call(presentation,"Update");Check(game.Panel=="dialogue","Opening press skips the conversation");
        for(int i=0;i<20 && game.Panel=="dialogue";i++)
        {
            game.Player.input.Interact.pressedThisFrame=false;Time.unscaledDeltaTime=10;Call(presentation,"Update");Call(heaven,"Update");
            game.Player.input.Interact.pressedThisFrame=true;Time.unscaledDeltaTime=.016f;Call(presentation,"Update");Call(heaven,"Update");
        }
        Check(game.Panel=="","Finishing keeper dialogue reopens it on the same E press");
        Time.unscaledDeltaTime=.01f;Call(heaven,"Update");Check(game.Panel=="","Closing press bypasses the keeper grace interval");
        game.Player.input.Interact.pressedThisFrame=false;Time.unscaledDeltaTime=.5f;Call(heaven,"Update");game.Player.input.Interact.pressedThisFrame=true;Call(heaven,"Update");Check(game.Panel=="dialogue","Keeper cannot be spoken to again with a later press");
        game.Close();game.Player.input.Interact.pressedThisFrame=false;game.Player.transform.position=Vector3.zero;Call(heaven,"Update");Call(dressing,"LateUpdate");
        Check(!village.forceRenderingOff && alreadyHidden.forceRenderingOff,"Village's original render states are not restored on return");
        Check(!gardenPainting.forceRenderingOff && !playerPainting.forceRenderingOff,"Return changes exempt render states");
        game.Player.transform.position=HeavenlyGarden.Centre;Call(heaven,"Update");Call(dressing,"LateUpdate");Check(village.forceRenderingOff,"Second garden visit does not isolate village");Call(heaven,"OnDisable");heaven.isActiveAndEnabled=false;Call(dressing,"LateUpdate");Check(!village.forceRenderingOff && alreadyHidden.forceRenderingOff,"Disabling garden strands world visibility");
        heaven.isActiveAndEnabled=true;Call(heaven,"Update");Call(dressing,"LateUpdate");Check(village.forceRenderingOff,"Re-enabled garden does not hide the village again");Call(heaven,"OnDisable");heaven.isActiveAndEnabled=false;Call(dressing,"LateUpdate");Check(!village.forceRenderingOff,"Repeated disable fails to restore village");
        SceneQuery.objects=Array.Empty<UnityEngine.Object>();game.Close();
        Console.WriteLine("PASS "+checks+" actual keeper dialogue/E-input ordering and shared interior/heaven visibility, including moving world-space effects checks; engine doubles, not Unity");
    }
}
