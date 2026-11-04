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
        public static bool Unlock(ProfileData p)
        {
            if(p==null || Owns(p))return false;
            if(p.owned==null)p.owned=new[]{"spear"};
            if(Array.IndexOf(p.owned,"wp29")<0){Array.Resize(ref p.owned,p.owned.Length+1);p.owned[p.owned.Length-1]="wp29";}
            Array.Resize(ref p.owned,p.owned.Length+1);p.owned[p.owned.Length-1]=ThunderId;p.equipped=ThunderId;return true;
        }
        public static float Power(string id)=>id==ThunderId?1.35f:1;
        public static float Reach(string id)=>id==ThunderId?1.15f:1;
        public static void Attach(Transform parent,bool unscaled=false)
        {
            var sparks=OriginalAtmosphere.Create("Spark",parent,Vector3.zero,9,.12f,.5f,.02f,.25f);if(sparks){var main=sparks.main;main.useUnscaledTime=unscaled;main.startColor=new Color(.7f,.85f,1,.85f);}
            var halo=OriginalAtmosphere.Create("SpiritGlow",parent,Vector3.zero,3,.18f,1,.02f,.25f);if(halo){var main=halo.main;main.useUnscaledTime=unscaled;main.startColor=new Color(.5f,.75f,1,.45f);}
        }
    }
}
