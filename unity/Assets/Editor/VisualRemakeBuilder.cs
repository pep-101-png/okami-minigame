using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    // A visual-only migration. It never imports Amaterasu, processes animation
    // clips, rebuilds gameplay prefabs, or recreates the user's scene.
    public static class VisualRemakeBuilder
    {
        const string RootName = "Windflower · visual remake";
        const string RockRoot = "Windflower · individually seated replacement rocks";
        const string Folder = "Assets/Sunward/Generated/Remake/";
        const string Model = "Assets/Sunward/Models/Remake/WindflowerRemake.fbx";
        [Serializable]
        public class Library
        {
            public Part[] assets;
            public Pigment[] materials;
        }

        [Serializable]
        public class Part
        {
            public string name, mesh, front;
            public string[] materials;
        }

        [Serializable]
        public class Pigment
        {
            public string name, texture;
            public float[] color;
        }

        static Library library;
        static GameObject model;
        static Transform root;
        static WorldData world;
        static readonly Dictionary<string, Material> paint = new Dictionary<string, Material>();
        static readonly Dictionary<string, GameObject> prefabs = new Dictionary<string, GameObject>();
        static float Ground(Vector3 p) => Valley.SurfaceHeight(world.terrain, p);
        static Transform Group(string name, Transform parent, Vector3 position)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = position;
            return t;
        }

        static T Save<T>(T value, string name)
            where T : UnityEngine.Object
        {
            string path = Folder + name;
            var existing = AssetDatabase.LoadAssetAtPath<T>(path);
            if (existing)
            {
                EditorUtility.CopySerialized(value, existing);
                UnityEngine.Object.DestroyImmediate(value);
                EditorUtility.SetDirty(existing);
                return existing;
            }

            AssetDatabase.CreateAsset(value, path);
            return value;
        }

        static GameObject Box(string name, Transform parent, Vector3 p, Vector3 size, string material, bool solid = false)
        {
            var o = GameObject.CreatePrimitive(PrimitiveType.Cube);
            o.name = name;
            o.transform.SetParent(parent, false);
            o.transform.localPosition = p;
            o.transform.localScale = size;
            o.GetComponent<Renderer>().sharedMaterial = paint[material];
            var col = o.GetComponent<BoxCollider>();
            if (!solid)
                UnityEngine.Object.DestroyImmediate(col);
            else
            {
                o.layer = 6;
                o.AddComponent<VillageWorldSolid>();
            }

            return o;
        }

        static GameObject Rod(string name, Transform parent, Vector3 a, Vector3 b, float radius, string material)
        {
            var o = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            o.name = name;
            o.transform.SetParent(parent, false);
            o.transform.localPosition = (a + b) * .5f;
            o.transform.localRotation = Quaternion.FromToRotation(Vector3.up, b - a);
            o.transform.localScale = new Vector3(radius * 2, (b - a).magnitude * .5f, radius * 2);
            UnityEngine.Object.DestroyImmediate(o.GetComponent<Collider>());
            o.GetComponent<Renderer>().sharedMaterial = paint[material];
            return o;
        }

        static void Prepare()
        {
            Directory.CreateDirectory(Folder);
            AssetDatabase.Refresh();
            library = JsonUtility.FromJson<Library>(File.ReadAllText("Review/remake-library.json"));
            model = AssetDatabase.LoadAssetAtPath<GameObject>(Model);
            if (!model)
                throw new InvalidDataException("Replacement FBX is missing or has not imported. Wait for imports to finish.");
            paint.Clear();
            prefabs.Clear();
            var waterShader = Shader.Find("Sunward/Brush River");
            if (!waterShader || ShaderUtil.ShaderHasError(waterShader))
                throw new InvalidDataException("Brush River shader did not compile. Read the first Console shader error.");
            var shader = Shader.Find("Sunward/Surface Pigment");
            if (!shader || ShaderUtil.ShaderHasError(shader))
                throw new InvalidDataException("Surface Pigment shader missing.");
            foreach (var item in library.materials)
            {
                var m = new Material(shader)
                {
                    name = "Remake · " + item.name,
                    enableInstancing = true
                };
                m.SetFloat("_VertexTint", 0);
                if (item.name == "Leaf" || item.name == "Meadow" || item.name == "Pink" || item.name == "Cream")
                    m.SetFloat("_Cull", 0);
                m.SetFloat("_Pigment", .16f);
                m.SetFloat("_NormalStrength", .30f);
                if (!string.IsNullOrEmpty(item.texture))
                {
                    var color = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Sunward/Textures/Remake/" + item.texture);
                    var normal = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Sunward/Textures/Remake/" + item.name + "-normal.png");
                    if (!color || !normal)
                        throw new InvalidDataException("Missing new painting: " + item.texture);
                    m.SetColor("_BaseColor", Color.white);
                    m.SetTexture("_DetailMap", color);
                    m.SetTexture("_DetailNormal", normal);
                    m.SetFloat("_ArtStrength", 1);
                    m.SetFloat("_ArtTiling", item.name == "Bark" ? .55f : .38f);
                }
                else
                    m.SetColor("_BaseColor", new Color(item.color[0], item.color[1], item.color[2], item.color[3]));
                m.SetFloat("_SurfaceKind", item.name == "Oak" || item.name == "Bark" ? 1 : 2);
                paint[item.name] = Save(m, item.name + ".mat");
            }

            foreach (var part in library.assets)
            {
                var source = model.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == part.name);
                if (!source)
                    throw new InvalidDataException("FBX asset not found: " + part.name);
                var temp = new GameObject(part.name);
                var copy = UnityEngine.Object.Instantiate(source.gameObject, temp.transform, false);
                copy.transform.localPosition = Vector3.zero;
                // Preserve imported ancestor axis/unit conversion, then normalize
                // against the authoring guide, whose length is exactly one metre.
                copy.transform.localRotation = source.rotation;
                copy.transform.localScale = source.lossyScale;
                var front = copy.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == part.front);
                if (!front)
                    throw new InvalidDataException("Missing facing datum: " + part.front);
                Vector3 forward = temp.transform.InverseTransformPoint(front.position);
                forward.y = 0;
                if (forward.magnitude < .000001f || !MeshSafety.Finite(forward))
                    throw new InvalidDataException("Invalid FBX facing datum.");
                copy.transform.localRotation = Quaternion.FromToRotation(forward.normalized, Vector3.forward) * copy.transform.localRotation;
                copy.transform.localScale /= forward.magnitude;
                var renderers = temp.GetComponentsInChildren<MeshRenderer>(true);
                if (renderers.Length != 1 || renderers[0].GetComponent<MeshFilter>().sharedMesh.subMeshCount != part.materials.Length)
                    throw new InvalidDataException("Material section order/count changed: " + part.name);
                float height = renderers[0].bounds.size.y;
                if (part.name.StartsWith("Resident_") && (height < 1.8f || height > 2.4f) || part.name.StartsWith("House_") && (height < 3 || height > 6))
                    throw new InvalidDataException("Imported axis/unit dimensions are wrong: " + part.name + " height " + height);
                renderers[0].sharedMaterials = part.materials.Select(n => paint[n]).ToArray();
                var mesh = renderers[0].GetComponent<MeshFilter>().sharedMesh;
                if (mesh.vertexCount < 20)
                    throw new InvalidDataException("Empty replacement mesh: " + part.name);
                prefabs[part.name] = PrefabUtility.SaveAsPrefabAsset(temp, Folder + part.name + ".prefab");
                UnityEngine.Object.DestroyImmediate(temp);
            }
        }

        static GameObject Place(string name, Vector3 p, Vector3 scale, float angle = 0, Transform parent = null)
        {
            var o = (GameObject)PrefabUtility.InstantiatePrefab(prefabs[name]);
            o.transform.SetParent(parent ? parent : root, false);
            o.transform.localPosition = p;
            o.transform.localScale = scale;
            o.transform.localRotation = Quaternion.Euler(0, angle, 0);
            return o;
        }

        [MenuItem("Sunward/Apply Visual Remake to Windflower")]
        public static void Apply()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Exit Play Mode first.");
            var scene = EditorSceneManager.GetActiveScene();
            var flow = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
            var town = GameObject.Find("V3 · preserved painted valley");
            if (!flow || !town || scene.path != "Assets/Sunward/Scenes/Windflower.unity")
                throw new InvalidOperationException("Open the existing Windflower scene first.");
            if (!town.transform.Find(WindflowerRenovation.RootName))
                throw new InvalidOperationException("This update expects the improved home/mill build. Install the complete project if it is missing.");
            // Serialized scene checkpoint is copied before touching anything. Assets
            // remain recoverable in the previous downloaded project / Git revision.
            EditorSceneManager.SaveScene(scene);
            Directory.CreateDirectory("Review/LocalBackups");
            File.Copy(scene.path, "Review/LocalBackups/Windflower-before-remake-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + ".unity", true);
            Prepare();
            var data = JsonUtility.FromJson<ValleyData>(flow.valley.source.text);
            world = data.world;
            world.terrain.visualRelief = true;
            var old = town.transform.Find(RootName);
            if (old)
                UnityEngine.Object.DestroyImmediate(old.gameObject);
            root = Group(RootName, town.transform, Vector3.zero);
            var filters = town.GetComponentsInChildren<MeshFilter>(true).Where(f => f.sharedMesh && f.sharedMesh.name.StartsWith("Valley-")).ToDictionary(f => f.sharedMesh.name);
            for (int id = 743; id <= 750; id++)
                if (filters.TryGetValue("Valley-" + id, out var spear))
                    spear.GetComponent<Renderer>().enabled = false;
            int buildings = ReplaceBuildingsAndTrees(data, filters, out int trees);
            int rocks = ReplaceRocks(data, filters, town.transform);
            Terrain(data, filters);
            flow.valley.visualRelief = true;
            EditorUtility.SetDirty(flow.valley);
            SurfaceMaterials(data);
            Vegetation();
            Market(flow, town.transform);
            Residents(flow);
            HouseDetails();
            Decorations(town.transform);
            Mill(town.transform);
            River(town.transform);
            AssetDatabase.SaveAssets();
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            WatersideRepair.Apply();
            ValidateApplied(flow, town, filters);
            Debug.Log($"Windflower visual remake applied and saved: {buildings} buildings, {trees} trees, {rocks} new individually seated rocks, 4 distinct market stalls and {flow.npcObjects.Length} replacement resident appearances. Wolf/animations untouched. Native visual and Play Mode testing still required.");
        }

        static Bounds BoundsOf(IEnumerable<MeshFilter> filters)
        {
            var all = filters.ToArray();
            var b = all[0].GetComponent<Renderer>().bounds;
            foreach (var f in all.Skip(1))
                b.Encapsulate(f.GetComponent<Renderer>().bounds);
            return b;
        }

        static int ReplaceBuildingsAndTrees(ValleyData data, Dictionary<string, MeshFilter> filters, out int trees)
        {
            int id = 0, houses = 0;
            trees = 0;
            foreach (var asset in data.assets)
            {
                int first = id;
                id += asset.meshes.Length;
                if (asset.name != "TownV3" || asset.meshes.Length == 0 || first == 600)
                    continue; // Accepted accessible home stays intact.
                var fs = Enumerable.Range(first, asset.meshes.Length).Where(i => filters.ContainsKey("Valley-" + i)).Select(i => filters["Valley-" + i]).ToArray();
                if (fs.Length == 0)
                    continue;
                var b = BoundsOf(fs);
                bool leaves = asset.meshes.Any(m => data.materials[m.material].kind == "leaves");
                bool roof = asset.meshes.Any(m => data.materials[m.material].kind == "roof");
                if (leaves && b.size.x < 24 && b.size.z < 24 && b.size.y > 2 && b.size.y < 16)
                {
                    var p = new Vector3(b.center.x, 0, b.center.z);
                    var trunk = world.obstacles.Where(c => c.r > .24f && c.r < .8f).OrderBy(c => Mathf.Pow(c.x - p.x, 2) + Mathf.Pow(-c.z - p.z, 2)).FirstOrDefault();
                    if (trunk != null && Vector2.Distance(new Vector2(p.x, p.z), new Vector2(trunk.x, -trunk.z)) < 2.8f)
                    {
                        p.x = trunk.x;
                        p.z = -trunk.z;
                    }

                    p.y = Ground(p) - .035f;
                    string kind = new[]
                    {
                        "Cherry_A",
                        "Cherry_B",
                        "Maple_A",
                        "Pine_A"
                    }[trees % 4];
                    float scale = Mathf.Clamp(b.size.y / 4.7f, .8f, 1.65f);
                    var tree = Place(kind, p, Vector3.one * scale, (trees * 137.5f) % 360);
                    foreach (var r in tree.GetComponentsInChildren<Renderer>())
                    {
                        var block = new MaterialPropertyBlock();
                        block.SetFloat("_TreeWind", 1);
                        block.SetFloat("_TreeBaseY", p.y);
                        block.SetFloat("_TreePhase", trees * 2.3f);
                        r.SetPropertyBlock(block);
                    }

                    foreach (var f in fs)
                        f.GetComponent<Renderer>().enabled = false;
                    trees++;
                }
                else if (roof && b.size.x > 4 && b.size.x < 13 && b.size.z > 3 && b.size.z < 12 && b.size.y > 2.5f && b.size.y < 9)
                {
                    var box = world.boxes.Take(19).OrderBy(q => Mathf.Pow(q.x - b.center.x, 2) + Mathf.Pow(-q.z - b.center.z, 2)).First();
                    if (Mathf.Abs(box.x - b.center.x) > 1.4f || Mathf.Abs(-box.z - b.center.z) > 1.4f)
                        continue;
                    var p = new Vector3(box.x, 0, -box.z);
                    p.y = Ground(p) - .08f;
                    // Existing collision footprint and town layout remain unchanged.
                    var scale = new Vector3((box.halfX * 2 + .25f) / 6, Mathf.Clamp(b.size.y / 4.5f, .85f, 1.25f), (box.halfZ * 2 + .15f) / 5);
                    Place(houses % 3 == 1 ? "House_B" : "House_A", p, scale, box.x < -20 ? 0 : box.x < 0 ? 90 : -90);
                    // Rotation swaps width/depth. Respect existing collider footprint.
                    var placed = root.GetChild(root.childCount - 1);
                    if (box.x >= -20)
                        placed.localScale = new Vector3((box.halfZ * 2 + .25f) / 6, scale.y, (box.halfX * 2 + .15f) / 5);
                    foreach (var f in fs)
                        f.GetComponent<Renderer>().enabled = false;
                    houses++;
                }
            }

            return houses;
        }

        static int ReplaceRocks(ValleyData data, Dictionary<string, MeshFilter> filters, Transform town)
        {
            var rockRoot = town.Find(RockRoot);
            if (!rockRoot)
                rockRoot = Group(RockRoot, town, Vector3.zero);
            int count = 0, id = 0;
            foreach (var asset in data.assets)
                foreach (var record in asset.meshes)
                {
                    int n = id++;
                    if (!RockSeating.Source(n) || asset.name != "TownV3" || data.materials[record.material].kind != "stone" || !filters.TryGetValue("Valley-" + n, out var filter) || !filter.GetComponent<Renderer>().enabled)
                        continue;
                    var mesh = filter.sharedMesh;
                    var v = mesh.vertices;
                    var ix = mesh.triangles;
                    var remove = new HashSet<int>();
                    foreach (var group in SurfaceIslands.Find(v, ix))
                    {
                        var b = new Bounds(v[group[0]], Vector3.zero);
                        foreach (int k in group)
                            b.Encapsulate(v[k]);
                        if (!RockSeating.Suitable(world, b))
                            continue;
                        var p = b.center;
                        p.y = Ground(p);
                        float bottom = RockSeating.Bottom(world, b);
                        var rock = Place("Rock_" + ((n + count) % 4), Vector3.zero, Vector3.one, 0, rockRoot);
                        var rb = rock.GetComponentInChildren<Renderer>().bounds;
                        var scale = new Vector3(b.size.x / rb.size.x, Mathf.Max(.08f, b.size.y) / rb.size.y, b.size.z / rb.size.z);
                        rock.transform.localScale = scale;
                        rb = rock.GetComponentInChildren<Renderer>().bounds;
                        p.y = bottom - rb.min.y;
                        rock.transform.position = p;
                        rock.name = "Seated rock · source " + n + " · " + group[0];
                        foreach (int k in group)
                            remove.Add(k);
                        count++;
                    }

                    if (remove.Count == 0)
                        continue;
                    var keep = new List<int>();
                    for (int t = 0; t < ix.Length; t += 3)
                        if (!remove.Contains(ix[t]))
                        {
                            keep.Add(ix[t]);
                            keep.Add(ix[t + 1]);
                            keep.Add(ix[t + 2]);
                        }

                    mesh.triangles = keep.ToArray();
                    mesh.RecalculateBounds();
                    EditorUtility.SetDirty(mesh);
                }

            return count;
        }

        static void Terrain(ValleyData data, Dictionary<string, MeshFilter> filters)
        {
            int id = 0;
            using (var reader = new BinaryReader(File.OpenRead("Assets/Sunward/Data/Valley.bytes")))
                foreach (var asset in data.assets)
                    foreach (var record in asset.meshes)
                    {
                        int n = id++;
                        if (asset.name != "TownV3" || data.materials[record.material].kind != "landscape" || !filters.TryGetValue("Valley-" + n, out var f))
                            continue;
                        reader.BaseStream.Position = record.offset;
                        int nv = reader.ReadInt32();
                        reader.ReadInt32();
                        var v = new Vector3[nv];
                        for (int k = 0; k < nv; k++)
                        {
                            v[k] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
                            reader.BaseStream.Position += 36;
                            v[k].y += TerrainRelief.Offset(v[k]);
                        }

                        f.sharedMesh.vertices = v;
                        f.sharedMesh.RecalculateNormals();
                        f.sharedMesh.RecalculateBounds();
                        EditorUtility.SetDirty(f.sharedMesh);
                        foreach (var collider in UnityEngine.Object.FindObjectsByType<MeshCollider>(FindObjectsInactive.Include))
                            if (collider.sharedMesh == f.sharedMesh)
                            {
                                collider.sharedMesh = null;
                                collider.sharedMesh = f.sharedMesh;
                            }
                    }
        }

        static void SurfaceMaterials(ValleyData data)
        {
            for (int id = 0; id < data.materials.Length; id++)
            {
                var source = data.materials[id];
                var m = AssetDatabase.LoadAssetAtPath<Material>("Assets/Sunward/Generated/Paint-" + id + ".mat");
                if (!m || m.shader.name != "Sunward/Surface Pigment")
                    continue;
                string family = source.kind == "wood" ? "Oak" : source.kind == "stone" ? "Stone" : source.kind == "roof" ? "Roof" : source.kind == "shoji" ? "Paper" : source.kind == "landscape" ? "Meadow" : null;
                if (family == null)
                    continue;
                m.SetTexture("_DetailMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Sunward/Textures/Remake/" + family + ".png"));
                m.SetTexture("_DetailNormal", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Sunward/Textures/Remake/" + family + "-normal.png"));
                m.SetFloat("_ArtStrength", .9f);
                m.SetFloat("_ArtTiling", family == "Meadow" ? .2f : .38f);
                if (family == "Meadow")
                {
                    m.SetTexture("_PathMap", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Sunward/Textures/Remake/Earth.png"));
                    m.SetTexture("_PathNormal", AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Sunward/Textures/Remake/Earth-normal.png"));
                }

                EditorUtility.SetDirty(m);
            }
        }

        static void Vegetation()
        {
            var plants = Group("Meadows · curved blades and wildflowers", root, Vector3.zero);
            for (int i = 0; i < 220; i++)
            {
                float x = -48 + ((i * 17.931f) % 107), z = -35 + ((i * 11.317f) % 72);
                var p = new Vector3(x, 0, z);
                if (Mathf.Abs(x) < 3.2f || Mathf.Abs(x + 32) < 2.8f || Valley.Depth(p) > .05f || Valley.OnBridge(x, -z))
                    continue;
                if (world.boxes.Any(b => Mathf.Abs(x - b.x) < b.halfX + .8f && Mathf.Abs(z + b.z) < b.halfZ + .8f))
                    continue;
                if (Mathf.Abs(x - 28) + Mathf.Abs(z - 8) < 23)
                    continue;
                p.y = Ground(p) - .025f;
                var plant = Place(i % 4 == 0 ? "Flower_Patch" : "Grass_Patch", p, Vector3.one * (.8f + i % 5 * .1f), i * 137.5f, plants);
                foreach (var r in plant.GetComponentsInChildren<Renderer>())
                {
                    var block = new MaterialPropertyBlock();
                    block.SetFloat("_Wind", .65f);
                    block.SetFloat("_TreeBaseY", p.y);
                    r.SetPropertyBlock(block);
                }
            }
        }

        static void Market(GameFlow flow, Transform town)
        {
            var renovation = town.Find(WindflowerRenovation.RootName);
            var old = renovation.Find("Market · crafted stalls and arranged goods");
            if (old)
            {
                foreach (var r in old.GetComponentsInChildren<MeshRenderer>(true))
                    r.enabled = false;
                foreach (var c in old.GetComponentsInChildren<Collider>(true))
                    c.enabled = false;
            } // Keep the original audio graph alive.

            var market = Group("Market · four artisan courtyards", root, Vector3.zero);
            string[] stalls =
            {
                "Market_Flowers",
                "Market_Produce",
                "Market_Ceramics",
                "Market_Textiles"
            };
            for (int i = 0; i < 4; i++)
            {
                float side = i % 2 == 0 ? -1 : 1, z = i < 2 ? 0 : 5.5f;
                var p = new Vector3(side * 4.8f, 0, z);
                p.y = Ground(p) + .03f;
                var stall = Place(stalls[i], p, Vector3.one, -side * 90, market);
                Box("Solid merchant counter", stall.transform, new Vector3(0, .48f, 0), new Vector3(2.96f, .96f, 1.38f), "Oak", true).GetComponent<Renderer>().enabled = false;
                for (int corner = 0; corner < 4; corner++)
                    Box("Solid awning post", stall.transform, new Vector3(corner % 2 == 0 ? -1.5f : 1.5f, 1.4f, corner < 2 ? -.75f : .75f), new Vector3(.14f, 2.8f, .14f), "Oak", true).GetComponent<Renderer>().enabled = false;
                // Preserve a wide central pedestrian route; boards stay under stalls.
                Box("Weathered stall deck", market, p + Vector3.down * .02f, new Vector3(2.35f, .08f, 3.7f), "Oak");
                var glow = Group("Warm hanging lantern light", stall.transform, new Vector3(0, 2.1f, .6f)).gameObject.AddComponent<Light>();
                glow.type = LightType.Point;
                glow.color = new Color(1, .69f, .37f);
                glow.intensity = 1.2f;
                glow.range = 3.5f;
                glow.shadows = LightShadows.None;
                var sign = Group("Cloth shop pennant", stall.transform, new Vector3(1.6f, 2.4f, .2f));
                Box("Seigaiha fabric", sign, Vector3.down * .42f, new Vector3(.38f, .82f, .018f), new[] { "Jade", "Vermilion", "Indigo", "Paper" }[i]);
                sign.gameObject.AddComponent<HangingWind>().phase = i * 2;
                if (i == 3)
                    for (int tool = 0; tool < 4; tool++)
                    {
                        var a = new Vector3(-1.1f + tool * .65f, 1.45f, -.35f);
                        Rod("Craft tool wooden handle", stall.transform, a, a + Vector3.up * .37f, .018f, "Oak");
                        Box("Forged hand tool head", stall.transform, a + Vector3.up * .38f, new Vector3(.21f, .065f, .08f), "Ink");
                    }
            }

            Motes("Market · drifting paper lights", market, new Vector3(0, 2.7f, 2.6f), 3, 60, new Color(.97f, .80f, .49f, .5f), 5);
            // The two existing merchant identities remain behind their own counters.
            for (int i = 0; i < Mathf.Min(2, flow.npcObjects.Length); i++)
            {
                var npc = flow.npcObjects[i];
                if (!npc)
                    continue;
                float side = i == 0 ? -1 : 1;
                var p = new Vector3(side * 6.15f, 0, 0);
                p.y = Ground(p);
                npc.transform.position = p;
                npc.transform.rotation = Quaternion.Euler(0, -side * 90, 0);
                EditorUtility.SetDirty(npc);
            }
        }

        static void Residents(GameFlow flow)
        {
            for (int i = 0; i < flow.npcObjects.Length; i++)
            {
                var npc = flow.npcObjects[i];
                if (!npc)
                    continue;
                var old = npc.transform.Find("Remake · character source");
                if (old)
                    UnityEngine.Object.DestroyImmediate(old.gameObject);
                foreach (var r in npc.GetComponentsInChildren<Renderer>(true))
                    r.enabled = false;
                string role = i == 0 || i == 3 ? "Resident_Artisan" : i == 1 || i == 5 ? "Resident_Merchant" : "Resident_Pilgrim";
                var source = Place(role, Vector3.zero, Vector3.one, 0, npc.transform);
                source.name = "Remake · character source";
                ResidentRigAuthoring.Build(npc, flow, i, source);
                var locomotion = npc.GetComponent<ResidentLocomotion>();
                // Preserve the musician/pilgrim's original village roles; the two
                // town browsers alternate between shop fronts and open paving.
                if (i == 2 || i == 3)
                {
                    var resident = npc.GetComponent<VillageResident>();
                    float side = i == 2 ? -1 : 1;
                    resident.route = new[]
                    {
                        new Vector3(side * 2.9f, 0, 0),
                        new Vector3(side * 2.9f, 0, 5.5f),
                        new Vector3(side * 1.7f, 0, 8),
                        new Vector3(side * 1.7f, 0, -2)
                    };
                    EditorUtility.SetDirty(resident);
                }

                EditorUtility.SetDirty(locomotion);
            }
        }

        static void HouseDetails()
        {
            var home = Group("Home · painted keepsakes and textiles", root, Vector3.zero);
            var scroll = Group("Bamboo ink scroll · east wall", home, new Vector3(-29.15f, 1.6f, -17.6f));
            scroll.localRotation = Quaternion.Euler(0, 90, 0);
            Box("Original bamboo painting", scroll, Vector3.zero, new Vector3(.86f, 1.20f, .02f), "Paper");
            for (int sign = -1; sign <= 1; sign += 2)
                Rod("Scroll wooden roller", scroll, new Vector3(-.5f, sign * .64f, 0), new Vector3(.5f, sign * .64f, 0), .024f, "Oak");
            // A narrow storage bench follows the north wall, outside mirror/shelf access.
            Box("Keepsake cabinet", home, new Vector3(-34.0f, .34f, -12.45f), new Vector3(2.1f, .5f, .47f), "Oak", true);
            for (int door = 0; door < 3; door++)
            {
                Box("Cabinet recessed door", home, new Vector3(-34.68f + door * .68f, .34f, -12.71f), new Vector3(.60f, .36f, .025f), "Indigo");
                Box("Bronze cabinet pull", home, new Vector3(-34.68f + door * .68f, .34f, -12.74f), new Vector3(.07f, .025f, .015f), "Bronze");
            }

            for (int i = 0; i < 2; i++)
            {
                Box("Woven floor cushion", home, new Vector3(-37.6f, .22f, -13.8f - i * .72f), new Vector3(.58f, .15f, .52f), i == 0 ? "Jade" : "Vermilion");
                var o = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                o.name = "Celadon keepsake bowl";
                o.transform.SetParent(home, false);
                o.transform.localPosition = new Vector3(-34.5f + i, .68f, -12.45f);
                o.transform.localScale = new Vector3(.24f, .16f, .24f);
                UnityEngine.Object.DestroyImmediate(o.GetComponent<Collider>());
                o.GetComponent<Renderer>().sharedMaterial = paint["Jade"];
            }

            var light = Group("Home · warm alcove wash", home, new Vector3(-35, 2.6f, -13)).gameObject.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = 4;
            light.intensity = .8f;
            light.color = new Color(1, .73f, .43f);
        }

        static void Decorations(Transform town)
        {
            var old = town.Find(WindflowerRenovation.RootName + "/Market · supported festival line");
            if (old)
            {
                foreach (var r in old.GetComponentsInChildren<Renderer>(true))
                    r.enabled = false;
                foreach (var c in old.GetComponentsInChildren<Collider>(true))
                    c.enabled = false;
            }

            var decorations = Group("Festival · seigaiha cloth, ofuda and tassels", root, Vector3.zero);
            for (int span = 0; span < 3; span++)
            {
                float z = -2.5f + span * 5.5f;
                for (int side = -1; side <= 1; side += 2)
                {
                    float y = Ground(new Vector3(side * 3.45f, 0, z));
                    Box("Festival anchor post", decorations, new Vector3(side * 3.45f, y + 1.95f, z), new Vector3(.13f, 3.9f, .13f), "Oak", true);
                    Box("Post stone shoe", decorations, new Vector3(side * 3.45f, y + .12f, z), new Vector3(.29f, .24f, .29f), "Stone");
                }

                Vector3 Cable(float t) => new Vector3(Mathf.Lerp(-3.45f, 3.45f, t), Mathf.Lerp(Ground(new Vector3(-3.45f, 0, z)), Ground(new Vector3(3.45f, 0, z)), t) + 3.9f - Mathf.Sin(t * Mathf.PI) * .48f, z);
                for (int segment = 0; segment < 24; segment++)
                    Rod("Sagging braided rope", decorations, Cable(segment / 24f), Cable((segment + 1) / 24f), .016f, "Oak");
                for (int i = 0; i < 13; i++)
                {
                    float t = (i + .6f) / 13.2f;
                    var charm = Group("Wind-tied ornament " + span + "-" + i, decorations, Cable(t));
                    float length = .34f + (i % 4) * .13f;
                    string pigment = new[]
                    {
                        "Indigo",
                        "Jade",
                        "Vermilion",
                        "Paper",
                        "Cream"
                    }[(i + span) % 5];
                    Rod("Hanging silk cord", charm, Vector3.zero, Vector3.down * .12f, .006f, "Bronze");
                    Box("Painted festival strip", charm, Vector3.down * (.12f + length / 2), new Vector3(.19f + i % 3 * .035f, length, .012f), pigment);
                    if (i % 3 == 0)
                    {
                        for (int tail = 0; tail < 5; tail++)
                            Rod("Fine silk tassel", charm, new Vector3((tail - 2) * .023f, -.12f - length, 0), new Vector3((tail - 2) * .025f, -.27f - length, .015f), .006f, "Vermilion");
                    }
                    else if (i % 3 == 1)
                    {
                        var seal = Box("Ofuda ink seal", charm, new Vector3(0, -.23f, -.009f), new Vector3(.07f, .11f, .006f), "Ink");
                        seal.transform.localRotation = Quaternion.Euler(0, 0, 15);
                    }

                    charm.gameObject.AddComponent<HangingWind>().phase = i * 1.17f + span;
                    charm.GetComponent<HangingWind>().amplitude = 4 + i % 3;
                }
            }

            Motes("Festival · soft drifting lights", decorations, new Vector3(0, 3, 3), 1.6f, 32, new Color(.9f, .82f, .63f, .48f), 7);
        }

        static void Motes(string name, Transform parent, Vector3 position, float rate, int cap, Color color, float radius)
        {
            var ps = Group(name, parent, position).gameObject.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.startLifetime = 5;
            main.startSpeed = .12f;
            main.startSize = new ParticleSystem.MinMaxCurve(.018f, .045f);
            main.maxParticles = cap;
            main.startColor = color;
            var emission = ps.emission;
            emission.rateOverTime = rate;
            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Sphere;
            shape.radius = radius;
            var noise = ps.noise;
            noise.enabled = true;
            noise.strength = .15f;
            noise.frequency = .25f;
            var material = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            material.SetColor("_BaseColor", color);
            material.SetFloat("_Surface", 1);
            material.SetFloat("_SrcBlend", 5);
            material.SetFloat("_DstBlend", 10);
            material.SetFloat("_ZWrite", 0);
            material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            material.renderQueue = 3000;
            material.SetOverrideTag("RenderType", "Transparent");
            // Reuse the existing soft spray dab, so particles never render as squares.
            var sprayMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Sunward/Generated/Renovation/MillSpray.mat");
            if (sprayMat && sprayMat.HasProperty("_BaseMap"))
                material.SetTexture("_BaseMap", sprayMat.GetTexture("_BaseMap"));
            material = Save(material, name.Replace('·', '-') + ".mat");
            ps.GetComponent<ParticleSystemRenderer>().sharedMaterial = material;
            var fade = ps.colorOverLifetime;
            fade.enabled = true;
            var gradient = new Gradient();
            gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) }, new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(.7f, .2f), new GradientAlphaKey(0, 1) });
            fade.color = gradient;
        }

        static void Mill(Transform town)
        {
            var motion = town.GetComponentInChildren<WaterMillMotion>(true);
            if (!motion)
                throw new InvalidDataException("Accepted river mill is missing.");
            var datum = motion.GetComponent<MillVisualDatum>();
            if (!datum)
            {
                datum = motion.gameObject.AddComponent<MillVisualDatum>();
                datum.wheelScale = motion.wheel.localScale;
                datum.wheelPosition = motion.wheel.localPosition;
                datum.mechanismPositions = new[]
                {
                    motion.shaft.localPosition,
                    motion.pinion.localPosition,
                    motion.spindle.localPosition,
                    motion.millstone.localPosition
                };
                datum.fixedStone = motion.transform.Find("Fixed lower millstone");
                if (datum.fixedStone)
                    datum.fixedStonePosition = datum.fixedStone.localPosition;
            }

            const float lift = 1.58f * .15f; // Radius grows 15%; bottom retains its original river immersion.
            motion.wheel.localScale = new Vector3(datum.wheelScale.x, datum.wheelScale.y * 1.15f, datum.wheelScale.z * 1.15f);
            motion.wheel.localPosition = datum.wheelPosition + Vector3.up * lift;
            var mechanisms = new[]
            {
                motion.shaft,
                motion.pinion,
                motion.spindle,
                motion.millstone
            };
            for (int i = 0; i < mechanisms.Length; i++)
                mechanisms[i].localPosition = datum.mechanismPositions[i] + Vector3.up * lift;
            if (datum.fixedStone)
                datum.fixedStone.localPosition = datum.fixedStonePosition + Vector3.up * lift;
            var previous = motion.wheel.Find("Remake · wheel joinery");
            if (previous)
                UnityEngine.Object.DestroyImmediate(previous.gameObject);
            var joinery = Group("Remake · wheel joinery", motion.wheel, Vector3.zero);
            for (int side = -1; side <= 1; side += 2)
                for (int i = 0; i < 16; i++)
                {
                    float angle = i * Mathf.PI / 8;
                    var p = new Vector3(side * .365f, Mathf.Cos(angle) * 1.49f, Mathf.Sin(angle) * 1.49f);
                    Rod("Bronze rim fastener", joinery, p - Vector3.right * .012f, p + Vector3.right * .012f, .032f, "Bronze");
                    if (i % 2 == 0)
                        Box("Paddle end shoe", joinery, new Vector3(side * .365f, Mathf.Cos(angle) * 1.47f, Mathf.Sin(angle) * 1.47f), new Vector3(.06f, .14f, .38f), "Bronze").transform.localRotation = Quaternion.Euler(angle * Mathf.Rad2Deg, 0, 0);
                }

            var support = Group("Mill · raised bearings and mortise braces", root, motion.transform.position);
            support.rotation = motion.transform.rotation;
            for (int k = 0; k < 2; k++)
            {
                float x = k == 0 ? .65f : 2.35f;
                Box("Bearing extension seat", support, new Vector3(x, -.03f + lift / 2, 0), new Vector3(.29f, lift + .04f, .44f), "Oak");
                Box("Bronze bearing cap", support, new Vector3(x, .14f + lift, 0), new Vector3(.36f, .055f, .45f), "Bronze");
                for (int s = -1; s <= 1; s += 2)
                    Rod("Raised timber diagonal", support, new Vector3(x, -.45f, s * .35f), new Vector3(x, lift, 0), .045f, "Oak");
            }

            float foundation = Ground(support.position + Vector3.right * 2.9f) - support.position.y;
            Box("Grounded stone grinding pedestal", support, new Vector3(2.9f, (foundation + lift - .05f) / 2, 0), new Vector3(1.18f, lift - .05f - foundation, 1.18f), "Stone");
            foreach (var r in motion.GetComponentsInChildren<MeshRenderer>())
                if (r.sharedMaterial && r.sharedMaterial.name.Contains("Joinery"))
                    r.sharedMaterial = paint["Oak"];
            EditorUtility.SetDirty(motion);
            EditorUtility.SetDirty(datum);
        }

        static void River(Transform town)
        {
            var water = town.GetComponentsInChildren<Renderer>(true).Where(r => r.sharedMaterial && r.sharedMaterial.shader.name == "Sunward/Brush River").ToArray();
            var detail = root.gameObject.AddComponent<RiverSurfaceDetail>();
            detail.surfaces = water.Select(r => r.sharedMaterial).Distinct().ToArray();
            var contacts = new List<Vector4>();
            var mill = town.GetComponentInChildren<WaterMillMotion>(true);
            if (mill)
                contacts.Add(new Vector4(mill.wheel.position.x, mill.wheel.position.z, .42f, 0));
            var rockRoot = town.Find(RockRoot);
            if (rockRoot)
                foreach (Transform rock in rockRoot)
                {
                    var b = rock.GetComponentInChildren<Renderer>().bounds;
                    if (Mathf.Abs(b.center.x - Valley.RiverX(-b.center.z)) > 3.5f || b.max.y < -.65f)
                        continue;
                    contacts.Add(new Vector4(b.center.x, b.center.z, Mathf.Min(b.size.x, b.size.z) * .46f, 0));
                }

            detail.contacts = contacts.OrderBy(p => Mathf.Abs(p.y - 5)).Take(16).ToArray();
        }

        [MenuItem("Sunward/Validate Visual Remake Connections")]
        public static void ValidateConnections()
        {
            var flow = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
            var town = GameObject.Find("V3 · preserved painted valley");
            if (!flow || !town)
                throw new InvalidOperationException("Open Windflower.");
            var filters = town.GetComponentsInChildren<MeshFilter>(true).Where(f => f.sharedMesh && f.sharedMesh.name.StartsWith("Valley-")).ToDictionary(f => f.sharedMesh.name);
            world = JsonUtility.FromJson<ValleyData>(flow.valley.source.text).world;
            world.terrain.visualRelief = flow.valley.visualRelief;
            ValidateApplied(flow, town, filters);
        }

        static void ValidateApplied(GameFlow flow, GameObject town, Dictionary<string, MeshFilter> filters)
        {
            var visual = town.transform.Find(RootName);
            if (!visual)
                throw new InvalidDataException("Remake is not connected to the scene.");
            for (int n = 743; n <= 750; n++)
                if (filters.TryGetValue("Valley-" + n, out var f) && f.GetComponent<Renderer>().enabled)
                    throw new InvalidDataException("Legacy spear still visible: " + n);
            var market = visual.Find("Market · four artisan courtyards");
            if (!market || new[]
            {
                "Market_Produce",
                "Market_Ceramics",
                "Market_Flowers",
                "Market_Textiles"
            }.Any(n => !market.Find(n)))
                throw new InvalidDataException("Replacement market missing.");
            foreach (var r in visual.GetComponentsInChildren<Renderer>(true))
                if (r.sharedMaterials.Any(m => !m || !m.shader || m.shader.name == "Hidden/InternalErrorShader" || ShaderUtil.ShaderHasError(m.shader)))
                    throw new InvalidDataException("Missing material/shader: " + r.name);
            foreach (var npc in flow.npcObjects)
                if (npc && (!npc.GetComponentInChildren<SkinnedMeshRenderer>() || !npc.GetComponent<ResidentLocomotion>()))
                    throw new InvalidDataException("Resident skin/locomotion missing: " + npc.name);
            var mill = town.GetComponentInChildren<WaterMillMotion>(true);
            if (!mill || !mill.wheel || !mill.shaft || !mill.spindle || !mill.millstone)
                throw new InvalidDataException("Mill transmission missing.");
            var surfaceRepair = town.GetComponentInChildren<SurfaceRepairState>(true);
            if (!surfaceRepair || !surfaceRepair.validated)
            {
                var rocks = town.transform.Find(RockRoot);
                if (!rocks || rocks.childCount == 0)
                    throw new InvalidDataException("Seated replacement rock group missing.");
                foreach (Transform rock in rocks)
                {
                    if (!rocks.gameObject.activeInHierarchy)
                        continue;
                    var b = rock.GetComponentInChildren<Renderer>().bounds;
                    if (b.min.y > Ground(b.center) + .035f)
                        throw new InvalidDataException("Rock base floats above terrain/bed: " + rock.name);
                }
            }

            if (!flow.valley.visualRelief)
                throw new InvalidDataException("Terrain/render height agreement not enabled.");
            Debug.Log("Visual-remake scene references checked. This is a connection check, not visual approval or Play Mode validation.");
        }
    }
}
