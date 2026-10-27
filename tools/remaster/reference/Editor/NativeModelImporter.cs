using System;
using System.IO;
using UnityEditor;
using UnityEditor.AssetImporters;
using UnityEngine;
using UnityEngine.Rendering;

namespace Sunward.Remaster.Editor
{
    // Research assets only: these do not bind to WolfMotor, combat, save IDs or the live prefab.
    [ScriptedImporter(1, "okamimodel")]
    public sealed class NativeModelImporter : ScriptedImporter
    {
        [Serializable] sealed class Bone { public int parent; public float[] position; }
        [Serializable] sealed class TextureReference { public int index; public string path, sourceSHA256; }
        [Serializable] sealed class Part
        {
            public string name; public int texture;
            public float[] positions, uv, colors, weights;
            public int[] indices, boneIndices;
        }
        [Serializable] sealed class Model
        {
            public int version; public string name, sourceSHA256, sourceUnits;
            public Bone[] bones; public Part[] parts; public TextureReference[] textures;
        }
        const string ShaderPath = "Assets/OkamiRemaster/Village/Demo/Shaders/FarmAnimals.shader";
        static void Require(bool condition, string message) { if (!condition) throw new InvalidDataException(message); }
        static Vector3 Vector(float[] data, int offset) => new Vector3(data[offset], data[offset + 1], data[offset + 2]);
        public override void OnImportAsset(AssetImportContext context)
        {
            Model model = JsonUtility.FromJson<Model>(File.ReadAllText(context.assetPath));
            Require(model != null && model.version == 1, "Unsupported native review model.");
            Require(model.bones != null && model.bones.Length > 0 && model.bones.Length <= 128, "Invalid skeleton.");
            Require(model.parts != null && model.parts.Length > 0 && model.parts.Length <= 128, "Invalid mesh parts.");
            context.DependsOnSourceAsset(ShaderPath);
            Shader shader = AssetDatabase.LoadAssetAtPath<Shader>(ShaderPath);
            Require(shader != null, "Painted review shader is missing.");
            GameObject root = new GameObject(model.name + " - native review, unscaled");
            context.AddObjectToAsset("root", root); context.SetMainObject(root);
            Transform[] bones = new Transform[model.bones.Length];
            Matrix4x4[] bindposes = new Matrix4x4[bones.Length];
            for (int i = 0; i < bones.Length; ++i)
            {
                Bone b = model.bones[i];
                Require(b.parent >= -1 && b.parent < i && b.position != null && b.position.Length == 3, "Invalid native bone hierarchy.");
                bones[i] = new GameObject("NativeBone_" + i.ToString("D2")).transform;
                bones[i].SetParent(b.parent < 0 ? root.transform : bones[b.parent], false);
                bones[i].localPosition = Vector(b.position, 0);
                bindposes[i] = bones[i].worldToLocalMatrix * root.transform.localToWorldMatrix;
            }
            for (int partIndex = 0; partIndex < model.parts.Length; ++partIndex)
            {
                Part part = model.parts[partIndex];
                Require(part.positions != null && part.positions.Length >= 9 && part.positions.Length % 3 == 0, "Invalid vertex positions.");
                int count = part.positions.Length / 3;
                Require(part.uv != null && part.uv.Length == count * 2 && part.colors != null && part.colors.Length == count * 4, "Invalid UV/color stream.");
                Require(part.weights != null && part.weights.Length == count * 3 && part.boneIndices != null && part.boneIndices.Length == count * 3, "Invalid native skin weights.");
                Require(part.indices != null && part.indices.Length % 3 == 0, "Invalid triangle stream.");
                Vector3[] positions = new Vector3[count]; Vector2[] uv = new Vector2[count];
                Color[] colors = new Color[count]; BoneWeight[] weights = new BoneWeight[count];
                for (int i = 0; i < count; ++i)
                {
                    positions[i] = Vector(part.positions, i * 3); uv[i] = new Vector2(part.uv[i * 2], part.uv[i * 2 + 1]);
                    colors[i] = new Color(part.colors[i * 4], part.colors[i * 4 + 1], part.colors[i * 4 + 2], part.colors[i * 4 + 3]);
                    float sum = 0;
                    for (int j = 0; j < 3; ++j)
                    {
                        Require(part.boneIndices[i * 3 + j] >= 0 && part.boneIndices[i * 3 + j] < bones.Length, "Skin bone is out of range.");
                        float weight = part.weights[i * 3 + j]; Require(weight >= 0 && weight <= 1, "Invalid skin weight."); sum += weight;
                    }
                    Require(Mathf.Abs(sum - 1) <= .005f, "Native skin weight sum is invalid.");
                    weights[i] = new BoneWeight { boneIndex0 = part.boneIndices[i * 3], boneIndex1 = part.boneIndices[i * 3 + 1], boneIndex2 = part.boneIndices[i * 3 + 2], weight0 = part.weights[i * 3], weight1 = part.weights[i * 3 + 1], weight2 = part.weights[i * 3 + 2] };
                }
                foreach (int index in part.indices) Require(index >= 0 && index < count, "Triangle index is out of range.");
                TextureReference reference = Array.Find(model.textures, t => t.index == part.texture);
                Require(reference != null && Path.GetFileName(reference.path) == reference.path, "Invalid original texture reference.");
                string texturePath = Path.GetDirectoryName(context.assetPath).Replace('\\', '/') + "/" + reference.path;
                context.DependsOnSourceAsset(texturePath);
                Texture2D texture = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
                Require(texture != null, "Missing original texture: " + texturePath);
                Mesh mesh = new Mesh { name = part.name, indexFormat = IndexFormat.UInt32 };
                mesh.vertices = positions; mesh.uv = uv; mesh.colors = colors; mesh.triangles = part.indices;
                // These MD files contain no normal stream. Normals are derived only for diagnostic lighting.
                mesh.RecalculateNormals(); mesh.RecalculateBounds(); mesh.bindposes = bindposes; mesh.boneWeights = weights;
                context.AddObjectToAsset("mesh-" + partIndex, mesh);
                Material material = new Material(shader) { name = model.name + " painted slot " + part.texture };
                material.SetTexture("_MainTex", texture); material.SetFloat("_Cutoff", .3f);
                context.AddObjectToAsset("material-" + partIndex, material);
                GameObject visual = new GameObject(part.name); visual.transform.SetParent(root.transform, false);
                SkinnedMeshRenderer renderer = visual.AddComponent<SkinnedMeshRenderer>();
                renderer.sharedMesh = mesh; renderer.sharedMaterial = material; renderer.bones = bones; renderer.rootBone = root.transform;
                renderer.localBounds = mesh.bounds; renderer.quality = SkinQuality.Bone4;
            }
        }
    }
}
