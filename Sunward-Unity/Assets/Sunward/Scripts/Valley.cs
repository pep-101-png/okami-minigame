using UnityEngine;

namespace Sunward
{
    public sealed class Valley : MonoBehaviour
    {
        public TextAsset source;
        public bool visualRelief, gardenPondBasin, exactTerrainSurface;
        public float homeBridgeSourceZ = 12;
        public static float HomeBridgeSourceZ = 12;
        public WorldData Data { get; private set; }

        void Awake()
        {
            Data = JsonUtility.FromJson<ValleyData>(source.text).world;
            HomeBridgeSourceZ = homeBridgeSourceZ;
            foreach (var box in Data.boxes)
                if (EnvironmentLayout.IsHomeRail(box))
                    box.z += homeBridgeSourceZ - 12;
            Data.terrain.visualRelief = visualRelief;
            Data.terrain.gardenPondBasin = gardenPondBasin;
            Data.terrain.exactSurface = exactTerrainSurface;
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

        public static bool OnBridge(float x, float z) => ((Mathf.Abs(z - HomeBridgeSourceZ) < 1.28f || Mathf.Abs(z + 14) < 1.28f) && x >= -27.8f && x <= -18.2f);
        public static float Depth(Vector3 p)
        {
            float z = -p.z;
            if (OnBridge(p.x, z))
                return 0;
            return WaterDepth(p);
        }

        // Geometry of the river bed, including water beneath bridge decks.
        public static float WaterDepth(Vector3 p)
        {
            float z = -p.z;
            float width = 2.45f + .40f * Mathf.Sin(z * .17f + .4f) + .25f * Mathf.Cos(z * .31f), n = Mathf.Abs(p.x - RiverX(z)) / width;
            float deep = 1.15f + .35f * Mathf.Sin(z * .10f + .4f), bed = (-.34f - deep) * (1 - Smooth(.56f, 1.12f, n)) + .10f * Smooth(.56f, 1.12f, n);
            return Mathf.Max(0, -.34f - bed);
        }

        public Vector3 GuardRiver(Vector3 previous, Vector3 next)
        {
            // Swimming now owns deep-water movement. Keep the compatibility entry
            // point for callers; boundaries/solid-world sweeps remain in WolfMotor.
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
            return TerrainHeight(terrain, p);
        }

        // Physical ground only: never return the bridge deck or home floor.
        public static float TerrainHeight(TerrainData t, Vector3 p)
        {
            float z = -p.z;
            float xg = Mathf.Clamp((p.x - t.minX) / t.step, 0, t.nx - 1.001f), zg = Mathf.Clamp((z - t.minZ) / t.step, 0, t.nz - 1.001f);
            int x = (int)xg, j = (int)zg;
            float u = xg - x, v = zg - j;
            if (!t.exactSurface)
                return Mathf.Lerp(Mathf.Lerp(t.heights[j * t.nx + x], t.heights[j * t.nx + x + 1], u), Mathf.Lerp(t.heights[(j + 1) * t.nx + x], t.heights[(j + 1) * t.nx + x + 1], u), v) + (t.visualRelief ? TerrainRelief.Offset(p) : 0);
            float H(int dx, int dz)
            {
                var q = new Vector3(t.minX + (x + dx) * t.step, t.heights[(j + dz) * t.nx + x + dx], -(t.minZ + (j + dz) * t.step));
                return RenderHeight(t, q);
            }

            float h00 = H(0, 0), h10 = H(1, 0), h01 = H(0, 1), h11 = H(1, 1);
            // The actual exported terrain uses the 10--01 diagonal, not a
            // bilinear patch. This exactly matches its two rendered triangles.
            return u + v <= 1 ? h00 + (h10 - h00) * u + (h01 - h00) * v : h11 + (h01 - h11) * (1 - u) + (h10 - h11) * (1 - v);
        }

        public static float RenderHeight(TerrainData t, Vector3 original)
        {
            float h = original.y + (t.visualRelief ? TerrainRelief.Offset(original) : 0);
            return t.gardenPondBasin ? GardenPond.Shape(original, h) : h;
        }
    }
}
