using UnityEngine;
using UnityEngine.InputSystem;

namespace Sunward
{
    public sealed class ScrollUI : MonoBehaviour
    {
        public GameFlow game;
        GUIStyle body, title, small, button;
        Texture2D paper, red;
        Vector2 scroll;
        string importText = "";
        bool importOpen;
        int selected, lastCount, buttonCount;
        bool activate;
        float nextNavigation;
        string lastPanel = "";
        void Update()
        {
            if (!game || !game.Blocked)
                return;
            if (lastPanel != game.Panel)
            {
                selected = 0;
                lastPanel = game.Panel;
            }

            var pad = Gamepad.current;
            if (pad == null)
                return;
            if (pad.buttonSouth.wasPressedThisFrame)
                activate = true;
            float y = Mathf.Abs(pad.dpad.y.ReadValue()) > .2f ? pad.dpad.y.ReadValue() : pad.leftStick.y.ReadValue();
            if (Time.unscaledTime > nextNavigation && Mathf.Abs(y) > .5f)
            {
                selected = Mathf.Clamp(selected + (y > 0 ? -1 : 1), 0, Mathf.Max(0, lastCount - 1));
                nextNavigation = Time.unscaledTime + .20f;
            }
        }

        bool Button(string label, GUIStyle style)
        {
            int index = buttonCount++;
            Color old = GUI.backgroundColor;
            if (index == selected && Gamepad.current != null)
                GUI.backgroundColor = new Color(.7f, .8f, .6f);
            bool click = GUILayout.Button((index == selected && Gamepad.current != null ? "› " : "") + label, style);
            GUI.backgroundColor = old;
            if (activate && index == selected && Event.current.type == EventType.Repaint)
            {
                activate = false;
                return true;
            }

            return click;
        }

        Texture2D Tex(Color c)
        {
            bool parchment = c.a < 1;
            int size = parchment ? 256 : 1;
            var t = new Texture2D(size, size)
            {
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            var random = new System.Random(197);
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float noise = parchment ? ((float)random.NextDouble() - .5f) * .035f : 0;
                    float edge = parchment ? Mathf.Min(Mathf.Min(x, size - 1 - x), Mathf.Min(y, size - 1 - y)) : 10;
                    float ripple = parchment ? 1.5f + Mathf.Sin(x * .14f + y * .09f) * 1.2f : 0;
                    float alpha = parchment ? Mathf.Clamp01((edge - ripple) / 2) : 1;
                    float ink = parchment ? 1 - Mathf.Exp(-Mathf.Pow((edge - 4 - ripple) / 1.1f, 2)) * .24f : 1;
                    t.SetPixel(x, y, new Color((c.r + noise) * ink, (c.g + noise) * ink, (c.b + noise) * ink, c.a * alpha));
                }

            t.Apply();
            return t;
        }

        void Styles()
        {
            if (body != null)
                return;
            paper = Tex(new Color(.91f, .86f, .73f, .95f));
            red = Tex(new Color(.64f, .19f, .15f));
            body = new GUIStyle(GUI.skin.label)
            {
                fontSize = 17,
                wordWrap = true
            };
            body.normal.textColor = new Color(.20f, .19f, .16f);
            body.font = Font.CreateDynamicFontFromOSFont(new[] { "Georgia", "Times New Roman", "Liberation Serif" }, 18);
            title = new GUIStyle(body)
            {
                fontSize = 30,
                fontStyle = FontStyle.Bold
            };
            small = new GUIStyle(body)
            {
                fontSize = 13
            };
            button = new GUIStyle(GUI.skin.button)
            {
                fontSize = 16,
                wordWrap = true,
                padding = new RectOffset(12, 12, 10, 10)
            };
            button.normal.textColor = body.normal.textColor;
        }

