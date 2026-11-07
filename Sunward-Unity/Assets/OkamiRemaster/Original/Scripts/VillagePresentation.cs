using UnityEngine;
using UnityEngine.InputSystem;
namespace Sunward.Remaster
{
    // Sunward title/camera direction using original paintings, logo, ink and glyphs.
    public sealed class VillagePresentation : MonoBehaviour
    {
        public GameFlow game;
        public bool Playing {get;private set;}
        public int SkipHandledFrame {get;private set;}=-1;
        public void Skip(){SkipHandledFrame=Time.frameCount;Cancel();}
        public string MusicCue=>Title || skyTransition?"gardenmusic":bossVictory?"boss-victory":breaking || victory?"trial-victory":"festivalrace";
        public bool Title=>game && game.Panel=="title";
        float elapsed,duration,dialogueTime,entryGrace;bool victory,breaking,shaftRevealed,bossVictory,skyTransition,skyNight,howled;
        public bool Breaking=>Playing && breaking;
        readonly System.Collections.Generic.List<GameObject> cinemaEffects=new System.Collections.Generic.List<GameObject>();
        OrbitCamera orbit;Texture2D painting,logo,bubble,ink;
        string lastDialogue="";int page;bool dialogueWasOpen;
        System.Collections.Generic.List<string> dialoguePages=new System.Collections.Generic.List<string>();
        float pageWidth,pageHeight,pageEm;
        string CurrentPage=>dialoguePages.Count>0?dialoguePages[Mathf.Clamp(page,0,dialoguePages.Count-1)]:"";
        bool MorePages=>page+1<dialoguePages.Count;
        public bool Dialogue=>game && (game.Panel=="dialogue" || game.Panel=="elder" || game.Panel=="tea");
        void Start(){painting=Resources.Load<Texture2D>("Okami/UI/TitlePainting");logo=Resources.Load<Texture2D>("Okami/UI/TitleLogo");bubble=Resources.Load<Texture2D>("Okami/UI/DialogueBubble");ink=Resources.Load<Texture2D>("Okami/UI/BrushTip");}
        public void Festival(bool won)
        {
            if(Playing)Cancel();bossVictory=skyTransition=false;breaking=false;victory=won;elapsed=0;duration=won?4.2f:3.4f;Playing=true;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;game.Player.animationView.Play(won?"Bark":"Idle_Natural",.12f,won?1.93f:0,true);
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();
            CinemaBurst("SpiritGlow",won?32:16,.35f);
            if(won)CinemaBurst("Blossom",35,.5f);
        }
        public void ShaftCollapse()
        {
            if(Playing)Cancel();bossVictory=skyTransition=false;breaking=true;shaftRevealed=false;victory=false;elapsed=0;duration=3.8f;Playing=true;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();
        }
        public void BossVictory()
        {
            if(Playing)Cancel();bossVictory=true;skyTransition=breaking=false;howled=false;elapsed=0;duration=6.5f;Playing=true;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;
            foreach(var enemy in game.Enemies)if(enemy && enemy.Dead && enemy.definition.id=="boss")enemy.gameObject.SetActive(false);
            if(LowerArena.Inside(game.Player.transform.position)){game.Player.Teleport(LowerArena.Centre+new Vector3(0,.08f,-4));game.Player.transform.rotation=Quaternion.Euler(0,135,0);}
            game.Player.animationView.Play("Idle_Natural",.12f,0,true);orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic(false);
            CinemaBurst("Blossom",48,.32f);CinemaBurst("SpiritGlow",24,.18f);
        }
        public void SkyTransition(bool night)
        {
            if(Playing)Cancel();skyTransition=true;skyNight=night;bossVictory=breaking=false;elapsed=0;duration=6;Playing=true;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;game.Player.animationView.Play("Idle_Natural",.15f,0,true);
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic(false);
        }
        void CinemaBurst(string sprite,int count,float size)
        {
            var fx=OriginalAtmosphere.Create(sprite,null,game.Player.transform.position+Vector3.up,0,size,2.6f,.5f,.8f);
            if(fx){var main=fx.main;main.useUnscaledTime=true;fx.Emit(count);cinemaEffects.Add(fx.gameObject);}
        }
        public void Cancel()
        {
            if(!Playing)return;if(breaking && !shaftRevealed)LowerArena.RevealShaft();breaking=false;Playing=false;foreach(var fx in cinemaEffects)if(fx)Destroy(fx);cinemaEffects.Clear();if(orbit)orbit.EndCinematic();if(game && game.Player){game.Player.Locked=game.Health<=0;game.Player.animationView.Play("Idle_Natural",.15f,0,true);}
        }
        void Update()
        {
            if(!game || !game.Player)return;
            if(Title)
            {
                bool pressed=(Keyboard.current!=null && Keyboard.current.anyKey.wasPressedThisFrame) || (Mouse.current!=null && (Mouse.current.leftButton.wasPressedThisFrame || Mouse.current.rightButton.wasPressedThisFrame || Mouse.current.middleButton.wasPressedThisFrame));
                if(Gamepad.current!=null)foreach(var control in Gamepad.current.allControls)if(control is UnityEngine.InputSystem.Controls.ButtonControl button && button.wasPressedThisFrame)pressed=true;
                if(pressed){game.Close();game.Notify("");game.Player.Locked=true;entryGrace=.18f;}return;
            }
            if(entryGrace>0){entryGrace=Mathf.Max(0,entryGrace-Time.unscaledDeltaTime);if(entryGrace==0)game.Player.Locked=game.Health<=0;return;}
            if(Playing)
            {
                elapsed+=Time.unscaledDeltaTime;float t=Mathf.Clamp01(elapsed/duration);
                if(bossVictory)
                {
                    if(!howled && elapsed>=1){howled=true;game.Player.animationView.Play("Bark",.1f,1.93f,true);game.Audio.VictoryHowl();}
                    var focus=game.Player.transform.position+Vector3.up*.8f;if(orbit)orbit.CinematicFrame(focus,game.Player.transform.eulerAngles.y+Mathf.Lerp(-50,45,t),Mathf.Lerp(10,24,t),Mathf.Lerp(5.5f,7,t),39);
                }
                else if(skyTransition)
                {if(orbit)orbit.CinematicFrame(game.Player.transform.position+Vector3.up*Mathf.Lerp(6,18,t),-35,Mathf.Lerp(-18,-35,t),7,50);}
                else if(breaking)
                {
                    if(orbit)orbit.CinematicFrame(new Vector3(35,0,0),Mathf.Lerp(25,80,t),Mathf.Lerp(48,68,t),Mathf.Lerp(19,13,t),48);
                    if(!shaftRevealed && elapsed>=.9f){shaftRevealed=true;LowerArena.RevealShaft();game.Audio.Cue("land");
                        var dust=OriginalAtmosphere.Create("Cloud",null,new Vector3(35,.3f,0),0,1.7f,2,.6f,3);if(dust){var main=dust.main;main.useUnscaledTime=true;dust.Emit(28);Destroy(dust.gameObject,5);}}
                }
                else
                {
                if(orbit)orbit.CinematicFrame(victory?game.Player.transform.position+Vector3.up*.9f:Vector3.Lerp(game.Player.transform.position+Vector3.up*.9f,FestivalChallenges.Board+Vector3.up*1.8f,t*.65f),game.Player.transform.eulerAngles.y+Mathf.Lerp(-45,32,t),victory?16:22,victory?5.8f:8,42);
                }
                if(game.Player.input.Pause.WasPressedThisFrame())Skip();else if(elapsed>=duration || game.Health<=0)Cancel();
            }
            if(Dialogue)
            {
                EnsureDialoguePages();dialogueTime+=Time.unscaledDeltaTime;if(dialogueTime*65<CurrentPage.Length && game.Audio)game.Audio.DialogueSyllable();
                dialogueWasOpen=true;if(dialogueTime>.2f && (game.Panel=="dialogue" || MorePages) && game.Player.input.Interact.WasPressedThisFrame())Advance();
            }
            else dialogueWasOpen=false;
        }
        string DialogueText()=>game.Panel=="tea"?game.GetComponent<VillageTeaVisit>().Story:game.Dialogue;
        static Rect DialogueBounds()
        {float w=Mathf.Min(1360,Screen.width*.96f),h=Mathf.Min(460,Screen.height*.56f);return new Rect((Screen.width-w)*.5f,Screen.height-h-25,w,h);}
        static Rect DialogueBody(Rect r)=>new Rect(r.x+r.width*.23f,r.y+r.height*.28f,r.width*.56f,r.height*.38f);
        static float DialogueEm=>40*Mathf.Min(1,Screen.height/900f);
        void EnsureDialoguePages()
        {
            string text=DialogueText()??"";var body=DialogueBody(DialogueBounds());float em=DialogueEm;
            bool changed=!dialogueWasOpen || text!=lastDialogue;
            if(!changed && body.width==pageWidth && body.height==pageHeight && em==pageEm)return;
            int offset=0;if(!changed)for(int i=0;i<page && i<dialoguePages.Count;i++)offset+=dialoguePages[i].Length;
            dialoguePages=InkText.Paginate(text,body.width,body.height,em);lastDialogue=text;pageWidth=body.width;pageHeight=body.height;pageEm=em;page=0;
            if(!changed)while(page+1<dialoguePages.Count && offset>=dialoguePages[page].Length){offset-=dialoguePages[page].Length;page++;}
            dialogueTime=changed?0:999;
        }
        void Advance(){EnsureDialoguePages();if(dialogueTime*65<CurrentPage.Length){dialogueTime=999;return;}if(MorePages){page++;dialogueTime=0;}else game.Close();}
        void OnGUI()
        {
            if(!game || (!Title && !Playing && !Dialogue))return;var previousMatrix=GUI.matrix;GUI.matrix=Matrix4x4.identity;var previous=GUI.color;
            if(Title)
            {
                GUI.color=Color.white;if(painting)GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height),painting,ScaleMode.ScaleAndCrop);
                float w=Mathf.Min(Screen.width*.43f,680),h=w*455/530;
                if(logo)GUI.DrawTexture(new Rect(Screen.width*.5f-w*.5f,Screen.height*.08f,w,h),logo,ScaleMode.ScaleToFit);
                InkText.Draw("SUNWARD",new Rect(Screen.width*.5f-90,Screen.height*.65f,240,70),55,new Color(.14f,.07f,.035f,1),false);
                InkText.Draw("Press any button",new Rect(Screen.width*.5f-110,Screen.height*.79f,300,60),38,new Color(.14f,.07f,.035f,.65f+.2f*Mathf.Sin(Time.unscaledTime*1.8f)),false);
                GUI.color=previous;GUI.matrix=previousMatrix;return;
            }
            if(Playing)
            {
                if(ink){GUI.color=new Color(.03f,.02f,.01f,.85f);GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height*.055f),ink);GUI.DrawTexture(new Rect(0,Screen.height*.945f,Screen.width,Screen.height*.055f),ink);}
                InkText.Draw(bossVictory?"Crimson Helm defeated · the sun endures":skyTransition?(skyNight?"The moon rises · festival night":"The sun returns · a new day"):breaking?"The earth yields to the sun":victory?"Festival blessing · +3 tokens":"Festival night · follow the spirit lights",new Rect(Screen.width*.5f-260,Screen.height*.8f,600,70),42,new Color(1,.94f,.78f,1),false);
            }
            if(Dialogue)
            {
                EnsureDialoguePages();var r=DialogueBounds();float w=r.width,h=r.height;
                GUI.color=new Color(1,1,1,.97f);if(bubble)GUI.DrawTexture(r,bubble);
                InkText.Draw(CurrentPage,DialogueBody(r),DialogueEm,new Color(.09f,.06f,.035f,1),true,Mathf.FloorToInt(dialogueTime*65));
                float y=r.y+h*.77f;
                bool more=MorePages;
                if(dialoguePages.Count>1 && (more || game.Panel=="dialogue"))InkText.Draw((page+1)+" / "+dialoguePages.Count,new Rect(r.x+w*.2f,y,w*.2f,45),Mathf.Min(24,DialogueEm),new Color(.32f,.10f,.055f,1),false);
                if(more){if(InkButton("E · Next",new Rect(r.x+w*.72f,y,w*.22f,45)))Advance();}
                else if(game.Panel=="elder"){if(InkButton("Yes · tea sounds lovely",new Rect(r.x+w*.15f,y,w*.5f,45)))game.GetComponent<VillageTeaVisit>().Invite();}
                else if(game.Panel=="tea")
                {if(InkButton("Another story",new Rect(r.x+w*.14f,y,w*.29f,45)))game.GetComponent<VillageTeaVisit>().NextStory();if(InkButton("Sit for tea",new Rect(r.x+w*.47f,y,w*.23f,45)))game.GetComponent<VillageTeaVisit>().SitForTea();}
                if(!more && InkButton(game.Panel=="dialogue"?"E · Finish":"Leave",new Rect(r.x+w*.73f,y,w*.22f,45))){if(game.Panel=="dialogue")Advance();else game.Close();}
            }
            GUI.color=previous;GUI.matrix=previousMatrix;
        }
        static bool InkButton(string label,Rect r){float em=Mathf.Min(30,r.height*.7f);while(em>12 && InkText.MeasureHeight(label,r.width,em)>em+.001f)em--;InkText.Draw(label,r,em,new Color(.32f,.10f,.055f,1),false);return GUI.Button(r,"",GUIStyle.none);}
        void OnDisable(){Cancel();}
    }
}
