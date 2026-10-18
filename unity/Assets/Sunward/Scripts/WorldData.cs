using System;
using UnityEngine;

namespace Sunward
{
    [Serializable]
    public class ValleyData
    {
        public AssetGroup[] assets;
        public PaintData[] materials;
        public WorldData world;
    }

    [Serializable]
    public class AssetGroup
    {
        public string name;
        public MeshData[] meshes;
    }

    [Serializable]
    public class MeshData
    {
        public string name;
        public int material, vertices, indices, offset;
    }

    [Serializable]
    public class PaintData
    {
        public string name, color, kind;
        public int texture, side;
        public float opacity, cutout;
        public bool transparent, doubleSided, vertexColors;
    }

    [Serializable]
    public class WorldData
    {
        public BoundsData bounds;
        public BoxData[] boxes;
        public CircleData[] obstacles;
        public TerrainData terrain;
        public NpcData[] npcs;
        public string source;
    }

    [Serializable]
    public class BoundsData
    {
        public float minX, maxX, minZ, maxZ;
    }

    [Serializable]
    public class BoxData
    {
        public float x, z, halfX, halfZ;
    }

    [Serializable]
    public class CircleData
    {
        public float x, z, r;
    }

    [Serializable]
    public class TerrainData
    {
        public float minX, minZ, step;
        public int nx, nz;
        public float[] heights;
    }

    [Serializable]
    public class NpcData
    {
        public string asset, name;
        public float[] position;
        public string[] lines;
    }
}
