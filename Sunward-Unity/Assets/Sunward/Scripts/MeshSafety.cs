using System;
using UnityEngine;

namespace Sunward
{
    public static class MeshSafety
    {
        public static bool Finite(Vector3 point) => float.IsFinite(point.x) && float.IsFinite(point.y) && float.IsFinite(point.z);
        public static void Validate(string owner, Vector3[] vertices, int[] indices)
        {
            for (int i = 0; i < vertices.Length; i++)
                if (!Finite(vertices[i]))
                    throw new InvalidOperationException(owner + " contains invalid vertex " + i + ": " + vertices[i]);
            if (indices.Length % 3 != 0)
                throw new InvalidOperationException(owner + " contains an incomplete triangle");
            foreach (int index in indices)
                if (index < 0 || index >= vertices.Length)
                    throw new InvalidOperationException(owner + " has invalid triangle index " + index);
        }
    }
}
