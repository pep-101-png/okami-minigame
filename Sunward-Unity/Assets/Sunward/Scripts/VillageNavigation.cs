using UnityEngine;

namespace Sunward
{
    // Analytic navigation matches the ported source's building/rail and rock shapes.
    // No baked NavMesh or additional package is needed for short village strolls.
    public static class VillageNavigation
    {
        static readonly Vector3[] Directions =
        {
            Vector3.right,
            Vector3.left,
            Vector3.forward,
            Vector3.back
        };
        public static bool Clear(WorldData world, Vector3 p, float radius = .45f)
        {
            if (!float.IsFinite(p.x) || !float.IsFinite(p.z))
                return false;
            // Outdoor residents must not spawn or route through enterable rooms.
            if(Mathf.Abs(p.x)<8.7f+radius && p.z>14.5f-radius && p.z<35.5f+radius ||
                Mathf.Abs(p.x-10)<6.2f+radius && Mathf.Abs(p.z+15)<4.4f+radius)return false;
            var bounds = world.bounds;
            if (p.x < bounds.minX + radius || p.x > bounds.maxX - radius || p.z < -bounds.maxZ + radius || p.z > -bounds.minZ - radius || Valley.Depth(p) > .10f)
                return false;
            foreach (var box in world.boxes)
                if (Mathf.Abs(p.x - box.x) < box.halfX + radius && Mathf.Abs(p.z + box.z) < box.halfZ + radius)
                    return false;
            foreach (var obstacle in world.obstacles)
                if (new Vector2(p.x - obstacle.x, p.z + obstacle.z).sqrMagnitude < (radius + obstacle.r) * (radius + obstacle.r))
                    return false;
            float h = Valley.SurfaceHeight(world.terrain, p);
            // Reject cliff edges, steep banks and ledges, including the footprint.
            foreach (var direction in Directions)
                if (Mathf.Abs(Valley.SurfaceHeight(world.terrain, p + direction * radius) - h) > radius * .75f)
                    return false;
            return true;
        }

        public static bool FindSafe(WorldData world, Vector3 desired, out Vector3 result, float radius = .45f, float search = 12)
        {
            if (Clear(world, desired, radius))
            {
                result = desired;
                result.y = Valley.SurfaceHeight(world.terrain, result);
                return true;
            }

            for (float distance = .4f; distance <= search; distance += .4f)
                for (int i = 0; i < 48; i++)
                {
                    float angle = i * Mathf.PI * 2 / 48;
                    var p = desired + new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * distance;
                    if (!Clear(world, p, radius))
                        continue;
                    p.y = Valley.SurfaceHeight(world.terrain, p);
                    result = p;
                    return true;
                }

            result = desired;
            return false;
        }

        public static bool SegmentClear(WorldData world, Vector3 from, Vector3 to, float radius = .45f)
        {
            int steps = Mathf.Max(1, Mathf.CeilToInt(Vector3.Distance(from, to) / .15f));
            for (int i = 1; i <= steps; i++)
                if (!Clear(world, Vector3.Lerp(from, to, i / (float)steps), radius))
                    return false;
            return true;
        }
    }
}
