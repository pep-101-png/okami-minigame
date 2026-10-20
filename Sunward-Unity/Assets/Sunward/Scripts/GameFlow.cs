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
        public string Panel { get; private set; } = "welcome";
        public bool Blocked => Panel != "";
        public int Wave { get; private set; }
        public string Prompt { get; private set; } = "";
        public string Message { get; private set; } = "Welcome to Windflower Village.";
        public string Dialogue { get; private set; } = "";

        public GameObject[] npcObjects;
        public NpcData[] npcData;
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
            },
            new[]
            {
                "boss"
            }
        };
        void Awake()
        {
            Save = new SaveStore();
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
            foreach (var r in FindObjectsByType<MeshRenderer>())
                foreach (string id in new[]
                {
                    "garden",
                    "mill",
                    "shrine"
                }

                )
                    if (r.name.StartsWith("QuestFlower-" + id))
                        r.enabled = !Profile.shrine && System.Array.IndexOf(Profile.windflowers, id) < 0;
        }

        public void Notify(string text)
        {
            Message = text;
            messageUntil = Time.unscaledTime + 5;
        }

        public void SetPanel(string panel)
        {
            Panel = panel;
            Cursor.visible = true;
            Cursor.lockState = CursorLockMode.None;
        }

        public void Close()
        {
            Panel = "";
        }

        public void HitPause(float t)
        {
            hitUntil = Mathf.Max(hitUntil, Time.unscaledTime + t);
        }

        void Update()
        {
            Time.timeScale = Panel == "pause" ? 0 : Time.unscaledTime < hitUntil ? .08f : 1;
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
                    if (Wave >= waves.Length)
                        Finish(true);
                    else
                    {
                        waiting = true;
                        breakTimer = 3.5f;
                        Health = Mathf.Min(MaxHealth, Health + 18);
                        Notify("The ink thins · prepare for the next seal");
                    }
                }

                Prompt = "Trial " + (Profile.wins + 1) + " · " + (Wave == 3 ? "KUROGANE" : ("Wave " + (Wave + 1) + " / 3"));
                return;
            }

            string action = Nearest();
            Prompt = Home.Active ? "E · Wake gently" : action == "bed" ? "E · Lie down and sleep" : action == "mirror" ? "E · Memory mirror · save / load" : action == "shop" ? "E · Taro · weapons & blessings" : action == "arena" ? "E · Enter the Hollow Bell trial" : action.StartsWith("flower:") ? "E · Collect windflower" : action == "offering" ? "E · Windflower offering" : action.StartsWith("npc:") ? "E · Speak to " + npcData[int.Parse(action.Substring(4))].name : "Explore · follow the bridge to the market";
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
                    case "arena":
                        StartTrial();
                        break;
                    case "offering":
                        if (Profile.windflowers.Length >= 3 && !Profile.shrine)
                        {
                            Profile.shrine = true;
                            Health = MaxHealth;
                            Save.Save();
                            RefreshQuest();
                            Fx.Ring(new Vector3(0, 0, 20), new Color(.7f, .85f, .65f), 4);
                            Notify("Windflowers offered · permanent vitality +20");
                        }
                        else
                            Notify(Profile.shrine ? "The shrine remembers your blessing." : "Find all three windflowers in the village.");
                        break;
                    default:
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
            float best = 2.5f;
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

            Consider("bed", HomeLayout.Bed, 1.9f);
            Consider("mirror", HomeLayout.Mirror, 2.1f);
            Consider("shop", npcObjects != null && npcObjects.Length > 1 && npcObjects[1] ? npcObjects[1].transform.position : new Vector3(3, 0, 0));
            Consider("arena", new Vector3(12.8f, 0, 0));
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

            Consider("offering", new Vector3(0, 0, 20), 2);
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

        public void StartTrial()
        {
            Close();
            ClearEnemies();
            InTrial = true;
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
            barrier = new GameObject("Hollow Bell · calligraphic seal");
            var mesh = new Mesh
            {
                name = "Hollow Bell arena barrier"
            };
            const int N = 160, K = 6;
            var v = new Vector3[(N + 1) * (K + 1)];
            var uv = new Vector2[v.Length];
            var index = new int[N * K * 6];
            int n = 0;
            for (int i = 0; i <= N; i++)
                for (int j = 0; j <= K; j++)
                {
                    float a = i / (float)N * Mathf.PI * 2;
                    int k = i * (K + 1) + j;
                    float radius = 17.8f + Mathf.Sin(a * 13 + j * .4f) * .10f;
                    v[k] = new Vector3(35 + Mathf.Sin(a) * radius, j * .64f, Mathf.Cos(a) * radius);
                    uv[k] = new Vector2(i / (float)N * 20, j / (float)K);
                    if (i < N && j < K)
                    {
                        index[n++] = k;
                        index[n++] = k + 1;
                        index[n++] = k + K + 1;
                        index[n++] = k + 1;
                        index[n++] = k + K + 2;
                        index[n++] = k + K + 1;
                    }
                }

            MeshSafety.Validate("Hollow Bell arena barrier", v, index);
            mesh.vertices = v;
            mesh.uv = uv;
            mesh.triangles = index;
            mesh.RecalculateNormals();
            barrier.AddComponent<MeshFilter>().sharedMesh = mesh;
            barrier.AddComponent<MeshRenderer>().sharedMaterial = barrierMaterial;
            Notify("Three waves, then Kurogane. Every earned reward is permanent.");
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
            Notify(Wave == 3 ? "Kurogane awakens · jump the slam, dodge the charge and ink fan." : "Wave " + (Wave + 1) + " · break the seal");
        }

        void ClearEnemies()
        {
            foreach (var e in Enemies)
                if (e)
                    Destroy(e.gameObject);
            Enemies.Clear();
            foreach (var b in FindObjectsByType<InkProjectile>())
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
            InTrial = false;
            Combat.Equip();
            if (barrier)
            {
                Destroy(barrier.GetComponent<MeshFilter>().sharedMesh);
                Destroy(barrier);
            }

            if (win)
            {
                Profile.wins++;
                Profile.coins += 65 + Profile.wins * 10;
                Profile.xp += 100;
                Profile.milestones.hollowBell = true;
            }
            else
                Profile.defeats++;
            Save.Save();
            Combat.Cancel();
            Dialogue = win ? "Light returns.\n\nKurogane’s seal dissolves." : "Your spirit endures.\n\nEarned currency and permanent growth are safe.";
            Dialogue += "\n\n" + runCoins + " combat coins · " + runXp + " combat XP";
            SetPanel("result");
        }

        public void ReturnHome()
        {
            ClearEnemies();
            InTrial = false;
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
            var line = obj.AddComponent<LineRenderer>();
            line.sharedMaterial = projectileMaterial;
            line.useWorldSpace = false;
            line.positionCount = 3;
            line.SetPositions(new[] { -direction * .4f, Vector3.zero, direction * .35f });
            line.startWidth = .12f;
            line.endWidth = 0;
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
