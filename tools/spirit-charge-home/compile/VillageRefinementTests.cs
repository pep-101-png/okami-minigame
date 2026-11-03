using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using Sunward;
using Sunward.Remaster;
public static class VillageRefinementTests
{
    static int checks;
    static void Check(bool v,string why){checks++;if(!v)throw new Exception(why);}
    static void Call(object target,string method)=>target.GetType().GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic).Invoke(target,null);
    public static void Run()
    {
        var circle=new List<Vector2>();for(int i=0;i<=40;i++){float t=i*Mathf.PI*2/40;circle.Add(new Vector2(200+80*MathF.Cos(t),200+80*MathF.Sin(t)));}
        Check(!BrushPatterns.CherryBomb(circle),"Bloom circle misclassified as a bomb");
        var bomb=new List<Vector2>(circle);for(int i=1;i<=8;i++)bomb.Add(new Vector2(280,200-i*10));
        Check(BrushPatterns.CherryBomb(bomb),"Circle with straight fuse not recognised");
        var slash=new List<Vector2>();for(int i=0;i<35;i++)slash.Add(new Vector2(i*8,100));Check(!BrushPatterns.CherryBomb(slash),"Power Slash misclassified as a bomb");
        Check(!BrushPatterns.CherryBomb(new List<Vector2>{new Vector2(1,1)}),"Tiny stroke creates a bomb");
        var game=new GameFlow{Player=new WolfMotor(),Panel="",Health=120};game.Player.game=game;game.Services.game=game;
        var lower=new LowerArena{game=game,cover=new GameObject(),chamber=new GameObject(),fragments=Array.Empty<Transform>()};game.Profile.wins=5;Call(lower,"Awake");Call(lower,"Start");
        game.Player.transform.position=new Vector3(35,0,0);Call(lower,"Update");Check(!LowerArena.Shaft(game.Player.transform.position),"Saved win opens floor during a peaceful walk");
        LowerArena.TrialFinished(false);Check(!LowerArena.Shaft(game.Player.transform.position),"Defeat reopens shaft from saved unlock");
        LowerArena.TrialFinished(true);Time.deltaTime=3.1f;Call(lower,"Update");Check(LowerArena.Shaft(game.Player.transform.position),"Current trial victory no longer opens shaft");
        LowerArena.Leave();Call(lower,"Update");Check(!LowerArena.Shaft(game.Player.transform.position),"Leaving and revisiting reopens floor");Call(lower,"OnDestroy");
        game.Player.transform.position=new Vector3(GardenPond.X,GardenPond.Water,GardenPond.Z);
        var spa=new SpaRest{game=game};game.Spa=spa;spa.Bathe();Check(spa.Bonus==25&&game.MaxHealth==145&&spa.Remaining==300,"Spring bonus has wrong size/duration");
        spa.Bathe();Check(spa.Bonus==25&&game.MaxHealth==145,"Bathing stacks the maximum-health bonus");
        var method=typeof(VillageServices).GetMethod("SitAt",BindingFlags.Instance|BindingFlags.NonPublic);
        var sit=(IEnumerator)method.Invoke(game.Services,new object[]{game.Player.transform.position,0f});Check(sit.MoveNext(),"Original rest coroutine failed to start");Time.deltaTime=.1f;
        for(int i=0;i<30;i++)sit.MoveNext();Check(game.Health>120&&game.Health<145,"Spring healing is instant or absent");
        for(int i=0;i<90;i++)sit.MoveNext();Check(Math.Abs(game.Health-145)<.01f,"Rest does not fill temporary vitality cap");
        game.Player.input.Interact.pressedThisFrame=true;while(sit.MoveNext()){}Check(!game.Player.Locked&&!game.Services.Resting,"Leaving bath leaves controls locked");game.Player.input.Interact.pressedThisFrame=false;
        Time.deltaTime=300;Call(spa,"Update");Check(spa.Bonus==0&&game.MaxHealth==120&&game.Health==120,"Expired bonus leaves permanent excess health");
        spa.Bathe();game.Blocked=true;Time.deltaTime=5;Call(spa,"Update");Check(spa.Remaining==300,"Pause consumes the five-minute blessing");game.Blocked=false;
        game.Health=0;Call(spa,"Update");Check(spa.Bonus==0,"Death preserves temporary spring vitality");game.Health=120;
        var presentation=new VillagePresentation{game=game};Time.unscaledDeltaTime=.016f;game.ShowDialogue("Farmer\n\nFresh vegetables today.");game.Player.input.Interact.pressedThisFrame=true;Call(presentation,"Update");Check(game.Panel=="dialogue","Opening E immediately closes the NPC bubble");
        game.Player.input.Interact.pressedThisFrame=false;Time.unscaledDeltaTime=.3f;Call(presentation,"Update");game.Player.input.Interact.pressedThisFrame=true;Call(presentation,"Update");Check(game.Panel=="","NPC bubble cannot be dismissed with E");game.Player.input.Interact.pressedThisFrame=false;
        game.Close();game.Presentation=presentation;MonoBehaviour.CameraInstance=null;
        var challenge=new FestivalChallenges{game=game};game.Profile.night=true;challenge.Begin(2);
        Check(presentation.Playing&&game.Player.Locked,"Festival intro does not own player control");
        string before=challenge.Status;Time.deltaTime=50;Call(challenge,"Update");Check(challenge.Active&&challenge.Status==before,"Introduction consumes the challenge countdown");
        Time.unscaledDeltaTime=.1f;for(int i=0;i<40;i++)Call(presentation,"Update");Check(!presentation.Playing&&!game.Player.Locked,"Intro does not restore controls after its duration");
        int tokens=game.Profile.festivalTokens;presentation.Festival(true);game.Player.input.Pause.pressedThisFrame=true;Call(presentation,"Update");Check(!presentation.Playing&&!game.Player.Locked&&game.Profile.festivalTokens==tokens,"Skipping victory changes reward balance or leaves controls locked");game.Player.input.Pause.pressedThisFrame=false;challenge.Cancel();
        InkText.Draw("E · Noticeboard",new Rect(0,0,600,70),30,Color.white);
        Console.WriteLine("PASS "+checks+" current-win shaft, spring health/expiry, native rest, brush-gesture and dialogue input contracts; engine doubles");
    }
}
