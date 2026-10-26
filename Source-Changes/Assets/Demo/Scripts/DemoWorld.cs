using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using UnityEngine;
using UnityEngine.Rendering;

namespace SunwardVillageDemo
{
    [ExecuteAlways, DefaultExecutionOrder(-200)]
    public sealed class DemoWorld : MonoBehaviour
    {
        public string geometryResource = "DemoGeometry/VillageWorld";
        GameObject generated;
        readonly List<Mesh> meshes = new List<Mesh>();
        bool building;
        public string LastError { get; private set; }
        void Awake() { if (Application.isPlaying) BuildWorld(); }
        void OnEnable()
        {
            if (Application.isPlaying) { BuildWorld(); return; }
#if UNITY_EDITOR
            UnityEditor.EditorApplication.delayCall += BuildWhenReady;
#endif
        }
#if UNITY_EDITOR
        void BuildWhenReady()
        {
            if (this == null || !isActiveAndEnabled) return;
            if (UnityEditor.EditorApplication.isCompiling || UnityEditor.EditorApplication.isUpdating) { UnityEditor.EditorApplication.delayCall += BuildWhenReady; return; }
            BuildWorld();
        }
#endif
        public void BuildWorld()
        {
            if (building || generated != null) return;
            building = true;
            try
            {
                TextAsset data = Resources.Load<TextAsset>(geometryResource);
                if (data == null) throw new InvalidDataException("The separate demo geometry bundle is missing.");
                generated = new GameObject("Generated village - local demo only"); generated.transform.SetParent(transform, false);
                if (!Application.isPlaying) generated.hideFlags = HideFlags.DontSaveInEditor;
                Dictionary<string, Material> materials = new Dictionary<string, Material>();
                Dictionary<string, Transform> parts = new Dictionary<string, Transform>();
                using (MemoryStream input = new MemoryStream(data.bytes, false))
                using (GZipStream gzip = new GZipStream(input, CompressionMode.Decompress))
                using (BinaryReader reader = new BinaryReader(gzip))
                {
                    if (reader.ReadInt32() != 0x32565753 || reader.ReadInt32() != 1) throw new InvalidDataException("Unsupported village data format.");
                    int count = reader.ReadInt32();
                    if (count < 1 || count > 4096) throw new InvalidDataException("Invalid village mesh count.");
                    for (int k = 0; k < count; ++k)
                    {
                        string name = ReadText(reader), materialId = ReadText(reader); bool collider = reader.ReadByte() != 0;
                        int vertexCount = reader.ReadInt32(), indexCount = reader.ReadInt32();
                        if (vertexCount < 3 || vertexCount > 500000 || indexCount < 3 || indexCount > 3000000 || indexCount % 3 != 0) throw new InvalidDataException("Invalid mesh metadata: " + name);
                        Vector3[] positions = new Vector3[vertexCount], normals = new Vector3[vertexCount];
                        Color32[] colors = new Color32[vertexCount]; Vector2[] uv = new Vector2[vertexCount];
                        for (int i = 0; i < vertexCount; ++i)
                        {
                            positions[i] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
                            normals[i] = new Vector3(reader.ReadInt16() / 32767f, reader.ReadInt16() / 32767f, reader.ReadInt16() / 32767f).normalized;
                            colors[i] = new Color32(reader.ReadByte(), reader.ReadByte(), reader.ReadByte(), reader.ReadByte());
                            uv[i] = new Vector2(reader.ReadSingle(), reader.ReadSingle());
                        }
                        int[] indices = new int[indexCount];
                        for (int i = 0; i < indexCount; ++i) { indices[i] = reader.ReadInt32(); if (indices[i] < 0 || indices[i] >= vertexCount) throw new InvalidDataException("Invalid triangle index."); }
                        Mesh mesh = new Mesh(); mesh.name = name; mesh.indexFormat = IndexFormat.UInt32;
                        mesh.vertices = positions; mesh.normals = normals; mesh.colors32 = colors; mesh.uv = uv;
                        mesh.SetIndices(indices, MeshTopology.Triangles, 0, true); meshes.Add(mesh);
                        GameObject part = new GameObject(name); if (!Application.isPlaying) part.hideFlags = HideFlags.DontSaveInEditor; part.transform.SetParent(generated.transform, false);
                        parts.Add(name, part.transform);
                        part.AddComponent<MeshFilter>().sharedMesh = mesh; MeshRenderer renderer = part.AddComponent<MeshRenderer>();
                        Material material;
                        if (!materials.TryGetValue(materialId, out material))
                        {
                            material = Resources.Load<Material>("DemoMaterials/Mat-" + materialId);
                            if (material == null) throw new InvalidDataException("Missing painted material: " + materialId);
                            materials.Add(materialId, material);
                        }
                        renderer.sharedMaterial = material;
                        if (material.shader != null && material.shader.name.Contains("Ink Hull")) renderer.shadowCastingMode = ShadowCastingMode.Off;
                        if (collider) part.AddComponent<MeshCollider>().sharedMesh = mesh;
                        mesh.UploadMeshData(!collider);
                    }
                    if (reader.BaseStream.ReadByte() != -1) throw new InvalidDataException("Unexpected trailing geometry data.");
                    Debug.Log("Separate village geometry loaded: " + count + " mesh batches.");
                }
                CreateSimpleColliders(); CreatePropColliders();
                if (Application.isPlaying)
                {
                    generated.AddComponent<DemoHouseDoors>().Initialize(parts);
                    generated.AddComponent<DemoStairCollision>().Initialize();
                    generated.AddComponent<DemoFarmAnimals>().Initialize();
                    generated.AddComponent<DemoBlossomPetals>().Initialize();
                    generated.AddComponent<DemoWaterAtmosphere>().Initialize();
                }
                Physics.SyncTransforms(); LastError = null;
            }
            catch (Exception error) { LastError = error.Message; Debug.LogException(error); ClearWorld(); }
            finally { building = false; }
        }
        static string ReadText(BinaryReader reader)
        {
            int length = reader.ReadInt32(); if (length < 0 || length > 4096) throw new InvalidDataException("Invalid name length.");
            byte[] bytes = reader.ReadBytes(length); if (bytes.Length != length) throw new EndOfStreamException();
            return System.Text.Encoding.UTF8.GetString(bytes);
        }
        void Box(string name, Vector3 center, Vector3 size)
        {
            GameObject part = new GameObject(name); if (!Application.isPlaying) part.hideFlags = HideFlags.DontSaveInEditor; part.transform.SetParent(generated.transform, false); part.transform.localPosition = center;
            part.AddComponent<BoxCollider>().size = size;
        }
        void CreateSimpleColliders()
        {
            Box("Hall table west", new Vector3(-4.4f, .705f, 18.4f), new Vector3(2.2f, .14f, 1.25f));
            Box("Hall table east", new Vector3(2.4f, .705f, 18.4f), new Vector3(2.2f, .14f, 1.25f));
            Box("Hall table rear", new Vector3(-1, .705f, 20.7f), new Vector3(2.2f, .14f, 1.25f));
        }
        [Serializable] sealed class ProxySet { public ProxyBox[] boxes; }
        [Serializable] sealed class ProxyBox { public string name; public Vector3 center; public Vector3 size; public float yaw; }
        void CreatePropColliders()
        {
            TextAsset asset = Resources.Load<TextAsset>("DemoGeometry/CollisionProxies");
            if (asset == null) throw new InvalidDataException("The separate demo collision data is missing.");
            ProxySet data = JsonUtility.FromJson<ProxySet>(asset.text);
            if (data == null || data.boxes == null) throw new InvalidDataException("Invalid demo collision data.");
            foreach (ProxyBox box in data.boxes)
            {
                GameObject part = new GameObject("Collision: " + box.name);
                if (!Application.isPlaying) part.hideFlags = HideFlags.DontSaveInEditor;
                part.transform.SetParent(generated.transform, false); part.transform.localPosition = box.center;
                part.transform.localRotation = Quaternion.Euler(0, box.yaw, 0); part.AddComponent<BoxCollider>().size = box.size;
            }
        }
        void OnDisable() { ClearWorld(); }
        void ClearWorld()
        {
            if (generated != null) { if (Application.isPlaying) Destroy(generated); else DestroyImmediate(generated); generated = null; }
            foreach (Mesh mesh in meshes) { if (mesh == null) continue; if (Application.isPlaying) Destroy(mesh); else DestroyImmediate(mesh); }
            meshes.Clear();
        }
        void OnGUI()
        {
            if (!string.IsNullOrEmpty(LastError)) GUI.Box(new Rect(10, 205, 700, 70), "Village could not load: " + LastError + "\nSee the Unity Console / player log.");
        }
    }
}
