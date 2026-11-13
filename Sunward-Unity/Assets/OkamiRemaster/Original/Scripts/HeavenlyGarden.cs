using UnityEngine;
namespace Sunward.Remaster
{
    // A new reachable Sunward sanctuary assembled from original geometry, paint,
    // characters and effects. It is not presented as an original Ōkami stage.
    [DefaultExecutionOrder(75)]
    public sealed partial class HeavenlyGarden : MonoBehaviour
    {
        public GameFlow game;
        public const float WalkRadiusX=35,WalkRadiusZ=32,WaterfallLip=36;
        public static readonly Vector3 Centre=new Vector3(230,70,0);
        public static readonly Vector3 Altar=Centre+new Vector3(0,0,22),Return=Centre+new Vector3(0,0,-25);
        public bool Playing {get;private set;}
        bool keeperConversation;float keeperCooldown;
        Vector2 mazeMin,mazeMax;
        float fallTime;Vector3 fallStart;OrbitCamera orbit;GameObject garden,river,riverPassage;bool visible;
        public static bool Inside(Vector3 p)=>CelestialTrials.InArena(p) || PalaceInside(p) || p.y>58 && p.y<100 && Mathf.Abs(p.x-Centre.x)<49 && Mathf.Abs(p.z)<47;
        public static bool RiverLip(Vector3 p)=>p.y>-2 && p.y<2 && p.z>WaterfallLip-.75f && p.z<WaterfallLip+1 && Mathf.Abs(p.x-Valley.RiverX(-p.z))<2.8f;
        public static int UpgradeRanks(ProfileData p){int n=0;foreach(var id in ProgressionRules.Upgrades)n+=p.upgrades.Get(id);if(p.weaponMastery!=null)foreach(var weapon in p.weaponMastery)if(weapon!=null)n+=weapon.rank;return n;}
        public static bool GrowthReady(ProfileData p)=>ProgressionRules.DawnReady(p);
        public static bool RiverOpen(ProfileData p)=>p!=null && p.bossWins>0;
        public static Vector3 Guard(Vector3 p)
        {
            if(CelestialTrials.InArena(p))return CelestialTrials.Guard(p);
            if(p.y>76 && p.z>90)return PalaceGuard(p);
            Vector2 d=new Vector2((p.x-Centre.x)/WalkRadiusX,p.z/WalkRadiusZ);if(d.magnitude>1){d=d.normalized;p.x=Centre.x+d.x*WalkRadiusX;p.z=d.y*WalkRadiusZ;}return p;
        }
        static readonly RaycastHit[] hits=new RaycastHit[40];
        public static bool Height(Vector3 p,out float y)
        {
            if(CelestialTrials.Floor(p,out y))return true;
            y=Centre.y;if(PalaceInside(p)){y=PalaceCentre.y+.025f;return true;}if(!Inside(p))return false;
            int n=Physics.RaycastNonAlloc(new Vector3(p.x,98,p.z),Vector3.down,hits,35,1<<6,QueryTriggerInteraction.Ignore);
            float top=float.NegativeInfinity;
            for(int i=0;i<n;i++)if(hits[i].collider.name.StartsWith("Heaven garden ground"))
            {
                // A deck above the wolf is a ceiling until reached by its real stairs.
                if(hits[i].collider.name.Contains("shrine stairs/landing") && hits[i].point.y>p.y+.4f)continue;
                top=Mathf.Max(top,hits[i].point.y);
            }
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
            riverPassage=new GameObject("River passage · awakened after Crimson Helm");riverPassage.transform.SetParent(river.transform,false);
            var passage=OriginalAtmosphere.Create("OriginalWhiteRing",riverPassage.transform,new Vector3(x,-6.2f,40.5f),2.2f,4.5f,1.8f,0);
            if(passage){var main=passage.main;main.startRotation=0;main.startColor=new Color(.7f,.9f,1,.9f);var velocity=passage.velocityOverLifetime;velocity.enabled=false;passage.GetComponent<ParticleSystemRenderer>().renderMode=ParticleSystemRenderMode.HorizontalBillboard;}
            OriginalAtmosphere.Create("Steam",riverPassage.transform,new Vector3(x,-5.8f,39.7f),7,1.8f,2.8f,.3f,2.1f);
            OriginalAtmosphere.Create("SpiritGlow",riverPassage.transform,new Vector3(x,-5.5f,40.5f),12,.6f,2,.15f,2.6f);
            var lamp=new GameObject("Waterfall portal light");lamp.transform.SetParent(riverPassage.transform,false);lamp.transform.localPosition=new Vector3(x,-3.8f,40.5f);var light=lamp.AddComponent<Light>();light.type=LightType.Point;light.range=13;light.intensity=6;light.color=new Color(.4f,.85f,1);light.shadows=LightShadows.None;
        }
        [System.Serializable]sealed class GardenLayout{public int version;public GardenItem[] items;public GardenWalk[] walks;public GardenWall[] mazeWalls;public GardenPool[] ponds;public Vector3 treasure,lookout,tea;}
        [System.Serializable]sealed class GardenItem{public string resource,kind;public Vector3 position,size;public float yaw;public bool absoluteHeight;}
        [System.Serializable]sealed class GardenWalk{public Vector3 a,b;public float width;}
        [System.Serializable]sealed class GardenWall{public Vector3 a,b;}
        void BuildGarden()
        {
            garden=new GameObject("Celestial garden · original stone walks, flower gardens and cloud sea");garden.transform.SetParent(transform,false);garden.transform.position=Centre;
            var source=Resources.Load<TextAsset>("Okami/CelestialGarden");
            if(!source){Debug.LogError("Celestial garden layout is missing");return;}
            var layout=JsonUtility.FromJson<GardenLayout>(source.text);PrepareFeatures(layout);
            // Ground first, so every flower, lamp and visitor sits on its actual painted surface.
            foreach(var item in layout.items)if(item.kind=="ground")
            {
                // One continuous original terrain mesh owns both the painted walks
                // and collision. No elevated paper strips or stretched prop tiers.
                var ground=VillageFestival.Place(garden.transform,item.resource,item.position,item.size,new Vector3(0,item.yaw,0));
                if(!ground)continue;
                foreach(var renderer in ground.GetComponentsInChildren<SkinnedMeshRenderer>())
                {var material=new Material(renderer.sharedMaterial);material.shader=Resources.Load<Material>("Okami/Effects/CelestialGround").shader;
                bool meadow=item.resource=="Okami/celestial-meadow" || item.resource=="Okami/celestial-terrace" || item.resource=="Okami/celestial-grounded" || item.resource=="Okami/heaven-basin-terrain";
                material.SetFloat("_SurfaceKind",meadow?1:0);material.SetTexture("_BasinPaint",Resources.Load<Texture2D>("Okami/farm-earth/Earth"));material.SetTexture("_WalkPaint",Resources.Load<Texture2D>("Okami/celestial-stair/Texture-0"));bool twoSided=meadow;material.SetFloat("_Cull",twoSided?0:2);material.SetTexture("_GroundPaint",Resources.Load<Texture2D>("Okami/farm-earth/Grass"));material.SetTexture("_CloudPaint",Resources.Load<Texture2D>("Okami/Effects/Cloud"));renderer.sharedMaterial=material;renderer.gameObject.AddComponent<OriginalParticleMaterial>();
                renderer.gameObject.layer=6;renderer.gameObject.name="Heaven garden ground · original mesh";var collider=renderer.gameObject.AddComponent<MeshCollider>();collider.sharedMesh=renderer.sharedMesh;}
                Physics.SyncTransforms();
            }
            var walks=new Vector4[96];var styles=new Vector4[96];int count=layout.walks==null?0:Mathf.Min(96,layout.walks.Length);
            for(int i=0;i<count;i++){var w=layout.walks[i];walks[i]=new Vector4(w.a.x,w.a.z,w.b.x,w.b.z);styles[i]=new Vector4(w.width,0,0,0);}
            Shader.SetGlobalVectorArray("_SunwardHeavenWalks",walks);Shader.SetGlobalVectorArray("_SunwardHeavenWalkStyle",styles);Shader.SetGlobalFloat("_SunwardHeavenWalkCount",count);
            Shader.SetGlobalTexture("_SunwardHeavenClouds",Resources.Load<Texture2D>("Okami/Effects/Cloud"));
            Physics.SyncTransforms();
            foreach(var item in layout.items)if(item.kind!="ground")
            {
                var p=item.position;if(!item.absoluteHeight && item.kind!="cloud" && item.kind!="cloudsea" && Height(Centre+p,out var h))p.y+=h-Centre.y+.005f;
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
                if(item.kind=="pond")PondMaterial(prop,item);
                if(item.resource=="Okami/vtaa")SolidProp(prop,true);
                else if(item.resource=="Okami/vt4a"){SolidProp(prop);gongs.Add(prop.transform.position);}
                else if(item.resource=="Okami/heaven-gate"){SolidGate(prop);BuildReturnGate(prop.transform);}

            }
            BuildMazeBoundaries(layout.mazeWalls);
            foreach(var p in new[]{new Vector3(22,3,-18),new Vector3(23,3,19),new Vector3(-20,3,20),new Vector3(0,3,22),new Vector3(0,2,-25)})
            {
                var at=p;if(Height(Centre+p,out var floor))at.y=floor-Centre.y+2;
                OriginalAtmosphere.Create("SpiritGlow",garden.transform,at,9,.30f,7,.10f,6);
                OriginalAtmosphere.Create("Blossom",garden.transform,at+Vector3.up*3,2,.23f,9,.10f,5);
            }
            for(int i=0;i<3;i++)
            {
                var p=new Vector3(i==0?0:i==1?22:23,3,i==0?22:i==1?-18:19);
                if(Height(Centre+p,out var floor))p.y=floor-Centre.y+3;
                var sun=new GameObject("Soft celestial garden radiance");sun.transform.SetParent(garden.transform,false);sun.transform.localPosition=p+Vector3.up*5;var lamp=sun.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=24;lamp.intensity=4;lamp.color=new Color(1,.91f,.73f);lamp.shadows=LightShadows.None;

            }
            // Original spirit artwork drawn as soft shafts over the altar and ponds.
            foreach(var p in new[]{new Vector3(0,1,23),new Vector3(22,1,-18),new Vector3(23,1,19)})
            {
                var ray=new GameObject("Celestial shaft · original spirit paint");ray.transform.SetParent(garden.transform,false);var at=p;if(Height(Centre+p,out var floor))at.y=floor-Centre.y+1;ray.transform.localPosition=at;
                var beam=ray.AddComponent<LineRenderer>();beam.positionCount=2;beam.useWorldSpace=false;
                beam.SetPosition(0,Vector3.up*20);beam.SetPosition(1,Vector3.zero);beam.startWidth=.35f;beam.endWidth=1.8f;
                beam.startColor=new Color(1.5f,1.3f,1.7f,.035f);beam.endColor=new Color(1.5f,1.6f,2,.14f);
                beam.sharedMaterial=new Material(Resources.Load<Material>("Okami/Effects/SpiritRadiance")){mainTexture=Resources.Load<Texture2D>("Okami/Effects/SpiritGlow")};ray.AddComponent<OriginalParticleMaterial>();
            }
            foreach(var p in new[]{new Vector3(-4,0,17.3f),new Vector3(4,0,17.3f),new Vector3(-4,0,23),new Vector3(4,0,23)})
            {
                var at=p;if(Height(Centre+p,out var h))at.y=h-Centre.y+1.34f;
                OriginalAtmosphere.Create("Flame",garden.transform,at,2,.16f,1.2f,.04f,.02f);
                OriginalAtmosphere.Create("SpiritGlow",garden.transform,at,1,.23f,2,.02f,.05f);
            }
            SpawnVisitor("garden-hm50","hm05_000",new Vector3(0,1,17),180);
            SpawnVisitor("garden-hm40","hm95_000",new Vector3(12,1,-22),240);
            SpawnVisitor("garden-hm06","hm05_000",new Vector3(-15,1,26),90);
            FinishFeatures();
        }
        void BuildMazeBoundaries(GardenWall[] walls)
        {
            mazeMin=new Vector2(float.PositiveInfinity,float.PositiveInfinity);mazeMax=new Vector2(float.NegativeInfinity,float.NegativeInfinity);
            if(walls==null)return;
            foreach(var wall in walls)
            {
                mazeMin=new Vector2(Mathf.Min(mazeMin.x,Mathf.Min(wall.a.x,wall.b.x)),Mathf.Min(mazeMin.y,Mathf.Min(wall.a.z,wall.b.z)));
                mazeMax=new Vector2(Mathf.Max(mazeMax.x,Mathf.Max(wall.a.x,wall.b.x)),Mathf.Max(mazeMax.y,Mathf.Max(wall.a.z,wall.b.z)));
                var mid=(wall.a+wall.b)*.5f;Height(Centre+wall.a,out var ya);Height(Centre+wall.b,out var yb);Height(Centre+mid,out var ym);
                float low=Mathf.Min(ym,Mathf.Min(ya,yb))-Centre.y,high=Mathf.Max(ym,Mathf.Max(ya,yb))-Centre.y+7f;
                var root=new GameObject("Original bamboo garden maze boundary");root.transform.SetParent(garden.transform,false);root.transform.localPosition=new Vector3(mid.x,(low+high)*.5f,mid.z);
                var boundary=root.AddComponent<BoxCollider>();boundary.size=new Vector3(Mathf.Abs(wall.a.x-wall.b.x)+.65f,high-low,Mathf.Abs(wall.a.z-wall.b.z)+.65f);
                MazeMagic(root,wall.a,wall.b,high-low);
            }
        }
        bool InMaze(Vector3 player){float x=player.x-Centre.x;return x>=mazeMin.x && x<=mazeMax.x && player.z>=mazeMin.y && player.z<=mazeMax.y;}
        void SpawnVisitor(string resource,string idle,Vector3 p,float yaw)
        {
            var person=new GameObject("Original celestial visitor · "+resource);person.SetActive(false);person.transform.SetParent(garden.transform,false);var world=garden.transform.TransformPoint(p);if(Height(world,out var y))p.y=y-Centre.y+.025f;person.transform.localPosition=p;person.transform.rotation=Quaternion.Euler(0,yaw,0);
            var actor=person.AddComponent<OriginalActor>();actor.game=game;actor.resource="Okami/"+resource;actor.idle=actor.windup=actor.strike=actor.recover=actor.death=idle;actor.walk=actor.run=resource=="garden-hm40"?"hm95_010":"hm05_010";actor.modelScale=1.25f;person.SetActive(true);
            if(resource!="garden-hm50"){var stroll=person.AddComponent<GardenVisitor>();stroll.game=game;stroll.anchor=person.transform.position;stroll.phase=yaw;}
        }
        public bool OwnsRenderer(Renderer renderer)
        {
            if(!renderer)return false;
            int realm=game && game.Player?CelestialTrials.ArenaAt(game.Player.transform.position):0;
            if(realm!=0)return renderer.transform.IsChildOf(game.Player.transform) || CelestialTrials.ArenaAt(renderer.bounds.center)==realm;
            if(CelestialTrials.InArena(renderer.bounds.center))return false;
            bool inPalace=game && game.Player && PalaceInside(game.Player.transform.position);
            bool belongsPalace=palace && renderer.transform.IsChildOf(palace.transform);
            if(inPalace)return belongsPalace || (game && game.Player && renderer.transform.IsChildOf(game.Player.transform)) || PalaceInside(renderer.bounds.center);
            if(belongsPalace || PalaceInside(renderer.bounds.center))return false;
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
            if(rewardPlaying){FinishTreasure(false);return;}
            if(!Playing)return;Playing=false;if(orbit)orbit.EndCinematic();game.Player.Locked=game.Health<=0;
        }
        void Update()
        {
            if(!game || !game.Player || !garden)return;
            if(riverPassage)riverPassage.SetActive(RiverOpen(game.Profile));
            bool inside=Inside(game.Player.transform.position);Shader.SetGlobalFloat("_HeavenPalace",PalaceInside(game.Player.transform.position)?1:0);
            if(inside!=visible){visible=inside;garden.SetActive(visible);if(visible){Physics.SyncTransforms();var p=game.Player.transform.position;if(Height(p,out var h))game.Player.Teleport(new Vector3(p.x,h+.05f,p.z));}}
            Shader.SetGlobalFloat("_SunwardHeaven",inside?1:0);Shader.SetGlobalFloat("_SunwardRiverClock",Time.unscaledTime);
            if(rewardPlaying){TickTreasure();return;}
            if(Playing)
            {
                fallTime+=Time.unscaledDeltaTime;float t=Mathf.Clamp01(fallTime/1.6f);
                var p=fallStart+new Vector3(0,-6.7f*t*t,5.2f*t);game.Player.Teleport(p);
                if(orbit)orbit.CinematicFrame(p+Vector3.up,Mathf.Lerp(-100,-70,t),Mathf.Lerp(32,60,t),12,44);
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
            if(!inside){if(RiverLip(player) && RiverOpen(game.Profile))BeginFall();else if(player.z>28 && Mathf.Abs(player.x-Valley.RiverX(-player.z))<4)game.WorldPrompt(RiverOpen(game.Profile)?"A pale light moves behind the falling water":"The waterfall sings, but the mist will not part");return;}

            if(CelestialTrials.InArena(player))return;
            if(PalaceInteractions())return;
            if(GardenInteractions())return;
            bool nearReturn=new Vector2(player.x-Return.x,player.z-Return.z).magnitude<3.2f;
            bool nearKeeper=new Vector2(player.x-Altar.x,player.z-(Altar.z-5)).magnitude<4.2f;
            game.WorldPrompt(nearReturn?"Walk through the glowing torii passage to return":nearKeeper?"E · Speak with the garden keeper":InMaze(player)?"Bamboo garden maze · the east gates lead back to the garden":"Heavenly garden · seek the keeper by the altar");
            if(game.Player.input.Interact.WasPressedThisFrame())
            {
                if(nearKeeper && keeperCooldown<=0)
                {
                    keeperConversation=true;
                    game.ShowDialogue(CelestialHints.Keeper(game.Profile));
                }
            }
        }
        void OnDisable(){if(garden)garden.SetActive(false);visible=false;keeperConversation=false;keeperCooldown=0;Cancel();Shader.SetGlobalFloat("_HeavenPalace",0);Shader.SetGlobalFloat("_SunwardHeaven",0);}
        void OnDestroy(){ClearFeatures();if(garden)Destroy(garden);if(river)Destroy(river);}
    }
}
