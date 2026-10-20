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
        public string equipped = "spear";
        public string[] owned =
        {
            "spear"
        };
        public UpgradeLevels upgrades = new UpgradeLevels();
        public bool shrine;
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

        public static int MaxHp(ProfileData p) => 100 + (Level(p) - 1) * 4 + p.upgrades.vitality * 12 + (p.shrine ? 20 : 0);
        public static int Cost(ProfileData p, string id)
        {
            int i = Array.IndexOf(Upgrades, id);
            return i < 0 ? int.MaxValue : (int)Math.Floor(BaseCosts[i] * Math.Pow(1.48, p.upgrades.Get(id)) + .5);
        }

        public static bool Buy(ProfileData p, string id)
        {
            if (id == "unlock-sundial")
            {
                if (Array.IndexOf(p.owned, "sundial") >= 0 || p.coins < 110)
                    return false;
                p.coins -= 110;
                Array.Resize(ref p.owned, p.owned.Length + 1);
                p.owned[p.owned.Length - 1] = "sundial";
                p.equipped = "sundial";
                return true;
            }

            int i = Array.IndexOf(Upgrades, id);
            if (i < 0 || p.upgrades.Get(id) >= Caps[i] || p.coins < Cost(p, id) || (id == "sundial" && Array.IndexOf(p.owned, "sundial") < 0))
                return false;
            p.coins -= Cost(p, id);
            p.upgrades.Add(id);
            return true;
        }

        public static bool Validate(ProfileData p)
        {
            if (p == null || (p.version != 1 && p.version != 2) || p.coins < 0 || p.xp < 0 || p.wins < 0 || p.defeats < 0 || p.revision < 0 || p.upgrades == null || p.owned == null || Array.IndexOf(p.owned, "spear") < 0 || Array.IndexOf(p.owned, p.equipped) < 0)
                return false;
            for (int i = 0; i < Upgrades.Length; i++)
                if (p.upgrades.Get(Upgrades[i]) < 0 || p.upgrades.Get(Upgrades[i]) > Caps[i])
                    return false;
            p.collectibles = p.collectibles ?? Array.Empty<string>();
            p.windflowers = p.windflowers ?? Array.Empty<string>();
            p.milestones = p.milestones ?? new Milestones();
            p.version = 2;
            return true;
        }
    }
}
