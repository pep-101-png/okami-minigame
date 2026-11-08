using System;using System.Linq;using System.Reflection;using System.Collections.Generic;using UnityEngine;using Sunward;using Sunward.Remaster;
static class FullPowerTests
{
 static int n;static BindingFlags f=BindingFlags.Instance|BindingFlags.NonPublic;
 static void Check(bool b,string why){n++;if(!b)throw new Exception(why);}
 static void Set(object o,string k,object v)=>o.GetType().GetField(k,f).SetValue(o,v);
 static T Get<T>(object o,string k)=>(T)o.GetType().GetField(k,f).GetValue(o);
 static void Call(object o,string m)=>o.GetType().GetMethod(m,f).Invoke(o,null);
 public static void Run()
 {
  var p=new ProfileData{owned=new[]{"spear","wp29","wp2e","wp29e"},equipped="wp29"};OriginalWeaponEvolution.Normalize(p);Check(!p.owned.Contains("wp29")&&p.owned.Contains("wp2e")&&p.equipped=="wp29e","Old save migration discarded another weapon or retained base Thunder Edge");Check(!OriginalWeaponEvolution.Unlock(p)&&p.owned.Count(x=>x=="wp29e")==1,"Repeated unlock duplicated evolved weapon");
  foreach(int fps in new[]{15,30,60,120})foreach(bool skip in new[]{false,true})
  {
   var body=new NativeAmaterasu();Call(body,"Awake");Check(body.Ready,"Native wolf did not load");var normal=Get<NativePaintedRig>(body,"rig");Check(body.ApplyPowerForm(1),"Second form failed");var second=Get<NativePaintedRig>(body,"rig");Check(second!=normal&&!normal.Root.activeSelf,"Second form overlaps normal model");
   var player=new WolfMotor{Grounded=true};var g=new GameFlow{Player=player,Panel="",Health=100};player.game=g;Set(g.Audio,"transformationVoice",new AudioSource());Set(g.Audio,"transformationBurst",new AudioSource());Set(g.Audio,"fullPowerVoice",new AudioSource());var bank=Get<Dictionary<string,List<AudioClip>>>(g.Audio,"bank");bank["full-power"]=new List<AudioClip>{new AudioClip()};
   MonoBehaviour.CameraInstance=new OrbitCamera{target=player,virtualCamera=new Unity.Cinemachine.CinemachineCamera()};var sequence=new ShiranuiTransformation{game=g};sequence.Begin(body);Check(sequence.Playing&&player.Locked&&Time.timeScale==0,"Full power cutscene did not lock controls");Check(Get<AudioSource>(g.Audio,"fullPowerVoice").plays==1,"EVBC power-up cue did not begin with cutscene");
   Time.unscaledDeltaTime=1f/fps;if(skip)sequence.Skip();else {for(int i=0;i<fps*4;i++)Call(sequence,"Update");Check(sequence.Playing,"Full power cutscene ended as quickly as second form");for(int i=0;i<fps*3;i++)Call(sequence,"Update");}
   Check(body.FullPower&&body.FormLevel==2&&body.Shiranui,"Third form not revealed");var full=Get<NativePaintedRig>(body,"rig");Check(Math.Abs(full.Root.transform.localScale.x-1.2f)<.0001f&&!second.Root.activeSelf,"Third form size or exclusive visibility wrong");Check(!sequence.Playing&&!player.Locked&&Time.timeScale==1,"Full power cutscene/skip strands controls");Check(!Get<AudioSource>(g.Audio,"fullPowerVoice").isPlaying,"Power-up audio survives cleanup");Check(body.ApplyPowerForm(0)&&!body.FullPower&&!body.Shiranui&&normal.Root.activeSelf&&!full.Root.activeSelf,"Normal form return failed");
  }
  {
   var a=new ValleyAudio();var bank=Get<Dictionary<string,List<AudioClip>>>(a,"bank");var clips=new[]{new AudioClip(),new AudioClip(),new AudioClip()};bank["ammy-swing"]=clips.ToList();var weapon=new AudioSource{isPlaying=true};Set(a,"tundraSwing",weapon);var voice=new AudioSource();Set(a,"ammyVoice",voice);for(int i=0;i<6;i++){a.AmmyAttack();Check(voice.clip==clips[i%3]&&weapon.isPlaying,"Ammy voice replaced weapon playback or lost round-robin");}
  }
  {
   var body=new NativeAmaterasu();Call(body,"Awake");Check(body.ApplyPowerForm(2),"Full form for tendrils failed");var ribbons=new SpectralTendrils();Set(ribbons,"native",body);Time.unscaledDeltaTime=.1f;Time.deltaTime=0;Call(ribbons,"LateUpdate");var rigs=Get<NativePaintedRig[]>(ribbons,"rigs");Check(rigs.Length==10&&rigs.All(r=>r.Root.activeSelf),"Recovered tendril pair missing at idle");var before=Get<Vector4[][]>(ribbons,"curves").Select(row=>row.Select(v=>new Vector3(v.x,v.y,v.z)).ToArray()).ToArray();for(int i=0;i<6;i++)Call(ribbons,"LateUpdate");var after=Get<Vector4[][]>(ribbons,"curves");Check(after.Where((row,i)=>row.Where((v,j)=>Vector3.Distance(new Vector3(v.x,v.y,v.z),before[i][j])>.001f).Any()).Any(),"Wisps freeze when timeScale is zero");body.ApplyPowerForm(0);Call(ribbons,"LateUpdate");Check(rigs.All(r=>!r.Root.activeSelf),"Spirit tendrils remain on normal Ammy");
  }
  Console.WriteLine("PASS "+n+" full-power reveal/skip/control/size, native idle tendril motion, layered attack voice and evolution migration checks; engine doubles, not Unity");
 }
}
