using System;
using UnityEngine;

namespace Sunward.Remaster
{
    public static class OriginalWeaponCatalog
    {
        public sealed class Entry
        {
            public string id, title, resource, family;
            public int cost;
            public Entry(string id, string title, string resource, string family, int cost)
            { this.id=id;this.title=title;this.resource=resource;this.family=family;this.cost=cost; }
        }
        // Fifteen original divine instruments. wp30+ are alternate/subweapon
        // appearances or other objects, not additional distinct shop weapons.
        public static readonly Entry[] All = {
            new Entry("wp20","Divine Retribution","wp20","reflector",70),
            new Entry("wp21","Snarling Beast","wp21","reflector",140),
            new Entry("wp22","Infinity Judge","wp22","reflector",230),
            new Entry("wp23","Trinity Mirror","wp23","reflector",340),
            new Entry("sundial","Solar Flare","wp24","reflector",110),
            new Entry("spear","Tsumugari","wp25","glaive",0),
            new Entry("wp26","Seven Strike","wp26","glaive",140),
            new Entry("wp27","Blade of Kusanagi","wp27","glaive",230),
            new Entry("wp28","Eighth Wonder","wp28","glaive",340),
            new Entry("wp29","Thunder Edge","wp29","glaive",450),
            new Entry("wp2a","Devout Beads","wp2a","rosary",70),
            new Entry("wp2b","Life Beads","wp2b","rosary",140),
            new Entry("wp2c","Exorcism Beads","wp2c","rosary",230),
            new Entry("wp2d","Resurrection Beads","wp2d","rosary",340),
            new Entry("wp2e","Tundra Beads","wp2e","rosary",450)
        };
        public static readonly Entry AwakenedThunder=new Entry(OriginalWeaponEvolution.ThunderId,"Thunder Edge · Awakened","wp29","glaive",450);
        public static Entry Find(string id)
        {
            if(id==OriginalWeaponEvolution.ThunderId)return AwakenedThunder;
            var entry=Array.Find(All,e=>e.id==OriginalWeaponEvolution.BaseId(id));
            return entry==null || !OriginalWeaponEvolution.IsAwakened(id)?entry:new Entry(id,entry.title+" · Awakened",entry.resource,entry.family,entry.cost);
        }
        public static Entry Display(ProfileData p,Entry entry)=>OriginalWeaponEvolution.Replaced(p,entry.id)?Find(OriginalWeaponEvolution.EvolvedId(entry.id)):entry;
        public static bool Owns(ProfileData profile, string id) => profile.owned != null && Array.IndexOf(profile.owned,id)>=0;
        public static bool Buy(ProfileData profile, string id)
        {
            var entry=Find(id);
            if(OriginalWeaponEvolution.Replaced(profile,id) || OriginalWeaponEvolution.IsAwakened(id) || entry==null || Owns(profile,id) || profile.coins<entry.cost) return false;
            profile.coins-=entry.cost;Array.Resize(ref profile.owned,profile.owned.Length+1);
            profile.owned[profile.owned.Length-1]=id;profile.equipped=id;return true;
        }
        public static string Next(ProfileData profile)
        {
            int start=Array.FindIndex(All,e=>e.id==OriginalWeaponEvolution.BaseId(profile.equipped));
            for(int i=1;i<=All.Length;i++){var entry=Display(profile,All[(start+i+All.Length)%All.Length]);if(Owns(profile,entry.id))return entry.id;}
            return profile.equipped;
        }
        public static WeaponDefinition Definition(Entry entry, WeaponDefinition spear, WeaponDefinition solar,ProfileData profile=null)
        {
            var result=UnityEngine.Object.Instantiate(entry.family=="reflector"?solar:spear);
            result.id=entry.id;result.title=entry.title;
            string[] clips=entry.family=="reflector"?new[]{"500","501","502"}:entry.family=="glaive"?new[]{"520","521","522"}:new[]{"540","542","544","546","548","54a"};
            float[] damage=entry.family=="reflector"?new[]{1.4f,2.1f,3.8f}:entry.family=="glaive"?new[]{1f,2f,3f}:new[]{1f,1.7f,2.4f,2.9f,3.4f,3.8f};
            result.light=new Strike[clips.Length];
            for(int i=0;i<clips.Length;i++)result.light[i]=Native(clips[i],damage[i],entry.family=="rosary"?5.5f:entry.family=="glaive"?3.8f:3.3f,entry.family=="glaive"?.20f:-.25f);
            string heavy=entry.family=="reflector"?"503":entry.family=="glaive"?"523":"54b";
            result.heavy=new[]{Native(heavy,entry.family=="reflector"?4f:entry.family=="rosary"?2.8f:3.3f,4.2f,-.4f)};
            string charged=entry.family=="reflector"?"504":entry.family=="glaive"?"524":"54c";
            result.charged=Native(charged,entry.family=="reflector"?5f:entry.family=="rosary"?4.2f:4.5f,5.2f,.1f);result.chargedHeavy=Native(charged,entry.family=="rosary"?4.6f:6f,5.2f,-.3f);
            result.air=Native(entry.family=="reflector"?"505":entry.family=="glaive"?"525":"54f",entry.family=="rosary"?3f:4.5f,4.5f,-1);
            if(entry.resource=="wp2e")
            {
                float[] tundraDamage={1f,1.4f,1.7f,2.1f,2.4f,2.9f,3.4f,3.8f};
                result.light=new Strike[8];for(int i=0;i<8;i++)result.light[i]=Tundra(TundraAttackRules.Primary(i),tundraDamage[i]);
                result.heavy=new[]{Tundra(TundraAttackRules.Primary(7),4f)};
                result.charged=Tundra(TundraAttackRules.Cast,4.2f);result.chargedHeavy=Tundra(TundraAttackRules.Cast,4.6f);
                result.air=Tundra("Tundra_54f",3f);
            }
            float reach=OriginalWeaponEvolution.Reach(entry.id);
            float power=entry.id=="spear" || entry.id=="sundial"?1:1+Mathf.Clamp01((entry.cost-70)/380f)*.35f;
            power*=OriginalWeaponEvolution.Power(entry.id)*(1+(profile==null?0:AwakeningProgress.Rank(profile,entry.id))*.08f);
            if(profile!=null)reach+=AwakeningProgress.Rank(profile,entry.id)*.02f;
            foreach(var strike in result.light){strike.damage*=power;strike.range*=reach;}
            foreach(var strike in result.heavy){strike.damage*=power;strike.range*=reach;}
            result.charged.damage*=power;result.chargedHeavy.damage*=power;result.air.damage*=power;result.charged.range*=reach;result.chargedHeavy.range*=reach;result.air.range*=reach;
            return result;
        }
        static Strike Tundra(string state,float damage)=>new Strike {clip=state,duration=.9666667f,damage=damage,range=15,arc=-1,start=.12f,end=.85f,lunge=.15f,stagger=.3f};
        static Strike Native(string clip,float damage,float range,float arc)=>new Strike {
            clip="NativeAttack_"+clip,duration=.6f,damage=damage,range=range,arc=arc,start=.22f,end=.68f,lunge=.45f,stagger=.3f };
    }
}
