using System;
using UnityEngine;
using UnityEngine.InputSystem;
namespace Sunward.Remaster
{
    public sealed class MemoryMirrorMenu:MonoBehaviour
    {
        public GameFlow game;int selected;bool loading,wasOpen;float openedAt;ProfileData[] slots;
        void RefreshSlots(){slots=new ProfileData[4];for(int i=0;i<4;i++)slots[i]=game.Save.ReadSlot(i);}
        Texture2D paper,body,roll,brush;
        void Start(){paper=Resources.Load<Texture2D>("Okami/UI/MenuPaper");body=Resources.Load<Texture2D>("Okami/UI/MenuScrollBody");roll=Resources.Load<Texture2D>("Okami/UI/MenuScrollRoll");brush=Resources.Load<Texture2D>("Okami/UI/BrushTip");}
        bool Button(string text,Rect r){InkText.Draw(text,r,Mathf.Min(28,r.height*.65f),new Color(.1f,.12f,.055f,1),false);return GUI.Button(r,"",GUIStyle.none);}
        void Paper(Rect r,Color tint)
        {GUI.color=tint;if(body)GUI.DrawTexture(r,body);GUI.color=Color.white;if(roll){GUI.DrawTexture(new Rect(r.x-7,r.y,14,r.height),roll);GUI.DrawTexture(new Rect(r.x+r.width-7,r.y,14,r.height),roll);}}
        static string TimeLabel(ProfileData p){int n=(int)Mathf.Max(0,p.playSeconds);return (n/3600)+" hr. "+(n/60%60)+" min. "+(n%60)+" sec.";}
        void Activate()
        {
            if(!loading)game.Profile.milestones.homeVisited=true;
            bool ok=loading?game.Save.LoadSlot(selected):game.Save.SaveSlot(selected);
            if(ok && loading){game.ReturnHome();game.Combat.Equip();game.Shelf.Refresh();game.RefreshQuest();}
            RefreshSlots();game.Notify(game.Save.Status);
        }
        void Update()
        {
            if(!game)return;if(game.Panel!="mirror"){wasOpen=false;return;}if(!wasOpen){wasOpen=true;openedAt=Time.unscaledTime;RefreshSlots();return;}if(Time.unscaledTime-openedAt<.25f)return;
            var keys=Keyboard.current;if(keys!=null){if(keys.upArrowKey.wasPressedThisFrame)selected=(selected+3)%4;if(keys.downArrowKey.wasPressedThisFrame)selected=(selected+1)%4;if(keys.leftArrowKey.wasPressedThisFrame || keys.rightArrowKey.wasPressedThisFrame)loading=!loading;}
            if(game.Player.input.Interact.WasPressedThisFrame())Activate();
        }
        void OnGUI()
        {
            if(!game || game.Panel!="mirror")return;if(slots==null)RefreshSlots();
            var old=GUI.matrix;var color=GUI.color;GUI.matrix=Matrix4x4.identity;
            // Original paper and scroll assets; four real backed-up save slots.
            float scale=Mathf.Min(Screen.width/960f,Screen.height/640f);GUI.matrix=Matrix4x4.Scale(new Vector3(scale,scale,1));float x=(Screen.width/scale-900)*.5f,y=(Screen.height/scale-600)*.5f;
            GUI.color=new Color(.78f,.76f,.65f,1);if(paper)GUI.DrawTexture(new Rect(0,0,Screen.width/scale,Screen.height/scale),paper);GUI.color=Color.white;
            Paper(new Rect(x+25,y+20,360,56),new Color(.88f,.88f,.74f,1));InkText.Draw(loading?"Load":"Save",new Rect(x+155,y+31,200,42),34,new Color(.06f,.065f,.035f,1),false);
            if(!game.Profile.shrine && game.Profile.windflowers.Length>=3 && Button("Offer windflowers",new Rect(x+555,y+28,290,44)))game.OfferWindflowers();
            for(int i=0;i<4;i++)
            {
                var row=new Rect(x+65,y+100+i*67,780,59);Paper(row,i==selected?new Color(.75f,.84f,.58f,1):new Color(.91f,.87f,.73f,1));var data=slots[i];
                if(i==selected){InkText.Draw("→",new Rect(row.x-37,row.y+10,32,40),32,new Color(.25f,.42f,.08f,1),false);}
                InkText.Draw((i+1)+"   "+(data==null?"Empty memory":"Windflower Village"),new Rect(row.x+15,row.y+12,410,40),28,new Color(.05f,.07f,.03f,1),false);
                if(data!=null)InkText.Draw(TimeLabel(data),new Rect(row.x+465,row.y+15,300,40),24,new Color(.08f,.15f,.07f,1),false);
                if(GUI.Button(row,"",GUIStyle.none))selected=i;
            }
            var preview=slots[selected];Paper(new Rect(x+45,y+382,820,132),new Color(.68f,.82f,.43f,1));
            if(preview!=null)
            {
                InkText.Draw("Life "+ProgressionRules.MaxHp(preview)+"    Ink "+(80+preview.upgrades.energy*15)+"    Level "+ProgressionRules.Level(preview),new Rect(x+72,y+399,760,40),28,new Color(.10f,.16f,.055f,1),false);
                InkText.Draw(preview.coins+" coins    "+preview.owned.Length+" instruments    "+preview.bossWins+" Crimson Helm victories",new Rect(x+72,y+443,760,32),21,new Color(.10f,.16f,.055f,1),false);
            }
            if(preview!=null)
            {
                int count=Mathf.Min(12,preview.owned.Length);for(int i=0;i<count;i++){var entry=OriginalWeaponCatalog.Find(preview.owned[i]);if(entry==null)continue;var art=Resources.Load<Texture2D>("Okami/WeaponPortraits/"+entry.resource);if(art)GUI.DrawTexture(new Rect(x+72+i*62,y+473,55,35),art,ScaleMode.ScaleToFit);}
            }
            if(preview==null)InkText.Draw("A new memory can be inscribed here.",new Rect(x+90,y+420,720,45),28,new Color(.10f,.16f,.055f,1),false);
            if(Button(loading?"← Save":"Load →",new Rect(x+65,y+535,220,44)))loading=!loading;
            if(Button(loading?"Restore memory":"Inscribe memory",new Rect(x+325,y+535,310,44)))
            {
                Activate();
            }
            if(Button("Return",new Rect(x+700,y+535,150,44)))game.Close();
            GUI.color=color;GUI.matrix=old;
        }
    }
}
