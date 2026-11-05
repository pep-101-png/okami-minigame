using System;
using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    public sealed partial class HeavenlyGarden
    {
        [Serializable]sealed class GardenPool{public Vector3 position;public Vector2 radius;public float depth;}
        static HeavenlyGarden activeGarden;
        GardenPool[] pools=Array.Empty<GardenPool>();
        readonly List<Mesh> featureMeshes=new List<Mesh>();
        readonly List<Vector3> gongs=new List<Vector3>();
        readonly List<LineRenderer> gongWaves=new List<LineRenderer>();
        readonly List<float> gongWaveTime=new List<float>();
        Vector3 treasurePoint,lookoutPoint,teaPoint;GameObject digGlow,chest,rewardBlade;
        bool rewardPlaying;float rewardTime,featureCooldown,gongCooldown,wetTime,chimeTime;
        Vector3 cranePoint;OrbitCamera treasureCamera;readonly List<GameObject> treasureEffects=new List<GameObject>();
        public static bool Water(Vector3 point,out float level,out float depth)
        {
            level=depth=0;var owner=activeGarden;
            if(!owner || !owner.isActiveAndEnabled || !Inside(point))return false;
            foreach(var pool in owner.pools)
            {
                float x=(point.x-Centre.x-pool.position.x)/pool.radius.x,z=(point.z-pool.position.z)/pool.radius.y;
                if(x*x+z*z>.99f*.99f)continue;
                level=Centre.y+pool.position.y;Height(point,out var floor);depth=Mathf.Max(0,level-floor);return true;
            }
            return false;
        }
        void PrepareFeatures(GardenLayout layout)
        {
            activeGarden=this;pools=layout.ponds??Array.Empty<GardenPool>();treasurePoint=Centre+layout.treasure;lookoutPoint=Centre+layout.lookout;teaPoint=Centre+layout.tea;
            Shader.SetGlobalVectorArray("_HeavenDig",new[]{new Vector4(layout.treasure.x,layout.treasure.z,.8f,OriginalWeaponEvolution.Owns(game.Profile)?0:1)});
            var areas=new Vector4[4];var levels=new Vector4[4];
            for(int i=0;i<Mathf.Min(4,pools.Length);i++)
            {var p=pools[i];areas[i]=new Vector4(p.position.x,p.position.z,p.radius.x,p.radius.y);levels[i]=new Vector4(p.position.y,p.depth,0,0);}
            Shader.SetGlobalVectorArray("_HeavenPonds",areas);Shader.SetGlobalVectorArray("_HeavenPondLevels",levels);Shader.SetGlobalFloat("_HeavenPondCount",Mathf.Min(4,pools.Length));
        }
        void PondMaterial(GameObject prop,GardenItem item)
        {
            var pool=Array.Find(pools,p=>Mathf.Abs(p.position.x-item.position.x)<.1f && Mathf.Abs(p.position.z-item.position.z)<.1f);if(pool==null)return;
            foreach(var r in prop.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                if(r.sharedMesh.name=="Native-1-0")
                {
                    var mat=new Material(r.sharedMaterial);mat.shader=Resources.Load<Material>("Okami/Effects/CelestialWater").shader;
                    mat.SetTexture("_RipplePaint",Resources.Load<Texture2D>("Okami/celestial-pond/Texture-0"));mat.SetFloat("_CentreX",Centre.x+pool.position.x);mat.SetFloat("_CentreZ",pool.position.z);mat.SetFloat("_RadiusX",pool.radius.x);mat.SetFloat("_RadiusZ",pool.radius.y);mat.SetFloat("_WaterLevel",Centre.y+pool.position.y);r.sharedMaterial=mat;r.localBounds=new Bounds(r.sharedMesh.bounds.center,r.sharedMesh.bounds.size+Vector3.up*6);r.updateWhenOffscreen=true;r.gameObject.AddComponent<OriginalParticleMaterial>();
                }
                else
                {r.gameObject.layer=6;r.gameObject.name="Heaven garden ground · native pond rim";r.gameObject.AddComponent<MeshCollider>().sharedMesh=r.sharedMesh;}
            }
            var steam=OriginalAtmosphere.Create("Steam",garden.transform,new Vector3(pool.position.x,pool.position.y+.05f,pool.position.z),.65f,.65f,3,.01f,1.5f);
            if(steam){var main=steam.main;main.startColor=new Color(.8f,.9f,1,.13f);}
        }
        void SolidProp(GameObject prop,bool temple=false)
        {
            foreach(var r in prop.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                // The original complete model blocks the body, including risers/posts.
                r.gameObject.AddComponent<MeshCollider>().sharedMesh=r.sharedMesh;
                if(!temple)continue;
                var mesh=r.sharedMesh;var v=mesh.vertices;var t=mesh.triangles;var walk=new List<int>();
                float limit=prop.transform.position.y+3.1f;
                for(int i=0;i<t.Length;i+=3)
                {
                    var a=r.transform.TransformPoint(v[t[i]]);var b=r.transform.TransformPoint(v[t[i+1]]);var c=r.transform.TransformPoint(v[t[i+2]]);
                    if(Mathf.Max(a.y,Mathf.Max(b.y,c.y))>limit)continue;
                    var normal=Vector3.Cross(b-a,c-a).normalized;if(normal.y<.55f)continue;
                    walk.Add(t[i]);walk.Add(t[i+1]);walk.Add(t[i+2]);
                }
                if(walk.Count==0)continue;
                var floor=new Mesh{name="Original shrine stair treads and timber landing"};floor.vertices=v;floor.triangles=walk.ToArray();floor.RecalculateBounds();featureMeshes.Add(floor);
                var surface=new GameObject("Heaven garden ground · real shrine stairs/landing");surface.layer=6;surface.transform.SetParent(r.transform,false);surface.AddComponent<MeshCollider>().sharedMesh=floor;
            }
        }
        Vector3 OnGround(Vector3 world,float extra=0){Height(world,out var y);world.y=y+extra;return world;}
        GameObject FeatureProp(string resource,Vector3 world,Vector3 size,float yaw=0)
        {return VillageFestival.Place(garden.transform,"Okami/"+resource,world-Centre,size,new Vector3(0,yaw,0));}
        void FinishFeatures()
        {
            BuildPalace();BuildReturnGate();
            treasurePoint=OnGround(treasurePoint);lookoutPoint=OnGround(lookoutPoint);teaPoint=OnGround(teaPoint);
            chest=FeatureProp("vt4b",treasurePoint-Vector3.up*.7f,new Vector3(.9f,.65f,.75f));if(chest){bool found=OriginalWeaponEvolution.Owns(game.Profile);chest.SetActive(found);if(found){chest.transform.position=treasurePoint+Vector3.up*.03f;chest.GetComponent<OriginalVisual>().SampleMotion("Okami/vt4b","vt4b_001",1);}}
            var glow=OriginalAtmosphere.Create("SpiritGlow",garden.transform,treasurePoint-Centre+Vector3.up*.08f,3,.14f,2,.015f,.42f);digGlow=glow?glow.gameObject:null;
            if(digGlow)digGlow.SetActive(!OriginalWeaponEvolution.Owns(game.Profile));
            var table=FeatureProp("dr0d",teaPoint+Vector3.up*.52f,new Vector3(1.9f,.09f,1.25f));if(table)SolidProp(table);
            foreach(float x in new[]{-.75f,.75f})foreach(float z in new[]{-.43f,.43f}){var leg=FeatureProp("vt00",teaPoint+new Vector3(x,0,z),new Vector3(.12f,.52f,.12f));if(leg)SolidProp(leg);}
            foreach(int side in new[]{-1,1})FeatureProp("heaven-tea-tray",teaPoint+new Vector3(side*.55f,.615f,0),new Vector3(.4f,.15f,.28f),side<0?90:270);
            foreach(int side in new[]{-1,1})
            {
                var seat=OnGround(teaPoint+Vector3.right*side*1.45f);var stump=FeatureProp("heaven-tea-seat",seat,new Vector3(.9f,.27f,.9f));if(stump)SolidProp(stump);
                var actorRoot=new GameObject("Celestial tea guest · recovered seated and sipping motions");actorRoot.SetActive(false);actorRoot.transform.SetParent(garden.transform,false);actorRoot.transform.position=seat+Vector3.up*.25f;actorRoot.transform.rotation=Quaternion.Euler(0,side<0?90:270,0);
                var actor=actorRoot.AddComponent<OriginalActor>();actor.game=game;actor.resource="Okami/heaven-tea-hm50";actor.idle=actor.walk=actor.run=actor.windup=actor.strike=actor.recover=actor.death="hm05_003";actor.modelScale=.82f;
                var body=actorRoot.AddComponent<BoxCollider>();body.center=Vector3.up*.65f;body.size=new Vector3(.65f,1.3f,.65f);var tea=actorRoot.AddComponent<HeavenTeaGuest>();tea.actor=actor;tea.phase=side<0?.1f:.65f;actorRoot.SetActive(true);
            }
            var roof=FeatureProp("heaven-lookout-roof",lookoutPoint+Vector3.up*2.65f,new Vector3(5,1.35f,4.7f));if(roof)SolidProp(roof);
            foreach(float x in new[]{-1.9f,1.9f})foreach(float z in new[]{-1.65f,1.65f})
            {var pillar=FeatureProp("vt00",OnGround(lookoutPoint+new Vector3(x,0,z)),new Vector3(.23f,2.9f,.23f));if(pillar)SolidProp(pillar);}
            cranePoint=OnGround(Centre+new Vector3(17,0,22));
            var crane=new GameObject("Original crane · quiet garden bird");crane.SetActive(false);crane.transform.SetParent(garden.transform,false);crane.transform.position=cranePoint;crane.transform.rotation=Quaternion.Euler(0,160,0);var bird=crane.AddComponent<OriginalActor>();bird.game=game;bird.resource="Okami/heaven-crane";bird.idle=bird.walk=bird.run=bird.windup=bird.strike=bird.recover=bird.death="an01_000";bird.modelScale=.6f;crane.SetActive(true);
        }
        void MazeMagic(GameObject boundary,Vector3 a,Vector3 b,float height)
        {
            var lineRoot=new GameObject("Mystical maze veil · original spirit artwork");lineRoot.transform.SetParent(garden.transform,false);
            var line=lineRoot.AddComponent<LineRenderer>();line.useWorldSpace=false;line.positionCount=2;line.SetPosition(0,new Vector3(a.x,boundary.transform.localPosition.y,a.z));line.SetPosition(1,new Vector3(b.x,boundary.transform.localPosition.y,b.z));line.startWidth=line.endWidth=height;line.startColor=line.endColor=Color.white;line.sharedMaterial=Resources.Load<Material>("Okami/Effects/HeavenBarrier");
            var motes=OriginalAtmosphere.Create("Spirit",garden.transform,new Vector3((a.x+b.x)*.5f,boundary.transform.localPosition.y-height*.5f+.1f,(a.z+b.z)*.5f),3,.11f,3,0,.1f);
            if(motes){var v=motes.velocityOverLifetime;v.enabled=true;v.y=2.3f;var main=motes.main;main.startColor=new Color(.4f,.85f,1,.5f);}
        }
        public bool TryDigTreasure()
        {
            if(!game || !Inside(game.Player.transform.position) || Vector2.Distance(new Vector2(game.Player.transform.position.x,game.Player.transform.position.z),new Vector2(treasurePoint.x,treasurePoint.z))>1.6f || !game.Player.input.Dig.WasPressedThisFrame())return false;
            if(Playing || !game.Player.Grounded)return true;
            Playing=rewardPlaying=true;rewardTime=0;game.Combat.Cancel();game.Services.CancelRest();game.Player.StopMotion();game.Player.Teleport(OnGround(treasurePoint+Vector3.right*1.8f,.03f));game.Player.Locked=true;var facing=treasurePoint-game.Player.transform.position;facing.y=0;if(facing.sqrMagnitude>.001f)game.Player.transform.rotation=Quaternion.LookRotation(facing);game.Player.animationView.Play("Dig",.12f,1.25f,true);
            treasureCamera=FindFirstObjectByType<OrbitCamera>();if(treasureCamera)treasureCamera.BeginCinematic(false);if(digGlow)digGlow.SetActive(false);if(chest){chest.transform.position=treasurePoint-Vector3.up*.7f;chest.SetActive(true);}return true;
        }
        void TickTreasure()
        {
            rewardTime+=Time.unscaledDeltaTime;float t=rewardTime;
            if(treasureCamera)treasureCamera.CinematicFrame(treasurePoint+Vector3.up*1.25f,Mathf.Lerp(125,160,Mathf.Clamp01(t/7)),34,6.8f,43);
            if(chest){chest.transform.position=treasurePoint+Vector3.up*Mathf.Lerp(-.7f,.03f,Mathf.SmoothStep(0,1,(t-1)/1.2f));chest.GetComponent<OriginalVisual>().SampleMotion("Okami/vt4b",t<2.1f?"vt4b_000":"vt4b_001",Mathf.Max(0,t-2.1f));}
            if(t>1 && t-Time.unscaledDeltaTime<=1){TreasureBurst("Cloud",treasurePoint,10,.25f);game.Audio.Cue("land");}
            if(t>2.4f && !rewardBlade)
            {rewardBlade=FeatureProp("thunder-awakened",treasurePoint+Vector3.up*.6f,new Vector3(.7f,.16f,2.2f));if(rewardBlade)OriginalWeaponEvolution.Attach(rewardBlade.GetComponent<OriginalVisual>().PaintRoot,true);WeaponElementFx.Thunder(game,treasurePoint+Vector3.up,true);TreasureBurst("SpiritGlow",treasurePoint+Vector3.up,14,.35f);game.Audio.Cue("collect");}
            if(rewardBlade){rewardBlade.transform.position=treasurePoint+Vector3.up*(.6f+1.3f*Mathf.SmoothStep(0,1,(t-2.4f)/.65f)+Mathf.Sin(t*2)*.05f);rewardBlade.transform.rotation=Quaternion.Euler(-90,t*23,0);}
            if(game.Health<=0)FinishTreasure(false);
            else if(t>=7 || game.Player.input.Pause.WasPressedThisFrame())FinishTreasure(true);
        }
        void TreasureBurst(string sprite,Vector3 point,int count,float size)
        {var effect=OriginalAtmosphere.Create(sprite,null,point,0,size,1.2f,.4f,.3f);if(effect){var main=effect.main;main.useUnscaledTime=true;if(sprite=="Cloud")main.startColor=new Color(.45f,.32f,.18f,.65f);effect.Emit(count);treasureEffects.Add(effect.gameObject);}}
        void FinishTreasure(bool grant)
        {
            if(!rewardPlaying)return;
            if(grant && OriginalWeaponEvolution.Unlock(game.Profile)){game.Save.Save();game.Combat.Equip();game.Audio.Cue("collect");game.Notify("Thunder Edge awakened · +35% damage, +15% reach · Q cycles your owned instruments");}
            Shader.SetGlobalVectorArray("_HeavenDig",new[]{new Vector4(treasurePoint.x-Centre.x,treasurePoint.z,.8f,OriginalWeaponEvolution.Owns(game.Profile)?0:1)});
            foreach(var effect in treasureEffects)if(effect)Destroy(effect);treasureEffects.Clear();
            rewardPlaying=Playing=false;if(treasureCamera)treasureCamera.EndCinematic();if(game && game.Player){game.Player.Locked=game.Health<=0;if(game.Player.animationView!=null)game.Player.animationView.Play("Idle_Natural",.12f,0,true);}if(chest){bool found=OriginalWeaponEvolution.Owns(game.Profile);chest.SetActive(found);if(found){chest.transform.position=treasurePoint+Vector3.up*.03f;chest.GetComponent<OriginalVisual>().SampleMotion("Okami/vt4b","vt4b_001",1);}}if(rewardBlade)Destroy(rewardBlade);rewardBlade=null;if(digGlow)digGlow.SetActive(!OriginalWeaponEvolution.Owns(game.Profile));featureCooldown=.6f;
        }
        void Gong(Vector3 point)
        {
            game.Audio.World("heaven-gong",point,24,.8f);game.Audio.World("heaven-gong-strike",point,24,1);gongCooldown=4;
            var root=new GameObject("Gong blessing · spreading native spirit light");root.transform.SetParent(garden.transform,false);root.transform.position=point;
            var wave=root.AddComponent<LineRenderer>();wave.useWorldSpace=false;wave.loop=true;wave.positionCount=64;wave.startWidth=wave.endWidth=.22f;wave.sharedMaterial=new Material(Resources.Load<Material>("Okami/Effects/SpiritRadiance")){mainTexture=Resources.Load<Texture2D>("Okami/Effects/SpiritGlow")};root.AddComponent<OriginalParticleMaterial>();gongWaves.Add(wave);gongWaveTime.Add(0);
            foreach(var offset in new[]{Vector3.zero,new Vector3(3,0,2),new Vector3(-3,0,2)})
            {CelestialBrush.Burst("Blossom",point+offset+Vector3.up*.5f,14,.24f);CelestialBrush.Burst("SpiritGlow",point+offset,12,.16f);}
        }
        bool GardenInteractions()
        {
            featureCooldown=Mathf.Max(0,featureCooldown-Time.unscaledDeltaTime);gongCooldown=Mathf.Max(0,gongCooldown-Time.deltaTime);
            for(int i=gongWaves.Count-1;i>=0;i--)
            {var line=gongWaves[i];float t=gongWaveTime[i]+=Time.deltaTime;if(!line || t>3){if(line)Destroy(line.gameObject);gongWaves.RemoveAt(i);gongWaveTime.RemoveAt(i);continue;}float r=1+t*4;for(int k=0;k<64;k++){float a=k*Mathf.PI*2/64;line.SetPosition(k,new Vector3(Mathf.Sin(a)*r,.18f,Mathf.Cos(a)*r));}line.startColor=line.endColor=new Color(1,.86f,.45f,(1-t/3)*.6f);}
            var p=game.Player.transform.position;if(game.Services.Resting){game.WorldPrompt("E or movement · Stand up");return true;}if(game.Player.Locked)return false;

            if(Time.time>chimeTime){chimeTime=Time.time+49;game.Audio.World("heaven-gong",lookoutPoint,16,.045f);}
            if(Water(p,out var level,out var depth) && depth>.05f && game.Player.Speed>.2f && Time.time>wetTime){wetTime=Time.time+.8f;game.Audio.World("water",p,6,.055f);}
            bool use=game.Player.input.Interact.WasPressedThisFrame() && featureCooldown<=0;
            if(Water(p,out var sitLevel,out var sitDepth) && sitDepth>.035f)
            {game.WorldPrompt("E · Sit in the shallow pond");if(use){game.Services.RestAt(OnGround(p,.025f),game.Player.transform.eulerAngles.y);featureCooldown=.6f;}return true;}
            foreach(var gong in gongs)if(new Vector2(p.x-gong.x,p.z-gong.z).magnitude<2.6f)
            {game.WorldPrompt(gongCooldown>0?"The gong's blessing drifts through the garden":"E · Strike the gong");if(use && gongCooldown<=0){Gong(gong);featureCooldown=.6f;}return true;}
            if(new Vector2(p.x-treasurePoint.x,p.z-treasurePoint.z).magnitude<2){game.WorldPrompt(OriginalWeaponEvolution.Owns(game.Profile)?"F · Revisit the awakened chest":"F · Dig beneath the glowing earth");return true;}
            if(Vector3.Distance(p,lookoutPoint)<3)
            {game.WorldPrompt("E · Rest at the cloud lookout");if(use){game.Services.RestAt(OnGround(lookoutPoint,.03f),270);featureCooldown=.6f;}return true;}
            if(Vector3.Distance(p,teaPoint)<3)
            {game.WorldPrompt("E · Join the celestial tea gathering");if(use){featureCooldown=.6f;game.ShowDialogue("The Celestial Plain was the gods' home. Shiranui's courage lived on in the stories of Nippon, and Amaterasu restored hope wherever she travelled. Rest a moment; even a long journey has room for tea.");}return true;}
            return false;
        }
        void ClearFeatures()
        {FinishTreasure(false);if(activeGarden==this)activeGarden=null;foreach(var mesh in featureMeshes)if(mesh)Destroy(mesh);featureMeshes.Clear();}
    }
}
