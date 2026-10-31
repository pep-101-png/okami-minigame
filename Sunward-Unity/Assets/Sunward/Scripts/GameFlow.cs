using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    public sealed class GameFlow : MonoBehaviour
    {
        public Valley valley;
        public WolfMotor Player;
        public WolfCombat Combat;
        public PaintedEffects Fx;
        public ValleyAudio Audio;
        public HomeRest Home;
        public CollectibleShelf Shelf;
        public EnemyDefinition[] spirits;
        public Material barrierMaterial, projectileMaterial;
        public SaveStore Save { get; private set; }
        public ProfileData Profile => Save.Data;

        public float Health, Stamina, Energy;
        public int MaxHealth => ProgressionRules.MaxHp(Profile);
        public float MaxStamina => 100 + Profile.upgrades.stamina * 15;
        public float MaxEnergy => 80 + Profile.upgrades.energy * 15;

        public readonly List<EnemyBrain> Enemies = new List<EnemyBrain>();
        public bool InTrial { get; private set; }
        public bool BossTrial { get; private set; }
        public string Panel { get; private set; } = "welcome";
        public bool Blocked => Panel != "" || (Brush && Brush.Drawing);
        public Sunward.Remaster.CelestialBrush Brush { get; private set; }
        public int Wave { get; private set; }
        public string Prompt { get; private set; } = "";
        public string Message { get; private set; } = "Welcome to Windflower Village.";
        public string Dialogue { get; private set; } = "";

        public GameObject[] npcObjects;
        public NpcData[] npcData;
        public Sunward.Remaster.VillageServices Services { get; private set; }
        float messageUntil = 9, breakTimer, hitUntil;
        GameObject barrier;
        bool waiting;
        int runCoins, runXp;
        static readonly string[][] waves =
        {
            new[]
            {
                "wisp",
                "reed",
                "wisp"
            },
            new[]
            {
                "reed",
                "ranged",
                "heavy",
                "wisp",
                "ranged"
            },
            new[]
            {
                "elite",
                "heavy",
                "ranged",
                "wisp",
                "reed",
                "elite"
            }
        };
        void Awake()
        {
            Save = new SaveStore();
            Brush=GetComponent<Sunward.Remaster.CelestialBrush>();if(!Brush)Brush=gameObject.AddComponent<Sunward.Remaster.CelestialBrush>();Brush.game=this;
            var life=GetComponent<Sunward.Remaster.VillageLife>();if(!life)life=gameObject.AddComponent<Sunward.Remaster.VillageLife>();life.game=this;
            Services = GetComponent<Sunward.Remaster.VillageServices>();
            if (!Services) Services = gameObject.AddComponent<Sunward.Remaster.VillageServices>();
            Services.game = this;
            Health = MaxHealth;
            Stamina = MaxStamina;
            Energy = MaxEnergy;
            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount = 1;
        }

        public void Start()
        {
            RefreshQuest();
        }

        public void RefreshQuest()
        {
            foreach (var r in FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
                foreach (string id in new[]
                {
                    "garden",
                    "mill",
                    "shrine"
                }

                )
                    if (r.name.StartsWith("OriginalQuestFlower-" + id))
                        r.enabled = !Profile.shrine && System.Array.IndexOf(Profile.windflowers, id) < 0;
                    else if (r.name.StartsWith("QuestFlower-" + id))
                        r.enabled = false;
        }

        public void WorldPrompt(string text){Prompt=text;}

        public void Notify(string text)
        {
            Message = text;
            messageUntil = Time.unscaledTime + 5;
        }

        public void SetPanel(string panel)
        {
            if(Health<=0 && panel!="result")return;
            Panel = panel;
            Cursor.visible = true;
            Cursor.lockState = CursorLockMode.None;
        }

        public void Close()
        {
            if(Health<=0){ReturnHome();return;}
            Panel = "";Player.Locked=false;
        }

        public void HitPause(float t)
        {
            hitUntil = Mathf.Max(hitUntil, Time.unscaledTime + t);
        }

        void Update()
        {
            Time.timeScale = (Panel == "pause" || (Brush && Brush.Drawing)) ? 0 : Time.unscaledTime < hitUntil ? .08f : 1;
            if (Time.unscaledTime > messageUntil)
                Message = "";
            if (Player.input.Pause.WasPressedThisFrame() && !Home.Active)
            {
                if (Panel == "result")
                    ReturnHome();
                else
                    SetPanel(Panel == "" ? "pause" : "");
            }

            if (Player.input.Journal.WasPressedThisFrame() && !InTrial && !Home.Active)
                SetPanel(Panel == "" ? "shop" : "");
            if (Blocked)
                return;
            if (Services && Services.Resting) return;
            Enemies.RemoveAll(e => !e);
            if (InTrial)
            {
                if (waiting)
                {
                    breakTimer -= Time.deltaTime;
                    if (breakTimer <= 0)
                        SpawnWave();
                }
                else if (Enemies.TrueForAll(e => e.Dead))
                {
                    Wave++;
                    if (BossTrial || Wave >= waves.Length)
                        Finish(true);
                    else
                    {
                        waiting = true;
                        breakTimer = 3.5f;
                        Health = Mathf.Min(MaxHealth, Health + 18);
                        Notify("The ink thins · prepare for the next seal");
                    }
                }

                Prompt = BossTrial?"CRIMSON HELM · beneath the village":"Trial "+(Profile.wins+1)+" · Wave "+(Wave+1)+" / 3";
                return;
            }

            if(Sunward.Remaster.LowerArena.Inside(Player.transform.position))return;
            string action = Nearest();
            Prompt = Home.Active ? "E · Wake gently" : action == "bed" ? "E · Lie down and sleep" : action == "mirror" ? "E · Memory mirror · save / load" : action == "weapons" ? "E · Weapons · fifteen divine instruments" : action == "shop" ? "E · Upgrades & blessings" : action == "arena" ? "E · Ring the Hollow Bell · enter the trial" : action.StartsWith("flower:") ? "E · Collect windflower" : action == "offering" ? "E · Windflower offering" : action.StartsWith("npc:") ? "E · Speak to " + npcData[int.Parse(action.Substring(4))].name : "Explore · follow the bridge to the market";
            if(action.StartsWith("home:"))Prompt="E · "+(action.EndsWith(":exit")?"Leave home":"Enter village home");
            if (action.StartsWith("venue:")) Prompt = Sunward.Remaster.VillageServices.Label(action,Player.transform.position);
            if (Player.input.Interact.WasPressedThisFrame() && !Home.Active)
            {
                switch (action)
                {
                    case "bed":
                        Home.Begin();
                        break;
                    case "mirror":
                        Profile.milestones.homeVisited = true;
                        SetPanel("mirror");
                        break;
                    case "shop":
                        SetPanel("shop");
                        break;
                    case "weapons":
                        SetPanel("weapons");
                        break;
                    case "arena":
                        StartTrial();
                        break;
                    case "offering":
                        OfferWindflowers();
                        break;
                    default:
                        if(action.StartsWith("home:")){Sunward.Remaster.NativeHomeRoom.Interact(this,action);break;}
                        if (action.StartsWith("venue:")) { Services.Interact(action); break; }
                        if (action.StartsWith("flower:"))
                        {
                            string id = action.Substring(7);
                            var flowers = Profile.windflowers;
                            System.Array.Resize(ref flowers, flowers.Length + 1);
                            flowers[flowers.Length - 1] = id;
                            Profile.windflowers = flowers;
                            Save.Save();
                            RefreshQuest();
                            Audio.Cue("collect");
                            Notify("Windflower found · " + flowers.Length + " / 3");
                            break;
                        }

                        if (action.StartsWith("npc:"))
                        {
                            int i = int.Parse(action.Substring(4));
                            Audio.Npc(i,npcObjects[i].transform.position);
                            Dialogue = npcData[i].name + "\n\n" + string.Join("\n\n", npcData[i].lines);
                            SetPanel("dialogue");
                        }

                        break;
                }
            }
        }

        string Nearest()
        {
            Vector3 p = Player.transform.position;
            // Interior exits remain reachable throughout the room. The old
            // outside-only radius stranded the player after the entry teleport.
            if (Sunward.Remaster.VillageServices.InDojo(p)) return "venue:dojo";
            if (Sunward.Remaster.VillageServices.InFoodHouse(p))
                return Vector3.Distance(p,Sunward.Remaster.VillageServices.Mat)<1.6f ? "venue:mat" : "venue:food";
            float best = 3.5f;
            string result = "";
            void Consider(string id, Vector3 q, float r = 2.5f)
            {
                float d = Vector3.Distance(p, q);
                if (d < Mathf.Min(r, best))
                {
                    best = d;
                    result = id;
                }
            }

            if(Sunward.Remaster.NativeHomeRoom.At(p))
                for(int i=0;i<npcObjects.Length;i++)if(npcObjects[i] && Vector3.Distance(p,npcObjects[i].transform.position)<2.1f)return "npc:"+i;
            if(Sunward.Remaster.NativeHomeRoom.NearestAction(p,out var homeAction))return homeAction;
            Consider("bed", HomeLayout.Bed, 1.9f);
            Consider("mirror", HomeLayout.Mirror, 2.1f);
            Consider("weapons", new Vector3(-6, 0, -27.5f), 3);
            Consider("shop", new Vector3(5, 0, -27.5f), 3);
            Consider("arena", new Vector3(12.8f, 0, 0));
            Consider("venue:dojo", Sunward.Remaster.VillageServices.DojoDoor, 3.5f);
            Consider("venue:food", Sunward.Remaster.VillageServices.FoodDoor, 3.5f);
            if (Sunward.Remaster.VillageServices.InFoodHouse(p)) Consider("venue:mat", Sunward.Remaster.VillageServices.Mat, 1.6f);
            Consider("venue:pond",new Vector3(GardenPond.X+3.7f,.04f,GardenPond.Z),2);
            Consider("venue:farmer", Sunward.Remaster.VillageServices.Farmer, 2.4f);
            if (!Profile.shrine)
            {
                string[] ids =
                {
                    "garden",
                    "mill",
                    "shrine"
                };
                Vector3[] points =
                {
                    new Vector3(-3, 0, -7),
                    new Vector3(-15, 0, 13),
                    new Vector3(2, 0, 12)
                };
                for (int j = 0; j < 3; j++)
                    if (System.Array.IndexOf(Profile.windflowers, ids[j]) < 0)
                        Consider("flower:" + ids[j], points[j], 1.8f);
            }

            if (result == "")
                for (int i = 0; i < npcData.Length; i++)
                    Consider("npc:" + i, npcObjects[i].transform.position, 2.4f);
            return result;
        }

        public bool Buy(string id)
        {
            if (!ProgressionRules.Buy(Profile, id))
            {
                Notify("Not enough sun coins, or this blessing is complete.");
                return false;
            }

            Save.Save();
            Health = Mathf.Min(MaxHealth, Health + 12);
            Combat.Equip();
            Audio.Cue("collect");
            return true;
        }

        public void OfferWindflowers()
        {
                        if (Profile.windflowers.Length >= 3 && !Profile.shrine)
                        {
                            Profile.shrine = true;
                            Health = MaxHealth;
                            Save.Save();
                            RefreshQuest();
                            Fx.Ring(HomeLayout.Mirror, new Color(.7f, .85f, .65f), 4);
                            Notify("Windflowers offered · permanent vitality +20");
                        }
                        else
                            Notify(Profile.shrine ? "The shrine remembers your blessing." : "Find all three windflowers in the village.");
        }

        public void StartTrial()
        {
            Audio.Cue("bell");
            Close();
            ClearEnemies();
            Sunward.Remaster.LowerArena.TrialStarted();
            InTrial = true;BossTrial=false;Player.Locked=false;
            Combat.Equip();
            Wave = 0;
            waiting = true;
            breakTimer = 2.5f;
            runCoins = runXp = 0;
            Health = MaxHealth;
            Stamina = MaxStamina;
            Energy = MaxEnergy;
            Combat.Cancel();
            Player.Teleport(new Vector3(22, 0, 0));
            Player.transform.rotation = Quaternion.Euler(0, 90, 0);
            barrier = Fx.Boundary(new Vector3(35, 0, 0), 17.8f);
            Notify("Three normal enemy waves. Victory opens the depths where Crimson Helm waits.");
        }

        public void StartBossTrial()
        {
            if(InTrial || Health<=0 || !Sunward.Remaster.LowerArena.Inside(Player.transform.position))return;
            var spec=System.Array.Find(spirits,e=>e.id=="boss");
            if(!spec){Notify("Crimson Helm definition unavailable");return;}
            ClearEnemies();BossTrial=InTrial=true;waiting=false;Wave=0;runCoins=runXp=0;
            Health=MaxHealth;Stamina=MaxStamina;Energy=MaxEnergy;Combat.Cancel();Combat.Equip();
            var obj=new GameObject(spec.title);Vector3 p=Sunward.Remaster.LowerArena.Centre+new Vector3(16,1,8);
            if(Sunward.Remaster.LowerArena.Height(p,out var y))p.y=y;
            obj.transform.position=p;var brain=obj.AddComponent<EnemyBrain>();brain.Init(this,spec);Enemies.Add(brain);
            Notify("Crimson Helm · dodge the charge, jump the slam, slash the ink bolts");
        }

        void SpawnWave()
        {
            ClearEnemies();
            foreach (string kind in waves[Wave])
            {
                var spec = System.Array.Find(spirits, e => e.id == kind);
                if (!spec)
                {
                    Notify("Missing spirit definition: " + kind);
                    Finish(false);
                    return;
                }

                float a = Enemies.Count / (float)waves[Wave].Length * Mathf.PI * 2;
                var obj = new GameObject(spec.title);
                obj.transform.position = new Vector3(35 + Mathf.Sin(a) * 9, 0, Mathf.Cos(a) * 9);
                var brain = obj.AddComponent<EnemyBrain>();
                brain.Init(this, spec);
                Enemies.Add(brain);
            }

            waiting = false;
            Notify("Wave " + (Wave + 1) + " · break the seal");
        }

        void ClearEnemies()
        {
            foreach (var e in Enemies)
                if (e)
                    Destroy(e.gameObject);
            Enemies.Clear();
            foreach (var b in FindObjectsByType<InkProjectile>(FindObjectsSortMode.None))
                Destroy(b.gameObject);
        }

        public void Reward(EnemyBrain e)
        {
            int coins = Mathf.RoundToInt(e.definition.reward * (1 + Profile.wins * .15f)), xp = Mathf.RoundToInt(e.definition.xp * Mathf.Sqrt(1 + Profile.wins * .1f));
            Profile.coins += coins;
            Profile.xp += xp;
            Profile.kills++;
            runCoins += coins;
            runXp += xp;
            Save.Save();
            Notify("+" + coins + " sun coins · +" + xp + " XP · saved");
        }

        public void Hurt(float damage, Vector3 direction)
        {
            if (!InTrial || Player.Invulnerable > 0 || Home.Active)
                return;
            Health = Mathf.Max(0, Health - damage);
            Player.Invulnerable = .70f;
            Player.Push(direction * .40f);
            Fx.Impact(Player.transform.position + Vector3.up * .6f, new Color(.7f, .17f, .17f));
            Audio.Cue("hurt");
            if (Health <= 0)
                Finish(false);
        }

        public void Finish(bool win)
        {
            if (!InTrial)
                return;
            bool bossEncounter=BossTrial;InTrial=false;BossTrial=false;waiting=false;
            Player.Locked=Health<=0;
            Combat.Equip();
            if (barrier)
            {
                Destroy(barrier.GetComponent<MeshFilter>().sharedMesh);
                Destroy(barrier);
            }

            if (win)
            {
                if(bossEncounter)Profile.bossWins++;else Profile.wins++;
                Profile.coins += bossEncounter?150:65 + Profile.wins * 10;
                Profile.xp += 100;
                Profile.milestones.hollowBell = true;
            }
            else
                Profile.defeats++;
            Save.Save();
            Combat.Cancel();
            Dialogue = win ? (bossEncounter?"Crimson Helm falls.\n\nThe depths are quiet.":"The upper trial is complete.\n\nThe seal below has opened.") : "Your spirit endures.\n\nEarned currency and permanent growth are safe.";
            Dialogue += "\n\n" + runCoins + " combat coins · " + runXp + " combat XP";
            if(!bossEncounter)Sunward.Remaster.LowerArena.TrialFinished(win);
            if(!win)ClearEnemies();
            if(win && !bossEncounter)Dialogue+="\n\nThe centre floor breaks open. Crimson Helm waits below, or you can return home.";
            SetPanel("result");
        }

        public void ReturnHome()
        {
            ClearEnemies();
            InTrial = false;BossTrial=false;waiting=false;Player.Locked=false;
            if(barrier){Destroy(barrier.GetComponent<MeshFilter>().sharedMesh);Destroy(barrier);}
            Combat.Cancel();
            Combat.Equip();
            Player.Teleport(new Vector3(-34, valley.Height(new Vector3(-34, 0, -22)), -22));
            Player.transform.rotation = Quaternion.identity;
            Health = MaxHealth;
            Stamina = MaxStamina;
            Energy = MaxEnergy;
            Close();
            Notify("Welcome home · the next trial grows stronger.");
        }

        public void Projectile(Vector3 position, Vector3 direction, float damage)
        {
            var obj = new GameObject("Painted ink bolt");
            obj.transform.position = position;
            Fx.AttachProjectile(obj);
            var bolt = obj.AddComponent<InkProjectile>();
            bolt.game = this;
            bolt.direction = direction;
            bolt.damage = damage;
        }

        void OnApplicationQuit()
        {
            if (Save != null)
                Save.Save();
            Time.timeScale = 1;
        }
    }
}
