using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class RockSeating
    {
        // Frozen V3 provenance: free stones and river stones, never stone lantern
        // pillars, house foundations, bridge fittings or paving discs.
        public static bool Source(int id) => id == 371 || id >= 779 && id <= 783 || id >= 788 && id <= 789 || id >= 792 && id <= 793;
        public static bool Suitable(WorldData world, Bounds b)
        {
            if (b.size.y < .06f || b.size.y > 8 || b.size.x < .25f || b.size.z < .25f || b.size.x > 10 || b.size.z > 10)
                return false;
            if (Valley.OnBridge(b.center.x, -b.center.z))
                return false;
            foreach (var box in world.boxes)
                if (Mathf.Abs(b.center.x - box.x) < box.halfX + .65f && Mathf.Abs(b.center.z + box.z) < box.halfZ + .65f)
                    return false;
            return b.size.y < Mathf.Max(b.size.x, b.size.z) * 2.8f;
        }

        public static float Bottom(WorldData world, Bounds b)
        {
            float bed = float.PositiveInfinity;
            // Sample the whole footprint, on the physical terrain triangles.
            // A low point below a bridge's WALKING deck is not ground contact.
            for (int z = 0; z <= 8; z++)
                for (int x = 0; x <= 8; x++)
                {
                    var q = new Vector3(b.min.x + b.size.x * x / 8, 0, b.min.z + b.size.z * z / 8);
                    bed = Mathf.Min(bed, Valley.TerrainHeight(world.terrain, q));
                }

            return bed - Mathf.Min(.22f, b.size.y * .25f);
        }
    }
}