        void OnGUI()
        {
            if (!game || game.Save == null)
                return;
            Styles();
            buttonCount = 0;
            float scale = Mathf.Clamp(Screen.height / 900f, .65f, 1.6f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1));
            float w = Screen.width / scale, h = Screen.height / scale;
            DrawPaper(new Rect(20, 18, 320, 132));
            GUILayout.BeginArea(new Rect(34, 24, 292, 120));
            GUILayout.Label("SUNWARD · AMATERASU", title);
            GUILayout.Label("Vitality " + Mathf.CeilToInt(game.Health) + " / " + game.MaxHealth, body);
            Bar(280, game.Health / game.MaxHealth);
            GUILayout.Label("Stamina " + (int)game.Stamina + " · Ink " + (int)game.Energy, small);
            GUILayout.EndArea();
            DrawPaper(new Rect(w - 350, 18, 330, 112));
            GUILayout.BeginArea(new Rect(w - 336, 26, 308, 100));
            GUILayout.Label(game.Profile.coins + " sun coins · Level " + ProgressionRules.Level(game.Profile), body);
            GUILayout.Label(game.Profile.equipped == "spear" ? "REED SPEAR" : "SUNDIAL FLAME", body);
            GUILayout.Label("Power " + ProgressionRules.Power(game.Profile).ToString("0") + " · " + game.Save.Status, small);
            GUILayout.EndArea();
            var boss = game.Enemies.Find(e => e && !e.Dead && e.definition.id == "boss");
            if (boss)
            {
                DrawPaper(new Rect(w * .5f - 250, 20, 500, 64));
                GUILayout.BeginArea(new Rect(w * .5f - 236, 26, 472, 58));
                GUILayout.Label("KUROGANE · THE HOLLOW BELL · " + (boss.Phase2 ? "PHASE II" : "PHASE I"), body);
                Bar(470, boss.Hp / boss.MaxHp);
                GUILayout.EndArea();
            }

            DrawPaper(new Rect(20, h - 93, w - 40, 72));
            GUI.Label(new Rect(34, h - 88, w - 68, 28), game.Message != "" ? game.Message : game.Prompt, body);
            GUI.Label(new Rect(34, h - 57, w - 68, 28), game.InTrial ? "LMB / J light · RMB / L heavy · hold to charge · Q switch weapon · B bark · K dodge · Space jump · Esc pause" : "WASD move · Shift sprint · Ctrl walk · Space jump · E interact · Tab forge · Weapons stay on the home wall outside trials · Middle drag orbit", small);
            if (game.InTrial && GUI.Button(new Rect(w - 160, h - 140, 140, 34), "RETREAT", button))
                game.Finish(false);
            if (!game.Blocked)
                return;
            float pw = Mathf.Min(700, w - 40);
            var panel = new Rect((w - pw) * .5f, 150, pw, h - 270);
            DrawPaper(panel);
            GUILayout.BeginArea(new Rect(panel.x + 26, panel.y + 22, panel.width - 52, panel.height - 44));
            scroll = GUILayout.BeginScrollView(scroll);
            switch (game.Panel)
            {
                case "welcome":
                    GUILayout.Label("A light in the mist.", title);
                    GUILayout.Label("Explore the painted valley, cross its bridges, visit Taro for permanent blessings, then challenge the Hollow Bell. Rewards survive victory and defeat.\n\nThis separate Unity port reuses the existing wolf and V3 town. Controller: left stick moves, right stick looks, A jumps, B dodges, X interacts, RB/RT attack, LB barks, D-pad right switches weapons.", body);
                    if (Button("ENTER WINDFLOWER →", button))
                        game.Close();
                    break;
                case "shop":
                    Shop();
                    break;
                case "mirror":
                    GUILayout.Label("The Memory Mirror", title);
                    GUILayout.Label("Currency, experience, weapons, upgrades, milestones and collectibles share one backed-up Unity save.\n" + game.Save.Path, small);
                    if (Button("INSCRIBE MEMORY · SAVE", button))
                    {
                        game.Profile.milestones.homeVisited = true;
                        game.Save.Save();
                        game.Notify(game.Save.Status);
                    }

                    if (Button("LOAD SAVED MEMORY", button))
                    {
                        if (game.Save.Reload())
                        {
                            game.Combat.Equip();
                            game.Health = game.MaxHealth;
                            game.Shelf.Refresh();
                            game.RefreshQuest();
                        }

                        game.Notify(game.Save.Status);
                    }

                    if (Button("IMPORT THREE.JS SAVE JSON", button))
                        importOpen = !importOpen;
                    if (importOpen)
                    {
                        GUILayout.Label("In your old game’s browser console: copy(localStorage.getItem('sunward.rpg.v2')). Paste below. Existing Unity data is backed up on successful import.", small);
                        importText = GUILayout.TextArea(importText, GUILayout.Height(110));
                        if (Button("VALIDATE & IMPORT", button))
                        {
                            bool ok = game.Save.Import(importText);
                            if (ok)
                            {
                                game.Combat.Equip();
                                game.Health = game.MaxHealth;
                                game.Shelf.Refresh();
                                game.RefreshQuest();
                            }

                            game.Notify(ok ? "Browser progress imported and saved." : "Import rejected; current progress kept.");
                        }
                    }

                    break;
                case "pause":
                    GUILayout.Label("A moment of stillness.", title);
                    if (game.InTrial && Button("RETREAT · KEEP EARNED REWARDS", button))
                        game.Finish(false);
                    if (!game.InTrial && Button("RETURN HOME · KEEP PROGRESS", button))
                        game.ReturnHome();
                    GUILayout.Label("Quality presets change shadows, MSAA and render scale. Performance depends on your hardware.", body);
                    if (Button("QUALITY · HIGH", button))
                        Quality(true);
                    if (Button("QUALITY · LIGHTWEIGHT", button))
                        Quality(false);
                    if (Button("MUTE / UNMUTE", button))
                        AudioListener.volume = AudioListener.volume > 0 ? 0 : 1;
                    break;
                case "result":
                    GUILayout.Label(game.Dialogue, title);
                    if (Button("RETURN HOME →", button))
                        game.ReturnHome();
                    break;
                default:
                    GUILayout.Label(game.Dialogue, body);
                    break;
            }

