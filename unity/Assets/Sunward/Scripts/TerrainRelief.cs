using UnityEngine;

namespace Sunward
{
    public static class TerrainRelief
    {
        public static float Offset(Vector3 p)
        {
            // Keep roads, the river/bridges, home and arena exactly level. The
            // same continuous function is used by render mesh and locomotion.
            float river = Mathf.Clamp01((Mathf.Abs(p.x - Valley.RiverX(-p.z)) - 4.1f) / 2.4f);
            float roads = Mathf.Clamp01((Mathf.Abs(p.x) - 2.7f) / 2.2f);
            roads *= Mathf.Clamp01((Mathf.Abs(p.x + 32) - 2.4f) / 1.6f);
            if (p.x < -9 && p.x > -48)
                roads *= Mathf.Clamp01((Mathf.Abs(p.z + 12) - 2.5f) / 1.5f);
            float home = Mathf.Clamp01(Mathf.Max(Mathf.Abs(p.x + 34) - 5.8f, Mathf.Abs(p.z + 16) - 5f) / 2);
            float arena = Mathf.Clamp01((Mathf.Abs(p.x - 28) + Mathf.Abs(p.z - 8) - 22) / 5);
            float waves = .16f * Mathf.Sin(p.x * .75f + p.z * .31f) + .09f * Mathf.Cos(p.z * 1.1f - p.x * .22f);
            return waves * river * roads * home * arena;
        }
    }
}
