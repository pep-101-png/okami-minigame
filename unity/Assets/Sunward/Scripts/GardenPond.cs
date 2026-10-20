using System;
using UnityEngine;

namespace Sunward
{
    public static class GardenPond
    {
        public const float X = -15, Z = -22, RadiusX = 3.05f, RadiusZ = 2.05f, Water = -.23f;
        static float Ease(float a, float b, float v)
        {
            float t = Mathf.Clamp01((v - a) / (b - a));
            return t * t * (3 - 2 * t);
        }

        public static float Shape(Vector3 p, float original)
        {
            float x = (p.x - X) / RadiusX, z = (p.z - Z) / RadiusZ;
            float r = (float)Math.Sqrt(x * x + z * z);
            if (r >= 1.7f)
                return original;
            if (r < .70f)
                return -.66f + .12f * r * r / (.70f * .70f);
            if (r < .95f)
                return Mathf.Lerp(-.54f, .02f, Ease(.70f, .95f, r));
            if (r < 1.3f)
                return .02f;
            return Mathf.Lerp(.02f, original, Ease(1.3f, 1.7f, r));
        }
    }
}
