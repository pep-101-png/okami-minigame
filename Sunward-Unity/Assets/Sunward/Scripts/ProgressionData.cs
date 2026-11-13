using System;

namespace Sunward
{
    [Serializable]
    public class UpgradeLevels
    {
        public int vitality, strength, movement, stamina, energy, ability, spear, sundial;
        public int Get(string id)
        {
            switch (id)
            {
                case "vitality":
                    return vitality;
                case "strength":
                    return strength;
                case "movement":
                    return movement;
                case "stamina":
                    return stamina;
                case "energy":
                    return energy;
                case "ability":
                    return ability;
                case "spear":
                    return spear;
                case "sundial":
                    return sundial;
                default:
                    return 0;
            }
        }

        public void Add(string id)
        {
            switch (id)
            {
                case "vitality":
                    vitality++;
                    break;
                case "strength":
                    strength++;
                    break;
                case "movement":
                    movement++;
                    break;
                case "stamina":
                    stamina++;
                    break;
                case "energy":
                    energy++;
                    break;
                case "ability":
                    ability++;
                    break;
                case "spear":
                    spear++;
                    break;
                case "sundial":
                    sundial++;
                    break;
            }
        }
    }

    [Serializable]
    public class Milestones
    {
        public bool homeVisited, sleptAtHome, hollowBell;
    }

    [Serializable]
    public class ProfileData
    {
        public int version = 2, revision, coins = 35, xp, wins, defeats, kills;
        public int shiranuiUnlock;
        public int bossWins, vegetables, cropsSold, praise, restorationStage, farmVitality;
        public int festivalTokens, festivalRewards, festivalWins;
        public Sunward.Remaster.WeaponMastery[] weaponMastery=Array.Empty<Sunward.Remaster.WeaponMastery>();
        public string equipped = "spear";
        public string[] owned =
        {
            "spear"
        };
        public UpgradeLevels upgrades = new UpgradeLevels();
        public bool shrine, night,waterfallVision;
        public double dayElapsed;public float playSeconds;
        public long bedBlessingUntil,fireBlessingUntil;
        public string[] collectibles = Array.Empty<string>(), windflowers = Array.Empty<string>();
        public Milestones milestones = new Milestones();
    }

    public static class ProgressionRules
    {
        public static readonly string[] Upgrades =
        {
            "vitality",
            "strength",
            "movement",
            "stamina",
            "energy",
            "ability",
            "spear",
            "sundial"
        };
        static readonly int[] BaseCosts =
        {
            30,
            40,
            35,
            30,
            35,
            45,
            30,
            35
        }, Caps =
        {
            8,
            8,
            6,
            8,
            8,
            6,
            10,
            10
        };
        public static int Level(ProfileData p) => 1 + (int)Math.Floor(Math.Sqrt(Math.Max(0, p.xp) / 35.0));
        public static float Power(ProfileData p)
        {
            int total = 0;
            foreach (string id in Upgrades)
                total += p.upgrades.Get(id);
            return (Level(p) - 1) * 2 + total * 1.6f + p.wins * 2;
        }

        public static int MaxHp(ProfileData p) => 100 + (Level(p) - 1) * 4 + p.upgrades.vitality * 12 + (p.shrine ? 20 : 0)+Math.Max(0,Math.Min(10,p.farmVitality));
        public static int Cap(string id){int i=Array.IndexOf(Upgrades,id);return i<0?0:Caps[i];}
        public static bool Advanced(ProfileData p)=>p!=null && p.shiranuiUnlock>=1 && Level(p)>=30;
        public static int Cap(ProfileData p,string id)=>Cap(id)+(Advanced(p)?5:0);
        public static bool PathsComplete(ProfileData p,bool advanced=false)
        {if(p==null || p.upgrades==null)return false;foreach(var id in Upgrades)if(p.upgrades.Get(id)<Cap(id)+(advanced?5:0))return false;return true;}
        public static int CompletedPaths(ProfileData p,bool advanced=false)
        {int n=0;foreach(var id in Upgrades)if(p.upgrades.Get(id)>=Cap(id)+(advanced?5:0))n++;return n;}
        public static bool DawnReady(ProfileData p)=>p!=null && p.bossWins>0 && p.shiranuiUnlock==0 && Level(p)>=20 && PathsComplete(p);
        public static bool EclipseReady(ProfileData p)=>Advanced(p) && p.shiranuiUnlock==1 && PathsComplete(p,true);
        public static string Explain(string id)
        {
            switch(id)
            {
                case "vitality":return "+12 max health per rank.";
                case "strength":return "+18% weapon damage per rank.";
                case "movement":return "+3% speed per rank. Rank 2: double jump.";
                case "stamina":return "+15 stamina and faster recovery per rank.";
                case "energy":return "+15 Ink per rank for brush and bark.";
                case "ability":return "Bark cooldown: -0.45 seconds per rank.";
                case "spear":return "+12% glaive damage per rank.";
                case "sundial":return "+14% reflector and rosary damage per rank.";
                default:return "";
            }
        }
        public static int Cost(ProfileData p, string id)
        {
            int i = Array.IndexOf(Upgrades, id);
            return i < 0 ? int.MaxValue : (int)Math.Floor(BaseCosts[i] * Math.Pow(1.48, p.upgrades.Get(id)) + .5);
        }

