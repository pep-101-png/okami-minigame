using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(95)]
    public sealed class VillageFishing:MonoBehaviour
    {
        public GameFlow game;public bool Active{get;private set;}public bool Hooked{get;private set;}public float Tension{get;private set;}public float Progress{get;private set;}
        public static readonly Vector3 Bank=new Vector3(GardenPond.X,0,GardenPond.Z+3.7f);
        readonly List<OriginalActor> fish=new List<OriginalActor>();float clock,fedUntil,remaining;int selected=-1;bool hookFed;OrbitCamera camera;
        public bool Fed=>Time.time<fedUntil;
        public bool Near=>Vector2.Distance(new Vector2(game.Player.transform.position.x,game.Player.transform.position.z),new Vector2(Bank.x,Bank.z))<2.5f && game.Player.transform.position.y>-5 && game.Player.transform.position.y<5;
        public string Status=>!Hooked?"Hold R · draw from Ammy to a visible fish · release R":"Hold attack to reel · release to ease tension · "+Mathf.RoundToInt(Progress*100)+"% · tension "+Mathf.RoundToInt(Tension*100)+"%";
        void Start()
        {
            for(int i=0;i<6;i++)
            {
                string resource="Okami/pond-"+VillageAdventureRules.FishModels[i];var root=new GameObject("Living pond fish · "+VillageAdventureRules.FishNames[i]);root.SetActive(false);root.transform.SetParent(transform,false);
                var actor=root.AddComponent<OriginalActor>();actor.game=game;actor.resource=resource;actor.idle=actor.walk=actor.run=actor.windup=actor.strike=actor.recover=actor.death=VillageAdventureRules.FishModels[i]+"_003";
                var bounds=NativeBounds(resource);actor.modelScale=.55f/Mathf.Max(.01f,bounds.size.z);actor.modelOffset=-bounds.center*actor.modelScale;root.SetActive(true);fish.Add(actor);
            }
            var sign=new GameObject("Pond angler's notice");sign.transform.SetParent(transform,false);sign.transform.position=Ground(Bank+new Vector3(-2.3f,0,1.2f));VillageAdventures.Prop(sign.transform,"vt11",Vector3.zero,new Vector3(.65f,1.4f,.12f),90);
            var visitor=new GameObject("Pond angler · original village visitor");visitor.SetActive(false);visitor.transform.SetParent(transform,false);visitor.transform.position=Ground(Bank+new Vector3(-3,0,1));visitor.transform.rotation=Quaternion.Euler(0,155,0);var a=visitor.AddComponent<OriginalActor>();a.game=game;a.resource="Okami/hm05";a.idle=a.walk=a.run=a.windup=a.strike=a.recover=a.death="hm05_000";a.modelScale=1;visitor.SetActive(true);
        }
        [System.Serializable]sealed class Model{public Part[] parts;}[System.Serializable]sealed class Part{public float[] positions;}
        static Bounds NativeBounds(string resource)
        {var j=JsonUtility.FromJson<Model>(Resources.Load<TextAsset>(resource+"/Model").text);var lo=Vector3.one*float.PositiveInfinity;var hi=Vector3.one*float.NegativeInfinity;foreach(var p in j.parts)for(int i=0;i<p.positions.Length;i+=3){var v=new Vector3(p.positions[i],p.positions[i+1],p.positions[i+2]);lo=Vector3.Min(lo,v);hi=Vector3.Max(hi,v);}return new Bounds((lo+hi)*.5f,hi-lo);}
        Vector3 Ground(Vector3 p){p.y=game.valley.Height(p)+.04f;return p;}
        public bool Begin()
        {
            if(Active || !Near || game.InTrial || game.Health<=0 || game.CinematicActive)return false;var festival=game.GetComponent<FestivalChallenges>();if(festival && festival.Active)return false;
            game.Close();game.Combat.Cancel();game.Player.StopMotion();game.Player.Teleport(Ground(Bank));game.Player.transform.rotation=Quaternion.Euler(0,180,0);game.Player.animationView.Play("Sit",.15f,0,true);
            Active=true;Hooked=false;selected=-1;remaining=60;camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.BeginCinematic(false);return true;
        }
        public void Teach()=>game.ShowDialogue("Pond angler\n\nSit at the north bank. Hold R and draw a line from Ammy to a fish you can see, then release R. Once hooked, hold attack to reel. Let go when tension climbs; pull again when it settles.\n\nFood draws the koi out. A restored retreat brings other visitors after dark. The rare silver fish follows a well-fed pond beneath the moon.");
        public bool Feed()
        {if(!Near || Active || game.Profile.vegetables<1)return false;game.Profile.vegetables--;fedUntil=Time.time+120;game.Save.Save();CelestialBrush.Burst("Leaf",new Vector3(GardenPond.X,GardenPond.Water+.05f,GardenPond.Z),9,.12f);game.Notify("Produce scattered · fish gather for two minutes");return true;}
        public bool TryHook(Vector3 start,Vector3 end)
        {
            if(!Active || Hooked)return false;
            if(Vector2.Distance(new Vector2(start.x,start.z),new Vector2(game.Player.transform.position.x,game.Player.transform.position.z))>2.7f)return false;
            float best=.75f;int target=-1;for(int i=0;i<fish.Count;i++)if(fish[i].gameObject.activeSelf && VillageAdventureRules.FishAvailable(game.Profile,i,Fed)){var p=fish[i].transform.position;float d=Vector2.Distance(new Vector2(end.x,end.z),new Vector2(p.x,p.z));if(d<best){best=d;target=i;}}
            if(target<0)return false;if(game.Energy<8){game.Notify("Not enough Ink to hook a fish");return true;}
            game.Energy-=8;selected=target;hookFed=Fed;fish[target].PlayActivity(VillageAdventureRules.FishModels[target]+"_003",true,1.5f);Hooked=true;Tension=.28f;Progress=0;remaining=35;game.Audio.Cue("water");return true;
        }
        void Update()
        {
            if(!game || !game.Player)return;bool local=!VillageInteriors.AnyRoom(game.Player.transform.position) && !HeavenlyGarden.Inside(game.Player.transform.position) && !game.InTrial && game.Player.transform.position.y>-5;clock+=Time.deltaTime;
            for(int i=0;i<fish.Count;i++)
            {
                bool visible=local && (Active && Hooked && selected==i || VillageAdventureRules.FishAvailable(game.Profile,i,Fed));fish[i].gameObject.SetActive(visible);if(!visible)continue;
                float a=clock*(.28f+i*.018f)+i*1.7f;float rx=Fed?1.1f:1.8f,rz=Fed?.7f:1.1f;
                Vector3 p=new Vector3(GardenPond.X+Mathf.Sin(a)*rx,GardenPond.Water-.22f+Mathf.Sin(a*1.5f)*.035f,GardenPond.Z+Mathf.Cos(a)*rz);
                if(Active && Hooked && selected==i)p=Vector3.Lerp(p,new Vector3(Bank.x,GardenPond.Water-.18f,GardenPond.Z+1.25f),Progress);
                var d=p-fish[i].transform.position;fish[i].transform.position=p;if(d.sqrMagnitude>.000001f)fish[i].transform.rotation=Quaternion.Slerp(fish[i].transform.rotation,Quaternion.LookRotation(new Vector3(d.x,0,d.z)),Time.deltaTime*4);
            }
            if(!Active){if(local && Near && !game.Blocked){game.WorldPrompt("E · Fishing, feeding & the pond collection");if(game.Player.input.Interact.WasPressedThisFrame())game.SetPanel("fishing");}return;}
            if(!Near || game.InTrial || game.Health<=0 || game.Panel!=""){Cancel();return;}
            if(game.Player.input.Interact.WasPressedThisFrame() || game.Player.input.Pause.WasPressedThisFrame()){Cancel();return;}
            if(camera)camera.CinematicFrame(new Vector3(GardenPond.X,GardenPond.Water,GardenPond.Z),0,57,7.7f,48);
            game.WorldPrompt(Status);if(game.Blocked)return;
            remaining-=Time.deltaTime;if(remaining<=0){Cancel();game.Notify("The fish slip back into the pond · try again");return;}
            if(!Hooked)return;bool pull=game.Player.input.Light.IsPressed();Tension=Mathf.Clamp01(Tension+Time.deltaTime*(pull?.29f+selected*.018f:-.55f));
            if(pull && Tension<.86f)Progress=Mathf.Clamp01(Progress+Time.deltaTime*.18f);
            if(Tension>=1){Cancel();game.Notify("The line broke · ease off before tension fills");return;}
            if(Progress>=1)
            {
                int caught=selected;bool fed=hookFed;Cancel();if(VillageAdventureRules.Catch(game.Profile,caught,fed)){game.Save.Save();game.Audio.Cue("collect");game.Player.animationView.Play("Eat",.12f,.8f,true);game.Notify(VillageAdventureRules.FishNames[caught]+" caught · collection and pouch saved");}
            }
        }
        public void Cancel(){if(!Active)return;Active=Hooked=false;if(selected>=0 && selected<fish.Count)fish[selected].EndActivity();selected=-1;if(camera)camera.EndCinematic();if(game && game.Player){game.Player.StopMotion();game.Player.animationView.Play("Idle_Natural",.15f,0,true);}}
        void OnDisable(){Cancel();}
    }
}
