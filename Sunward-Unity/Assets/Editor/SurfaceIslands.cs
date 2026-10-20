using System.Collections.Generic;
using UnityEngine;

namespace Sunward.Editor
{
    // Material-separated source buffers retain unused vertices. Only referenced
    // triangles may participate in connectivity, bounds or placement decisions.
    public static class SurfaceIslands
    {
        public static List<List<int>> Find(Vector3[] vertices, int[] triangles)
        {
            var parent = new int[vertices.Length];
            var used = new bool[vertices.Length];
            for (int i = 0; i < parent.Length; i++)
                parent[i] = i;
            int Root(int a)
            {
                while (parent[a] != a)
                {
                    parent[a] = parent[parent[a]];
                    a = parent[a];
                }

                return a;
            }

            void Join(int a, int b)
            {
                a = Root(a);
                b = Root(b);
                if (a != b)
                    parent[b] = a;
            }

            foreach (int i in triangles)
                used[i] = true;
            var shared = new Dictionary<(int, int, int), int>();
            for (int i = 0; i < vertices.Length; i++)
            {
                if (!used[i])
                    continue;
                var p = vertices[i];
                var key = (Mathf.RoundToInt(p.x * 10000), Mathf.RoundToInt(p.y * 10000), Mathf.RoundToInt(p.z * 10000));
                if (shared.TryGetValue(key, out int prior))
                    Join(i, prior);
                else
                    shared[key] = i;
            }

            for (int t = 0; t < triangles.Length; t += 3)
            {
                Join(triangles[t], triangles[t + 1]);
                Join(triangles[t], triangles[t + 2]);
            }

            var groups = new Dictionary<int, List<int>>();
            for (int i = 0; i < vertices.Length; i++)
            {
                if (!used[i])
                    continue;
                int root = Root(i);
                if (!groups.TryGetValue(root, out var group))
                    groups[root] = group = new List<int>();
                group.Add(i);
            }

            return new List<List<int>>(groups.Values);
        }
    }
}
