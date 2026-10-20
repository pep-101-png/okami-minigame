using UnityEngine;

namespace Sunward
{
    // Serialized pre-upgrade datums make the 15% visual update idempotent.
    public sealed class MillVisualDatum : MonoBehaviour
    {
        public Vector3 wheelScale, wheelPosition, fixedStonePosition;
        public Vector3[] mechanismPositions;
        public Transform fixedStone;
    }
}
