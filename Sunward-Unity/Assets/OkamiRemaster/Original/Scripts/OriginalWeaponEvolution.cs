using System;
using UnityEngine;
namespace Sunward.Remaster
{
    // Empowered Sunward variants use recovered original models, not invented native forms.
    public static class OriginalWeaponEvolution
    {
        public const string ThunderId="wp29e";
        public static bool IsAwakened(string id)=>id!=null && (id=="speare" || id=="sundiale" || id.Length==5 && id.StartsWith("wp") && id.EndsWith("e"));
        public static string BaseId(string id)=>IsAwakened(id)?id.Substring(0,id.Length-1):id;
        public static string EvolvedId(string id)=>BaseId(id)+"e";
        public static bool Owns(ProfileData p)=>Owns(p,"wp29");
        public static bool Owns(ProfileData p,string id)=>p!=null && p.owned!=null && Array.IndexOf(p.owned,EvolvedId(id))>=0;
        public static bool Replaced(ProfileData p,string id)=>!IsAwakened(id) && Owns(p,id);
        public static void Normalize(ProfileData p)
        {
            if(p==null || p.owned==null)return;
            p.owned=Array.FindAll(p.owned,id=>!Replaced(p,id));if(Replaced(p,p.equipped))p.equipped=EvolvedId(p.equipped);
        }
        public static bool Unlock(ProfileData p)=>Unlock(p,"wp29",true);
        public static bool Unlock(ProfileData p,string id,bool forceEquip=false)
        {
            if(p==null)return false;id=BaseId(id);if(Owns(p,id)){Normalize(p);return false;}
            if(p.owned==null)p.owned=new[]{"spear"};if(id!="wp29" && Array.IndexOf(p.owned,id)<0)return false;
            Array.Resize(ref p.owned,p.owned.Length+1);p.owned[p.owned.Length-1]=EvolvedId(id);if(forceEquip || p.equipped==id)p.equipped=EvolvedId(id);Normalize(p);return true;
        }
        public static float Power(string id)=>IsAwakened(id)?id==ThunderId?1.35f:id=="wp28e"?1.45f:1.25f:1;
        public static float Reach(string id)=>IsAwakened(id)?1.15f:1;
        public static void Attach(Transform parent,bool unscaled=false)
        {var aura=parent.gameObject.AddComponent<ThunderWeaponAura>();aura.unscaled=unscaled;}
    }
}
