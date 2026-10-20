using System.Linq;
using UnityEngine;

namespace Sunward
{
    public sealed class EnvironmentReviewState : MonoBehaviour
    {
        public bool complete;
        public GameObject[] suppressed;
        public Vector3[] removedObstacles;
        void Awake()
        {
            if (suppressed != null)
                foreach (var o in suppressed)
                    if (o)
                        o.SetActive(false);
        }

        void Start()
        {
            var valley = Object.FindFirstObjectByType<Valley>();
            if (valley && removedObstacles != null)
                valley.Data.obstacles = valley.Data.obstacles.Where(c => !removedObstacles.Any(p => Mathf.Abs(c.x - p.x) < .45f && Mathf.Abs(c.z + p.z) < .45f)).ToArray();
        }
    }
}
