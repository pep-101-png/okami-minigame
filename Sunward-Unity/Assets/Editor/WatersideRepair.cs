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
    [InitializeOnLoad]
    public static class WatersideRepair
    {
        const string Marker = "Windflower · grounded waterside repair 1";
        const string Folder = "Assets/Sunward/Generated/Waterside/";
        const string Scene = "Assets/Sunward/Scenes/Windflower.unity";
        sealed class Source
        {
            public int id;
            public string asset;
            public MeshData record;
            public PaintData paint;
            public Vector3[] v;
            public int[] ix;
        }

        static readonly Dictionary<int, Source> sources = new Dictionary<int, Source>();
        static readonly List<GameObject> suppressed = new List<GameObject>();
        static WorldData world;
        static Transform root;
        static Dictionary<string, MeshFilter> filters;
        static Material stone, leaf, blossom;
        static WatersideRepair()
        {
            EditorApplication.delayCall += TryAutomatic;
            EditorSceneManager.activeSceneChangedInEditMode += (oldScene, newScene) =>
            {
                EditorApplication.delayCall += TryAutomatic;
            };
            EditorSceneManager.sceneOpened += (s, mode) =>
            {
                EditorApplication.delayCall += TryAutomatic;
            };
        }

        static void TryAutomatic()
        {
            if (Automation.AutomationIsolation.Enabled) return;
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorApplication.delayCall += TryAutomatic;
                return;
            }

            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorSceneManager.GetActiveScene().path != Scene)
                return;
            var town = GameObject.Find("V3 · preserved painted valley");
            var done = town ? town.transform.Find(Marker) : null;
            if (!town || done && done.GetComponent<SurfaceRepairState>() && done.GetComponent<SurfaceRepairState>().validated || !UnityEngine.Object.FindFirstObjectByType<GameFlow>())
                return;
            if (SessionState.GetBool("WatersideRepair1Attempted", false))
                return;
            SessionState.SetBool("WatersideRepair1Attempted", true);
            try
            {
                Apply();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.LogError("Waterside repair did not finish. Use Sunward > Repair Waterside and Home Display after resolving the first error. No animation repair/rebuild is needed.");
            }
        }

        [MenuItem("Sunward/Repair Waterside and Home Display")]
        public static void Apply()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Exit Play Mode before applying the scene repair.");
            var scene = EditorSceneManager.GetActiveScene();
            var flow = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
            var town = GameObject.Find("V3 · preserved painted valley");
            if (scene.path != Scene || !flow || !town)
                throw new InvalidOperationException("Open the existing Windflower scene first.");
            EditorSceneManager.SaveScene(scene);
            Directory.CreateDirectory("Review/LocalBackups");
            File.Copy(Scene, "Review/LocalBackups/Windflower-before-waterside-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + ".unity", true);
            Directory.CreateDirectory(Folder);
            AssetDatabase.Refresh();
            var data = JsonUtility.FromJson<ValleyData>(flow.valley.source.text);
            world = data.world;
            world.terrain.visualRelief = flow.valley.visualRelief;
            world.terrain.gardenPondBasin = world.terrain.exactSurface = true;
            flow.valley.gardenPondBasin = flow.valley.exactTerrainSurface = true;
            EditorUtility.SetDirty(flow.valley);
            sources.Clear();
            suppressed.Clear();
            int id = 0;
            foreach (var a in data.assets)
                foreach (var m in a.meshes)
                {
                    sources[id] = new Source
                    {
                        id = id,
                        asset = a.name,
                        record = m,
                        paint = data.materials[m.material]
                    };
                    id++;
                }

            filters = town.GetComponentsInChildren<MeshFilter>(true).Where(f => f.sharedMesh && f.sharedMesh.name.StartsWith("Valley-")).ToDictionary(f => f.sharedMesh.name);
            var prior = town.transform.Find(Marker);
            if (prior)
                UnityEngine.Object.DestroyImmediate(prior.gameObject);
            root = new GameObject(Marker).transform;
            root.SetParent(town.transform, false);
            stone = Material("Seated river stone", new Color(.49f, .55f, .49f), "Stone");
            leaf = Material("Lotus leaves", new Color(.35f, .48f, .31f), null);
            blossom = Material("Lotus petals", new Color(.93f, .69f, .63f), null);
            Terrain();
            int stones = Rocks(town.transform);
            Pond();
            int spears = Spear(flow, town);
            int trees = MarketTrees(data, town.transform, out var positions);
            var state = root.gameObject.AddComponent<SurfaceRepairState>();
            state.suppressedObjects = suppressed.Distinct().ToArray();
            state.removedTreePositions = positions.ToArray();
            Validate(state);
            state.validated = true;
            AssetDatabase.SaveAssets();
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            Debug.Log($"Waterside repair 1 saved: {stones} closed stones seated on physical terrain, recessed pond/water/lilies, {spears} legacy spear objects suppressed, {trees} market trees suppressed. Wolf and animations untouched. Visual Play Mode approval still required.");
        }

        static Source Read(int id)
        {
            var s = sources[id];
            if (s.v != null)
                return s;
            using (var r = new BinaryReader(File.OpenRead("Assets/Sunward/Data/Valley.bytes")))
            {
                r.BaseStream.Position = s.record.offset;
                int nv = r.ReadInt32(), ni = r.ReadInt32();
                s.v = new Vector3[nv];
                s.ix = new int[ni];
                for (int i = 0; i < nv; i++)
                {
                    s.v[i] = new Vector3(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                    r.BaseStream.Position += 36;
                }

                for (int i = 0; i < ni; i++)
                    s.ix[i] = r.ReadInt32();
            }

            return s;
        }

        static Bounds Bounds(Source s)
        {
            Read(s.id);
            var b = new Bounds(s.v[s.ix[0]], Vector3.zero);
            foreach (int i in s.ix)
                b.Encapsulate(s.v[i]);
            return b;
        }

        static T Save<T>(T value, string name)
            where T : UnityEngine.Object
        {
            var old = AssetDatabase.LoadAssetAtPath<T>(Folder + name);
            if (old)
            {
                EditorUtility.CopySerialized(value, old);
                UnityEngine.Object.DestroyImmediate(value);
                EditorUtility.SetDirty(old);
                return old;
            }

            AssetDatabase.CreateAsset(value, Folder + name);
            return value;
        }

        static Material Material(string name, Color color, string painting)
        {
            var shader = Shader.Find("Sunward/Surface Pigment");
            if (!shader || ShaderUtil.ShaderHasError(shader))
                throw new InvalidDataException("Surface Pigment shader must compile before the repair can run.");
            var m = new Material(shader);
            m.SetColor("_BaseColor", color);
            m.SetFloat("_VertexTint", 0);
            m.SetFloat("_Cull", 2);
            if (painting != null)
            {
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Sunward/Textures/Remake/" + painting + ".png");
                if (tex)
                {
                    m.SetColor("_BaseColor", Color.white);
                    m.SetTexture("_DetailMap", tex);
                    m.SetFloat("_ArtStrength", .85f);
                    m.SetFloat("_ArtTiling", .4f);
                }
            }

            return Save(m, name + ".mat");
        }

        static void Hide(GameObject o)
        {
            o.SetActive(false);
            suppressed.Add(o);
        }

        static void Hide(int id)
        {
            if (filters.TryGetValue("Valley-" + id, out var f))
                Hide(f.gameObject);
        }

        static void Terrain()
        {
            foreach (var s in sources.Values.Where(s => s.asset == "TownV3" && s.paint.kind == "landscape"))
            {
                if (!filters.TryGetValue("Valley-" + s.id, out var f))
                    continue;
                Read(s.id);
                var v = (Vector3[])s.v.Clone();
                for (int i = 0; i < v.Length; i++)
                    v[i].y = Valley.RenderHeight(world.terrain, v[i]);
                f.sharedMesh.vertices = v;
                f.sharedMesh.RecalculateNormals();
                // Exported terrain duplicates vertices at row seams. Average
                // their normals by position so the excavated bank shades smoothly.
                var normals = f.sharedMesh.normals;
                var sums = new Dictionary<Vector3, Vector3>();
                for (int i = 0; i < v.Length; i++)
                {
                    sums.TryGetValue(v[i], out var sum);
                    sums[v[i]] = sum + normals[i];
                }

                for (int i = 0; i < v.Length; i++)
                    normals[i] = sums[v[i]].normalized;
                f.sharedMesh.normals = normals;
                f.sharedMesh.RecalculateBounds();
                EditorUtility.SetDirty(f.sharedMesh);
            }
        }

        static int Rocks(Transform town)
        {
            var old = town.Find("Windflower · individually seated replacement rocks");
            if (old)
                Hide(old.gameObject);
            int count = 0;
            foreach (var s in sources.Values.Where(s => s.asset == "TownV3" && RockSeating.Source(s.id)))
            {
                if (!filters.TryGetValue("Valley-" + s.id, out var original))
                    continue;
                Read(s.id);
                var removed = new HashSet<int>();
                foreach (var group in SurfaceIslands.Find(s.v, s.ix))
                {
                    var b = new Bounds(s.v[group[0]], Vector3.zero);
                    foreach (int i in group)
                        b.Encapsulate(s.v[i]);
                    bool dedicated = s.id == 792 || s.id == 793 || s.id == 788 || s.id == 789;
                    if (!dedicated && !RockSeating.Suitable(world, b))
                        continue;
                    float bottom = RockSeating.Bottom(world, b), highest = float.NegativeInfinity;
                    for (int z = 0; z <= 8; z++)
                        for (int x = 0; x <= 8; x++)
                            highest = Mathf.Max(highest, Valley.TerrainHeight(world.terrain, new Vector3(b.min.x + b.size.x * x / 8, 0, b.min.z + b.size.z * z / 8)));
                    float height = Mathf.Max(b.size.y, highest - bottom + b.size.y * .30f);
                    SeatedStoneGeometry.Build((s.id + group[0]) % 4, out var v, out var ix);
                    float minX = v.Min(p => p.x), maxX = v.Max(p => p.x), minZ = v.Min(p => p.z), maxZ = v.Max(p => p.z);
                    for (int i = 0; i < v.Length; i++)
                        v[i] = new Vector3(b.center.x + v[i].x * b.size.x / (maxX - minX), bottom + v[i].y * height, b.center.z + v[i].z * b.size.z / (maxZ - minZ));
                    var mesh = new Mesh
                    {
                        name = "Closed seated stone " + count,
                        vertices = v,
                        triangles = ix
                    };
                    mesh.RecalculateNormals();
                    mesh.RecalculateBounds();
                    var go = new GameObject("Grounded stone " + count + " · source " + s.id);
                    go.transform.SetParent(root, false);
                    go.AddComponent<MeshFilter>().sharedMesh = Save(mesh, "Stone-" + count + ".asset");
                    go.AddComponent<MeshRenderer>().sharedMaterial = stone;
                    foreach (int i in group)
                        removed.Add(i);
                    count++;
                }

                // Always derive filtering from immutable source triangles, including
                // on repeat application after the previous update removed faces.
                var keep = new List<int>();
                for (int i = 0; i < s.ix.Length; i += 3)
                    if (!removed.Contains(s.ix[i]))
                        keep.AddRange(new[] { s.ix[i], s.ix[i + 1], s.ix[i + 2] });
                original.sharedMesh.triangles = keep.ToArray();
                original.sharedMesh.RecalculateBounds();
                EditorUtility.SetDirty(original.sharedMesh);
                if (keep.Count == 0)
                    Hide(original.gameObject);
            }

            return count;
        }

        static void Pond()
        {
            Hide(714); // Obsolete flat garden ground decal inside the new basin.
            Hide(787);
            Hide(790);
            Hide(791);
            var shader = Shader.Find("Sunward/Garden Pond");
            if (!shader || ShaderUtil.ShaderHasError(shader))
                throw new InvalidDataException("Garden Pond shader did not compile.");
            var mat = Save(new Material(shader), "Recessed pond water.mat");
            const int n = 96;
            var v = new List<Vector3>
            {
                new Vector3(GardenPond.X, GardenPond.Water, GardenPond.Z)
            };
            var uv = new List<Vector2>
            {
                new Vector2(.5f, .5f)
            };
            var ix = new List<int>();
            for (int i = 0; i < n; i++)
            {
                float a = i * Mathf.PI * 2 / n;
                v.Add(new Vector3(GardenPond.X + Mathf.Cos(a) * GardenPond.RadiusX * 1.15f, GardenPond.Water, GardenPond.Z + Mathf.Sin(a) * GardenPond.RadiusZ * 1.15f));
                uv.Add(new Vector2(.5f + Mathf.Cos(a) * .5f, .5f + Mathf.Sin(a) * .5f));
                ix.AddRange(new[] { 0, (i + 1) % n + 1, i + 1 });
            }

            var mesh = new Mesh
            {
                name = "Pond water inside excavated terrain basin",
                vertices = v.ToArray(),
                uv = uv.ToArray(),
                triangles = ix.ToArray()
            };
            mesh.RecalculateNormals();
            var water = new GameObject("Recessed garden pond · water below earthen rim");
            water.transform.SetParent(root, false);
            water.AddComponent<MeshFilter>().sharedMesh = Save(mesh, "PondWater.asset");
            water.AddComponent<MeshRenderer>().sharedMaterial = mat;
            for (int i = 0; i < 5; i++)
            {
                var p = new Vector3(GardenPond.X + Mathf.Sin(i * 2.4f) * 1.5f, GardenPond.Water + .008f, GardenPond.Z - Mathf.Cos(i * 2.4f) * .85f);
                var pad = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                pad.name = "Lotus leaf · touching pond surface";
                pad.transform.SetParent(root, false);
                pad.transform.position = p;
                pad.transform.localScale = new Vector3(.55f, .023f, .46f);
                UnityEngine.Object.DestroyImmediate(pad.GetComponent<Collider>());
                pad.GetComponent<Renderer>().sharedMaterial = leaf;
                if (i % 2 == 0)
                    for (int petal = 0; petal < 7; petal++)
                    {
                        float angle = petal * Mathf.PI * 2 / 7;
                        var flower = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                        flower.name = "Lotus cup petal";
                        flower.transform.SetParent(root, false);
                        flower.transform.position = p + new Vector3(Mathf.Sin(angle) * .055f, .025f, Mathf.Cos(angle) * .055f);
                        flower.transform.localScale = new Vector3(.065f, .05f, .16f);
                        flower.transform.rotation = Quaternion.Euler(12, angle * Mathf.Rad2Deg, 0);
                        UnityEngine.Object.DestroyImmediate(flower.GetComponent<Collider>());
                        flower.GetComponent<Renderer>().sharedMaterial = blossom;
                    }
            }
        }

        static int Spear(GameFlow flow, GameObject town)
        {
            int count = 0;
            var rack = town.GetComponent<HomeWeaponRack>();
            Transform allowed = rack && rack.displays ? rack.displays.transform : null;
            if (!allowed)
                throw new InvalidDataException("The accepted wall weapon rack is missing; no equipment has been altered.");
            for (int id = 743; id <= 750; id++)
            {
                Hide(id);
                count++;
            }

            // Also cover older separately instantiated decorative prefabs. Never
            // inspect/suppress anything beneath the player or the accepted rack.
            foreach (var t in town.GetComponentsInChildren<Transform>(true))
            {
                if (allowed && t.IsChildOf(allowed) || flow.Player && t.IsChildOf(flow.Player.transform))
                    continue;
                var source = PrefabUtility.GetCorrespondingObjectFromSource(t.gameObject);
                if (source && source.name == "Spear" || t.name == "Reed spear · wall display" || t.name == "Spear(Clone)" || t.name == "Spear · dedicated wall hooks")
                {
                    Hide(t.gameObject);
                    count++;
                }
            }

            int mounted = allowed.GetComponentsInChildren<Transform>(true).Count(t => t.name == "Spear · dedicated wall hooks" || t.name == "Reed spear · wall display" || t.name == "Spear(Clone)");
            if (mounted != 1)
                throw new InvalidDataException("Expected one mounted decorative spear, found " + mounted);
            return count;
        }

        static bool OverMarket(Bounds b) => b.min.x < 7.6f && b.max.x > -7.6f && b.min.z < 8.5f && b.max.z > -2.8f;
        static bool TreeTouchesMarket(Transform t)
        {
            var renderers = t.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length == 0)
                return false;
            var b = renderers[0].bounds;
            foreach (var r in renderers.Skip(1))
                b.Encapsulate(r.bounds);
            return OverMarket(b);
        }

        static int MarketTrees(ValleyData data, Transform town, out List<Vector3> positions)
        {
            positions = new List<Vector3>();
            int count = 0, id = 0;
            foreach (var a in data.assets)
            {
                int first = id;
                id += a.meshes.Length;
                if (a.name != "TownV3" || !a.meshes.Any(m => data.materials[m.material].kind == "leaves"))
                    continue;
                var list = Enumerable.Range(first, a.meshes.Length).Select(i => Read(i)).Where(s => s.ix.Length > 0).ToArray();
                if (list.Length == 0)
                    continue;
                var b = Bounds(list[0]);
                foreach (var s in list.Skip(1))
                {
                    var q = Bounds(s);
                    b.Encapsulate(q.min);
                    b.Encapsulate(q.max);
                }

                if (b.size.y < 2 || b.size.y > 16 || b.size.x > 24 || b.size.z > 24 || !OverMarket(b))
                    continue;
                foreach (var s in list)
                    Hide(s.id);
                positions.Add(b.center);
                count++;
            }

            var remake = town.Find("Windflower · visual remake");
            if (remake)
                foreach (var t in remake.GetComponentsInChildren<Transform>(true))
                    if ((t.name == "Cherry_A" || t.name == "Cherry_B" || t.name == "Maple_A" || t.name == "Pine_A") && TreeTouchesMarket(t))
                    {
                        positions.Add(t.position);
                        Hide(t.gameObject);
                        count++;
                    }

            var clearedPositions = positions;
            foreach (var c in town.GetComponentsInChildren<CapsuleCollider>(true))
                if (c.name == "Trunk / rock collider" && clearedPositions.Any(p => Mathf.Abs(p.x - c.transform.position.x) < .4f && Mathf.Abs(p.z - c.transform.position.z) < .4f))
                    c.enabled = false;
            return count;
        }

        static void Validate(SurfaceRepairState state)
        {
            foreach (var o in state.suppressedObjects)
                if (o && o.activeSelf)
                    throw new InvalidDataException("Old object still active: " + o.name);
            foreach (var f in root.GetComponentsInChildren<MeshFilter>())
                if (f.name.StartsWith("Grounded stone"))
                {
                    var v = f.sharedMesh.vertices;
                    foreach (var p in v.Where(p => p.y < f.sharedMesh.bounds.min.y + .0001f))
                        if (p.y > Valley.TerrainHeight(world.terrain, p) + .001f)
                            throw new InvalidDataException("Unsupported stone base: " + f.name);
                }

            for (int i = 0; i < 96; i++)
            {
                float a = i * Mathf.PI * 2 / 96;
                var rim = new Vector3(GardenPond.X + Mathf.Cos(a) * GardenPond.RadiusX * 1.15f, 0, GardenPond.Z + Mathf.Sin(a) * GardenPond.RadiusZ * 1.15f);
                if (Valley.TerrainHeight(world.terrain, rim) < GardenPond.Water + .07f)
                    throw new InvalidDataException("Pond rim too low at " + i);
            }
        }
    }
}