            if (game.Panel != "result" && game.Panel != "welcome" && Button("RETURN →", button))
                game.Close();
            GUILayout.EndScrollView();
            GUILayout.EndArea();
            lastCount = buttonCount;
            selected = Mathf.Clamp(selected, 0, Mathf.Max(0, lastCount - 1));
        }

        void Shop()
        {
            GUILayout.Label("Taro · weapons & blessings", title);
            GUILayout.Label(game.Profile.coins + " coins · permanent upgrades survive defeat.", body);
            if (System.Array.IndexOf(game.Profile.owned, "sundial") < 0)
            {
                if (Button("UNLOCK SUNDIAL FLAME · 110 coins", button))
                    game.Buy("unlock-sundial");
            }
            else if (Button("EQUIP " + (game.Profile.equipped == "spear" ? "SUNDIAL FLAME" : "REED SPEAR"), button))
            {
                game.Profile.equipped = game.Profile.equipped == "spear" ? "sundial" : "spear";
                game.Save.Save();
                game.Combat.Equip();
            }

            foreach (string id in ProgressionRules.Upgrades)
                if (Button(id.ToUpperInvariant() + " · level " + game.Profile.upgrades.Get(id) + " · " + ProgressionRules.Cost(game.Profile, id) + " coins", button))
                    game.Buy(id);
        }

        void DrawPaper(Rect r)
        {
            GUI.DrawTexture(r, paper);
        }

        void Bar(float width, float value)
        {
            Rect r = GUILayoutUtility.GetRect(width, 7);
            GUI.DrawTexture(new Rect(r.x, r.y, r.width * Mathf.Clamp01(value), r.height), red);
        }

        void Quality(bool high)
        {
            QualitySettings.shadows = high ? ShadowQuality.All : ShadowQuality.Disable;
            QualitySettings.lodBias = high ? 1.5f : .65f;
            var urp = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline as UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset;
            if (urp)
            {
                urp.renderScale = high ? 1 : .75f;
                urp.msaaSampleCount = high ? 4 : 1;
                urp.shadowDistance = high ? 80 : 35;
                urp.shadowCascadeCount = high ? 4 : 2;
            }

            game.Notify(high ? "High quality" : "Lightweight quality");
        }
    }
}
