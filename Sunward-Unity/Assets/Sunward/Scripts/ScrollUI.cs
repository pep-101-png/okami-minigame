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

        void Styles()
        {
            if (body != null)
                return;
            paper = Resources.Load<Texture2D>("Okami/UI/Paper");
            red = Resources.Load<Texture2D>("Okami/UI/Ink");
            body = new GUIStyle(GUI.skin.label)
            {
                fontSize = 19,
                wordWrap = true
            };
            body.normal.textColor = new Color(.075f, .055f, .035f, 1);
            body.font = Font.CreateDynamicFontFromOSFont(new[] { "Georgia", "Times New Roman", "Liberation Serif" }, 18);
            title = new GUIStyle(body)
            {
                fontSize = 27,
                fontStyle = FontStyle.Bold
            };
            small = new GUIStyle(body)
            {
                fontSize = 16
            };
            button = new GUIStyle(GUI.skin.button)
            {
                fontSize = 19,
                font = body.font,
                wordWrap = true,
                padding = new RectOffset(12, 12, 10, 10)
            };
            // Never inherit translucent/dark editor-skin button states. Every
            // panel and control uses the same clean original paper and ink.
            foreach (var style in new[] { body, title, small, button })
                foreach (var state in new[] { style.normal, style.hover, style.active, style.focused,
                    style.onNormal, style.onHover, style.onActive, style.onFocused })
                {
                    state.textColor = body.normal.textColor;
                    if (style == button) state.background = paper;
                }
            button.margin = new RectOffset(0, 0, 5, 5);
        }

        void OnGUI()
        {
            if (!game || game.Save == null)
                return;
            Styles();
            GUI.color = Color.white;
            GUI.contentColor = Color.white;
            GUI.backgroundColor = Color.white;
            buttonCount = 0;
            float scale = Mathf.Clamp(Mathf.Min(Screen.height / 900f, Screen.width / 1000f), .75f, 1.6f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1));
            float w = Screen.width / scale, h = Screen.height / scale;
            DrawPaper(new Rect(20, 18, 320, 132));
            GUILayout.BeginArea(new Rect(34, 24, 292, 120));
            GUILayout.Label("SUNWARD · AMATERASU", small);
            GUILayout.Label("Vitality " + Mathf.CeilToInt(game.Health) + " / " + game.MaxHealth, body);
            Bar(280, game.Health / game.MaxHealth);
            GUILayout.Label("Stamina " + (int)game.Stamina + " · Ink " + (int)game.Energy, small);
            GUILayout.EndArea();
            DrawPaper(new Rect(w - 350, 18, 330, 112));
            GUILayout.BeginArea(new Rect(w - 336, 26, 308, 100));
            GUILayout.Label(game.Profile.coins + " sun coins · Level " + ProgressionRules.Level(game.Profile), body);
            GUILayout.Label(game.Combat.EquippedTitle, body);
            GUILayout.Label("Power " + ProgressionRules.Power(game.Profile).ToString("0") + " · " + game.Save.Status, small);
            GUILayout.EndArea();
            var boss = game.Enemies.Find(e => e && !e.Dead && e.definition.id == "boss");
            if (boss)
            {
                DrawPaper(new Rect(w * .5f - 250, 20, 500, 64));
                GUILayout.BeginArea(new Rect(w * .5f - 236, 26, 472, 58));
                GUILayout.Label("CRIMSON HELM · THE HOLLOW BELL · " + (boss.Phase2 ? "PHASE II" : "PHASE I"), body);
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
                    GUILayout.Label("Explore the painted valley, cross its bridges, visit Taro for weapons and Hana for permanent blessings, then challenge the Hollow Bell. Visit the training hall or rest at the food house. Rewards survive victory and defeat.\n\nController: left stick moves, right stick looks, A jumps, B dodges, X interacts, RB/RT attack, LB barks, D-pad right switches owned weapons.", body);
                    if (Button("ENTER WINDFLOWER →", button))
                        game.Close();
                    break;
                case "shop":
                    Shop();
                    break;
                case "weapons":
                    Weapons();
                    break;
                case "mirror":
                    GUILayout.Label("The Memory Mirror", title);
                    if(!game.Profile.shrine && Button("OFFER THREE WINDFLOWERS · VITALITY BLESSING",button))game.OfferWindflowers();
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
                    if(game.Health>0 && game.Profile.wins>0 && Button("EXPLORE THE LOWER ARENA →",button)){game.Close();game.Notify("Jump through the broken centre floor · the mirror below returns you home.");}
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
            GUILayout.Label("Hana · upgrades & blessings", title);
            GUILayout.Label(game.Profile.coins + " coins · permanent upgrades survive defeat.", body);
            if (Button("TARO'S WEAPON CATALOGUE →", button)) game.SetPanel("weapons");
            foreach (string id in ProgressionRules.Upgrades)
            {
                string label=id=="spear"?"GLAIVE MASTERY":id=="sundial"?"MIRROR & ROSARY MASTERY":id.ToUpperInvariant();
                if (Button(label + " · level " + game.Profile.upgrades.Get(id) + " · " + ProgressionRules.Cost(game.Profile, id) + " coins", button))
                    game.Buy(id);
            }
        }
        void Weapons()
        {
            GUILayout.Label("Taro · divine instruments", title);
            GUILayout.Label(game.Profile.coins + " coins · purchased weapons stay in your save. Q cycles owned weapons in the arena.", body);
            foreach (var entry in Sunward.Remaster.OriginalWeaponCatalog.All)
            {
                bool owned = Sunward.Remaster.OriginalWeaponCatalog.Owns(game.Profile, entry.id);
                string label = entry.title + " · " + entry.family + (owned ? game.Profile.equipped == entry.id ? " · EQUIPPED" : " · EQUIP" : " · " + entry.cost + " coins");
                if (!Button(label, button)) continue;
                if (owned) { game.Profile.equipped = entry.id; game.Save.Save(); game.Combat.Equip(); }
                else game.Buy("weapon:" + entry.id);
            }
        }

        void DrawPaper(Rect r)
        {
            // Preserve the paper's aspect and opaque pixels, rather than
            // stretching a small crop across a portrait-shaped menu.
            Color old = GUI.color;
            GUI.color = Color.white;
            if (paper) GUI.DrawTexture(r, paper, ScaleMode.StretchToFill, false);
            GUI.color = old;
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
