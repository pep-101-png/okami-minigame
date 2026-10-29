using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;

namespace Sunward.Remaster
{
    // Uses the original MD skeleton and weights. It does not retarget to the FBX.
    public sealed class NativePaintedRig : IDisposable
    {
        [Serializable] sealed class Bone { public int parent; public float[] position; }
        [Serializable] sealed class TextureReference { public int index; public string path; public bool vertexOnly; }
        [Serializable] sealed class Part
        {
            public string name; public int texture;
            public float[] positions, uv, colors, weights;
            public int[] indices, boneIndices;
        }
        [Serializable] sealed class Model { public int version; public Bone[] bones; public Part[] parts; public TextureReference[] textures; }
        public readonly GameObject Root;
        public readonly Transform[] Bones;
        readonly List<UnityEngine.Object> owned = new List<UnityEngine.Object>();
        public NativePaintedRig(string resource, Transform parent)
        {
            var asset = Resources.Load<TextAsset>(resource + "/Model");
            if (!asset) throw new InvalidDataException("Missing native model: " + resource);
            var model = JsonUtility.FromJson<Model>(asset.text);
            if (model == null || model.version != 1 || model.bones == null || model.parts == null)
                throw new InvalidDataException("Invalid native MD model: " + resource);
            Root = new GameObject("Original Okami " + resource.Substring(resource.LastIndexOf('/') + 1));
            Root.transform.SetParent(parent, false);
            Root.SetActive(false);
            try
            {
                Bones = new Transform[model.bones.Length + 1];
                Bones[0] = new GameObject("MotionRoot (controller translation removed)").transform;
                Bones[0].SetParent(Root.transform, false);
                for (int i = 0; i < model.bones.Length; i++)
                {
                    var b = model.bones[i];
                    if (b.parent < -1 || b.parent >= i) throw new InvalidDataException("Invalid native hierarchy");
                    Bones[i + 1] = new GameObject("NativeBone_" + i.ToString("D2")).transform;
                    Bones[i + 1].SetParent(Bones[b.parent + 1], false);
                    Bones[i + 1].localPosition = Vector(b.position, 0);
                }
                var bindposes = new Matrix4x4[Bones.Length];
                for (int i = 0; i < Bones.Length; i++) bindposes[i] = Bones[i].worldToLocalMatrix * Root.transform.localToWorldMatrix;
                var template = Resources.Load<Material>("NativePlayer/Surface");
                if (!template || !template.shader || !template.shader.isSupported)
                    throw new InvalidDataException("Native painted material is unavailable");
                var materials = new Dictionary<int, Material>();
                foreach (var reference in model.textures)
                {
                    var material = new Material(template) { name = "Original painted texture " + reference.index };
                    if (!reference.vertexOnly)
                    {
                        var texture = Resources.Load<Texture2D>(resource + "/" + Path.GetFileNameWithoutExtension(reference.path));
                        if (!texture) { UnityEngine.Object.Destroy(material); throw new InvalidDataException("Missing native texture: " + reference.path); }
                        material.SetTexture("_MainTex", texture);
                    }
                    materials.Add(reference.index, material); owned.Add(material);
                }
                foreach (var part in model.parts)
                {
                    int count = part.positions.Length / 3;
                    if (part.weights.Length != count * 3 || part.boneIndices.Length != count * 3 || part.uv.Length != count * 2 || part.colors.Length != count * 4)
                        throw new InvalidDataException("Native vertex streams disagree");
                    var positions = new Vector3[count]; var uv = new Vector2[count];
                    var colors = new Color[count]; var weights = new BoneWeight[count];
                    for (int i = 0; i < count; i++)
                    {
                        positions[i] = Vector(part.positions, i * 3); uv[i] = new Vector2(part.uv[i * 2], part.uv[i * 2 + 1]);
                        colors[i] = new Color(part.colors[i * 4], part.colors[i * 4 + 1], part.colors[i * 4 + 2], part.colors[i * 4 + 3]);
                        int k = i * 3; float sum = part.weights[k] + part.weights[k + 1] + part.weights[k + 2];
                        if (sum < .99f || sum > 1.01f) throw new InvalidDataException("Invalid native skin weight sum");
                        for (int j = 0; j < 3; j++)
                            if (part.boneIndices[k + j] < -1 || part.boneIndices[k + j] >= model.bones.Length)
                                throw new InvalidDataException("Invalid native skin bone");
                        weights[i] = new BoneWeight { boneIndex0 = part.boneIndices[k] + 1, boneIndex1 = part.boneIndices[k + 1] + 1, boneIndex2 = part.boneIndices[k + 2] + 1,
                            weight0 = part.weights[k] / sum, weight1 = part.weights[k + 1] / sum, weight2 = part.weights[k + 2] / sum };
                    }
                    foreach (int index in part.indices) if (index < 0 || index >= count) throw new InvalidDataException("Invalid native triangle");
                    var mesh = new Mesh { name = part.name, indexFormat = IndexFormat.UInt32 };
                    owned.Add(mesh); mesh.vertices = positions; mesh.uv = uv; mesh.colors = colors;
                    mesh.triangles = part.indices; mesh.RecalculateNormals(); mesh.RecalculateBounds();
                    mesh.bindposes = bindposes; mesh.boneWeights = weights;
                    var visual = new GameObject(part.name); visual.layer = parent.gameObject.layer; visual.transform.SetParent(Root.transform, false);
                    var renderer = visual.AddComponent<SkinnedMeshRenderer>();
                    renderer.sharedMesh = mesh; renderer.sharedMaterial = materials[part.texture];
                    renderer.bones = Bones; renderer.rootBone = Bones[0]; renderer.quality = SkinQuality.Bone4;
                    renderer.localBounds = new Bounds(new Vector3(0, 1, 0), new Vector3(8, 8, 8));
                }
            }
            catch { Dispose(); throw; }
        }
        static Vector3 Vector(float[] data, int offset) => new Vector3(data[offset], data[offset + 1], data[offset + 2]);
        public void Dispose()
        {
            if (Root) UnityEngine.Object.Destroy(Root);
            foreach (var item in owned) if (item) UnityEngine.Object.Destroy(item);
            owned.Clear();
        }
    }
}
