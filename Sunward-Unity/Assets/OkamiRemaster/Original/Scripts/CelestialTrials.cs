using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(65)]
    public sealed class CelestialTrials:MonoBehaviour
    {
        public GameFlow game;public bool Active{get;private set;}public bool Playing{get;private set;}public int Kind{get;private set;}
        public static readonly Vector3 DawnCentre=new Vector3(380,70,0),EclipseCentre=new Vector3(380,100,140);
        public Vector3 ArenaCentre=>Kind==2?EclipseCentre:DawnCentre;
        public string Title=>Kind==2?"THE ECLIPSE WARDEN":"THE VEILED SENTINEL";
        GameObject dawnArena,eclipseArena;EnemyDefinition dawnSpec,eclipseSpec;OrbitCamera orbit;float elapsed;bool victory,vision,returned,restored;
        Vector3 visionOrigin;Quaternion visionRotation;readonly List<GameObject> effects=new List<GameObject>();
        public static int ArenaAt(Vector3 p)=>Mathf.Abs(p.x-380)<30 && Mathf.Abs(p.z)<30 && p.y>66 && p.y<83?1:Mathf.Abs(p.x-380)<30 && Mathf.Abs(p.z-140)<30 && p.y>96 && p.y<113?2:0;
        public static bool InArena(Vector3 p)=>ArenaAt(p)!=0;
        public static Vector3 Guard(Vector3 p)
        {var centre=ArenaAt(p)==2?EclipseCentre:DawnCentre;var d=p-centre;d.y=0;if(d.magnitude>24){d=d.normalized*24;p.x=centre.x+d.x;p.z=centre.z+d.z;}return p;}
        public static bool Floor(Vector3 p,out float y){int area=ArenaAt(p);y=area==2?EclipseCentre.y:DawnCentre.y;return area!=0;}
        void Start()
        {
            dawnArena=BuildArena(1);eclipseArena=BuildArena(2);dawnArena.SetActive(false);eclipseArena.SetActive(false);
            dawnSpec=Definition(1);eclipseSpec=Definition(2);
            Gate(1,HeavenlyGarden.Centre+new Vector3(14,1,24),0);
            Gate(2,HeavenlyGarden.PalaceCentre+new Vector3(0,.03f,12),0);
        }
        EnemyDefinition Definition(int kind)
        {
            bool eclipse=kind==2;var spec=ScriptableObject.CreateInstance<EnemyDefinition>();spec.id=eclipse?"guardian-eclipse":"guardian-dawn";spec.title=eclipse?"Eclipse Warden":"Veiled Sentinel";
            spec.hp=eclipse?11000:2600;spec.damage=eclipse?55:32;spec.speed=3;spec.scale=1;spec.windup=1.2f;spec.reward=eclipse?1200:600;spec.xp=eclipse?1200:700;
            var model=new GameObject(spec.title+" · original model template");model.SetActive(false);model.transform.SetParent(transform,false);
            if(!eclipse)Actor(model,"guardian-sentinel","em60",2.1f,"001");
            else{var tails=new GameObject("Original nine-tail companion");tails.SetActive(false);tails.transform.SetParent(model.transform,false);Actor(tails,"guardian-eclipse","em62",.34f,"000");tails.SetActive(true);}
            if(eclipse){var body=new GameObject("Original fox body · matching companion to native nine tails");body.SetActive(false);body.transform.SetParent(model.transform,false);Actor(body,"guardian-fox","em61",.34f,"000");body.SetActive(true);}
            spec.visual=model;return spec;
        }
        void Actor(GameObject root,string resource,string prefix,float scale,string idle)
        {
            var a=root.AddComponent<OriginalActor>();a.game=game;a.resource="Okami/"+resource;a.idle=prefix+"_"+idle;a.walk=prefix+"_010";a.run=prefix+"_011";
            a.windup=a.strike=a.recover=prefix+"_030";a.death=prefix+(prefix=="em60"?"_043":"_040");a.modelScale=scale;a.splitAttackClip=true;
            a.chargeAttack=prefix+"_030";a.slamAttack=prefix+(prefix=="em60"?"_035":"_031");a.rangedAttack=prefix+(prefix=="em60"?"_031":"_032");
        }
        public bool Ready(int kind)=>kind==1?ProgressionRules.DawnReady(game.Profile):ProgressionRules.EclipseReady(game.Profile);
        public bool Enter(int kind)
        {
            if(Active || Playing || game.Blocked || game.InTrial || !Ready(kind))return false;
            Kind=kind;var arena=kind==1?dawnArena:eclipseArena;arena.SetActive(true);Physics.SyncTransforms();
            if(!game.StartCelestialTrial(kind==1?dawnSpec:eclipseSpec,ArenaCentre)){arena.SetActive(false);return false;}
            Active=Playing=true;victory=vision=returned=false;elapsed=0;game.Player.Locked=true;
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();game.Audio.World("heaven-gong-strike",ArenaCentre,30,.5f);return true;
        }
        public void Complete(bool won)
        {
            Active=false;victory=won;vision=returned=false;elapsed=0;
            if(!won){Playing=false;ReturnToGate();game.Health=game.MaxHealth;game.Stamina=game.MaxStamina;game.Energy=game.MaxEnergy;game.Notify("The guardian waits · your earned growth is safe");return;}
            Playing=true;game.Player.Locked=true;orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();
            Burst("Blossom",game.Player.transform.position+Vector3.up,48,.3f);
        }
        public void RevealWaterfall()
        {
            if(!game || game.Profile.bossWins<=0 || game.Profile.waterfallVision)return;
            game.Profile.waterfallVision=true;game.Save.Save();visionOrigin=game.Player.transform.position;visionRotation=game.Player.transform.rotation;
            var at=new Vector3(Valley.RiverX(-33),1,32);at.x+=4;at.y=game.valley.Height(at)+.05f;game.Player.Teleport(at);game.Player.Locked=true;
            Playing=vision=true;victory=false;elapsed=0;orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();
            var shaft=new GameObject("River awakening · original spirit light");shaft.transform.position=new Vector3(Valley.RiverX(-36),0,36);effects.Add(shaft);
            var beam=shaft.AddComponent<LineRenderer>();beam.useWorldSpace=false;beam.positionCount=2;beam.SetPosition(0,Vector3.up*24);beam.SetPosition(1,Vector3.zero);beam.startWidth=.45f;beam.endWidth=2.2f;beam.startColor=new Color(1,.94f,.65f,.12f);beam.endColor=new Color(1,.94f,.65f,.65f);beam.sharedMaterial=Resources.Load<Material>("Okami/Effects/SpiritRadiance");
            Burst("SpiritGlow",new Vector3(Valley.RiverX(-36),1,36),60,.4f);game.Audio.Cue("bell");
        }
        void Update()
        {
            if(!game || !game.Player)return;
            if(!restored && game.Profile.shiranuiUnlock>0){restored=true;game.Heaven.RestoreLight();}
            if(Playing)
            {
                elapsed+=Time.unscaledDeltaTime;
                if(vision)
                {
                    var focus=new Vector3(Valley.RiverX(-36),-1.5f,37);if(orbit)orbit.CinematicFrame(focus,Mathf.Lerp(-115,-80,Mathf.Clamp01(elapsed/3)),22,11,45);
                    if(elapsed>=3)FinishScene();return;
                }
                if(victory)
                {
                    if(!returned && elapsed>=1.7f)
                    {returned=true;game.Player.Teleport(HeavenlyGarden.PalaceCentre+new Vector3(0,.04f,-6));game.Player.transform.rotation=Quaternion.identity;game.Heaven.RestoreLight();Burst("SpiritGlow",HeavenlyGarden.PalaceCentre+Vector3.up,65,.3f);game.Audio.VictoryHowl();}
                    var focus=returned?HeavenlyGarden.PalaceCentre+Vector3.up:ArenaCentre+Vector3.up*1.5f;
                    if(orbit)orbit.CinematicFrame(focus,Mathf.Lerp(20,75,Mathf.Clamp01(elapsed/3.6f)),18,returned?10:16,43);
                    if(elapsed>=3.6f)FinishScene();return;
                }
                if(orbit)orbit.CinematicFrame(ArenaCentre+new Vector3(0,1.4f,5),Mathf.Lerp(-35,22,Mathf.Clamp01(elapsed/2.8f)),20,14,43);
                if(elapsed>=2.8f)FinishScene();return;
            }
            if(!Active && !InArena(game.Player.transform.position)){if(dawnArena)dawnArena.SetActive(false);if(eclipseArena)eclipseArena.SetActive(false);}
        }
        public void Skip(){if(Playing)FinishScene();}
        void FinishScene()
        {
            bool wasVision=vision;Playing=vision=false;if(orbit)orbit.EndCinematic();ClearEffects();game.Player.Locked=game.Health<=0;
            if(wasVision){game.Player.Teleport(visionOrigin);game.Player.transform.rotation=visionRotation;game.Notify("A distant light answers from the river");}
            else if(victory)
            {
                game.Player.Teleport(HeavenlyGarden.PalaceCentre+new Vector3(0,.04f,-6));game.Heaven.RestoreLight();
                game.Health=game.MaxHealth;game.Stamina=game.MaxStamina;game.Energy=game.MaxEnergy;
                var native=game.Player.GetComponent<NativeAmaterasu>();if(native)game.Transformation.Reveal(native,Kind);
                game.Notify(Kind==1?"Shiranui awakened · T changes your earned forms":"Shiranui full power · T changes your earned forms");victory=false;
            }
            if(orbit)orbit.SnapFocus();
        }
        void ReturnToGate()
        {
            game.Player.Locked=false;var p=Kind==2?HeavenlyGarden.PalaceCentre+new Vector3(0,.05f,8):HeavenlyGarden.Centre+new Vector3(14,1,20);if(HeavenlyGarden.Height(p,out var y))p.y=y+.05f;game.Player.Teleport(p);var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();
        }
        public void Cancel(){Active=Playing=victory=vision=false;if(orbit)orbit.EndCinematic();ClearEffects();if(game && game.Player)game.Player.Locked=game.Health<=0;}
        void Burst(string sprite,Vector3 at,int count,float size)
        {var fx=OriginalAtmosphere.Create(sprite,null,at,0,size,2.4f,.6f,2);if(fx){var main=fx.main;main.useUnscaledTime=true;fx.Emit(count);effects.Add(fx.gameObject);}}
        void ClearEffects(){foreach(var fx in effects)if(fx)Destroy(fx);effects.Clear();}
        void OnDisable(){Cancel();}
        void OnDestroy(){if(dawnSpec)Destroy(dawnSpec);if(eclipseSpec)Destroy(eclipseSpec);}
        void Gate(int kind,Vector3 at,float yaw)
        {
            var root=new GameObject(kind==1?"Sealed courtyard behind the palace":"Eclipse passage inside Shiranui's chamber");root.transform.SetParent(transform,false);root.transform.position=at;root.transform.rotation=Quaternion.Euler(0,yaw,0);
            var prop=VillageFestival.Place(root.transform,"Okami/heaven-gate",Vector3.zero,new Vector3(5,5,1.2f),Vector3.zero);
            var gate=root.AddComponent<CelestialTrialGate>();gate.game=game;gate.kind=kind;
            var mist=OriginalAtmosphere.Create("SpiritGlow",root.transform,new Vector3(0,2,0),14,.2f,3,.3f,1.4f);gate.mist=mist;
            var lamp=root.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=8;lamp.intensity=2;lamp.color=kind==1?new Color(1,.82f,.5f):new Color(.6f,.65f,1);
        }
        static void Still(ParticleSystem p)
        {p.gameObject.AddComponent<CelestialStillPaint>();}
        GameObject BuildArena(int kind)
        {
            var root=new GameObject(kind==1?"Celestial courtyard behind the palace":"Eclipse sanctuary above the clouds");root.transform.SetParent(transform,false);root.transform.position=kind==1?DawnCentre:EclipseCentre;
            var floor=VillageFestival.Place(root.transform,"Okami/celestial-grounded",Vector3.zero,new Vector3(60,.025f,60),Vector3.zero);
            foreach(var r in floor.GetComponentsInChildren<SkinnedMeshRenderer>()){var mat=new Material(Resources.Load<Material>("Okami/Effects/CelestialCourt"));mat.SetVector("_CourtCentre",kind==1?DawnCentre:EclipseCentre);mat.SetFloat("_Eclipse",kind==2?1:0);r.sharedMaterial=mat;r.gameObject.layer=6;r.gameObject.AddComponent<MeshCollider>().sharedMesh=r.sharedMesh;}
            for(int i=0;i<12;i++)
            {
                float a=i*Mathf.PI/6;var pos=new Vector3(Mathf.Sin(a)*26,0,Mathf.Cos(a)*26);
                var cloud=VillageFestival.Place(root.transform,"Okami/heaven-cloud",pos-Vector3.up*1.8f,new Vector3(16,4,12),new Vector3(0,i*30,0));
                foreach(var r in cloud.GetComponentsInChildren<SkinnedMeshRenderer>()){var mat=new Material(r.sharedMaterial);mat.shader=Resources.Load<Material>("Okami/Effects/HeavenCloud").shader;r.sharedMaterial=mat;}
                VillageFestival.Place(root.transform,"Okami/vt35",pos*.87f,new Vector3(.9f,1.7f,.9f),Vector3.zero);
                if(i%2==0)VillageFestival.Place(root.transform,"Okami/heaven-gate",pos*.95f,new Vector3(7,6,1.2f),new Vector3(0,i*30+180,0));
                for(int j=0;j<3;j++){float angle=a+(j-1)*.075f;VillageFestival.Place(root.transform,j%2==0?"Okami/vt46":"Okami/vt47",new Vector3(Mathf.Sin(angle)*22.5f,.03f,Mathf.Cos(angle)*22.5f),new Vector3(1.6f,1.3f,1.6f),new Vector3(0,i*27+j*38,0));}
                OriginalAtmosphere.Create(kind==1?"Blossom":"SpiritGlow",root.transform,pos+Vector3.up*2,2,.18f,4,.1f,2);
            }
            var seal=OriginalAtmosphere.Create("OriginalGodSeal",root.transform,new Vector3(0,.035f,0),0,24,100,0,0);if(seal){seal.GetComponent<ParticleSystemRenderer>().renderMode=ParticleSystemRenderMode.HorizontalBillboard;Still(seal);}
            var sky=OriginalAtmosphere.Create(kind==1?"OriginalSun":"OriginalMoon",root.transform,new Vector3(0,15,35),0,kind==1?13:18,9999,0,0);if(sky)Still(sky);
            var skyGlow=OriginalAtmosphere.Create("SolarGlow",root.transform,new Vector3(0,15,35.2f),0,kind==1?20:24,9999,0,0);if(skyGlow){var main=skyGlow.main;main.startColor=kind==1?new Color(1,.8f,.45f,.3f):new Color(.5f,.57f,1,.3f);Still(skyGlow);}
            var sun=new GameObject(kind==1?"Warm courtyard light":"Pale eclipse light");sun.transform.SetParent(root.transform,false);sun.transform.localPosition=Vector3.up*14;var light=sun.AddComponent<Light>();light.type=LightType.Point;light.range=60;light.intensity=kind==1?3:2;light.color=kind==1?new Color(1,.86f,.63f):new Color(.65f,.72f,1);return root;
        }
    }
}
