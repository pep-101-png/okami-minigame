using UnityEngine;
namespace Sunward.Remaster
{
    // A new reachable Sunward sanctuary assembled from original geometry, paint,
    // characters and effects. It is not presented as an original Ōkami stage.
    [DefaultExecutionOrder(75)]
    public sealed class HeavenlyGarden : MonoBehaviour
    {
        public GameFlow game;
        public const float WalkRadiusX=35,WalkRadiusZ=32,WaterfallLip=36;
        public static readonly Vector3 Centre=new Vector3(230,70,0);
        public static readonly Vector3 Altar=Centre+new Vector3(0,0,22),Return=Centre+new Vector3(0,0,-25);
        public bool Playing {get;private set;}
        bool keeperConversation;float keeperCooldown;
        float fallTime;Vector3 fallStart;OrbitCamera orbit;GameObject garden,river;bool visible;
        public static bool Inside(Vector3 p)=>p.y>58 && p.y<100 && Mathf.Abs(p.x-Centre.x)<49 && Mathf.Abs(p.z)<47;
        public static bool RiverLip(Vector3 p)=>p.y>-2 && p.y<2 && p.z>WaterfallLip-.75f && p.z<WaterfallLip+1 && Mathf.Abs(p.x-Valley.RiverX(-p.z))<2.8f;
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
            float x=Valley.RiverX(-WaterfallLip);
            var waterfall=Put(river.transform,"Okami/river-waterfall",new Vector3(x-0.036361f,-6.54f,WaterfallLip+0.548696f),new Vector3(5,6.2f,4.5f),-37.445568f);
            if(waterfall)foreach(var r in waterfall.GetComponentsInChildren<SkinnedMeshRenderer>())
            {var material=new Material(r.sharedMaterial);material.shader=Resources.Load<Material>("Okami/Effects/FallingWater").shader;material.SetFloat("_FlowDirection",r.sharedMesh.name.StartsWith("Native-1-")?1:-1);r.sharedMaterial=material;r.gameObject.AddComponent<OriginalParticleMaterial>();}
            Put(river.transform,"Okami/vt28",new Vector3(x-5,-6.8f,39.5f),new Vector3(4,6.2f,8));
            Put(river.transform,"Okami/vt28",new Vector3(x+5,-6.8f,39.5f),new Vector3(4,6.2f,8),125);
            Put(river.transform,"Okami/river-spirit-portal",new Vector3(x,-6.1f,40.5f),new Vector3(8,.15f,8));
            OriginalAtmosphere.Create("Steam",river.transform,new Vector3(x,-5.8f,39.7f),7,1.8f,2.8f,.3f,2.1f);
            OriginalAtmosphere.Create("SpiritGlow",river.transform,new Vector3(x,-5.5f,40.5f),12,.6f,2,.15f,2.6f);
            var lamp=new GameObject("Waterfall portal light");lamp.transform.SetParent(river.transform,false);lamp.transform.localPosition=new Vector3(x,-3.8f,40.5f);var light=lamp.AddComponent<Light>();light.type=LightType.Point;light.range=13;light.intensity=6;light.color=new Color(.4f,.85f,1);light.shadows=LightShadows.None;
        }
        [System.Serializable]sealed class GardenLayout{public int version;public GardenItem[] items;}
        [System.Serializable]sealed class GardenItem{public string resource,kind;public Vector3 position,size;public float yaw;}
        void BuildGarden()
        {
            garden=new GameObject("Celestial garden · original stone walks, flower gardens and cloud sea");garden.transform.SetParent(transform,false);garden.transform.position=Centre;
            var source=Resources.Load<TextAsset>("Okami/CelestialGarden");
            if(!source){Debug.LogError("Celestial garden layout is missing");return;}
            var layout=JsonUtility.FromJson<GardenLayout>(source.text);
            // Ground first, so every flower, lamp and visitor sits on its actual painted surface.
            foreach(var item in layout.items)if(item.kind=="ground")
            {
                var at=item.position;
                if(item.resource!="Okami/celestial-meadow" && item.resource!="Okami/celestial-terrace" && Height(Centre+at,out var baseY))
                {
                    if(item.resource=="Okami/vt0a" && item.size.y>.5f)
                    {foreach(var d in new[]{new Vector3(-4,0,-4),new Vector3(4,0,-4),new Vector3(-4,0,4),new Vector3(4,0,4)})if(Height(Centre+at+d,out var edge))baseY=Mathf.Min(baseY,edge);}
                    at.y+=baseY-Centre.y;
                }
                var ground=VillageFestival.Place(garden.transform,item.resource,at,item.size,new Vector3(0,item.yaw,0));
                if(!ground)continue;
                foreach(var renderer in ground.GetComponentsInChildren<SkinnedMeshRenderer>())
                {var material=new Material(renderer.sharedMaterial);material.shader=Resources.Load<Material>("Okami/Effects/CelestialGround").shader;
                bool meadow=item.resource=="Okami/celestial-meadow" || item.resource=="Okami/celestial-terrace";
                material.SetFloat("_SurfaceKind",meadow?1:0);material.SetFloat("_Cull",meadow?0:2);material.SetTexture("_GroundPaint",Resources.Load<Texture2D>("Okami/farm-earth/Grass"));material.SetTexture("_CloudPaint",Resources.Load<Texture2D>("Okami/Effects/Cloud"));renderer.sharedMaterial=material;renderer.gameObject.AddComponent<OriginalParticleMaterial>();
                renderer.gameObject.layer=6;renderer.gameObject.name="Heaven garden ground · original mesh";var collider=renderer.gameObject.AddComponent<MeshCollider>();collider.sharedMesh=renderer.sharedMesh;}
                Physics.SyncTransforms();
            }
            Shader.SetGlobalTexture("_SunwardHeavenClouds",Resources.Load<Texture2D>("Okami/Effects/Cloud"));
            Physics.SyncTransforms();
            foreach(var item in layout.items)if(item.kind!="ground")
            {
                var p=item.position;if(item.kind!="cloud" && item.kind!="cloudsea" && Height(Centre+p,out var h))p.y=h-Centre.y+.025f;
                var prop=VillageFestival.Place(garden.transform,item.resource,p,item.size,new Vector3(0,item.yaw,0));
                if(!prop)continue;
                if(item.kind=="cloudsea")foreach(var renderer in prop.GetComponentsInChildren<SkinnedMeshRenderer>())
                {
                    var material=new Material(renderer.sharedMaterial);material.shader=Resources.Load<Material>("Okami/Effects/CelestialGround").shader;material.SetFloat("_SurfaceKind",2);material.SetFloat("_Cull",0);material.SetTexture("_CloudPaint",Resources.Load<Texture2D>("Okami/Effects/Cloud"));renderer.sharedMaterial=material;renderer.gameObject.AddComponent<OriginalParticleMaterial>();
                }
                if(item.kind=="tree")prop.AddComponent<OriginalBillboard>();
                if(item.kind=="cloud")foreach(var renderer in prop.GetComponentsInChildren<SkinnedMeshRenderer>())
                {
                    var material=new Material(renderer.sharedMaterial);material.shader=Resources.Load<Material>("Okami/Effects/HeavenCloud").shader;renderer.sharedMaterial=material;renderer.gameObject.AddComponent<OriginalParticleMaterial>();
                }
                if(item.kind=="pond")
                {
                    foreach(var renderer in prop.GetComponentsInChildren<SkinnedMeshRenderer>())if(renderer.sharedMesh.name=="Native-1-0")
                    {
                        var material=new Material(renderer.sharedMaterial);material.shader=Resources.Load<Material>("Okami/Effects/CelestialWater").shader;
                        material.SetFloat("_CentreX",Centre.x+p.x);material.SetFloat("_CentreZ",Centre.z+p.z);material.SetFloat("_RadiusX",item.size.x*.32f);material.SetFloat("_RadiusZ",item.size.z*.32f);
                        renderer.sharedMaterial=material;renderer.gameObject.AddComponent<OriginalParticleMaterial>();
                    }
                    OriginalAtmosphere.Create("Steam",garden.transform,p+Vector3.up*.5f,2,2.5f,5,.025f,3.5f);
                    OriginalAtmosphere.Create("SpiritGlow",garden.transform,p+Vector3.up*.8f,2,.16f,5,.02f,3.7f);
                }
            }
            foreach(var p in new[]{new Vector3(-20,3,-8),new Vector3(21,3,9),new Vector3(-18,3,22),new Vector3(0,3,22),new Vector3(0,2,-25)})
            {
                OriginalAtmosphere.Create("SpiritGlow",garden.transform,p,9,.30f,7,.10f,6);
                OriginalAtmosphere.Create("Blossom",garden.transform,p+Vector3.up*3,2,.23f,9,.10f,5);
            }
            for(int i=0;i<3;i++)
            {
                var p=new Vector3(i==0?0:i==1?-20:21,3,i==0?22:i==1?-8:9);
                var sun=new GameObject("Soft celestial garden radiance");sun.transform.SetParent(garden.transform,false);sun.transform.localPosition=p+Vector3.up*5;var lamp=sun.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=24;lamp.intensity=4;lamp.color=new Color(1,.91f,.73f);lamp.shadows=LightShadows.None;
                OriginalAtmosphere.Create("Wind",garden.transform,p,1.1f,3.5f,7,.25f,2);
            }
            // Original spirit artwork drawn as soft shafts over the altar and ponds.
            foreach(var p in new[]{new Vector3(0,1,23),new Vector3(-20,1,-8),new Vector3(21,1,9)})
            {
                var ray=new GameObject("Celestial shaft · original spirit paint");ray.transform.SetParent(garden.transform,false);ray.transform.localPosition=p;
                var beam=ray.AddComponent<LineRenderer>();beam.positionCount=2;beam.useWorldSpace=false;
                beam.SetPosition(0,Vector3.up*20);beam.SetPosition(1,Vector3.zero);beam.startWidth=.65f;beam.endWidth=3.5f;
                beam.startColor=new Color(1.5f,1.3f,1.7f,.12f);beam.endColor=new Color(1.5f,1.6f,2,.34f);
                beam.sharedMaterial=new Material(Resources.Load<Material>("Okami/Effects/SpiritRadiance")){mainTexture=Resources.Load<Texture2D>("Okami/Effects/SpiritGlow")};ray.AddComponent<OriginalParticleMaterial>();
            }
            foreach(var p in new[]{new Vector3(-4,0,17.3f),new Vector3(4,0,17.3f),new Vector3(-4,0,23),new Vector3(4,0,23)})
            {
                var at=p;if(Height(Centre+p,out var h))at.y=h-Centre.y+1.34f;
                OriginalAtmosphere.Create("Flame",garden.transform,at,2,.16f,1.2f,.04f,.02f);
                OriginalAtmosphere.Create("SpiritGlow",garden.transform,at,1,.23f,2,.02f,.05f);
            }
            SpawnVisitor("garden-hm50","hm05_000",new Vector3(0,1,17),180);
            SpawnVisitor("garden-hm40","hm95_000",new Vector3(18,1,-12),240);
            SpawnVisitor("garden-hm06","hm05_000",new Vector3(-23,1,7),90);
        }
        void SpawnVisitor(string resource,string idle,Vector3 p,float yaw)
        {
            var person=new GameObject("Original celestial visitor · "+resource);person.SetActive(false);person.transform.SetParent(garden.transform,false);var world=garden.transform.TransformPoint(p);if(Height(world,out var y))p.y=y-Centre.y+.025f;person.transform.localPosition=p;person.transform.rotation=Quaternion.Euler(0,yaw,0);
            var actor=person.AddComponent<OriginalActor>();actor.game=game;actor.resource="Okami/"+resource;actor.idle=actor.windup=actor.strike=actor.recover=actor.death=idle;actor.walk=actor.run=resource=="garden-hm40"?"hm95_010":"hm05_010";actor.modelScale=1.25f;person.SetActive(true);
            if(resource!="garden-hm50"){var stroll=person.AddComponent<GardenVisitor>();stroll.game=game;stroll.anchor=person.transform.position;stroll.phase=yaw;}
        }
        public bool OwnsRenderer(Renderer renderer)
        {
            if(!renderer)return false;
            return (garden && renderer.transform.IsChildOf(garden.transform)) ||
                (game && game.Player && renderer.transform.IsChildOf(game.Player.transform)) || Inside(renderer.bounds.center);
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
                {Cancel();if(game.Health>0){garden.SetActive(true);Physics.SyncTransforms();var at=Return+Vector3.forward*5;Height(at,out var y);at.y=y+.05f;game.Player.Teleport(at);visible=true;Shader.SetGlobalFloat("_SunwardHeaven",1);game.Notify("The river opens into a garden above the clouds · follow the altar lights");if(orbit)orbit.SnapFocus();}}
                return;
            }
            if(keeperConversation)
            {
                if(game.Panel=="dialogue")return;
                keeperConversation=false;keeperCooldown=.4f;return;
            }
            keeperCooldown=Mathf.Max(0,keeperCooldown-Time.unscaledDeltaTime);
            if(game.Blocked || game.InTrial || game.Health<=0)return;
            var player=game.Player.transform.position;
            if(!inside){if(RiverLip(player))BeginFall();else if(player.z>28 && Mathf.Abs(player.x-Valley.RiverX(-player.z))<4)game.WorldPrompt("The river falls into a spirit passage ahead");return;}
            bool nearReturn=new Vector2(player.x-Return.x,player.z-Return.z).magnitude<3.2f;
            bool nearKeeper=new Vector2(player.x-Altar.x,player.z-(Altar.z-5)).magnitude<4.2f;
            game.WorldPrompt(nearReturn?"E · Return to Windflower":nearKeeper?"E · Speak with the garden keeper":"Heavenly garden · seek the keeper by the altar");
            if(game.Player.input.Interact.WasPressedThisFrame())
            {
                if(nearReturn)game.ReturnHome();
                else if(nearKeeper && keeperCooldown<=0)
                {
                    keeperConversation=true;
                    game.ShowDialogue("Amaterasu, the Celestial Plain is the gods' home. A century ago, the white wolf Shiranui stood beside Nagi against Orochi. Your journey carries that light onward. This garden and its trial are Sunward's own story.\n\nTo awaken the altar's trial: reach level 15 (now "+ProgressionRules.Level(game.Profile)+"), earn 30 upgrade ranks (now "+UpgradeRanks(game.Profile)+"), and defeat the guardian. That future boss has not yet been added, so the quest cannot be completed. P remains a testing shortcut.");
                }
            }
        }
        void OnDisable(){if(garden)garden.SetActive(false);visible=false;keeperConversation=false;keeperCooldown=0;Cancel();Shader.SetGlobalFloat("_SunwardHeaven",0);}
        void OnDestroy(){if(garden)Destroy(garden);if(river)Destroy(river);}
    }
}
