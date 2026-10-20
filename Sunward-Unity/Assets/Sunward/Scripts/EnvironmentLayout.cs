using UnityEngine;

namespace Sunward
{
    public static class EnvironmentLayout
    {
        public const float OriginalHomeBridge = 12, HomeBridge = 8;
        public static bool IsHomeRail(BoxData box) => Mathf.Abs(box.x + 23) < .01f && Mathf.Abs(box.halfX - 4.8f) < .01f && box.z > 9 && box.z < 14;
        public static float MoveRail(float sourceZ) => sourceZ + HomeBridge - OriginalHomeBridge;
        public static bool OldBanner(Vector3 p) => p.x > -32 && p.x < -2 && p.z > -7.3f && p.z < -6.9f && p.y > 2.4f;
        public static bool Street(Bounds b) => b.min.x < 3.6f && b.max.x > -3.6f && b.min.z < 18 && b.max.z > -17;
        public static Vector3 ArenaPoint(float angle) => new Vector3(35 + Mathf.Cos(angle) * 18.7f, 0, Mathf.Sin(angle) * 18.7f);
        public static bool GateOpening(Vector3 p) => p.x < 18 && Mathf.Abs(p.z) < 4.7f;
    }
}
