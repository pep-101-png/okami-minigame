using System.Linq;
using UnityEngine;

namespace Sunward
{
    [DefaultExecutionOrder(-50)]
    public sealed class SurfaceRepairState : MonoBehaviour
    {
        public bool validated;
        public GameObject[] suppressedObjects;
        public Vector3[] removedTreePositions;
        void Awake()
        {
            foreach (var o in suppressedObjects)
                if (o)
                    o.SetActive(false);
        }

        void Start()
        {
            var valley = UnityEngine.Object.FindFirstObjectByType<Valley>();
            if (valley && removedTreePositions != null)
                valley.Data.obstacles = valley.Data.obstacles.Where(c => !removedTreePositions.Any(p => Mathf.Abs(c.x - p.x) < .35f && Mathf.Abs(c.z + p.z) < .35f)).ToArray();
        }
    }
}
