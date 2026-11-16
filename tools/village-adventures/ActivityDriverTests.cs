using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Reflection;using System.Text.Json;using UnityEngine;using Unity.Cinemachine;using Sunward;using Sunward.Remaster;
static class ActivityDriverTests
{
 const BindingFlags F=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
 static object Get(object o,string n)=>o.GetType().GetField(n,F).GetValue(o);static void Call(object o,string n)=>o.GetType().GetMethod(n,F).Invoke(o,null);
 static int checks;static void Check(bool b,string s){checks++;if(!b)throw new Exception(s);}
 static float[] V(Vector3 v)=>new[]{v.x,v.y,v.z};static float[] Q(Quaternion q)=>new[]{q.x,q.y,q.z,q.w};
 static float[][] Pose(NativePaintedRig r)=>r.Bones.Select(b=>V(b.localPosition).Concat(Q(b.localRotation)).Concat(V(b.localScale)).ToArray()).ToArray();
 static bool Visible(Transform t){for(var a=t;a!=null;a=a.parent)if(!a.gameObject.activeSelf || a.gameObject.wasDestroyed)return false;return true;}
 static void Capture(string path,Vector3 centre)
 {
  var eye=centre+(path.Contains("moonlit")?new Vector3(27,27,-32):new Vector3(6,6,-8));Camera.main.transform.position=eye;foreach(var ob in GameObject.created.ToArray()){var bb=ob.GetComponent<OriginalBillboard>();if(bb!=null)Call(bb,"LateUpdate");}
  var props=new List<object>();var actors=new List<object>();
  foreach(var go in GameObject.created.ToArray())
  {
   if(!Visible(go.transform))continue;var p=go.GetComponent<OriginalVisual>();if(p!=null){var r=(NativePaintedRig)Get(p,"rig");if(r!=null)props.Add(new{held=p.GetComponentInParent<OriginalActor>()!=null,resource=r.Resource,position=V(r.Root.transform.position),rotation=Q(r.Root.transform.rotation),scale=V(r.Root.transform.lossyScale),pose=Pose(r)});}
   var a=go.GetComponent<OriginalActor>();if(a!=null && a.Ready){Call(a,"LateUpdate");var r=(NativePaintedRig)Get(a,"rig");actors.Add(new{resource=r.Resource,position=V(r.Root.transform.position),rotation=Q(r.Root.transform.rotation),scale=V(r.Root.transform.lossyScale),pose=Pose(r),clip=a.CurrentSourceMotion});}
  }
  File.WriteAllText(path,JsonSerializer.Serialize(new{scope="Actual activity driver/native asset transform output; API doubles, not Unity",centre=V(centre),props,actors}));
 }
 static void Motion(string file,object driver)
 {
  var frames=new List<object>();for(int i=0;i<120;i++){
   Time.time+=Time.deltaTime;Call(driver,"Update");var samples=new List<object>();
   foreach(var go in GameObject.created.ToArray()){var a=go.GetComponent<OriginalActor>();if(a==null || !a.Ready || !Visible(go.transform))continue;Call(a,"LateUpdate");var r=(NativePaintedRig)Get(a,"rig");samples.Add(new{resource=r.Resource,position=V(r.Root.transform.position),rotation=Q(r.Root.transform.rotation),scale=V(r.Root.transform.lossyScale),pose=Pose(r),clip=a.CurrentSourceMotion});}
   var held=GameObject.created.Where(go=>Visible(go.transform)).Select(go=>go.GetComponent<OriginalVisual>()).Where(p=>p!=null && p.GetComponentInParent<OriginalActor>()!=null).Select(p=>{var r=(NativePaintedRig)Get(p,"rig");return new{resource=r.Resource,position=V(r.Root.transform.position),rotation=Q(r.Root.transform.rotation),scale=V(r.Root.transform.lossyScale)};}).ToArray();
   frames.Add(new{t=i/30f,actors=samples,held});
  }File.WriteAllText(file,JsonSerializer.Serialize(frames));
 }
 public static void Run(string output)
 {
  GameObject.created.Clear();StreetActorLifecycle.Enabled=true;
  var player=new GameObject("player").AddComponent<WolfMotor>();var game=new GameFlow{Player=player,Panel="",Health=100,Stamina=73,Energy=44};player.game=game;game.Combat.allowEquip=true;
  var camera=new OrbitCamera{target=player,virtualCamera=new CinemachineCamera()};MonoBehaviour.CameraInstance=camera;Camera.main.transform=camera.virtualCamera.transform;
  game.Audio=new ValleyAudio();typeof(ValleyAudio).GetField("game",F).SetValue(game.Audio,game);Call(game.Audio,"Awake");
  // Read the installed original imp prefab's actor configuration, rather than inventing an animation mapping.
  game.spirits=new[]{"reed","wisp","ranged","heavy"}.Select(id=>{
   string text=File.ReadAllText(Path.Combine(Resources.Root,"Sunward/Generated/Enemy-"+id+".prefab"));var visual=new GameObject("prefab "+id);visual.SetActive(false);var a=visual.AddComponent<OriginalActor>();a.game=game;
   foreach(var name in new[]{"resource","idle","walk","run","windup","strike","recover","death"}){var m=System.Text.RegularExpressions.Regex.Match(text,@"(?m)^  "+name+@": (.+)$");typeof(OriginalActor).GetField(name).SetValue(a,m.Groups[1].Value.Trim());}
   var mscale=System.Text.RegularExpressions.Regex.Match(text,@"(?m)^  modelScale: (.+)$");a.modelScale=float.Parse(mscale.Groups[1].Value,System.Globalization.CultureInfo.InvariantCulture);a.splitAttackClip=true;
   return new EnemyDefinition{id=id,title=id,hp=100,damage=5,speed=1.9f,scale=1,windup=.9f,visual=visual};}).ToArray();
  var adventures=new GameObject("Village activity drivers").AddComponent<VillageAdventures>();adventures.game=game;game.Adventures=adventures;Call(adventures,"Start");
  foreach(var c in new object[]{adventures.Mastery,adventures.Fishing,adventures.Projects,adventures.Trail})Call(c,"Start");
  foreach(var f in (List<OriginalActor>)Get(adventures.Fishing,"fish"))Check(f.Ready && f.ActivityLength(f.idle)>.25f,"Original living fish loads its swim bank");
  Time.deltaTime=Time.unscaledDeltaTime=1f/30;
  game.Profile.owned=OriginalWeaponCatalog.All.Select(e=>OriginalWeaponEvolution.EvolvedId(e.id)).ToArray();game.Profile.equipped="spear";
  for(int w=0;w<15;w++)for(int tier=1;tier<=3;tier++)
  {
   player.Teleport(WeaponMasteryTrials.Scroll);game.Health=100;game.Stamina=73;game.Energy=44;
   Check(adventures.Mastery.Begin(w,tier),"All owned awakened weapon lessons start");Check(game.InTrial && VillageAdventures.Realm(player.transform.position)==1,"Practice travels to isolated courtyard");
   Call(adventures.Mastery,"Update");Check(game.Enemies.Count==1 && game.Enemies[0].GetComponentsInChildren<OriginalActor>(true).Any(a=>a.Ready),"Practice spawns recovered imp actors");
   adventures.Mastery.Record("hit",6);adventures.Mastery.Record("charged",2);adventures.Mastery.Record("brush",3);adventures.Mastery.Record(WeaponMasteryTrials.Art[w],20);
   if(w==12 && tier>1){Check(!adventures.Mastery.GoalsMet,"Exorcism requires projectile deflections");adventures.Mastery.Record("deflect",3);}
   Check(adventures.Mastery.GoalsMet,"All 45 lesson objectives can complete");
   if(w==14 && tier==3)Capture(Path.Combine(output,"mastery-runtime.json"),VillageAdventures.PracticeCentre);
   Call(adventures.Mastery,"Update");Check(!adventures.Mastery.Active && !game.InTrial && game.Profile.adventures.mastery[w]==tier,"Completed lesson saves and ends practice");Check(Vector3.Distance(player.transform.position,WeaponMasteryTrials.Scroll)<.01f && game.Health==100 && game.Stamina==73 && game.Energy==44 && game.Profile.equipped==OriginalWeaponEvolution.EvolvedId("spear"),"Return restores position, weapon and vitals");
  }
  player.Teleport(WeaponMasteryTrials.Scroll);Check(adventures.Mastery.Begin(0,3),"Master replay begins");for(int j=0;j<6;j++)adventures.Mastery.Hurt();int coins=game.Profile.coins;Call(adventures.Mastery,"Update");Check(!adventures.Mastery.Active && game.Profile.coins==coins,"Six damage contacts fail without reward");
  Check(adventures.Mastery.Begin(0,1),"Cancelled lesson starts");adventures.Cancel();Check(!game.InTrial && !adventures.Mastery.Active,"Return/cancel clears lesson state");
  foreach(int w in new[]{0,1,2,3,4,5,6,7,8,10,12,13,14})
  {
   player.Teleport(WeaponMasteryTrials.Scroll);Check(adventures.Mastery.Begin(w,1),"Elemental fixture starts in actual lesson context");game.Health=50;game.Energy=10;
   var target=game.SpawnPracticeSpirit("reed",VillageAdventures.PracticeCentre+Vector3.forward,1000);target.Hp=target.MaxHp=1000;
   if(w==8){AwakenedWeaponArts.BrushHit(game,target);var effect=GameObject.created.Select(o=>o.GetComponent<FallingDivineSword>()).Last(e=>e!=null);for(int i=0;i<15;i++)Call(effect,"Update");}
   else if(w==12)AwakenedWeaponArts.BrushHit(game,target);
   else{AwakenedWeaponArts.Contact(game,target,true);if(w==6){var effect=GameObject.created.Select(o=>o.GetComponent<SevenCutSequence>()).Last(e=>e!=null);for(int i=0;i<25;i++)Call(effect,"Update");}}
   Check(adventures.Mastery.Count(WeaponMasteryTrials.Art[w])>0,"Actual awakened art records its real contact or recovered resource");
   if(w==14)Check(target.Frozen,"Tundra actually freezes the original imp");
   if(w==12){float hp=target.Hp;target.Damage(10,Vector3.zero,0);Check(hp-target.Hp>10,"Purification actually increases received damage");}
   adventures.Cancel();
  }
  player.Teleport(VillageFishing.Bank);game.Profile.vegetables=30;Check(adventures.Fishing.Feed(),"Feeding consumes produce at pond");Check(adventures.Fishing.Begin(),"Fishing sits and owns cinematic camera");
  Call(adventures.Fishing,"Update");Capture(Path.Combine(output,"fishing-runtime.json"),new Vector3(GardenPond.X,0,GardenPond.Z));
  Motion(Path.Combine(output,"fish-motion-runtime.json"),adventures.Fishing);var fish=(List<OriginalActor>)Get(adventures.Fishing,"fish");Check(adventures.Fishing.TryHook(player.transform.position,fish[0].transform.position) && adventures.Fishing.Hooked,"Brush connects player to actual visible carp");
  for(int i=0;i<900 && adventures.Fishing.Active;i++){player.input.Light.held=adventures.Fishing.Tension<.65f;Time.time+=Time.deltaTime;Call(adventures.Fishing,"Update");}
  player.input.Light.held=false;Check(!adventures.Fishing.Active && game.Profile.adventures.caught[0]==1,"Reel/ease loop catches exactly one fish");
  Check(adventures.Fishing.Begin(),"Can fish again");Call(adventures.Fishing,"Update");Check(adventures.Fishing.TryHook(player.transform.position,fish[0].transform.position),"Next fish hooks");player.input.Light.held=true;for(int i=0;i<200 && adventures.Fishing.Active;i++)Call(adventures.Fishing,"Update");player.input.Light.held=false;Check(!adventures.Fishing.Active && game.Profile.adventures.caught[0]==1,"Holding without easing breaks line and grants no catch");
  game.Profile.coins=10000;game.Profile.vegetables=100;game.Profile.adventures.caught[0]=game.Profile.adventures.fish[0]=20;player.Teleport(FestivalChallenges.Board);
  for(int i=0;i<4;i++){Check(adventures.Projects.Build(i),"Project builds from board");Check(adventures.Projects.Playing && player.Locked,"Restoration has a camera reveal");adventures.Projects.Skip();Check(!player.Locked,"Reveal skip releases movement");}
  for(int i=0;i<100;i++){Time.time+=Time.deltaTime;foreach(var go in GameObject.created.ToArray()){var guest=go.GetComponent<HeavenTeaGuest>();if(guest!=null)Call(guest,"Update");var a=go.GetComponent<OriginalActor>();if(a!=null && a.Ready && Visible(go.transform)){try{Call(a,"LateUpdate");}catch(Exception e){throw new Exception(a.resource+" / "+a.CurrentSourceMotion+" time="+Get(a,"time"),e);}}}}
  Motion(Path.Combine(output,"tea-motion-runtime.json"),adventures.Projects);Call(adventures.Projects,"Update");Capture(Path.Combine(output,"restoration-runtime.json"),VillageProjects.Tea);
  var trail=adventures.Trail;player.Teleport(MoonlitTrail.Entry);game.Profile.night=false;Check(!trail.Discover(),"Moon trail undiscoverable in daylight");game.Profile.night=true;Check(trail.Discover(),"Night reveals passage");Time.unscaledDeltaTime=2;Call(trail,"Update");Check(trail.Inside,"Walking into discovered gate enters realm");
  Time.unscaledDeltaTime=Time.deltaTime=1f/30;
  for(int stage=0;stage<3;stage++)
  {
   player.Teleport(VillageAdventures.TrailCentre+MoonlitTrail.Puzzles[stage]+Vector3.back*4);for(int i=0;i<50;i++)Call(trail,"Update");
   if(stage!=1){Check(trail.BattleActive && game.Enemies.Count==2,"Trail has two actual imp encounters");trail.Brush(stage==0?"bloom":"bomb",VillageAdventures.TrailCentre+MoonlitTrail.Puzzles[stage]);Check(game.Profile.adventures.moonStage==stage,"Puzzle cannot skip active encounter");game.EndTrailBattle(true);}
   trail.Brush("wrong",VillageAdventures.TrailCentre+MoonlitTrail.Puzzles[stage]);Check(game.Profile.adventures.moonStage==stage,"Wrong technique cannot solve puzzle");
   if(stage==0)Capture(Path.Combine(output,"moonlit-runtime.json"),VillageAdventures.TrailCentre);
   trail.Brush(stage==0?"bloom":stage==1?"slash":"bomb",VillageAdventures.TrailCentre+MoonlitTrail.Puzzles[stage]);Check(game.Profile.adventures.moonStage==stage+1,"Each original brush technique advances its seal");
  }
  player.Teleport(VillageAdventures.TrailCentre+new Vector3(0,0,19));player.input.Interact.pressedThisFrame=true;Call(trail,"Update");player.input.Interact.pressedThisFrame=false;Check(trail.Playing && game.Profile.adventures.moonCharm,"Chest grants saved charm and starts reveal");trail.Skip();Check(!player.Locked && !trail.Playing,"Chest skip releases control");
  player.Teleport(VillageAdventures.TrailCentre+new Vector3(0,0,-19));Call(trail,"Update");player.transform.position=VillageAdventures.TrailCentre+new Vector3(0,0,-25);Call(trail,"Update");Check(!trail.Inside,"Swept return gate leaves trail without thin trigger");
  var saved=JsonSerializer.Serialize(game.Profile,new JsonSerializerOptions{IncludeFields=true});var loaded=JsonUtility.FromJson<ProfileData>(saved);Check(ProgressionRules.Validate(loaded) && loaded.adventures.projects==15 && loaded.adventures.moonCharm && loaded.adventures.mastery.All(n=>n==3),"All four activities survive full profile serialization");
  Console.WriteLine("PASS "+checks+" activity driver assertions; actual original rigs, controlled inputs and API doubles, not Unity");StreetActorLifecycle.Enabled=false;
 }
}
