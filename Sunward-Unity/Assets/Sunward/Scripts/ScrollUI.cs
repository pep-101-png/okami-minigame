using UnityEngine;
using UnityEngine.InputSystem;

namespace Sunward
{
    public sealed class ScrollUI : MonoBehaviour
    {
        public GameFlow game;
        GUIStyle body, title, small, button;
        Texture2D paper, red,hintInk,scrollRoll;
        Vector2 scroll;
        string importText = "";
        bool importOpen;
        int selected, lastCount, buttonCount,weaponPage;
        float contentWidth=600;
        bool activate;
        float nextNavigation;
        string lastPanel = "";
        void Update()
        {
            if(game && game.CinematicActive){activate=false;return;}
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
            string text=(index==selected && Gamepad.current!=null?"› ":"")+label;
            float height=Mathf.Max(46,Mathf.Ceil(text.Length*13f/Mathf.Max(200,contentWidth-35))*27+16);
            var rect=GUILayoutUtility.GetRect(contentWidth,height);
            if(hintInk){GUI.color=new Color(.42f,.12f,.055f,index==selected?.22f:.10f);GUI.DrawTexture(rect,hintInk);GUI.color=Color.white;}
            Sunward.Remaster.InkText.Draw(text,new Rect(rect.x+14,rect.y+7,rect.width-28,rect.height-8),30,new Color(.16f,.07f,.035f,1));
            bool click=GUI.Button(rect,"",GUIStyle.none);
            GUI.backgroundColor = old;
            if (activate && index == selected && Event.current.type == EventType.Repaint)
            {
                activate = false;
                return true;
            }

            return click;
        }

        void Label(string text,GUIStyle style)
        {
            float em=style==title?38:style==small?27:31;
            int lines=0;foreach(var line in text.Split('\n'))lines+=Mathf.Max(1,Mathf.CeilToInt(line.Length*em*.47f/Mathf.Max(100,contentWidth-10)));
            var rect=GUILayoutUtility.GetRect(contentWidth,lines*em*.98f+8);
            Sunward.Remaster.InkText.Draw(text,rect,em,style.normal.textColor);
        }
        bool InkButton(Rect rect,string text)
        {Sunward.Remaster.InkText.Draw(text,rect,29,new Color(.3f,.09f,.045f,1));return GUI.Button(rect,"",GUIStyle.none);}
        void Styles()
        {
            if (body != null)
                return;
            paper = Resources.Load<Texture2D>("Okami/UI/MenuScrollBody");
            scrollRoll=Resources.Load<Texture2D>("Okami/UI/MenuScrollRoll");
            red = Resources.Load<Texture2D>("Okami/UI/Ink");hintInk=Resources.Load<Texture2D>("Okami/UI/HintInk");
            body = new GUIStyle(GUI.skin.label)
            {
                fontSize = 19,
                wordWrap = true
            };
            body.normal.textColor = new Color(.075f, .055f, .035f, 1);
            // Visible lettering is drawn exclusively from the original glyph atlas.
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
            if (!game || game.Save == null || game.CinematicActive || (game.Brush && game.Brush.Drawing))
                return;
            if(game.Presentation && (game.Presentation.Title || game.Presentation.Dialogue))return;
            Styles();
            GUI.color = Color.white;
            GUI.contentColor = Color.white;
            GUI.backgroundColor = Color.white;
            buttonCount = 0;
            float scale = Mathf.Clamp(Mathf.Min(Screen.height / 900f, Screen.width / 1000f), .75f, 1.6f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1));
            float w = Screen.width / scale, h = Screen.height / scale;
            DrawPaper(new Rect(20, 18, 320, 178));
            contentWidth=292;GUILayout.BeginArea(new Rect(34, 24, 292, 165));
            Label("SUNWARD · AMATERASU", small);
            Label("Vitality " + Mathf.CeilToInt(game.Health) + " / " + game.MaxHealth, body);
            Bar(280, game.Health / game.MaxHealth);
            Label("Stamina " + (int)game.Stamina + " · Ink " + (int)game.Energy, small);
            GUILayout.EndArea();
            DrawPaper(new Rect(w - 350, 18, 330, 170));
            contentWidth=308;GUILayout.BeginArea(new Rect(w - 336, 26, 308, 158));
            Label(game.Profile.coins + " sun coins · Level " + ProgressionRules.Level(game.Profile), body);
            Label(game.Combat.EquippedTitle, body);
            Label("Power " + ProgressionRules.Power(game.Profile).ToString("0"), small);
            GUILayout.EndArea();
            var boss = game.Enemies.Find(e => e && !e.Dead && e.definition.id == "boss");
            if (boss)
            {
                DrawPaper(new Rect(w * .5f - 250, 20, 500, 64));
                contentWidth=472;GUILayout.BeginArea(new Rect(w * .5f - 236, 26, 472, 88));
                Label("CRIMSON HELM · THE HOLLOW BELL · " + ("PHASE "+boss.BossPhase+" / 3 · "+(boss.BossRising?"TRANSFORMING":boss.BossPhase==1?"BURNING ARMOUR":boss.FlamePhase?"SKELETAL INFERNO":"ARMOUR SHATTERED")), body);
                Bar(470, boss.Hp / boss.MaxHp);
                GUILayout.EndArea();
            }

