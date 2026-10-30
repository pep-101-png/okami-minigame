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
        AudioSource effects, music, wind, river;
        readonly List<AudioSource> worldSources = new List<AudioSource>();
        readonly Dictionary<AudioSource,Vector2> worldLevels = new Dictionary<AudioSource,Vector2>();
        Transform ears;
        readonly Dictionary<string,float> cooldowns = new Dictionary<string,float>();
        float nextAnimal, nextVoice;
        GameFlow game;
        string musicCue;
        float steps, water;
        Vector3 lastPosition;
        void Awake()
        {
            effects = Source(.60f, false); music = Source(.45f, true);
            wind = Source(.22f, true); river = Source(.25f, true);
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
            var clip=Clip(cue);if(!clip)return;source.clip=clip;source.Play();
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
            Loop(wind,"wind");Loop(river,"river");
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
                else source.volume=level.y*Mathf.SmoothStep(1,0,Mathf.Clamp01(distance/level.x));
            }
            string desired=game.InTrial?"battle":Sunward.Remaster.VillageServices.InFoodHouse(p)?"housemusic":"town";
            if(desired!=musicCue){musicCue=desired;Loop(music,desired);}
            river.volume=.25f*Mathf.Clamp01(1-Mathf.Abs(p.x-Valley.RiverX(-p.z))/15);
            wind.volume=Sunward.Remaster.VillageServices.InFoodHouse(p)?.06f:.22f;
            music.volume=game.Panel=="dialogue"?.22f:.45f;
            Vector3 delta=p-lastPosition;delta.y=0;lastPosition=p;
            if(game.Blocked || game.Player.Locked || delta.magnitude>2)return;
            if(game.Player.Grounded && game.Player.Speed>.2f)
            {
                steps+=delta.magnitude;
                if(steps>(game.Player.Speed>5?1.5f:.85f)){steps=0;Cue("step");}
            }
            if(game.Player.Swimming && game.Player.Speed>.2f)
            {
                water+=Time.deltaTime;if(water>.7f){water=0;Cue("water");}
            }
        }
        bool Allow(string id,float interval)
        {
            if(cooldowns.TryGetValue(id,out var until) && Time.unscaledTime<until)return false;
            cooldowns[id]=Time.unscaledTime+interval;return true;
        }
        public void Cue(string id)
        {
            if(id=="flame-impact")id="impact";
            // World actors must supply a position; never route them through 2D playback.
            if(id=="cow" || id=="pig" || id=="rooster" || id.StartsWith("npc") || id.StartsWith("enemy"))return;
            if(!Allow(id,id=="step"?.16f:id=="water"?.35f:.07f))return;
            var clip=Clip(id);if(clip)effects.PlayOneShot(clip,id=="step"?.60f:id=="jump" || id=="land" || id=="dash"?.35f:.75f);
        }
        public bool World(string cue,Vector3 position,float range=10,float volume=.65f)
        {
            if(!game || !game.Player || game.Blocked)return false;
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
        public void Animal(string species,Vector3 position)
        {
            if(Time.unscaledTime<nextAnimal)return;
            if(World(species,position,species=="rooster"?6:9,species=="rooster"?.32f:.5f))nextAnimal=Time.unscaledTime+12;
        }
        public void Npc(int index) { Npc(index,game && game.Player?game.Player.transform.position:transform.position); }
        public void Npc(int index,Vector3 position)
        {
            if(Time.unscaledTime<nextVoice)return;
            if(World("npc"+index,position,7,.7f))
            {
                float length=bank.TryGetValue("npc"+index,out var voices)?voices[0].length:1.35f;
                nextVoice=Time.unscaledTime+Mathf.Max(1.5f,length+.15f);
            }
        }
        public void Enemy(string role,Vector3 position)
        {
            int index=Array.IndexOf(new[]{"wisp","reed","ranged","heavy","elite","boss"},role);
            if(index>=0)World("enemy"+index,position,12,.55f);
        }
    }
}
