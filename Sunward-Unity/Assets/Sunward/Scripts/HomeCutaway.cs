using UnityEngine;

namespace Sunward
{
    public sealed class HomeCutaway : MonoBehaviour
    {
        public WolfMotor player;
        public Renderer[] roof;
        public Renderer[] interior;
        public GameObject[] contents;
        public static bool Inside(Vector3 p)=>Mathf.Abs(p.x+34)<4.1f && Mathf.Abs(p.z+16)<2.9f;
        void LateUpdate()
        {
            if (!player)
                return;
            Vector3 p = player.transform.position;
            // The old bounds included the porch and the ground outside the
            // walls, exposing every furnishing while approaching the house.
            bool inside = Inside(p);
            foreach (var r in roof)
                if (r)
                    r.enabled = !inside;
            if (interior != null) foreach (var r in interior) if (r) r.enabled = inside;
            if(contents!=null)foreach(var obj in contents)if(obj && obj.activeSelf!=inside)obj.SetActive(inside);
        }
    }
}
