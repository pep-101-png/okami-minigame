using System;
using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class HomeWeaponDisplay:MonoBehaviour
    {
        public GameFlow game;
        public static readonly Vector3 Position=VillageInteriors.HomeCentre+new Vector3(-4.5f,.025f,-1.4f);
        GameObject root,weapon;string shown="";int index;
        public string Title=>OriginalWeaponCatalog.Find(shown)?.title??"Divine instrument";
        public void Cycle(){index++;Refresh();game.Notify(Title);}
        void Start()
        {
            root=new GameObject("Home · one floating divine instrument");root.transform.SetParent(transform,false);root.transform.position=Position;
            VillageFestival.Place(root.transform,"Okami/vt0a",Vector3.zero,new Vector3(1.2f,.55f,1.2f),Vector3.zero);
            var glow=OriginalAtmosphere.Create("SpiritGlow",root.transform,Vector3.up*.6f,7,.17f,2,.05f,.6f);
            var light=root.AddComponent<Light>();light.type=LightType.Point;light.color=new Color(1,.83f,.45f);light.range=4;light.intensity=2;
            Refresh();
        }
        void Refresh()
        {
            if(!root || game.Profile.owned==null || game.Profile.owned.Length==0)return;
            var owned=Array.FindAll(game.Profile.owned,id=>OriginalWeaponCatalog.Find(id)!=null);if(owned.Length==0)return;
            index=(index%owned.Length+owned.Length)%owned.Length;string next=owned[index];if(next==shown && weapon)return;shown=next;
            if(weapon){weapon.SetActive(false);Destroy(weapon);}var entry=OriginalWeaponCatalog.Find(shown);
            Vector3 size=entry.family=="glaive"?new Vector3(.55f,.18f,1.7f):entry.family=="rosary"?new Vector3(1.5f,.45f,1.5f):new Vector3(1.15f,.25f,1.15f);
            weapon=VillageFestival.Place(root.transform,"Okami/"+entry.resource,Vector3.up*1.45f,size,entry.family=="glaive"?new Vector3(-65,0,0):new Vector3(65,0,0));
            if(entry.id==OriginalWeaponEvolution.ThunderId && weapon)OriginalWeaponEvolution.Attach(weapon.GetComponent<OriginalVisual>().PaintRoot);
            if(entry.resource=="wp29" && weapon)foreach(var r in weapon.GetComponentsInChildren<SkinnedMeshRenderer>())
            {r.enabled=true;}
        }
        void Update()
        {
            if(!root || !game || !game.Player)return;
            bool visible=VillageInteriors.Home(game.Player.transform.position);root.SetActive(visible);if(!visible)return;Refresh();
            if(weapon){weapon.transform.localPosition=Vector3.up*(1.45f+Mathf.Sin(Time.time*1.6f)*.085f);var entry=OriginalWeaponCatalog.Find(shown);weapon.transform.localRotation=Quaternion.Euler(entry.family=="glaive"?-65:65,Time.time*17,0);}
        }
        void OnGUI()
        {
            if(!root || !root.activeSelf || !Camera.main || game.Blocked || Vector3.Distance(game.Player.transform.position,Position)>5)return;
            var p=Camera.main.WorldToScreenPoint(Position+Vector3.up*.4f);if(p.z<=0)return;
            var previous=GUI.matrix;var previousColor=GUI.color;GUI.matrix=Matrix4x4.identity;
            float width=Mathf.Min(540,Screen.width*.72f);var r=new Rect(Mathf.Clamp(p.x-width*.5f,12,Screen.width-width-12),Mathf.Clamp(Screen.height-p.y+12,12,Screen.height-155),width,142);
            var paper=Resources.Load<Texture2D>("Okami/UI/MenuScrollBody");var roll=Resources.Load<Texture2D>("Okami/UI/MenuScrollRoll");GUI.color=new Color(1,1,1,.96f);if(paper)GUI.DrawTexture(r,paper);GUI.color=Color.white;if(roll){GUI.DrawTexture(new Rect(r.x-6,r.y,12,r.height),roll);GUI.DrawTexture(new Rect(r.x+r.width-6,r.y,12,r.height),roll);}
            float titleSize=32;while(titleSize>20 && InkText.MeasureHeight(Title,width-36,titleSize)>titleSize+.01f)titleSize--;
            InkText.Draw(Title,new Rect(r.x+18,r.y+12,width-36,40),titleSize,new Color(.09f,.045f,.015f,1),false);
            var entry=OriginalWeaponCatalog.Find(shown);string text=entry==null?"":entry.family=="glaive"?"A divine blade for deliberate, powerful strikes.":entry.family=="rosary"?"Sacred beads for reaching whips and charged casts.":"A divine mirror for broad, close-range blows.";
            if(entry!=null && OriginalWeaponEvolution.IsAwakened(entry.id))text=AwakeningProgress.Ability(entry.resource);
            float bodySize=23;while(bodySize>15 && InkText.MeasureHeight(text,width-36,bodySize)>75)bodySize--;InkText.Draw(text,new Rect(r.x+18,r.y+54,width-36,75),bodySize,new Color(.13f,.075f,.035f,1));GUI.color=previousColor;GUI.matrix=previous;
        }
    }
}
