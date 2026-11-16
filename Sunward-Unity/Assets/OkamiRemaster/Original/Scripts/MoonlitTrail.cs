using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(95)]
    public sealed class MoonlitTrail:MonoBehaviour
    {
        public GameFlow game;public bool Playing{get;private set;}public bool BattleActive{get;private set;}
        public static readonly Vector3 Entry=new Vector3(-30,0,-8);
        public static readonly Vector3[] Puzzles={new Vector3(-12,0,-10),new Vector3(8,0,2),new Vector3(-4,0,14)};
        GameObject root,entryGate,chest;GameObject[] seals=new GameObject[3];float cooldown,clock;int battle;Vector3 previous;bool havePrevious;int revision;OrbitCamera camera;
        public bool Inside=>VillageAdventures.Realm(game.Player.transform.position)==2;
        Vector3 At(Vector3 p)=>VillageAdventures.TrailCentre+p;
        void Start()
        {
            root=VillageAdventures.Court(transform,VillageAdventures.TrailCentre,true);
            VillageAdventures.Prop(root.transform,"heaven-gate",new Vector3(0,0,-22),new Vector3(5,5,1.2f));
            for(int i=0;i<3;i++)
            {
                var at=Puzzles[i];seals[i]=new GameObject("Moonlit puzzle seal "+i);seals[i].transform.SetParent(root.transform,false);seals[i].transform.localPosition=at;
                if(i==2){VillageAdventures.Prop(seals[i].transform,"vt4a",Vector3.zero,new Vector3(3,2.6f,2.4f));var rock=seals[i].AddComponent<BoxCollider>();rock.size=new Vector3(2.5f,2.6f,2);rock.center=Vector3.up*1.3f;}
                else
                {
                    VillageAdventures.Prop(seals[i].transform,i==0?"vt46":"vt11",Vector3.zero,i==0?new Vector3(2.4f,1.2f,2.4f):new Vector3(1.4f,1.8f,.2f),i==0?0:90);
                    var gate=VillageAdventures.Prop(seals[i].transform,"heaven-gate",Vector3.forward*2,new Vector3(6,5,1.2f));var wall=seals[i].AddComponent<BoxCollider>();wall.size=new Vector3(7,6,.5f);wall.center=new Vector3(0,3,2);
                    var fx=OriginalAtmosphere.Create("OriginalGodSeal",seals[i].transform,Vector3.up*.04f,0,3,9999,0,0);if(fx){fx.GetComponent<ParticleSystemRenderer>().renderMode=ParticleSystemRenderMode.HorizontalBillboard;fx.gameObject.AddComponent<CelestialStillPaint>();}
                }
            }
            for(int i=0;i<14;i++)
            {float a=i*Mathf.PI/7;var tree=VillageAdventures.Prop(root.transform,i%2==0?"vt17":"vtba",new Vector3(Mathf.Sin(a)*23,0,Mathf.Cos(a)*23),new Vector3(5,6,5),i*31);if(tree)tree.AddComponent<OriginalBillboard>();VillageAdventures.Prop(root.transform,i%2==0?"vt46":"vt47",new Vector3(Mathf.Sin(a)*20,.03f,Mathf.Cos(a)*20),new Vector3(1.8f,1.4f,1.8f),i*51);}
            foreach(var at in new[]{new Vector3(-7,0,2),new Vector3(0,0,-9),new Vector3(14,0,11),new Vector3(-13,0,9),new Vector3(6,0,18),new Vector3(13,0,-13)})
            {
                var tree=VillageAdventures.Prop(root.transform,"vtba",at,new Vector3(4,6,4));if(tree)tree.AddComponent<OriginalBillboard>();
                for(int j=0;j<3;j++)VillageAdventures.Prop(root.transform,j%2==0?"vt46":"vt47",at+new Vector3(j-1,.03f,1.3f),new Vector3(1.2f,1.2f,1.2f),j*72);
            }
            for(int i=0;i<3;i++){var at=Puzzles[i]+new Vector3(3,0,-1);VillageAdventures.Prop(root.transform,"vt35",at,new Vector3(.8f,1.5f,.8f));OriginalAtmosphere.Create("SpiritGlow",root.transform,at+Vector3.up*1.1f,2,.12f,2,.05f,.2f);}
            chest=VillageAdventures.Prop(root.transform,"vt4b",new Vector3(0,.03f,20),new Vector3(1.1f,.8f,1));
            var moon=OriginalAtmosphere.Create("OriginalMoon",root.transform,new Vector3(0,15,28),0,13,9999,0,0);if(moon)moon.gameObject.AddComponent<CelestialStillPaint>();
            var marker=new GameObject("Moonlit trail · village marking");marker.transform.SetParent(transform,false);marker.transform.position=new Vector3(Entry.x,game.valley.Height(Entry)+.025f,Entry.z);
            VillageAdventures.Prop(marker.transform,"vt46",Vector3.zero,new Vector3(1.3f,.6f,1.3f));entryGate=VillageAdventures.Prop(marker.transform,"heaven-gate",Vector3.zero,new Vector3(4.5f,4.5f,1.2f));entryGate.SetActive(game.Profile.adventures.moonDiscovered);root.SetActive(false);Apply();
        }
        void Apply(){for(int i=0;i<3;i++)if(seals[i])seals[i].SetActive(game.Profile.adventures.moonStage<=i);if(chest && game.Profile.adventures.moonCharm)chest.GetComponent<OriginalVisual>().SampleMotion("Okami/vt4b","vt4b_001",1);}
        public void Brush(string technique,Vector3 point)
        {
            int stage=game.Profile.adventures.moonStage;if(!Inside || BattleActive || Playing || stage>=3)return;
            int fight=stage==0?1:stage==2?2:0;if(fight!=0 && (game.Profile.adventures.moonBattles&(1<<fight))==0){game.Notify("Restless spirits still guard this seal");return;}
            string needed=stage==0?"bloom":stage==1?"slash":"bomb";if(technique!=needed || Vector3.Distance(point,At(Puzzles[stage]))>4.5f)return;
            game.Profile.adventures.moonStage++;game.Save.Save();Apply();game.Audio.Cue("collect");CelestialBrush.Burst("Blossom",At(Puzzles[stage])+Vector3.up,24,.3f);game.Notify("The moonlit path remembers your brush");
        }
        public void Slash(Vector3 start,Vector3 end)
        {
            if(!Inside || game.Profile.adventures.moonStage!=1)return;var target=At(Puzzles[1]);var d=end-start;float t=d.sqrMagnitude>.0001f?Mathf.Clamp01(Vector3.Dot(target-start,d)/d.sqrMagnitude):0;Brush("slash",start+d*t);
        }
        public bool Discover()
        {
            if(!game.Profile.night || game.Profile.adventures.moonDiscovered)return false;
            game.Profile.adventures.moonDiscovered=true;game.Save.Save();entryGate.SetActive(true);cooldown=1;game.Notify("Moonlight reveals a passage through the flowers");return true;
        }
        void Enter()
        {var festival=game.GetComponent<FestivalChallenges>();if(festival && festival.Active)return;root.SetActive(true);Physics.SyncTransforms();game.Combat.Cancel();game.Player.Teleport(At(new Vector3(0,.05f,-18)));game.Player.transform.rotation=Quaternion.identity;cooldown=1.5f;havePrevious=false;var c=FindFirstObjectByType<OrbitCamera>();if(c)c.SnapFocus();game.Audio.Cue("bell");}
        void Leave()
        {game.Combat.Cancel();var p=Entry+Vector3.back*3;p.y=game.valley.Height(p)+.05f;game.Player.Teleport(p);game.Player.transform.rotation=Quaternion.Euler(0,180,0);root.SetActive(false);cooldown=1.5f;havePrevious=false;var c=FindFirstObjectByType<OrbitCamera>();if(c)c.SnapFocus();}
        void Update()
        {
            if(!game || !game.Player || !root)return;cooldown=Mathf.Max(0,cooldown-Time.unscaledDeltaTime);
            if(Playing){clock+=Time.unscaledDeltaTime;if(chest)chest.GetComponent<OriginalVisual>().SampleMotion("Okami/vt4b","vt4b_001",Mathf.Clamp01((clock-.5f)/1.1f));if(camera)camera.CinematicFrame(At(new Vector3(0,1,20)),Mathf.Lerp(-35,35,Mathf.Clamp01(clock/3.5f)),23,6,43);if(clock>=3.5f)Skip();return;}
            if(BattleActive){if(!game.InTrial){BattleFinished(false);return;}if(!game.Blocked && game.Enemies.TrueForAll(e=>!e || e.Dead))game.EndTrailBattle(true);return;}
            if(!Inside){if(root.activeSelf)root.SetActive(false);if(game.Blocked || game.InTrial || cooldown>0)return;var d=game.Player.transform.position-Entry;d.y=0;if(d.magnitude>6){havePrevious=false;return;}
                if(!game.Profile.adventures.moonDiscovered){if(game.Profile.night){game.WorldPrompt("E · Examine the flowers in the moonlight");if(game.Player.input.Interact.WasPressedThisFrame())Discover();}return;}
                game.WorldPrompt("Walk through the moonlit passage");d.y=game.Player.transform.position.y-game.valley.Height(Entry);bool entering=CelestialTrialGate.Crosses(havePrevious && revision==game.Player.TeleportRevision?previous:d,d);previous=d;revision=game.Player.TeleportRevision;havePrevious=true;if(entering)Enter();return;}
            if(!root.activeSelf)root.SetActive(true);if(game.Blocked || cooldown>0)return;
            var local=game.Player.transform.position-VillageAdventures.TrailCentre;var exit=local-new Vector3(0,0,-22);
            bool crosses=CelestialTrialGate.Crosses(havePrevious && revision==game.Player.TeleportRevision?previous:exit,exit);previous=exit;revision=game.Player.TeleportRevision;havePrevious=true;if(crosses){Leave();return;}
            int stage=game.Profile.adventures.moonStage;
            int pending=stage==0?1:stage==2?2:0;
            if(pending!=0 && (game.Profile.adventures.moonBattles&(1<<pending))==0 && Vector3.Distance(local,Puzzles[stage])<7)
            {battle=pending;BattleActive=true;game.StartTrailBattle(pending);return;}
            if(stage<3 && Vector3.Distance(local,Puzzles[stage])<7)game.WorldPrompt(stage==0?"The quiet flowers wait for a returning circle":stage==1?"A single clean brushstroke can part this seal":"The stone is cracked from within · a little fire may finish it");
            else if(Vector3.Distance(local,new Vector3(0,0,20))<2.5f)
            {game.WorldPrompt(game.Profile.adventures.moonCharm?"The moon charm rests with you":stage==3?"E · Open the moonlit chest":"Three seals still bind the chest");if(stage==3 && !game.Profile.adventures.moonCharm && game.Player.input.Interact.WasPressedThisFrame())Loot();}
            else game.WorldPrompt("Moonlit trail · follow the lanterns · the southern gate returns to the village");
        }
        void Loot()
        {
            if(!VillageAdventureRules.MoonReward(game.Profile))return;game.Save.Save();Playing=true;clock=0;game.Combat.Cancel();game.Player.Teleport(At(new Vector3(0,.05f,18)));game.Player.Locked=true;game.Player.animationView.Play("Bark",.15f,1.93f,true);game.Audio.VictoryHowl();camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.BeginCinematic();CelestialBrush.Burst("SpiritGlow",At(new Vector3(0,1,20)),35,.3f);
        }
        public void BattleFinished(bool won)
        {BattleActive=false;if(won){game.Profile.adventures.moonBattles|=1<<battle;game.Save.Save();game.Notify("The trail grows quiet · its seal remains");}else{game.Profile.defeats++;game.Save.Save();game.ReturnHome();}}
        public void Skip(){if(!Playing)return;Playing=false;Apply();if(camera)camera.EndCinematic();game.Player.Locked=game.Health<=0;game.Player.animationView.Play("Idle_Natural",.15f,0,true);game.Notify("Moon charm found · +400 coins, +500 XP · peaceful Ink recovery +3/sec");}
        public void Cancel(){if(BattleActive){BattleActive=false;}if(Playing){Playing=false;if(camera)camera.EndCinematic();if(game && game.Player)game.Player.Locked=game.Health<=0;}}
        void OnDisable(){Cancel();}
    }
}
