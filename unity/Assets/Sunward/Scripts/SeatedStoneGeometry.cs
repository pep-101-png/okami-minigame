using System;
using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    public static class SeatedStoneGeometry
    {
        public static void Build(int seed, out Vector3[] vertices, out int[] triangles)
        {
            const int n = 20;
            var v = new List<Vector3>();
            var ix = new List<int>();
            float[] height =
            {
                0,
                .12f,
                .38f,
                .71f,
                .92f
            };
            float[] radius =
            {
                .55f,
                .86f,
                1,
                .83f,
                .43f
            };
            for (int row = 0; row < height.Length; row++)
                for (int i = 0; i < n; i++)
                {
                    float a = i * Mathf.PI * 2 / n;
                    float r = radius[row] * (1 + .055f * Mathf.Sin(a * 3 + seed) + .035f * Mathf.Cos(a * 5 - seed));
                    v.Add(new Vector3(Mathf.Cos(a) * r, height[row], Mathf.Sin(a) * r));
                }

            for (int row = 0; row < height.Length - 1; row++)
                for (int i = 0; i < n; i++)
                {
                    int a = row * n + i, b = row * n + (i + 1) % n, c = a + n, d = b + n;
                    ix.AddRange(new[] { a, c, b, b, c, d });
                }

            int bottom = v.Count;
            v.Add(Vector3.zero);
            int top = v.Count;
            v.Add(new Vector3(.035f, 1, -.025f));
            for (int i = 0; i < n; i++)
            {
                int next = (i + 1) % n;
                ix.AddRange(new[] { bottom, i, next, top, 4 * n + next, 4 * n + i });
            }

            vertices = v.ToArray();
            triangles = ix.ToArray();
        }
    }
}