        public static bool Buy(ProfileData p, string id)
        {
            if(id.StartsWith("awakening:"))return Sunward.Remaster.AwakeningProgress.Upgrade(p,id.Substring(10));
            if (id.StartsWith("weapon:")) return Sunward.Remaster.OriginalWeaponCatalog.Buy(p, id.Substring(7));
            if (id == "unlock-sundial")
            {
                if ((Array.IndexOf(p.owned, "sundial") >= 0 || Array.IndexOf(p.owned,"sundiale")>=0) || p.coins < 110)
                    return false;
                p.coins -= 110;
                Array.Resize(ref p.owned, p.owned.Length + 1);
                p.owned[p.owned.Length - 1] = "sundial";
                p.equipped = "sundial";
                return true;
            }

            int i = Array.IndexOf(Upgrades, id);
            if (i < 0 || p.upgrades.Get(id) >= Cap(p,id) || p.coins < Cost(p, id) || (id == "sundial" && (Array.IndexOf(p.owned, "sundial") < 0 && Array.IndexOf(p.owned,"sundiale")<0)))
                return false;
            p.coins -= Cost(p, id);
            p.upgrades.Add(id);
            return true;
        }

        public static bool Validate(ProfileData p)
        {
            if(p==null || p.shiranuiUnlock<0 || p.shiranuiUnlock>2)return false;
            Sunward.Remaster.OriginalWeaponEvolution.Normalize(p);
            if (p == null || (p.version != 1 && p.version != 2) || p.coins < 0 || p.xp < 0 || p.wins < 0 || p.defeats < 0 || p.revision < 0 || p.upgrades == null || p.owned == null || (Array.IndexOf(p.owned, "spear") < 0 && Array.IndexOf(p.owned,"speare")<0) || Array.IndexOf(p.owned, p.equipped) < 0)
                return false;
            for (int i = 0; i < Upgrades.Length; i++)
                if (p.upgrades.Get(Upgrades[i]) < 0 || p.upgrades.Get(Upgrades[i]) > Cap(p,Upgrades[i]))
                    return false;
            p.collectibles = p.collectibles ?? Array.Empty<string>();
            p.windflowers = p.windflowers ?? Array.Empty<string>();
            p.milestones = p.milestones ?? new Milestones();
            if(p.bossWins<0 || p.vegetables<0 || p.cropsSold<0 || p.praise<0 || p.restorationStage<0 || p.restorationStage>3 || p.farmVitality<0 || p.farmVitality>10)return false;
            if(p.festivalTokens<0 || p.festivalTokens>1000000 || p.festivalRewards<0 || p.festivalRewards>7 || p.festivalWins<0)return false;
            p.weaponMastery=p.weaponMastery??Array.Empty<Sunward.Remaster.WeaponMastery>();
            var seen=new System.Collections.Generic.HashSet<string>();foreach(var row in p.weaponMastery)if(row==null || Sunward.Remaster.OriginalWeaponCatalog.Find(row.id)==null || !seen.Add(row.id) || row.rank<0 || row.rank>5 || row.hits<0 || row.kills<0 || row.charged<0 || row.brush<0 || row.deflected<0 || row.trials<0 || row.bosses<0)return false;
            p.version = 2;
            return true;
        }
    }
}
