using System;
using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    public sealed class ValleyAudio : MonoBehaviour
    {
        public AudioClip bark, growl, hit, howl;
        [Serializable] sealed class CueEntry { public string cue, resource; }
        [Serializable] sealed class CueBank { public CueEntry[] cues; }
        readonly Dictionary<string,List<AudioClip>> bank = new Dictionary<string,List<AudioClip>>();
        readonly Dictionary<string,int> next = new Dictionary<string,int>();
        AudioSource effects, music, wind, river,houseMusic,presentationMusic;
        float presentationBlend;
        float houseBlend;
        AudioSource tundraSwing,tundraImpact,transformationVoice,transformationBurst;
        readonly List<AudioSource> worldSources = new List<AudioSource>();
        readonly Dictionary<AudioSource,Vector2> worldLevels = new Dictionary<AudioSource,Vector2>();
        Transform ears;
        readonly Dictionary<string,float> cooldowns = new Dictionary<string,float>();
        float nextAnimal, nextVoice;
        string speakingPackage;Vector3 speakingPosition;
        GameFlow game;
        string musicCue;
        float steps, water;
        Vector3 lastPosition;
        void Awake()
        {
            effects = Source(.60f, false); music = Source(.45f, true);houseMusic=Source(0,true);presentationMusic=Source(0,true);
            wind = Source(.22f, true); river = Source(.25f, true);
            tundraSwing=Source(1,false);tundraImpact=Source(1,false);
            transformationVoice=Source(1,false);transformationBurst=Source(1,false);
            var data = Resources.Load<TextAsset>("Okami/NativeAudio");
            if (!data) { Debug.LogError("Original sound bank bindings are missing.", this); return; }
            foreach (var entry in JsonUtility.FromJson<CueBank>(data.text).cues)
            {
                var clip = Resources.Load<AudioClip>(entry.resource);
                if (!clip) { Debug.LogError("Original sound missing: " + entry.resource,this); continue; }
                if (!bank.ContainsKey(entry.cue)) bank.Add(entry.cue,new List<AudioClip>());
                bank[entry.cue].Add(clip);
            }
        }
        AudioSource Source(float volume,bool loop)
        {
            var s=gameObject.AddComponent<AudioSource>();s.volume=volume;s.loop=loop;
            s.playOnAwake=false;s.spatialBlend=0;return s;
        }
        AudioClip Clip(string cue)
        {
            if(!bank.TryGetValue(cue,out var list) || list.Count==0)return null;
            int i=next.TryGetValue(cue,out var n)?n:0;next[cue]=(i+1)%list.Count;return list[i%list.Count];
        }
        void Loop(AudioSource source,string cue)
        {
            source.Stop();source.clip=null;
            // Use an original quiet melodic passage for the musician; its track title
            // is unlabelled in source metadata. Keep it separate from battle.
            // Short cleansing/save cues must never become looping background music.
            if(cue!="battle" && cue!="housemusic")return;
            var clip=Clip(cue);if(!clip || clip.length<(cue=="housemusic"?8:45))return;source.clip=clip;source.Play();
        }
        void Start()
        {
            game=FindFirstObjectByType<GameFlow>();
            if(game && game.Player)lastPosition=game.Player.transform.position;
            if(game && game.Player)
            {
                var head=new GameObject("Player perspective audio listener");ears=head.transform;
                ears.SetParent(game.Player.transform,false);ears.localPosition=Vector3.up*.9f;
                var listener=head.AddComponent<AudioListener>();
                foreach(var old in FindObjectsByType<AudioListener>(FindObjectsSortMode.None))if(old!=listener)old.enabled=false;
            }
            // ST102 clips were assigned as ambience without identifying their
            // contents. Do not loop an unidentified animal/event sample globally.
            wind.Stop();river.Stop();
        }
        void LateUpdate()
        {
            if(ears && Camera.main)ears.rotation=Camera.main.transform.rotation;
        }
        void Update()
        {
            if(!game || !game.Player)return;
            Vector3 p=game.Player.transform.position;
            foreach(var source in worldSources)if(source && source.isPlaying && worldLevels.TryGetValue(source,out var level))
            {
                float distance=Vector3.Distance(p,source.transform.position);
                if(distance>=level.x)source.Stop();
                else source.volume=game.CinematicActive?0:level.y*Mathf.SmoothStep(1,0,Mathf.Clamp01(distance/level.x));
            }
            bool presentation=game.Presentation && (game.Presentation.Title || game.Presentation.Playing);
            float presentationTarget=presentation?(game.Presentation.Title?.065f:.10f):0;
            if(presentationTarget>0 && !presentationMusic.isPlaying)Loop(presentationMusic,"housemusic");
            presentationBlend=Mathf.MoveTowards(presentationBlend,presentationTarget,Time.unscaledDeltaTime*(presentation && !game.Presentation.Title?.12f:.03f));presentationMusic.volume=presentationBlend;
            if(!presentation && presentationBlend<=0 && presentationMusic.isPlaying)presentationMusic.Stop();
            bool inMusicHouse=Sunward.Remaster.VillageServices.InFoodHouse(p);
            string desired=game.InTrial?"battle":"town";
            bool heaven=Sunward.Remaster.HeavenlyGarden.Inside(p);
            float houseTarget=(inMusicHouse || heaven) && !game.InTrial && !presentation?.10f:0;
            if(houseTarget>0 && !houseMusic.isPlaying){houseMusic.volume=0;Loop(houseMusic,"housemusic");}
            houseBlend=Mathf.MoveTowards(houseBlend,houseTarget,Time.unscaledDeltaTime*.035f);
            houseMusic.volume=houseBlend*(game.CinematicActive?.3f:1);
            if(houseTarget==0 && houseBlend<=.0001f && houseMusic.isPlaying)houseMusic.Stop();
            if(desired!=musicCue){musicCue=desired;Loop(music,desired);}
            river.volume=(heaven?0:.25f)*Mathf.Clamp01(1-Mathf.Abs(p.x-Valley.RiverX(-p.z))/15);
            wind.volume=heaven?.025f:Sunward.Remaster.VillageServices.InFoodHouse(p)?.06f:.22f;
            music.volume=Mathf.MoveTowards(music.volume,heaven?0:game.CinematicActive?.10f:game.Panel=="dialogue"?.12f:musicCue=="housemusic"?.28f:.4f,Time.unscaledDeltaTime*.6f);
            Vector3 delta=p-lastPosition;delta.y=0;lastPosition=p;
            if(game.Blocked || game.Player.Locked || delta.magnitude>2)return;
            if(!game.Player.Swimming && game.Player.Grounded && game.Player.Speed>.2f)
            {
                steps+=delta.magnitude;
                if(steps>(game.Player.Speed>5?1.5f:.85f)){steps=0;Cue("step");}
            }
            if(game.Player.Swimming && game.Player.Speed>.2f)
            {
                water+=Time.deltaTime;if(water>1.1f){water=0;Cue("water");}
            }
        }
        bool Allow(string id,float interval)
        {
            if(cooldowns.TryGetValue(id,out var until) && Time.unscaledTime<until)return false;
            cooldowns[id]=Time.unscaledTime+interval;return true;
        }
        public void Cue(string id)
        {
            // User-requested Player Archive A + louder Shiranui 16 mix; see NativeAudio bark binding.
            if(id=="flame-impact")id="impact";
            // World actors must supply a position; never route them through 2D playback.
            if(id=="cow" || id=="pig" || id=="rooster" || id.StartsWith("npc") || id.StartsWith("enemy"))return;
            if(!Allow(id,id=="step"?.16f:id=="water"?.35f:.07f))return;
            if(id=="water" && (!game || !game.Player || !game.Player.Swimming))return;
            var clip=Clip(id);if(clip)effects.PlayOneShot(clip,id=="step"?.01125f:id=="jump"?.0875f:(id=="water" || id=="swim-exit")?.018f:id=="land"?.06f:id=="dash"?.175f:id=="bark"?.75f:.45f);
        }
        public void TundraAttack(bool charged,bool heavy)
        {
            // One bounded voice per swing. Avoid stacking the generic impact
            // and heavy fanfare over this instrument's own ice sounds.
            tundraSwing.Stop();tundraSwing.clip=Clip(charged?"weapon-wp2e-heavy":"weapon-wp2e");
            tundraSwing.volume=charged?.11f:heavy?.10f:.09f;
            if(tundraSwing.clip)tundraSwing.Play();
        }
        public void TundraContact()
        {
            if(tundraImpact.isPlaying)return;
            tundraImpact.clip=Clip("weapon-wp2e-impact");tundraImpact.volume=.04f;
            if(tundraImpact.clip)tundraImpact.Play();
        }
        public void StopTundra(){if(tundraSwing)tundraSwing.Stop();}
        public void TransformationVoice()
        {
            transformationVoice.Stop();transformationVoice.clip=Clip("transformation-voice");transformationVoice.volume=.38f;
            if(transformationVoice.clip)transformationVoice.Play();
        }
        public void VictoryHowl()
        {
            transformationVoice.Stop();transformationVoice.clip=Clip("transformation-voice");transformationVoice.volume=.38f;
            if(transformationVoice.clip)transformationVoice.Play();
        }
        public void BossTransformationVoice()
        {
            transformationVoice.Stop();transformationVoice.clip=Clip("enemy5");transformationVoice.volume=.35f;
            if(transformationVoice.clip)transformationVoice.Play();
        }
        public void TransformationBurst()
        {
            transformationBurst.Stop();transformationBurst.clip=Clip("weapon-wp2e-heavy");transformationBurst.volume=.28f;
            if(transformationBurst.clip)transformationBurst.Play();
        }
        public void StopTransformation()
        {if(transformationVoice)transformationVoice.Stop();if(transformationBurst)transformationBurst.Stop();}
        public bool World(string cue,Vector3 position,float range=10,float volume=.65f,bool dialogue=false)
        {
            if(!game || !game.Player || (game.Blocked && !dialogue) || game.CinematicActive)return false;
            float distance=Vector3.Distance(position,game.Player.transform.position);
            if(distance>=range || !Allow("world:"+cue,.5f))return false;
            var clip=Clip(cue);if(!clip)return false;
            AudioSource source=worldSources.Find(s=>!s.isPlaying);
            if(!source)
            {
                if(worldSources.Count>=4)return false;
                var go=new GameObject("Original positional sound");go.transform.SetParent(transform,false);
                source=go.AddComponent<AudioSource>();source.playOnAwake=false;source.spatialBlend=1;
                source.dopplerLevel=0;source.rolloffMode=AudioRolloffMode.Linear;
                source.minDistance=1.5f;source.maxDistance=range;worldSources.Add(source);
            }
            source.transform.position=position;source.clip=clip;source.maxDistance=range;
            worldLevels[source]=new Vector2(range,volume);
            source.volume=volume*Mathf.SmoothStep(1,0,Mathf.Clamp01(distance/range));source.Play();return true;
        }
        public bool Animal(string species,Vector3 position)
        {
            if(Time.unscaledTime<nextAnimal)return false;
            if(!World(species,position,species=="rooster"?7:10,species=="rooster"?.14f:.28f))return false;
            nextAnimal=Time.unscaledTime+3;return true;
        }
        public void Npc(int index) { Npc(index,game && game.Player?game.Player.transform.position:transform.position); }
        public void Npc(int index,Vector3 position)
        {
            if(!game || game.npcObjects==null || index<0 || index>=game.npcObjects.Length || !game.npcObjects[index])return;
            var actor=game.npcObjects[index].GetComponentInChildren<Sunward.Remaster.OriginalActor>(true);if(!actor)return;
            string resource=actor.resource.Substring(actor.resource.LastIndexOf('/')+1).Replace("dojo-","");NpcVoice(resource,position);
        }
        public void NpcVoice(string package,Vector3 position)
        {
            if(Time.unscaledTime<nextVoice)return;
            speakingPackage=package;speakingPosition=position;
            string cue="voice-"+package;
            if(World(cue,position,7,.22f,true))nextVoice=Time.unscaledTime+.45f;
        }
        public void DialogueSyllable(){if(!string.IsNullOrEmpty(speakingPackage))NpcVoice(speakingPackage,speakingPosition);}
        public void Enemy(string role,Vector3 position)
        {
            int index=Array.IndexOf(new[]{"wisp","reed","ranged","heavy","elite","boss"},role);
            if(index>=0)World("enemy"+index,position,12,.32f);
        }
    }
}
