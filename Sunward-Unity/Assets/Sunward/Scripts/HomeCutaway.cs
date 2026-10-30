using UnityEngine;

namespace Sunward
{
    public sealed class HomeCutaway : MonoBehaviour
    {
        public WolfMotor player;
        public Renderer[] roof;
        public Renderer[] interior;
        void LateUpdate()
        {
            if (!player)
                return;
            Vector3 p = player.transform.position;
            // The old bounds included the porch and the ground outside the
            // walls, exposing every furnishing while approaching the house.
            bool inside = Mathf.Abs(p.x + 34) < 4.5f && Mathf.Abs(p.z + 16) < 3.25f;
            foreach (var r in roof)
                if (r)
                    r.enabled = !inside;
            if (interior != null) foreach (var r in interior) if (r) r.enabled = inside;
        }
    }
}
