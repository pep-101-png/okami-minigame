using UnityEngine;

namespace Sunward
{
    public sealed class HomeCutaway : MonoBehaviour
    {
        public WolfMotor player;
        public Renderer[] roof;
        void LateUpdate()
        {
            if (!player)
                return;
            Vector3 p = player.transform.position;
            bool inside = Mathf.Abs(p.x + 34) < 5.6f && Mathf.Abs(p.z + 16) < 5;
            foreach (var r in roof)
                if (r)
                    r.enabled = !inside;
        }
    }
}
