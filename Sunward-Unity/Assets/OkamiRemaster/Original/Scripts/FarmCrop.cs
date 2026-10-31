using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class FarmCrop : MonoBehaviour
    {
        public int index;
        public string resource;
        public float carryScale=.45f;
        public Vector3 carryOffset;
        public bool Harvested { get; private set; }
        Vector3 planted;
        float regrow;
        Renderer[] visual;
        void Awake(){planted=transform.position;visual=GetComponentsInChildren<Renderer>();}
        public void Harvest(){Harvested=true;regrow=Time.time+180;foreach(var r in visual)r.enabled=false;}
        public bool Bloom(){if(!Harvested)return false;Restore();return true;}
        void Restore(){Harvested=false;transform.position=planted;foreach(var r in visual)r.enabled=true;}
        void Update(){if(Harvested && Time.time>=regrow)Restore();}
    }
}
