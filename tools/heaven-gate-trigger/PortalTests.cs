using System;using System.Linq;using System.Reflection;using Sunward;using Sunward.Remaster;using UnityEngine;
static class PortalTests
{
 static int checks;static BindingFlags flags=BindingFlags.Instance|BindingFlags.NonPublic;
 static void Check(bool b,string s){checks++;if(!b)throw new Exception(s);}
 static void Call(object o,string method,params object[] args)=>o.GetType().GetMethod(method,flags).Invoke(o,args);
 static void Put(object o,string field,object v)=>o.GetType().GetField(field,flags).SetValue(o,v);
 static GameFlow Game()
 {
  var root=new GameObject();var p=root.AddComponent<WolfMotor>();var native=root.AddComponent<NativeAmaterasu>();Call(native,"Awake");var g=new GameFlow{Player=p,Panel="",Health=20,Energy=4,Stamina=5};p.game=g;p.Grounded=true;
  var combat=root.AddComponent<WolfCombat>();g.Combat=combat;combat.game=g;combat.motor=p;combat.spear=new WeaponDefinition();combat.sundial=new WeaponDefinition();Put(combat,"nativeBody",native);combat.backSocket=native.CreateBackSocket();combat.Equip();g.Heaven=new HeavenlyGarden{game=g};g.Presentation=new VillagePresentation{game=g};g.Services.game=g;return g;
 }
 static HeavenReturnPortal Gate(GameFlow g)
 {
  // Deliberately shifted and rotated: a static garden coordinate cannot pass.
  var gate=new GameObject("Visible torii at actual layout transform");gate.transform.position=new Vector3(241,72,-22);gate.transform.rotation=Quaternion.Euler(0,37,0);
  Call(g.Heaven,"BuildReturnGate",gate.transform);var obj=GameObject.created.Last(x=>x.name=="Torii spirit passage · walk through to Windflower");var p=obj.GetComponent<HeavenReturnPortal>();Check(p!=null&&p.game==g,"Visible gate lacks its live passage component");Check(obj.transform.parent==gate.transform,"Passage is detached from visible gate");Check(obj.GetComponent<BoxCollider>().isTrigger,"Passage blocks the opening instead of triggering");Check(obj.GetComponent<Rigidbody>().isKinematic&&!obj.GetComponent<Rigidbody>().useGravity,"Trigger lacks stable kinematic body");return p;
 }
 static void Walk(GameFlow g,HeavenReturnPortal p,Vector3 local){g.Player.transform.position=p.transform.TransformPoint(local);Call(p,"Update");}
 static void Returned(GameFlow g)
 {
  Check(Math.Abs(g.Player.transform.position.x+34)<.001f&&Math.Abs(g.Player.transform.position.z+24)<.001f&&!HeavenlyGarden.Inside(g.Player.transform.position),"Actual ReturnHome did not put player in village");
  Check(!g.Player.Locked&&g.Panel==""&&Time.timeScale==1,"Actual return leaves controls/menu/time locked");Check(g.Health==g.MaxHealth&&g.Stamina==g.MaxStamina&&g.Energy==g.MaxEnergy,"Actual return fails to restore pools");Check(g.Player.animationView.current=="Idle_Natural","Actual return does not release the pose");
 }
 static void Main(string[] args)
 {
  Resources.Root=args[0];
  foreach(int fps in new[]{5,15,30,60,120})
  {
   var g=Game();var p=Gate(g);var enemy=new EnemyBrain();g.Enemies.Add(enemy);g.InTrial=g.BossTrial=true;g.Player.Locked=true;g.Panel="dialogue";Time.timeScale=0;
   // No ground probe, realm flag, dialogue state or stale movement lock owns this gate.
   HeavenPhysicsFixture.hits=new[]{new RaycastHit{collider=new Collider{name="Heaven garden ground · upper tier"},point=new Vector3(241,84,-22)}};
   float z=5;Walk(g,p,new Vector3(0,.1f,z));bool returned=false;
   for(int i=0;i<fps;i++){z-=20f/fps;Walk(g,p,new Vector3(0,.1f,z));if(g.Player.TeleportRevision>0){returned=true;break;}}
   Check(returned,"Walking across portal missed at "+fps+"fps");Returned(g);Check(g.Enemies.Count==0&&enemy.gameObject.wasDestroyed,"Return bypasses actual encounter cleanup");int revision=g.Player.TeleportRevision;Call(p,"Update");Check(g.Player.TeleportRevision==revision,"Return triggers repeatedly after leaving");
  }
  {
   var g=Game();var p=Gate(g);Walk(g,p,new Vector3(0,.1f,8));Walk(g,p,new Vector3(0,.1f,-8));Returned(g); // 16m step: no arbitrary speed cutoff.
  }
  {
   var g=Game();var p=Gate(g);Walk(g,p,new Vector3(0,.1f,5));g.Player.Teleport(p.transform.TransformPoint(new Vector3(0,.1f,-5)));int revision=g.Player.TeleportRevision;Call(p,"Update");Check(g.Player.TeleportRevision==revision&&HeavenlyGarden.Inside(g.Player.transform.position),"An unrelated teleport falsely sweeps through the gate");
   Walk(g,p,new Vector3(0,.1f,0));Returned(g);
  }
  {
   var g=Game();var p=Gate(g);Walk(g,p,new Vector3(3.5f,.1f,5));Walk(g,p,new Vector3(3.5f,.1f,-5));Check(g.Player.TeleportRevision==0,"Walking beside a post returns home");
   g.Player.transform.position=p.transform.TransformPoint(new Vector3(0,.1f,1.65f));Call(p,"OnTriggerEnter",new Collider());Check(g.Player.TeleportRevision==0,"Non-player triggers passage");Call(p,"OnTriggerEnter",new Collider{owner=g.Player});Returned(g);int revision=g.Player.TeleportRevision;Call(p,"OnTriggerStay",new Collider{owner=g.Player});Check(revision==g.Player.TeleportRevision,"Same overlap repeats return");
  }
  {
   var g=Game();var p=Gate(g);g.CinematicActive=true;Walk(g,p,new Vector3(0,.1f,0));Check(g.Player.TeleportRevision==0,"Portal interrupts a cinematic");g.CinematicActive=false;Call(p,"Update");Returned(g);
   Call(p,"Update");g.Player.Teleport(p.transform.TransformPoint(new Vector3(0,.1f,5)));Call(p,"Update");Walk(g,p,new Vector3(0,.1f,0));Returned(g);Check(g.Player.TeleportRevision==3,"Portal cannot be used on a later garden visit");
  }
  Check(!HeavenReturnPortal.Crosses(new Vector3(0,9,5),new Vector3(0,9,-5)),"Passing over the gate activates it");
  Console.WriteLine("PASS "+checks+" gate-owned component, trigger/sweep, moved/rotated gate, low-FPS crossing, actual ReturnHome/Teleport/control cleanup and repeat-visit cases. Engine doubles; Unity physics/playback unverified.");
 }
}