            string hint=game.Prompt.StartsWith("E ") || game.Prompt.StartsWith("E ·") || game.Prompt.StartsWith("F ")?game.Prompt:game.Message;
            if(!string.IsNullOrEmpty(hint))
            {
                float hw=Mathf.Min(w*.76f,Mathf.Max(280,hint.Length*11));
                if(hintInk){GUI.color=new Color(.04f,.025f,.015f,.42f);GUI.DrawTexture(new Rect((w-hw)*.5f-18,h-86,hw+36,61),hintInk);GUI.color=Color.white;}
                Sunward.Remaster.InkText.Draw(hint,new Rect((w-hw)*.5f,h-76,hw,55),30,new Color(1,.95f,.82f,.78f));
            }
            if(game.Spa && game.Spa.Bonus>0)Sunward.Remaster.InkText.Draw("Spring blessing +25 · "+Mathf.CeilToInt(game.Spa.Remaining/60)+" min",new Rect(28,200,360,55),28,new Color(.55f,1,.65f,.8f));
            if (game.InTrial && InkButton(new Rect(w - 160, h - 140, 140, 34), "RETREAT"))
                game.Finish(false);
            var festivalChallenge=game.GetComponent<Sunward.Remaster.FestivalChallenges>();
            if(festivalChallenge && festivalChallenge.Active)
            {
                DrawPaper(new Rect(w*.5f-220,92,440,60));
                Sunward.Remaster.InkText.Draw(festivalChallenge.Status,new Rect(w*.5f-206,100,412,46),28,new Color(.1f,.06f,.03f,1));
            }
            if (game.Panel=="")
                return;
            float pw = Mathf.Min(700, w - 40);
            var panel = new Rect((w - pw) * .5f, 150, pw, h - 270);
            DrawPaper(panel);contentWidth=panel.width-75;
            GUILayout.BeginArea(new Rect(panel.x + 26, panel.y + 22, panel.width - 52, panel.height - 44));
            scroll = GUILayout.BeginScrollView(scroll);
            switch (game.Panel)
            {
                case "shop":
                    Shop();
                    break;
                case "weapons":
                    Weapons();
                    break;
                case "mirror":
                    Label("The Memory Mirror", title);
                    if(!game.Profile.shrine && Button("OFFER THREE WINDFLOWERS · VITALITY BLESSING",button))game.OfferWindflowers();
                    Label("Currency, experience, weapons, upgrades, milestones and collectibles share one backed-up Unity save.\n" + game.Save.Path, small);
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
                        Label("In your old game’s browser console: copy(localStorage.getItem('sunward.rpg.v2')). Paste below. Existing Unity data is backed up on successful import.", small);
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
                    Label("A moment of stillness.", title);
                    if (game.InTrial && Button("RETREAT · KEEP EARNED REWARDS", button))
                        game.Finish(false);
                    if (!game.InTrial && Button("RETURN HOME · KEEP PROGRESS", button))
                        game.ReturnHome();
                    Label("Quality presets change shadows, MSAA and render scale. Performance depends on your hardware.", body);
                    if (Button("QUALITY · HIGH", button))
                        Quality(true);
                    if (Button("QUALITY · LIGHTWEIGHT", button))
                        Quality(false);
                    if (Button("MUTE / UNMUTE", button))
                        AudioListener.volume = AudioListener.volume > 0 ? 0 : 1;
                    break;
                case "elder":
                    Label(game.Dialogue,body);
                    if(Button("YES · LET’S HAVE TEA",button))game.GetComponent<Sunward.Remaster.VillageTeaVisit>().Invite();
                    break;
                case "tea":
                    var tea=game.GetComponent<Sunward.Remaster.VillageTeaVisit>();
                    Label("TEA & STORIES OF NIPPON",title);Label(tea.Story,body);
                    if(Button("TELL ME ANOTHER STORY",button))tea.NextStory();
                    if(Button("SIT FOR TEA",button))tea.SitForTea();
                    break;
                case "requests":
                    Label("VILLAGE REQUEST BOARD",title);
                    var requests=game.GetComponent<Sunward.Remaster.VillageLife>();
                    Label(requests.RequestDetails(),body);
                    Label("Turn in completed requests at the farmer’s stall in the northeast farm. These are optional village goals, separate from weapon purchases and arena entry.",small);
                    break;
                case "festival":
                    var festival=game.GetComponent<Sunward.Remaster.FestivalChallenges>();
                    Label("FESTIVAL NIGHT · "+game.Profile.festivalTokens+" tokens",title);
                    Label("Sleep in Ammy’s bed to reach night. Optional games award festival tokens; your arena progress is unchanged.",small);
                    Label(festival.Active?festival.Status:"Spirit run: collect thirteen floating spirit lights in order within 95 seconds. Harvest relay: dig up three different vegetables, then give three to the farmer within 90 seconds. Each win awards 3 tokens.",body);
                    if(!festival.Active){if(Button("START SPIRIT RUN · 95 seconds",button))festival.Begin(1);if(Button("START HARVEST RELAY · 90 seconds",button))festival.Begin(2);}
                    else if(Button("CANCEL CHALLENGE",button))festival.Cancel();
                    Label("Home decorations · permanent rewards placed inside Ammy’s house",body);
                    for(int reward=0;reward<3;reward++)
                    {
                        int choice=reward;string label=Sunward.Remaster.FestivalChallenges.RewardName(choice);
                        if((game.Profile.festivalRewards&(1<<choice))!=0)Label(label+" · owned",small);
                        else if(Button(label+" · "+Sunward.Remaster.FestivalChallenges.RewardCost(choice)+" tokens",button))festival.Buy(choice);
                    }
                    break;
                case "farm":
                    Label("FARM SHOP · "+game.Profile.vegetables+" vegetables · "+game.Profile.praise+" Praise",body);
                    var farm=game.GetComponent<Sunward.Remaster.VillageLife>();
                    Label("Bring harvested vegetables in your mouth or pouch. Hand over one, sell the pouch, or keep them for a village request.",small);
                    if(Button("HAND OVER ONE VEGETABLE · +5 coins",button))farm.GiveProduce();
                    if(Button("SELL PRODUCE · 5 coins each",button))farm.Sell();
                    if(Button("EAT VEGETABLE · +1 health",button))farm.Eat();
                    if(Button("FARM MEAL · 5 coins · +10 health",button))farm.BuyMeal();
                    if(Button("VITALITY · "+(25+game.Profile.farmVitality*10)+" coins · permanent +1 max health",button))farm.BuyVitality();
                    Label(farm.RequestDetails(),body);
                    if(game.Profile.restorationStage<3 && Button("TURN IN THIS REQUEST",button))farm.Request();
                    break;
                case "bossVictory":
                    Label("CRIMSON HELM DEFEATED",title);
                    Label("Three forms overcome. The chamber is yours.\n\n"+game.Dialogue,body);
                    if(Button("CONTINUE",button))game.Close();
                    break;
                case "result":
                    Label(game.Dialogue, title);
                    if (Button("RETURN HOME →", button))
                        game.ReturnHome();
                    break;
                default:
                    Label(game.Dialogue, body);
                    break;
            }

