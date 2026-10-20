using System.Linq;
using UnityEngine;

namespace Sunward
{
    // Extend the existing analytic navigation/recovery map with the actual
    // new solid furniture/stall/mill bounds after Valley's Awake deserializes it.
    [RequireComponent(typeof(BoxCollider))]
    public sealed class VillageWorldSolid : MonoBehaviour
    {
        void Start()
        {
            var valley = UnityEngine.Object.FindFirstObjectByType<Valley>();
            var box = GetComponent<BoxCollider>();
            if (!valley || !box.enabled)
                return;
            var b = box.bounds;
            valley.Data.boxes = valley.Data.boxes.Concat(new[] { new BoxData { x = b.center.x, z = -b.center.z, halfX = b.extents.x, halfZ = b.extents.z } }).ToArray();
        }
    }
}
