using System;
using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    public static class SeatedStoneGeometry
    {
        public static void Build(int seed, out Vector3[] vertices, out int[] triangles)
        {
            const int n = 32;
            var v = new List<Vector3>();
            var ix = new List<int>();
            float[] height =
            {
                0,
                .07f,
                .18f,
                .32f,
                .48f,
                .65f,
                .80f,
                .92f,
                .975f
            };
            float[] radius =
            {
                .55f,
                .73f,
                .90f,
                .99f,
                1,
                .92f,
                .76f,
                .51f,
                .24f
            };
            for (int row = 0; row < height.Length; row++)
                for (int i = 0; i < n; i++)
                {
                    float a = i * Mathf.PI * 2 / n;
                    float r = radius[row] * (1 + .055f * Mathf.Sin(a * 3 + seed) + .035f * Mathf.Cos(a * 5 - seed));
                    float twist = .045f * Mathf.Sin(row * .71f + seed);
                    v.Add(new Vector3(Mathf.Cos(a + twist) * r, height[row] + (row == 0 ? 0 : .008f * Mathf.Sin(a * 4 + row + seed)), Mathf.Sin(a + twist) * r));
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
                ix.AddRange(new[] { bottom, i, next, top, (height.Length - 1) * n + next, (height.Length - 1) * n + i });
            }

            vertices = v.ToArray();
            triangles = ix.ToArray();
        }
    }
}
