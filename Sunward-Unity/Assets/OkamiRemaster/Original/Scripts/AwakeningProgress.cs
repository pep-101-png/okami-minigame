using System;
namespace Sunward.Remaster
{
    [Serializable] public sealed class WeaponMastery
    {public string id;public int hits,kills,charged,brush,deflected,trials,bosses,rank;}
    // Sunward challenges and affinities; not original-game awakening lore.
    public static class AwakeningProgress
    {
        public static WeaponMastery Get(ProfileData p,string id)
        {
            id=OriginalWeaponEvolution.BaseId(id);if(p.weaponMastery==null)p.weaponMastery=Array.Empty<WeaponMastery>();
            var row=Array.Find(p.weaponMastery,r=>r!=null && r.id==id);if(row!=null)return row;
            row=new WeaponMastery{id=id};Array.Resize(ref p.weaponMastery,p.weaponMastery.Length+1);p.weaponMastery[p.weaponMastery.Length-1]=row;return row;
        }
        public static bool Ready(ProfileData p,string id)
        {
            var m=Get(p,id);switch(m.id)
            {
                case "wp20":return m.hits>=25 && m.charged>=3;
                case "wp21":return m.kills>=12 && m.charged>=5;
                case "wp22":return m.brush>=12;
                case "wp23":return m.trials>=2 && m.brush>=8;
                case "sundial":return m.bosses>=1;
                case "spear":return m.kills>=20 && m.charged>=8;
                case "wp26":return m.hits>=70;
                case "wp27":return m.brush>=20 && m.kills>=12;
                case "wp28":return m.charged>=15 && m.brush>=15;
                case "wp2a":return m.hits>=60;
                case "wp2b":return m.kills>=25;
                case "wp2c":return m.deflected>=8 && m.brush>=10;
                case "wp2d":return m.trials>=2 && m.kills>=20;
                case "wp2e":return m.charged>=10 && m.kills>=30;
                default:return false; // Thunder Edge remains the buried maze reward.
            }
        }
        public static string Challenge(ProfileData p,string id)
        {
            var m=Get(p,id);switch(m.id)
            {
                case "wp20":return "Land "+m.hits+"/25 hits and "+m.charged+"/3 charged hits.";
                case "wp21":return "Defeat "+m.kills+"/12 enemies; land "+m.charged+"/5 charged hits.";
                case "wp22":return "Strike "+m.brush+"/12 enemies with the brush while equipped.";
                case "wp23":return "Win "+m.trials+"/2 upper trials; brush-strike "+m.brush+"/8 enemies.";
                case "sundial":return "Defeat Crimson Helm with Solar Flare equipped ("+m.bosses+"/1).";
                case "spear":return "Defeat "+m.kills+"/20 enemies; land "+m.charged+"/8 charged hits.";
                case "wp26":return "Land "+m.hits+"/70 sword hits on enemies.";
                case "wp27":return "Brush-strike "+m.brush+"/20 enemies and defeat "+m.kills+"/12.";
                case "wp28":return "Land "+m.charged+"/15 charged hits and "+m.brush+"/15 brush hits.";
                case "wp29":return "Dig up the chest in the heavenly garden maze.";
                case "wp2a":return "Land "+m.hits+"/60 bead hits on enemies.";
                case "wp2b":return "Defeat "+m.kills+"/25 enemies with Life Beads equipped.";
                case "wp2c":return "Brush away "+m.deflected+"/8 projectiles and strike "+m.brush+"/10 enemies.";
                case "wp2d":return "Win "+m.trials+"/2 upper trials and defeat "+m.kills+"/20 enemies.";
                default:return "Land "+m.charged+"/10 charged casts and defeat "+m.kills+"/30 enemies.";
            }
        }
        public static void Record(GameFlow g,string kind,bool charged=false)
        {
            if(!g || !g.InTrial)return;string id=OriginalWeaponEvolution.BaseId(g.Profile.equipped);var m=Get(g.Profile,id);
            switch(kind){case "hit":m.hits++;if(charged)m.charged++;break;case "kill":m.kills++;break;case "brush":m.brush++;break;case "deflect":m.deflected++;break;case "trial":m.trials++;break;case "boss":m.bosses++;break;}
            if(!OriginalWeaponEvolution.IsAwakened(g.Profile.equipped) && Ready(g.Profile,id) && OriginalWeaponEvolution.Unlock(g.Profile,id))
            {g.Save.Save();g.Combat.QueueAwakeningEquip();g.Audio.Cue("collect");g.Notify(OriginalWeaponCatalog.Find(g.Profile.equipped).title+" · challenge complete");}
        }
        public static int Rank(ProfileData p,string id)=>OriginalWeaponEvolution.IsAwakened(id)?Get(p,id).rank:0;
        public static int Cost(ProfileData p,string id)=>180*(Rank(p,id)+1)*(Rank(p,id)+1);
        public static bool Upgrade(ProfileData p,string id)
        {
            if(!OriginalWeaponEvolution.IsAwakened(id) || !OriginalWeaponCatalog.Owns(p,id) || Rank(p,id)>=5 || p.coins<Cost(p,id))return false;
            p.coins-=Cost(p,id);Get(p,id).rank++;return true;
        }
        public static string Ability(string resource)
        {
            switch(resource)
            {
                case "wp20":return "Fire · charged reflector blows ignite nearby enemies.";
                case "wp21":return "Earth · charged blows send a stunning ground shockwave.";
                case "wp22":return "Purifying wind · stronger brush slashes and charged gusts.";
                case "wp23":return "Sacred light · charged hits restore Ink.";
                case "wp24":return "Solar fire · wide charged solar bursts and burning hits.";
                case "wp25":return "Divine cutting · stronger Power Slash and charged sword waves.";
                case "wp26":return "Wind · charged blows unleash seven cutting contacts.";
                case "wp27":return "Wind · broad charged crescent and boosted brush damage.";
                case "wp28":return "Earth / cutting · stronger attacks and brush; a giant falling sword on a brush hit.";
                case "wp29":return "Lightning · overflowing arcs; connect the blade to an enemy with the brush for a direct zap.";
                case "wp2a":return "Sacred light · long charged bead bursts.";
                case "wp2b":return "Life · enemy defeats restore 5 health.";
                case "wp2c":return "Purification · brush hits weaken enemies and recover Ink.";
                case "wp2d":return "Renewal · charged contacts restore health and Ink.";
                default:return "Ice · charged casts freeze ordinary enemies and spread frost.";
            }
        }
    }
}
