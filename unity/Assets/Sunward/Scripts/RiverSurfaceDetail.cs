using UnityEngine;

namespace Sunward
{
    // A fixed, bounded list of seated-rock contacts; all motion runs in the
    // water shader. No per-frame mesh generation, reflection camera or allocation.
    public sealed class RiverSurfaceDetail : MonoBehaviour
    {
        public Material[] surfaces;
        public Vector4[] contacts;
        void Start()
        {
            var points = new Vector4[16];
            int count = Mathf.Min(16, contacts == null ? 0 : contacts.Length);
            for (int i = 0; i < count; i++)
                points[i] = contacts[i];
            foreach (var m in surfaces)
                if (m)
                {
                    m.SetVectorArray("_RockCenters", points);
                    m.SetFloat("_RockCount", count);
                }
        }
    }
}
