using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class ThunderWeaponAura:MonoBehaviour
    {
        public bool unscaled;GameObject bolt;float clock;
        void Start(){bolt=VillageFestival.Place(transform,"Okami/thunder-lightning",new Vector3(0,.02f,-.9f),new Vector3(.22f,.12f,1.6f),Vector3.zero);if(bolt)WeaponElementFx.Tint(bolt,WeaponElementFx.Colour("wp29"));}
        void Update(){clock+=unscaled?Time.unscaledDeltaTime:Time.deltaTime;if(bolt)bolt.SetActive(Mathf.Repeat(clock,.55f)<.13f);}
    }
}
