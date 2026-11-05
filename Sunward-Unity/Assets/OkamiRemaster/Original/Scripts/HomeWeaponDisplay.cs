using System;
using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class HomeWeaponDisplay:MonoBehaviour
    {
        public GameFlow game;
        public static readonly Vector3 Position=VillageInteriors.HomeCentre+new Vector3(0,.025f,3.1f);
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
            if(entry.resource=="wp29" && weapon)foreach(var r in weapon.GetComponentsInChildren<SkinnedMeshRenderer>())
            {int g=int.Parse(r.sharedMesh.name.Split('-')[1]);r.enabled=g==1 || g==(shown==OriginalWeaponEvolution.ThunderId?4:2);}
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
            float w=Mathf.Min(400,Screen.width*.58f);var r=new Rect(Mathf.Clamp(p.x-w*.5f,12,Screen.width-w-12),Mathf.Clamp(Screen.height-p.y,12,Screen.height-120),w,110);
            var entry=OriginalWeaponCatalog.Find(shown);string text=Title+"\n"+(entry!=null?(entry.family=="glaive"?"A divine blade for deliberate, powerful strikes.":entry.family=="rosary"?"Sacred beads for reaching whips and charged casts.":"A divine mirror for broad, close-range blows."):"");InkText.Draw(text,r,22,new Color(.15f,.07f,.025f,1));
        }
    }
}
