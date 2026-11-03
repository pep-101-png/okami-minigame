using UnityEngine;
namespace Sunward.Remaster
{
    // A new reachable Sunward sanctuary assembled from original geometry, paint,
    // characters and effects. It is not presented as an original Ōkami stage.
    [DefaultExecutionOrder(75)]
    public sealed class HeavenlyGarden : MonoBehaviour
    {
        public GameFlow game;
        public const float WalkRadiusX=35,WalkRadiusZ=32;
        public static readonly Vector3 Centre=new Vector3(230,70,0);
        public static readonly Vector3 Altar=Centre+new Vector3(0,0,22),Return=Centre+new Vector3(0,0,-25);
        public bool Playing {get;private set;}
        float fallTime;Vector3 fallStart;OrbitCamera orbit;GameObject garden,river;bool visible;
        public static bool Inside(Vector3 p)=>p.y>58 && p.y<100 && Mathf.Abs(p.x-Centre.x)<49 && Mathf.Abs(p.z)<47;
        public static bool RiverLip(Vector3 p)=>p.y>-2 && p.y<2 && p.z>38.5f && p.z<43 && Mathf.Abs(p.x-Valley.RiverX(-p.z))<2.8f;
        public static int UpgradeRanks(ProfileData p){int n=0;foreach(var id in ProgressionRules.Upgrades)n+=p.upgrades.Get(id);return n;}
        public static bool GrowthReady(ProfileData p)=>ProgressionRules.Level(p)>=15 && UpgradeRanks(p)>=30;
        public static Vector3 Guard(Vector3 p)
        {
            Vector2 d=new Vector2((p.x-Centre.x)/WalkRadiusX,p.z/WalkRadiusZ);if(d.magnitude>1){d=d.normalized;p.x=Centre.x+d.x*WalkRadiusX;p.z=d.y*WalkRadiusZ;}return p;
        }
        static readonly RaycastHit[] hits=new RaycastHit[40];
        public static bool Height(Vector3 p,out float y)
        {
            y=Centre.y;if(!Inside(p))return false;
            int n=Physics.RaycastNonAlloc(new Vector3(p.x,98,p.z),Vector3.down,hits,35,1<<6,QueryTriggerInteraction.Ignore);
            float top=float.NegativeInfinity;
            for(int i=0;i<n;i++)if(hits[i].collider.name.StartsWith("Heaven garden ground"))top=Mathf.Max(top,hits[i].point.y);
            if(!float.IsNegativeInfinity(top))y=top;return true;
        }
        void Start()
        {
            if(!game)game=GetComponent<GameFlow>();BuildRiver();BuildGarden();garden.SetActive(false);
        }
        GameObject Put(Transform parent,string resource,Vector3 p,Vector3 size,float yaw=0)
        {
            if(garden && parent==garden.transform && resource!="Okami/heaven-island" && resource!="Okami/heaven-cloud")
            {var world=parent.TransformPoint(p);if(Height(world,out var y))p.y=y-Centre.y+.025f;}
            return VillageFestival.Place(parent,resource,p,size,new Vector3(0,yaw,0));
        }
        void BuildRiver()
        {
            river=new GameObject("River end · original waterfall and spirit passage");river.transform.SetParent(transform,false);
            float x=Valley.RiverX(-40);
            var waterfall=Put(river.transform,"Okami/river-waterfall",new Vector3(x,-6.5f,41),new Vector3(5,6.2f,4.5f),160);
            if(waterfall)foreach(var r in waterfall.GetComponentsInChildren<Renderer>())r.sharedMaterial.shader=Resources.Load<Material>("Okami/Effects/FallingWater").shader;
            Put(river.transform,"Okami/vt28",new Vector3(x-5,-6.8f,42.5f),new Vector3(4,6.2f,8));
            Put(river.transform,"Okami/vt28",new Vector3(x+5,-6.8f,42.5f),new Vector3(4,6.2f,8),125);
            Put(river.transform,"Okami/river-spirit-portal",new Vector3(x,-6.1f,44),new Vector3(8,.15f,8));
            OriginalAtmosphere.Create("Steam",river.transform,new Vector3(x,-5.8f,43),7,1.8f,2.8f,.3f,2.1f);
            OriginalAtmosphere.Create("SpiritGlow",river.transform,new Vector3(x,-5.5f,44),12,.6f,2,.15f,2.6f);
            var light=river.AddComponent<Light>();light.type=LightType.Point;light.range=13;light.intensity=6;light.color=new Color(.4f,.85f,1);light.shadows=LightShadows.None;
        }
        void BuildGarden()
        {
            garden=new GameObject("Heavenly garden · original painted sanctuary");garden.transform.SetParent(transform,false);garden.transform.position=Centre;
            var ground=Put(garden.transform,"Okami/heaven-island",Vector3.down*.7f,new Vector3(94,2.5f,88));
            foreach(var renderer in ground.GetComponentsInChildren<SkinnedMeshRenderer>())
            {renderer.gameObject.layer=6;renderer.gameObject.name="Heaven garden ground · original mesh";var collider=renderer.gameObject.AddComponent<MeshCollider>();collider.sharedMesh=renderer.sharedMesh;}
            Physics.SyncTransforms();
            Put(garden.transform,"Okami/heaven-cloud",new Vector3(0,-10,0),new Vector3(155,36,150),0);
            Put(garden.transform,"Okami/garden-gate",new Vector3(0,1,-28),new Vector3(10,8,2));
            Put(garden.transform,"Okami/garden-altar",new Vector3(0,1,22),new Vector3(9,.7f,8));
            Put(garden.transform,"Okami/vt31",new Vector3(0,1,24),new Vector3(3,3.7f,2.2f));
            OriginalAtmosphere.Create("SpiritGlow",garden.transform,new Vector3(0,3.2f,22),9,.4f,2.5f,.15f,1.7f);
            foreach(var p in new[]{new Vector3(-19,1,-8),new Vector3(21,1,8),new Vector3(-17,1,23)})
            {
                Put(garden.transform,"Okami/heaven-pond",p,new Vector3(11,.1f,8));
                OriginalAtmosphere.Create("Steam",garden.transform,p+Vector3.up*.3f,4,2.4f,4,.04f,3.2f);
                OriginalAtmosphere.Create("SpiritGlow",garden.transform,p+Vector3.up*.7f,3,.18f,3,.04f,3.6f);
            }
            for(int i=0;i<12;i++)
            {
                float a=i*Mathf.PI*2/12;Vector3 p=new Vector3(Mathf.Cos(a)*31,1,Mathf.Sin(a)*29);
                Put(garden.transform,i%3==0?"Okami/vt19":"Okami/vt17",p,i%3==0?new Vector3(3,5,3):new Vector3(2,5.5f,2),i*41);
                Put(garden.transform,"Okami/vt48",p+new Vector3(1,0,1.8f),new Vector3(2.4f,1.1f,2.1f));
                OriginalAtmosphere.Create("Blossom",garden.transform,p+Vector3.up*4,1,.2f,8,.08f,3);
            }
            SpawnVisitor("garden-hm50","hm05_000",new Vector3(0,1,17),180);
            SpawnVisitor("garden-hm40","hm95_000",new Vector3(18,1,-12),240);
            SpawnVisitor("garden-hm06","hm05_000",new Vector3(-23,1,7),90);
            Put(garden.transform,"Okami/river-spirit-portal",new Vector3(0,1,-25),new Vector3(5,.12f,5));
            OriginalAtmosphere.Create("SpiritGlow",garden.transform,new Vector3(0,2,-25),12,.4f,2,.06f,1.8f);
            var sun=new GameObject("Garden altar radiance");sun.transform.SetParent(garden.transform,false);sun.transform.localPosition=new Vector3(0,8,18);var lamp=sun.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=80;lamp.intensity=9;lamp.color=new Color(1,.92f,.74f);lamp.shadows=LightShadows.None;
        }
        void SpawnVisitor(string resource,string idle,Vector3 p,float yaw)
        {
            var person=new GameObject("Original celestial visitor · "+resource);person.SetActive(false);person.transform.SetParent(garden.transform,false);var world=garden.transform.TransformPoint(p);if(Height(world,out var y))p.y=y-Centre.y+.025f;person.transform.localPosition=p;person.transform.rotation=Quaternion.Euler(0,yaw,0);
            var actor=person.AddComponent<OriginalActor>();actor.game=game;actor.resource="Okami/"+resource;actor.idle=actor.windup=actor.strike=actor.recover=actor.death=idle;actor.walk=actor.run=resource=="garden-hm40"?"hm95_010":"hm05_010";actor.modelScale=1.25f;person.SetActive(true);
            if(resource!="garden-hm50"){var stroll=person.AddComponent<GardenVisitor>();stroll.game=game;stroll.anchor=person.transform.position;stroll.phase=yaw;}
        }
        void BeginFall()
        {
            Playing=true;fallTime=0;fallStart=game.Player.transform.position;game.Combat.Cancel();game.Services.CancelRest();game.Player.StopMotion();game.Player.Locked=true;
            game.Player.animationView.Play("Jump_Standing",.1f,0,true);orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();game.Audio.Cue("swim-exit");
        }
        public void Cancel()
        {
            if(!Playing)return;Playing=false;if(orbit)orbit.EndCinematic();game.Player.Locked=game.Health<=0;
        }
        void Update()
        {
            if(!game || !game.Player || !garden)return;
            bool inside=Inside(game.Player.transform.position);
            if(inside!=visible){visible=inside;garden.SetActive(visible);if(visible){Physics.SyncTransforms();var p=game.Player.transform.position;if(Height(p,out var h))game.Player.Teleport(new Vector3(p.x,h+.05f,p.z));}}
            Shader.SetGlobalFloat("_SunwardHeaven",inside?1:0);Shader.SetGlobalFloat("_SunwardRiverClock",Time.unscaledTime);
            if(Playing)
            {
                fallTime+=Time.unscaledDeltaTime;float t=Mathf.Clamp01(fallTime/1.6f);
                var p=fallStart+new Vector3(0,-6.7f*t*t,5.2f*t);game.Player.Teleport(p);
                if(orbit)orbit.CinematicFrame(p+Vector3.up,Mathf.Lerp(110,150,t),18,10,48);
                if(t>=1 || game.Health<=0)
                {Cancel();if(game.Health>0){garden.SetActive(true);Physics.SyncTransforms();var at=Return+Vector3.forward*5;Height(at,out var y);at.y=y+.05f;game.Player.Teleport(at);game.Notify("The river opens into a garden above the clouds · follow the altar lights");if(orbit)orbit.SnapFocus();}}
                return;
            }
            if(game.Blocked || game.InTrial || game.Health<=0)return;
            var player=game.Player.transform.position;
            if(!inside){if(RiverLip(player))BeginFall();else if(player.z>28 && Mathf.Abs(player.x-Valley.RiverX(-player.z))<4)game.WorldPrompt("The river falls into a spirit passage ahead");return;}
            bool nearReturn=new Vector2(player.x-Return.x,player.z-Return.z).magnitude<3.2f;
            bool nearKeeper=new Vector2(player.x-Altar.x,player.z-(Altar.z-5)).magnitude<4.2f;
            game.WorldPrompt(nearReturn?"E · Return to Windflower":nearKeeper?"E · Speak with the garden keeper":"Heavenly garden · seek the keeper by the altar");
            if(game.Player.input.Interact.WasPressedThisFrame())
            {
                if(nearReturn)game.ReturnHome();
                else if(nearKeeper)
                {
                    game.ShowDialogue("Amaterasu, the Celestial Plain is the gods' home. A century ago, the white wolf Shiranui stood beside Nagi against Orochi. Your journey carries that light onward. This garden and its trial are Sunward's own story.\n\nTo awaken the altar's trial: reach level 15 (now "+ProgressionRules.Level(game.Profile)+"), earn 30 upgrade ranks (now "+UpgradeRanks(game.Profile)+"), and defeat the guardian. That future boss has not yet been added, so the quest cannot be completed. P remains a testing shortcut.");
                }
            }
        }
        void OnDisable(){Cancel();Shader.SetGlobalFloat("_SunwardHeaven",0);}
        void OnDestroy(){if(garden)Destroy(garden);if(river)Destroy(river);}
    }
}
