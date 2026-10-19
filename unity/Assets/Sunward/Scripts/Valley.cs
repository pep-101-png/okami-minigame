using UnityEngine;

namespace Sunward
{
    public sealed class Valley : MonoBehaviour
    {
        public TextAsset source;
        public bool visualRelief;
        public WorldData Data { get; private set; }

        void Awake()
        {
            Data = JsonUtility.FromJson<ValleyData>(source.text).world;
            Data.terrain.visualRelief = visualRelief;
        }

        public static Vector3 Point(float x, float y, float threeZ) => new Vector3(x, y, -threeZ);
        static float Smooth(float a, float b, float v)
        {
            float t = Mathf.Clamp01((v - a) / (b - a));
            return t * t * (3 - 2 * t);
        }

        public static float RiverX(float z)
        {
            float Raw(float q) => 1.1f * Mathf.Sin(q * .13f) + .45f * Mathf.Sin(q * .31f) + 2 * Mathf.Exp(-Mathf.Pow((q + 8) / 4, 2));
            float cross = Mathf.Exp(-Mathf.Pow(26 / 4f, 2));
            float a = (Raw(12) - Raw(-14) * cross) / (1 - cross * cross), b = Raw(-14) - a * cross;
            return -23 + Raw(z) - a * Mathf.Exp(-Mathf.Pow((z - 12) / 4, 2)) - b * Mathf.Exp(-Mathf.Pow((z + 14) / 4, 2));
        }

        public static bool OnBridge(float x, float z) => ((Mathf.Abs(z - 12) < 1.28f || Mathf.Abs(z + 14) < 1.28f) && x >= -27.8f && x <= -18.2f);
        public static float Depth(Vector3 p)
        {
            float z = -p.z;
            if (OnBridge(p.x, z))
                return 0;
            float width = 2.45f + .40f * Mathf.Sin(z * .17f + .4f) + .25f * Mathf.Cos(z * .31f), n = Mathf.Abs(p.x - RiverX(z)) / width;
            float deep = 1.15f + .35f * Mathf.Sin(z * .10f + .4f), bed = (-.34f - deep) * (1 - Smooth(.56f, 1.12f, n)) + .10f * Smooth(.56f, 1.12f, n);
            return Mathf.Max(0, -.34f - bed);
        }

        public Vector3 GuardRiver(Vector3 previous, Vector3 next)
        {
            if (Depth(next) <= .34f)
                return next;
            // If already in deep water, allow escape rather than pinning both ends
            // of the bisection inside the river. WaterContact supplies the failsafe.
            if (Depth(previous) > .34f)
                return next;
            Vector3 lo = previous, hi = next;
            for (int i = 0; i < 12; i++)
            {
                Vector3 mid = (lo + hi) * .5f;
                if (Depth(mid) > .32f)
                    hi = mid;
                else
                    lo = mid;
            }

            next.x = lo.x;
            next.z = lo.z;
            return next;
        }

        // Clamp both the bridge coordinate and the sine: sin(float PI) can be
        // slightly negative, which is undefined for the fractional exponent.
        public static float BridgeHeight(float progress)
        {
            float arch = Mathf.Max(0f, Mathf.Sin(Mathf.PI * Mathf.Clamp01(progress)));
            return .10f + .42f * Mathf.Pow(arch, 1.5f);
        }

        public float Height(Vector3 p) => SurfaceHeight(Data.terrain, p);
        public static float SurfaceHeight(TerrainData terrain, Vector3 p)
        {
            float z = -p.z;
            if (OnBridge(p.x, z))
                return BridgeHeight((p.x + 27.8f) / 9.6f);
            if (Mathf.Abs(p.x + 34) < 5.2f && Mathf.Abs(z - 16) < 4.25f)
                return .105f;
            var t = terrain;
            float xg = Mathf.Clamp((p.x - t.minX) / t.step, 0, t.nx - 1.001f), zg = Mathf.Clamp((z - t.minZ) / t.step, 0, t.nz - 1.001f);
            int x = (int)xg, j = (int)zg;
            return Mathf.Lerp(Mathf.Lerp(t.heights[j * t.nx + x], t.heights[j * t.nx + x + 1], xg - x), Mathf.Lerp(t.heights[(j + 1) * t.nx + x], t.heights[(j + 1) * t.nx + x + 1], xg - x), zg - j) + (t.visualRelief ? TerrainRelief.Offset(p) : 0);
        }
    }
}
