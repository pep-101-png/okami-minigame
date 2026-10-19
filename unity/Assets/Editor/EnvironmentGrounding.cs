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
            var groups = SurfaceIslands.Find(vertices, triangles);
            int adjusted = 0;
            foreach (var group in groups)
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
