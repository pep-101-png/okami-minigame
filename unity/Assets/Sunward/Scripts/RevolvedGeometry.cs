using System;
using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    // Closed, indexed surface of revolution. Poles and the periodic seam share
    // vertices, unlike the legacy lanterns' open lathe sections.
    public static class RevolvedGeometry
    {
        public static readonly Vector2[] LanternRoof =
        {
            new Vector2(0, 1.50f),
            new Vector2(.49f, 1.50f),
            new Vector2(.51f, 1.57f),
            new Vector2(.39f, 1.65f),
            new Vector2(.25f, 1.80f),
            new Vector2(.09f, 1.86f),
            new Vector2(.07f, 1.98f),
            new Vector2(0, 2.03f)
        };
        public static void Build(Vector2[] profile, int sides, out Vector3[] vertices, out Vector2[] uvs, out int[] indices)
        {
            if (sides < 3 || profile.Length < 2)
                throw new ArgumentException("Invalid lathe profile.");
            var v = new List<Vector3>();
            var uv = new List<Vector2>();
            var tri = new List<int>();
            var rings = new int[profile.Length][];
            for (int j = 0; j < profile.Length; j++)
            {
                var p = profile[j];
                if (!float.IsFinite(p.x) || !float.IsFinite(p.y) || p.x < 0)
                    throw new ArgumentException("Invalid profile radius/height.");
                if (j == profile.Length - 1 && p.x == profile[0].x && p.y == profile[0].y)
                {
                    rings[j] = rings[0];
                    continue;
                }

                rings[j] = new int[sides];
                int pole = -1;
                for (int i = 0; i < sides; i++)
                {
                    if (p.x == 0 && pole >= 0)
                    {
                        rings[j][i] = pole;
                        continue;
                    }

                    float a = i * MathF.PI * 2 / sides;
                    rings[j][i] = v.Count;
                    pole = v.Count;
                    v.Add(new Vector3(MathF.Cos(a) * p.x, p.y, MathF.Sin(a) * p.x));
                    uv.Add(new Vector2(i / (float)sides, j / (float)(profile.Length - 1)));
                }
            }

            void Triangle(int a, int b, int c)
            {
                if (a != b && b != c && a != c)
                    tri.AddRange(new[] { a, b, c });
            }

            for (int j = 0; j < profile.Length - 1; j++)
                for (int i = 0; i < sides; i++)
                {
                    int next = (i + 1) % sides;
                    Triangle(rings[j][i], rings[j + 1][i], rings[j][next]);
                    Triangle(rings[j][next], rings[j + 1][i], rings[j + 1][next]);
                }

            vertices = v.ToArray();
            uvs = uv.ToArray();
            indices = tri.ToArray();
        }
    }
}