            if (game.Panel != "result" && game.Panel != "title" && Button("RETURN →", button))
                game.Close();
            GUILayout.EndScrollView();
            GUILayout.EndArea();
            lastCount = buttonCount;
            selected = Mathf.Clamp(selected, 0, Mathf.Max(0, lastCount - 1));
        }

        void Shop()
        {
            Label("Hana · upgrades & blessings", title);
            Label(game.Profile.coins + " coins · permanent upgrades survive defeat.", body);
            if (Button("TARO'S WEAPON CATALOGUE →", button)) game.SetPanel("weapons");
            if(Button("VILLAGE REQUEST BOARD · goals & rewards",button))game.SetPanel("requests");
            foreach (string id in ProgressionRules.Upgrades)
            {
                string label=id=="spear"?"GLAIVE MASTERY":id=="sundial"?"MIRROR & ROSARY MASTERY":id=="energy"?"INK CAPACITY":id=="ability"?"BARK TECHNIQUE":id.ToUpperInvariant();
                int rank=game.Profile.upgrades.Get(id),cap=ProgressionRules.Cap(id);
                if(rank>=cap)Label(label+" · "+rank+" / "+cap+" · MAXIMUM",body);
                else if(Button(label+" · rank "+rank+" / "+cap+" · "+ProgressionRules.Cost(game.Profile,id)+" coins",button))game.Buy(id);
                Label(ProgressionRules.Explain(id),small);
            }
        }
        void Weapons()
        {
            Label("Taro · divine instruments", title);
            Label(game.Profile.coins + " coins · purchased weapons stay in your save. Q cycles owned weapons in the arena.", body);
            if(Button("VILLAGE REQUEST BOARD · goals & rewards",button))game.SetPanel("requests");
            Label("Glaives: sword strikes. Reflectors: broad close-range attacks. Rosaries: bead whips with reach. Hold either attack button to charge; release to strike.",small);
            var catalogue=Sunward.Remaster.OriginalWeaponCatalog.All;
            weaponPage=Mathf.Clamp(weaponPage,0,catalogue.Length-1);var entry=catalogue[weaponPage];
            Label((weaponPage+1)+" / "+catalogue.Length+" · "+entry.title,title);
            var portrait=Resources.Load<Texture2D>("Okami/WeaponPortraits/"+entry.resource);
            if(portrait){var image=GUILayoutUtility.GetRect(contentWidth,210);GUI.DrawTexture(image,portrait,ScaleMode.ScaleToFit);}
            Label(entry.family.ToUpperInvariant()+" · "+entry.cost+" coins",body);
            Label(Sunward.Remaster.WeaponLore.Description(entry),body);
            Label(Sunward.Remaster.WeaponLore.Lore(entry),small);
            bool owned=Sunward.Remaster.OriginalWeaponCatalog.Owns(game.Profile,entry.id);
            if(Button(owned?(game.Profile.equipped==entry.id?"EQUIPPED":"EQUIP THIS INSTRUMENT"):"PURCHASE · "+entry.cost+" coins",button))
            {if(owned){game.Profile.equipped=entry.id;game.Save.Save();game.Combat.Equip();}else game.Buy("weapon:"+entry.id);}
            if(Button("PREVIOUS INSTRUMENT",button))weaponPage=(weaponPage+catalogue.Length-1)%catalogue.Length;
            if(Button("NEXT INSTRUMENT",button))weaponPage=(weaponPage+1)%catalogue.Length;
        }

        void DrawPaper(Rect r)
        {
            // Preserve the paper's aspect and opaque pixels, rather than
            // stretching a small crop across a portrait-shaped menu.
            Color old = GUI.color;
            GUI.color = Color.white;
            if(paper)GUI.DrawTexture(new Rect(r.x+17,r.y,r.width-34,r.height),paper,ScaleMode.StretchToFill,true);
            if(scrollRoll){GUI.DrawTexture(new Rect(r.x-4,r.y-5,32,r.height+10),scrollRoll);GUI.DrawTextureWithTexCoords(new Rect(r.xMax-28,r.y-5,32,r.height+10),scrollRoll,new Rect(1,0,-1,1));}
            if(hintInk){GUI.color=new Color(.34f,.085f,.035f,.75f);GUI.DrawTexture(new Rect(r.x+24,r.y+10,r.width-48,12),hintInk);GUI.DrawTexture(new Rect(r.x+24,r.yMax-22,r.width-48,12),hintInk);}
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
