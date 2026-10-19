using System.Collections.Generic;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class EnvironmentGrounding
    {
        public static int Adjust(Vector3[] vertices, int[] triangles, PaintData material, WorldData world)
        {
            bool rocks = material.kind == "stone", grass = material.kind == "grass-blade";
            if (!rocks && !grass)
                return 0;
            var parent = new int[vertices.Length];
            for (int i = 0; i < parent.Length; i++)
                parent[i] = i;
            int Find(int a)
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
                a = Find(a);
                b = Find(b);
                if (a != b)
                    parent[b] = a;
            }

            // Weld positions for connectivity only; never change the authored topology.
            var shared = new Dictionary<Vector3Int, int>();
            for (int i = 0; i < vertices.Length; i++)
            {
                var v = vertices[i];
                var key = new Vector3Int(Mathf.RoundToInt(v.x * 10000), Mathf.RoundToInt(v.y * 10000), Mathf.RoundToInt(v.z * 10000));
                if (shared.TryGetValue(key, out int other))
                    Join(i, other);
                else
                    shared.Add(key, i);
            }

            for (int i = 0; i < triangles.Length; i += 3)
            {
                Join(triangles[i], triangles[i + 1]);
                Join(triangles[i], triangles[i + 2]);
            }

            // UV seams split coincident vertices. Join by position before finding
            // whole rocks; otherwise each cap/face can be missed as a tiny island.
            var welded = new Dictionary<(int, int, int), int>();
            for (int i = 0; i < vertices.Length; i++)
            {
                var p = vertices[i];
                var key = (Mathf.RoundToInt(p.x * 10000), Mathf.RoundToInt(p.y * 10000), Mathf.RoundToInt(p.z * 10000));
                if (welded.TryGetValue(key, out int prior))
                    Join(i, prior);
                else
                    welded[key] = i;
            }

            var groups = new Dictionary<int, List<int>>();
            for (int i = 0; i < vertices.Length; i++)
            {
                int root = Find(i);
                if (!groups.TryGetValue(root, out var group))
                    groups[root] = group = new List<int>();
                group.Add(i);
            }

            int adjusted = 0;
            foreach (var group in groups.Values)
            {
                if (rocks && (group.Count < 35 || group.Count > 5000))
                    continue;
                var bounds = new Bounds(vertices[group[0]], Vector3.zero);
                foreach (int i in group)
                    bounds.Encapsulate(vertices[i]);
                if (bounds.size.x > 12 || bounds.size.z > 12 || bounds.size.y > 16 || bounds.size.y < .08f)
                    continue;
                var center = bounds.center;
                // Architectural stone, bridge fittings and intentional underwater rocks stay put.
                bool architectural = false;
                foreach (var box in world.boxes)
                    if (Mathf.Abs(center.x - box.x) < box.halfX + .7f && Mathf.Abs(center.z + box.z) < box.halfZ + .7f)
                    {
                        architectural = true;
                        break;
                    }

                if (architectural || Valley.OnBridge(center.x, -center.z))
                    continue;
                float ground = Valley.SurfaceHeight(world.terrain, center);
                float gap = bounds.min.y - ground;
                if (gap < (grass ? .055f : .12f) || gap > 4)
                    continue;
                float shift = ground - bounds.min.y - (grass ? .025f : Mathf.Min(.13f, bounds.size.y * .12f));
                foreach (int i in group)
                    vertices[i].y += shift;
                adjusted++;
            }

            return adjusted;
        }
    }
}
