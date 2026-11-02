using UnityEngine;
using UnityEngine.InputSystem;
namespace Sunward.Remaster
{
    // Sunward title/camera direction using original paintings, logo, ink and glyphs.
    public sealed class VillagePresentation : MonoBehaviour
    {
        public GameFlow game;
        public bool Playing {get;private set;}
        public bool Title=>game && game.Panel=="title";
        float elapsed,duration,dialogueTime,entryGrace;bool victory;
        readonly System.Collections.Generic.List<GameObject> cinemaEffects=new System.Collections.Generic.List<GameObject>();
        OrbitCamera orbit;Texture2D painting,logo,bubble,ink;
        string lastDialogue="";int page;bool dialogueWasOpen;
        public bool Dialogue=>game && (game.Panel=="dialogue" || game.Panel=="elder" || game.Panel=="tea");
        void Start(){painting=Resources.Load<Texture2D>("Okami/UI/TitlePainting");logo=Resources.Load<Texture2D>("Okami/UI/TitleLogo");bubble=Resources.Load<Texture2D>("Okami/UI/DialogueBubble");ink=Resources.Load<Texture2D>("Okami/UI/BrushTip");}
        public void Festival(bool won)
        {
            if(Playing)Cancel();victory=won;elapsed=0;duration=won?4.2f:3.4f;Playing=true;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;game.Player.animationView.Play(won?"Bark":"Idle_Natural",.12f,won?1.93f:0,true);
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();
            CinemaBurst("SpiritGlow",won?32:16,.35f);
            if(won)CinemaBurst("Blossom",35,.5f);
        }
        void CinemaBurst(string sprite,int count,float size)
        {
            var fx=OriginalAtmosphere.Create(sprite,null,game.Player.transform.position+Vector3.up,0,size,2.6f,.5f,.8f);
            if(fx){var main=fx.main;main.useUnscaledTime=true;fx.Emit(count);cinemaEffects.Add(fx.gameObject);}
        }
        public void Cancel()
        {
            if(!Playing)return;Playing=false;foreach(var fx in cinemaEffects)if(fx)Destroy(fx);cinemaEffects.Clear();if(orbit)orbit.EndCinematic();if(game && game.Player){game.Player.Locked=game.Health<=0;game.Player.animationView.Play("Idle_Natural",.15f,0,true);}
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
                if(orbit)orbit.CinematicFrame(victory?game.Player.transform.position+Vector3.up*.9f:Vector3.Lerp(game.Player.transform.position+Vector3.up*.9f,FestivalChallenges.Board+Vector3.up*1.8f,t*.65f),game.Player.transform.eulerAngles.y+Mathf.Lerp(-45,32,t),victory?16:22,victory?5.8f:8,42);
                if(elapsed>=duration || game.Health<=0 || game.Player.input.Pause.WasPressedThisFrame())Cancel();
            }
            if(Dialogue)
            {
                string text=DialogueText();if(!dialogueWasOpen || text!=lastDialogue){lastDialogue=text;page=0;dialogueTime=0;}dialogueTime+=Time.unscaledDeltaTime;if(dialogueTime*65<Mathf.Min(160,text.Length-page*160) && game.Audio)game.Audio.DialogueSyllable();
                dialogueWasOpen=true;if(dialogueTime>.2f && (game.Panel=="dialogue" || (page+1)*160<text.Length) && game.Player.input.Interact.WasPressedThisFrame())Advance();
            }
            else dialogueWasOpen=false;
        }
        string DialogueText()=>game.Panel=="tea"?game.GetComponent<VillageTeaVisit>().Story:game.Dialogue;
        void Advance(){if(dialogueTime*65<Mathf.Min(160,DialogueText().Length-page*160)){dialogueTime=999;return;}if((page+1)*160<DialogueText().Length){page++;dialogueTime=0;}else game.Close();}
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
                InkText.Draw(victory?"Festival blessing · +3 tokens":"Festival night · follow the spirit lights",new Rect(Screen.width*.5f-260,Screen.height*.8f,600,70),42,new Color(1,.94f,.78f,1),false);
            }
            if(Dialogue)
            {
                float w=Mathf.Min(1050,Screen.width*.9f),h=Mathf.Min(350,Screen.height*.45f);var r=new Rect((Screen.width-w)*.5f,Screen.height-h-25,w,h);
                GUI.color=new Color(1,1,1,.97f);if(bubble)GUI.DrawTexture(r,bubble);
                string text=DialogueText();int from=Mathf.Min(page*160,text.Length),count=Mathf.Min(160,text.Length-from);string shown=text.Substring(from,count);shown=shown.Substring(0,Mathf.Min(shown.Length,Mathf.FloorToInt(dialogueTime*65)));
                InkText.Draw(shown,new Rect(r.x+w*.19f,r.y+h*.26f,w*.66f,h*.47f),34*Mathf.Min(1,Screen.height/900f),new Color(.09f,.06f,.035f,1));
                float y=r.y+h*.77f;
                bool more=(page+1)*160<text.Length;
                if(more){if(InkButton("E · Next",new Rect(r.x+w*.72f,y,w*.22f,45)))Advance();}
                else if(game.Panel=="elder"){if(InkButton("Yes · tea sounds lovely",new Rect(r.x+w*.15f,y,w*.5f,45)))game.GetComponent<VillageTeaVisit>().Invite();}
                else if(game.Panel=="tea")
                {if(InkButton("Another story",new Rect(r.x+w*.14f,y,w*.29f,45)))game.GetComponent<VillageTeaVisit>().NextStory();if(InkButton("Sit for tea",new Rect(r.x+w*.47f,y,w*.23f,45)))game.GetComponent<VillageTeaVisit>().SitForTea();}
                if(!more && InkButton(game.Panel=="dialogue"?"E · Continue":"Leave",new Rect(r.x+w*.73f,y,w*.22f,45))){if(game.Panel=="dialogue")Advance();else game.Close();}
            }
            GUI.color=previous;GUI.matrix=previousMatrix;
        }
        static bool InkButton(string label,Rect r){InkText.Draw(label,r,30,new Color(.32f,.10f,.055f,1),false);return GUI.Button(r,"",GUIStyle.none);}
        void OnDisable(){Cancel();}
    }
}
