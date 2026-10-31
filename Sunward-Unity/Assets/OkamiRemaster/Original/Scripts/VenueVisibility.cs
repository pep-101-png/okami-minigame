using UnityEngine;

namespace Sunward.Remaster
{
    public sealed class VenueVisibility : MonoBehaviour
    {
        public string venue;
        public WolfMotor player;
        public Renderer[] roof;
        public Renderer[] interiorSurfaces;
        public GameObject[] contents;
        void LateUpdate()
        {
            if(!player)return;
            bool inside=venue=="dojo"?VillageServices.InDojo(player.transform.position):VillageServices.InFoodHouse(player.transform.position);
            if(roof!=null)foreach(var r in roof)if(r)r.enabled=!inside;
            if(interiorSurfaces!=null)foreach(var r in interiorSurfaces)if(r)r.enabled=inside;
            if(contents!=null)foreach(var obj in contents)if(obj && obj.activeSelf!=inside)obj.SetActive(inside);
        }
    }
}
