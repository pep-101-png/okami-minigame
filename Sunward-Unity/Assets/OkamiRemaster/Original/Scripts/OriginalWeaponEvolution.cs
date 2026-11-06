using System;
using UnityEngine;
namespace Sunward.Remaster
{
    // A Sunward reward, using the genuine WP29 model and recovered motions.
    // WP49 was inspected and is a rolled mat, not an evolved Thunder Edge model.
    public static class OriginalWeaponEvolution
    {
        public const string ThunderId="wp29e";
        public static bool Owns(ProfileData p)=>p!=null && p.owned!=null && Array.IndexOf(p.owned,ThunderId)>=0;
        public static bool Replaced(ProfileData p,string id)=>id=="wp29" && Owns(p);
        public static void Normalize(ProfileData p)
        {
            if(!Owns(p))return;p.owned=Array.FindAll(p.owned,id=>id!="wp29");if(p.equipped=="wp29")p.equipped=ThunderId;
        }
        public static bool Unlock(ProfileData p)
        {
            if(p==null)return false;if(Owns(p)){Normalize(p);return false;}if(p.owned==null)p.owned=new[]{"spear"};
            Array.Resize(ref p.owned,p.owned.Length+1);p.owned[p.owned.Length-1]=ThunderId;p.equipped=ThunderId;Normalize(p);return true;
        }
        public static float Power(string id)=>id==ThunderId?1.35f:1;
        public static float Reach(string id)=>id==ThunderId?1.15f:1;
        public static void Attach(Transform parent,bool unscaled=false)
        {
            var aura=parent.gameObject.AddComponent<ThunderWeaponAura>();aura.unscaled=unscaled;
        }
    }
}
