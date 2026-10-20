using System;
using UnityEngine;

namespace Sunward
{
    public static class MarketTreeRules
    {
        static string Clean(string name) => (name ?? "").Replace("(Clone)", "").Replace("(Instance)", "").Trim();
        public static bool TreeMesh(string name)
        {
            name = Clean(name);
            foreach (string family in new[]
            {
                "Cherry_A",
                "Cherry_B",
                "Maple_A",
                "Pine_A"
            }

            )
                if (name == family + "_Mesh" || name.StartsWith(family + "_Mesh.", StringComparison.Ordinal) || name.StartsWith(family + "_Mesh_", StringComparison.Ordinal) || name.StartsWith(family + "_MeshPart", StringComparison.Ordinal))
                    return true;
            return System.Text.RegularExpressions.Regex.IsMatch(name, @"(?i)(^|[_ .-])tree([_ .-]|\d|$)");
        }

        public static bool KnownFamily(string name)
        {
            name = Clean(name);
            return name == "Cherry_A" || name == "Cherry_B" || name == "Maple_A" || name == "Pine_A";
        }

        public static bool TreeOwner(string name)
        {
            name = Clean(name);
            return name == "Cherry_A" || name == "Cherry_B" || name == "Maple_A" || name == "Pine_A" || name.Equals("Tree", StringComparison.OrdinalIgnoreCase) || name.StartsWith("Tree_", StringComparison.OrdinalIgnoreCase) || name.StartsWith("Tree ", StringComparison.OrdinalIgnoreCase) || name.EndsWith(" Tree", StringComparison.OrdinalIgnoreCase);
        }

        // Use the tree's ground datum as well as its visible bounds: a large
        // background canopy touching the street is not a tree in the street.
        public static bool InMarket(Vector3 datum, Bounds visible) => Mathf.Abs(datum.x) < 4.3f && datum.z > -18 && datum.z < 19 && visible.size.y > 1.5f && visible.max.y > 1.8f;
    }
}
