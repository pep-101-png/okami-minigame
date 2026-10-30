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
        GameFlow game;
        string musicCue;
        float steps, water;
        Vector3 lastPosition;
        void Awake()
        {
            effects = Source(.55f, false); music = Source(.15f, true);
            wind = Source(.09f, true); river = Source(.13f, true);
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
            Loop(wind,"wind");Loop(river,"river");
        }
        void Update()
        {
            if(!game || !game.Player)return;
            Vector3 p=game.Player.transform.position;
            string desired=game.InTrial?"battle":Sunward.Remaster.VillageServices.InFoodHouse(p)?"housemusic":"town";
            if(desired!=musicCue){musicCue=desired;Loop(music,desired);}
            river.volume=.13f*Mathf.Clamp01(1-Mathf.Abs(p.x-Valley.RiverX(-p.z))/15);
            wind.volume=Sunward.Remaster.VillageServices.InFoodHouse(p)?.025f:.09f;
            music.volume=game.Panel=="dialogue"?.075f:.15f;
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
        public void Cue(string id)
        {
            if(id=="flame-impact")id="impact";
            var clip=Clip(id);if(clip)effects.PlayOneShot(clip,id=="step"?.42f:id=="cow" || id=="pig" || id=="rooster" || id.StartsWith("enemy")?.35f:1);
        }
        public void Npc(int index) { Cue("npc"+index); }
        public void Enemy(string role)
        {
            int index=Array.IndexOf(new[]{"wisp","reed","ranged","heavy","elite","boss"},role);
            if(index>=0)Cue("enemy"+index);
        }
    }
}
