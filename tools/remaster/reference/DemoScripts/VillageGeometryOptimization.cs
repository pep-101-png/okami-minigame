using System;
using System.Collections.Generic;
using UnityEngine;

namespace SunwardVillageDemo
{
    internal static class VillageGeometryOptimization
    {
        readonly struct Face : IEquatable<Face>
        {
            readonly int a, b, c;
            public Face(int x, int y, int z)
            {
                if (x > y) { int t = x; x = y; y = t; }
                if (y > z) { int t = y; y = z; z = t; }
                if (x > y) { int t = x; x = y; y = t; }
                a = x; b = y; c = z;
            }
            public bool Equals(Face other) => a == other.a && b == other.b && c == other.c;
            public override bool Equals(object other) => other is Face face && Equals(face);
            public override int GetHashCode() { unchecked { return ((a * 397) ^ b) * 397 ^ c; } }
        }
        public static int[] RemoveRedundantOpaqueFaces(int[] indices, Material material, bool collider)
        {
            // These four review shaders are opaque, Z-writing and Cull Off. Drawing
            // the same vertex triplet again (including reversed winding) adds no art.
            // Transparent paint and every original physics mesh retain all indices.
            if (collider || material == null || material.shader == null || material.renderQueue >= 2500) return indices;
            string shader = material.shader.name;
            if (shader != "VillageDemo/Painted Surface" && shader != "VillageDemo/Physical Ink Hull" &&
                shader != "VillageDemo/Continuous Painted Water" && shader != "VillageDemo/Grass Dirt Transition") return indices;
            HashSet<Face> seen = new HashSet<Face>();
            List<int> kept = new List<int>(indices.Length);
            for (int i = 0; i < indices.Length; i += 3)
            {
                if (!seen.Add(new Face(indices[i], indices[i + 1], indices[i + 2]))) continue;
                kept.Add(indices[i]); kept.Add(indices[i + 1]); kept.Add(indices[i + 2]);
            }
            return kept.Count == indices.Length ? indices : kept.ToArray();
        }
    }
}
