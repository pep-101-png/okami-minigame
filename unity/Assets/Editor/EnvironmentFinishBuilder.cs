using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    // Targeted scene migration, not a world/player rebuild. Source data stays immutable.
    [InitializeOnLoad]
    public static class EnvironmentFinishBuilder
    {
        const string ScenePath = "Assets/Sunward/Scenes/Windflower.unity";
        const string Marker = "Windflower · environment review 2";
        const string Folder = "Assets/Sunward/Generated/EnvironmentReview/";
        static Transform root, town;
        static GameFlow flow;
        static ValleyData data;
        static Dictionary<int, MeshFilter> filters;
        static readonly List<GameObject> hidden = new List<GameObject>();
        static readonly List<Vector3> removed = new List<Vector3>();
        static readonly Dictionary<int, Vector3[]> source = new Dictionary<int, Vector3[]>();
        static readonly List<Bounds> oldStoneBounds = new List<Bounds>();
        static readonly List<MeshData> records = new List<MeshData>();
        static Material stone, cedar, endgrain, earth, grass, gold, plaster, slate;
        static int serial;
        static readonly Dictionary<string, Mesh> lathes = new Dictionary<string, Mesh>();
        static EnvironmentFinishBuilder()
        {
            EditorApplication.delayCall += Automatic;
            EditorSceneManager.sceneOpened += (s, m) => EditorApplication.delayCall += Automatic;
            EditorSceneManager.activeSceneChangedInEditMode += (a, b) => EditorApplication.delayCall += Automatic;
        }

        static void Automatic()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorApplication.delayCall += Automatic;
                return;
            }

            if (File.Exists("Review/DISABLE-ENVIRONMENT-REVIEW-2.txt") || EditorApplication.isPlayingOrWillChangePlaymode || EditorSceneManager.GetActiveScene().path != ScenePath)
                return;
            var world = GameObject.Find("V3 · preserved painted valley");
            if (!world || !UnityEngine.Object.FindFirstObjectByType<GameFlow>())
                return;
            var prior = world.transform.Find(Marker);
            if (prior && prior.GetComponent<EnvironmentReviewState>() && prior.GetComponent<EnvironmentReviewState>().complete)
                return;
            if (SessionState.GetBool("SunwardEnvironmentReview2Attempt", false))
                return;
            SessionState.SetBool("SunwardEnvironmentReview2Attempt", true);
            try
            {
                Apply();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.LogError("Environment review 2 did not finish. Resolve the FIRST Console error before using Sunward > Apply Environment Review 2. The wolf has not been rebuilt.");
            }
        }

        [MenuItem("Sunward/Apply Environment Review 2")]
        public static void Apply()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Exit Play Mode first.");
            flow = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
            var go = GameObject.Find("V3 · preserved painted valley");
            if (!flow || !go || EditorSceneManager.GetActiveScene().path != ScenePath)
                throw new InvalidOperationException("Open Windflower first.");
            // Explicit dependency ordering: callback registration order is unspecified.
            var dependency = go.transform.Find("Windflower · grounded waterside repair 1");
            if (!dependency || !dependency.GetComponent<SurfaceRepairState>() || !dependency.GetComponent<SurfaceRepairState>().validated)
                WatersideRepair.Apply();
            var scene = EditorSceneManager.GetActiveScene();
            EditorSceneManager.SaveScene(scene);
            Directory.CreateDirectory("Review/LocalBackups");
            string stamp = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss");
            string backup = "Review/LocalBackups/Environment-" + stamp + "/";
            Directory.CreateDirectory(backup);
            File.Copy(ScenePath, backup + "Windflower.unity", true);
            foreach (string suffix in new[]
            {
                "",
                ".meta"
            }

            )
            {
                string src = "Assets/Sunward/Generated/ValleyMeshes.asset" + suffix;
                if (File.Exists(src))
                    File.Copy(src, backup + "ValleyMeshes.asset" + suffix, true);
            }

            File.WriteAllText(backup + "RESTORE.txt", "Close Unity. Create Review/DISABLE-ENVIRONMENT-REVIEW-2.txt to pause automatic migration. Restore Windflower.unity into Assets/Sunward/Scenes and ValleyMeshes.asset (and its meta) into Assets/Sunward/Generated. Reopen Unity. This restores the scene and pre-migration source geometry.\n");
            town = go.transform;
            data = JsonUtility.FromJson<ValleyData>(flow.valley.source.text);
            data.world.terrain.visualRelief = flow.valley.visualRelief;
            data.world.terrain.gardenPondBasin = data.world.terrain.exactSurface = true;
            hidden.Clear();
            removed.Clear();
            source.Clear();
            records.Clear();
            oldStoneBounds.Clear();
            lathes.Clear();
            serial = 0;
            foreach (var a in data.assets)
                records.AddRange(a.meshes);
            filters = town.GetComponentsInChildren<MeshFilter>(true).Where(f => f.sharedMesh && f.sharedMesh.name.StartsWith("Valley-")).ToDictionary(f => int.Parse(f.sharedMesh.name.Substring(7)));
            var old = town.Find(Marker);
            if (old)
                UnityEngine.Object.DestroyImmediate(old.gameObject);
            Directory.CreateDirectory(Folder);
            AssetDatabase.Refresh();
            root = Group(Marker, town, Vector3.zero);
            PrepareMaterials();
            int outlines = RemoveOldStoneOutlines();
            Bridge();
            int ribbons = Filter(408, EnvironmentLayout.OldBanner) + Filter(409, EnvironmentLayout.OldBanner);
            HideSource(892);
            int trees = ClearStreet();
            Arena();
            Market();
            Surfaces();
            Shoppers();
            var state = root.gameObject.AddComponent<EnvironmentReviewState>();
            state.suppressed = hidden.Distinct().ToArray();
            state.removedObstacles = removed.ToArray();
            Verify();
            state.complete = true;
            EditorUtility.SetDirty(flow.valley);
            AssetDatabase.SaveAssets();
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            Debug.Log($"Environment review 2 saved: bridge moved 4m with deck/rails/navigation, {outlines} obsolete stone-outline faces and {ribbons} floating banner faces removed, {trees} street trees cleared, closed perimeter lamps, cedar arena logs, five coloured festival spans and six ambient shoppers. Wolf/animations/save untouched. Native visual approval is still required.");
        }

        static T Save<T>(T obj, string name)
            where T : UnityEngine.Object
        {
            var old = AssetDatabase.LoadAssetAtPath<T>(Folder + name);
            if (old)
            {
                EditorUtility.CopySerialized(obj, old);
                UnityEngine.Object.DestroyImmediate(obj);
                EditorUtility.SetDirty(old);
                return old;
            }

            AssetDatabase.CreateAsset(obj, Folder + name);
            return obj;
        }

        static Transform Group(string name, Transform parent, Vector3 p)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = p;
            return t;
        }

        static void Hide(GameObject o)
        {
            if (!o)
                return;
            o.SetActive(false);
            hidden.Add(o);
        }

        static void HideSource(int id)
        {
            if (filters.TryGetValue(id, out var f))
                Hide(f.gameObject);
        }

        static Vector3[] Read(int id)
        {
            if (source.TryGetValue(id, out var v))
                return v;
            using (var r = new BinaryReader(File.OpenRead("Assets/Sunward/Data/Valley.bytes")))
            {
                r.BaseStream.Position = records[id].offset;
                int nv = r.ReadInt32();
                r.ReadInt32();
                v = new Vector3[nv];
                for (int i = 0; i < nv; i++)
                {
                    v[i] = new Vector3(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                    r.BaseStream.Position += 36;
                }
            }

            source[id] = v;
            return v;
        }

        static int[] SourceIndices(int id)
        {
            using (var r = new BinaryReader(File.OpenRead("Assets/Sunward/Data/Valley.bytes")))
            {
                r.BaseStream.Position = records[id].offset;
                int nv = r.ReadInt32(), ni = r.ReadInt32();
                r.BaseStream.Position += nv * 48;
                var ix = new int[ni];
                for (int i = 0; i < ni; i++)
                    ix[i] = r.ReadInt32();
                return ix;
            }
        }

        // Filter CURRENT triangle indices so independent prior home/market removals stay removed.
        static int Filter(int id, Func<Vector3, bool> predicate)
        {
            if (!filters.TryGetValue(id, out var f))
                return 0;
            var v = Read(id);
            var ix = f.sharedMesh.triangles;
            var keep = new List<int>();
            int count = 0;
            for (int i = 0; i < ix.Length; i += 3)
                if (predicate(v[ix[i]]) && predicate(v[ix[i + 1]]) && predicate(v[ix[i + 2]]))
                    count++;
                else
                    keep.AddRange(new[] { ix[i], ix[i + 1], ix[i + 2] });
            if (count > 0)
            {
                f.sharedMesh.triangles = keep.ToArray();
                f.sharedMesh.RecalculateBounds();
                EditorUtility.SetDirty(f.sharedMesh);
                if (keep.Count == 0)
                    Hide(f.gameObject);
            }

            return count;
        }

        static float Ground(Vector3 p) => Valley.TerrainHeight(data.world.terrain, p);
        static void PrepareMaterials()
        {
            string path = "Assets/Sunward/Textures/SurfaceDetail/";
            foreach (string rawFile in Directory.GetFiles(path, "*.png"))
            {
                string file = rawFile.Replace('\\', '/');
                var importer = AssetImporter.GetAtPath(file) as TextureImporter;
                if (!importer)
                    throw new InvalidDataException("Texture not imported: " + file);
                bool normal = file.EndsWith("-Normal.png"), mask = file.EndsWith("-Mask.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (importer.textureType != type || importer.sRGBTexture != (!normal && !mask) || importer.textureShape != TextureImporterShape.Texture2D || importer.anisoLevel != 4)
                {
                    importer.textureShape = TextureImporterShape.Texture2D;
                    importer.textureType = type;
                    importer.sRGBTexture = !normal && !mask;
                    importer.wrapMode = TextureWrapMode.Repeat;
                    importer.filterMode = FilterMode.Trilinear;
                    importer.anisoLevel = 4;
                    importer.maxTextureSize = 1024;
                    importer.SaveAndReimport();
                }
            }

            stone = Detail("Granite", false);
            cedar = UvDetail("Cedar");
            endgrain = UvDetail("Endgrain");
            earth = Detail("Earth", false);
            grass = Detail("Meadow", true);
            plaster = Detail("Plaster", false);
            slate = Detail("Slate", false);
            gold = Colour("Antique brass", new Color(.58f, .39f, .12f), 0);
        }

        static Material Detail(string name, bool terrain)
        {
            var shader = Shader.Find("Sunward/Surface Detail PBR");
            if (!shader || ShaderUtil.ShaderHasError(shader))
                throw new InvalidDataException("Surface Detail PBR did not compile; scene was not marked complete.");
            var m = new Material(shader);
            string path = "Assets/Sunward/Textures/SurfaceDetail/";
            foreach (string channel in new[]
            {
                "Color",
                "Normal",
                "Mask"
            }

            )
            {
                m.SetTexture("_Detail" + channel, AssetDatabase.LoadAssetAtPath<Texture2D>(path + name + "-" + channel + ".png"));
                m.SetTexture("_Earth" + channel, AssetDatabase.LoadAssetAtPath<Texture2D>(path + "Earth-" + channel + ".png"));
            }

            m.SetFloat("_Scale", name == "Cedar" ? 1.3f : name == "Endgrain" ? 1 : .9f);
            m.SetFloat("_Terrain", terrain ? 1 : 0);
            m.enableInstancing = true;
            return Save(m, name + ".mat");
        }

        static Material UvDetail(string name)
        {
            string path = "Assets/Sunward/Textures/SurfaceDetail/";
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            m.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(path + name + "-Color.png"));
            m.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>(path + name + "-Normal.png"));
            m.EnableKeyword("_NORMALMAP");
            m.SetFloat("_BumpScale", .65f);
            var mask = AssetDatabase.LoadAssetAtPath<Texture2D>(path + name + "-Mask.png");
            m.SetTexture("_MetallicGlossMap", mask);
            m.SetTexture("_OcclusionMap", mask);
            m.EnableKeyword("_METALLICSPECGLOSSMAP");
            m.EnableKeyword("_OCCLUSIONMAP");
            m.SetFloat("_Smoothness", 1);
            m.enableInstancing = true;
            return Save(m, name + "-UV.mat");
        }

        static Mesh EndCap(float y, float radius)
        {
            RevolvedGeometry.Build(new[] { new Vector2(0, y), new Vector2(radius, y), new Vector2(radius, y + .008f), new Vector2(0, y + .008f) }, 32, out var v, out var uv, out var ix);
            for (int i = 0; i < v.Length; i++)
                uv[i] = new Vector2(v[i].x / (radius * 2) + .5f, v[i].z / (radius * 2) + .5f);
            return MeshAsset(v, ix, uv);
        }

        static Material Colour(string name, Color colour, float glow)
        {
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            m.SetColor("_BaseColor", colour);
            m.SetFloat("_Smoothness", .27f);
            m.enableInstancing = true;
            if (glow > 0)
            {
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", colour * glow);
            }

            return Save(m, name + ".mat");
        }

        static Mesh MeshAsset(Vector3[] v, int[] ix, Vector2[] uv = null)
        {
            MeshSafety.Validate("Environment detail", v, ix);
            var m = new Mesh
            {
                vertices = v,
                triangles = ix
            };
            if (uv != null)
                m.uv = uv;
            m.RecalculateNormals();
            m.RecalculateBounds();
            if (uv != null)
                m.RecalculateTangents();
            return Save(m, "Mesh-" + serial++ + ".asset");
        }

        static GameObject MeshObject(string name, Transform parent, Mesh mesh, Material mat, Vector3 p)
        {
            var go = Group(name, parent, p).gameObject;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            r.receiveShadows = true;
            return go;
        }

        static GameObject Box(string name, Transform parent, Vector3 p, Vector3 scale, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = p;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
            return go;
        }

        static Mesh Lathe(Vector2[] profile, int sides = 40)
        {
            string key = sides + ":" + string.Join(";", profile.Select(p => p.x.ToString("R", System.Globalization.CultureInfo.InvariantCulture) + "," + p.y.ToString("R", System.Globalization.CultureInfo.InvariantCulture)));
            if (lathes.TryGetValue(key, out var cached))
                return cached;
            RevolvedGeometry.Build(profile, sides, out var v, out var uv, out var ix);
            var mesh = MeshAsset(v, ix, uv);
            // Duplicate only UV seam vertices, retaining smooth shared-surface normals.
            // Without this the last strip interpolates across the entire grain texture.
            var vv = mesh.vertices.ToList();
            var nn = mesh.normals.ToList();
            var uu = mesh.uv.ToList();
            var seam = new Dictionary<int, int>();
            for (int t = 0; t < ix.Length; t += 3)
            {
                float lo = Mathf.Min(uv[ix[t]].x, Mathf.Min(uv[ix[t + 1]].x, uv[ix[t + 2]].x));
                float hi = Mathf.Max(uv[ix[t]].x, Mathf.Max(uv[ix[t + 1]].x, uv[ix[t + 2]].x));
                if (hi - lo < .5f)
                    continue;
                for (int j = 0; j < 3; j++)
                {
                    int k = ix[t + j];
                    if (uv[k].x > .5f)
                        continue;
                    if (!seam.TryGetValue(k, out int duplicate))
                    {
                        duplicate = vv.Count;
                        seam[k] = duplicate;
                        vv.Add(v[k]);
                        nn.Add(mesh.normals[k]);
                        uu.Add(new Vector2(uv[k].x + 1, uv[k].y));
                    }

                    ix[t + j] = duplicate;
                }
            }

            mesh.vertices = vv.ToArray();
            mesh.normals = nn.ToArray();
            mesh.uv = uu.ToArray();
            mesh.triangles = ix;
            mesh.RecalculateTangents();
            EditorUtility.SetDirty(mesh);
            lathes[key] = mesh;
            return mesh;
        }

        static GameObject Rod(string name, Transform parent, Vector3 a, Vector3 b, float r, Material mat)
        {
            var go = MeshObject(name, parent, Lathe(new[] { new Vector2(0, -.5f), new Vector2(1, -.5f), new Vector2(1, .5f), new Vector2(0, .5f) }, 16), mat, (a + b) * .5f);
            go.transform.localScale = new Vector3(r, (b - a).magnitude, r);
            go.transform.localRotation = Quaternion.FromToRotation(Vector3.up, b - a);
            return go;
        }

        static int RemoveOldStoneOutlines()
        {
            foreach (int id in new[]
            {
                371,
                779,
                780,
                781,
                782,
                783,
                788,
                789,
                792,
                793
            }

            )
            {
                var v = Read(id);
                foreach (var island in SurfaceIslands.Find(v, SourceIndices(id)))
                {
                    var b = new Bounds(v[island[0]], Vector3.zero);
                    foreach (int i in island)
                        b.Encapsulate(v[i]);
                    bool dedicated = id == 792 || id == 793 || id == 788 || id == 789;
                    if (!dedicated && !RockSeating.Suitable(data.world, b))
                        continue;
                    b.Expand(.10f);
                    oldStoneBounds.Add(b);
                }
            }

            int count = 0;
            foreach (var pair in filters)
                if (data.materials[records[pair.Key].material].kind == "ink")
                    count += Filter(pair.Key, p => oldStoneBounds.Any(b => b.Contains(p)));
            return count;
        }

        static void Bridge()
        {
            flow.valley.homeBridgeSourceZ = 8;
            Valley.HomeBridgeSourceZ = 8;
            for (int id = 795; id <= 799; id++)
                if (filters.TryGetValue(id, out var f))
                {
                    var v = Read(id).Select(p => p + Vector3.forward * 4).ToArray();
                    f.sharedMesh.vertices = v;
                    f.sharedMesh.RecalculateBounds();
                    EditorUtility.SetDirty(f.sharedMesh);
                }

            foreach (var c in town.GetComponentsInChildren<Collider>(true))
            {
                if (c is MeshCollider mc && mc.sharedMesh && mc.sharedMesh.name == "Arched bridge collision · 12")
                    c.transform.localPosition = new Vector3(0, 0, 4);
                if (c.name == "Building / rail collider" && Mathf.Abs(c.transform.position.x + 23) < .01f && (Mathf.Abs(c.transform.position.z + 10.6f) < .01f || Mathf.Abs(c.transform.position.z + 13.4f) < .01f))
                    c.transform.position += Vector3.forward * 4;
            }

            var old = new Vector3(-29, 0, -11);
            RemoveLantern(old);
            Lantern(new Vector3(-30, 0, -5.2f), "Bridge approach · clear of house and landing");
            // Rough-laid flagstones bridge the deck to the physical riverbanks.
            foreach (int side in new[]
            {
                -1,
                1
            }

            )
                for (int j = 0; j < 5; j++)
                {
                    float x = side < 0 ? -28.05f - j * .31f : -17.95f + j * .31f;
                    var p = new Vector3(x, 0, -8);
                    p.y = Ground(p) + .025f;
                    var slab = MeshObject("Bridge approach flagstone", root, Lathe(new[] { new Vector2(0, 0), new Vector2(.48f, 0), new Vector2(.49f, .045f), new Vector2(.45f, .075f), new Vector2(0, .075f) }, 8), stone, p);
                    slab.transform.localScale = new Vector3(.55f, 1, 2.4f);
                    slab.transform.localRotation = Quaternion.Euler(0, j % 2 * 8 - 4, 0);
                }
        }

        static void RemoveLantern(Vector3 p)
        {
            // All source cap/window/stem/outline faces, including the formerly open roof.
            foreach (var pair in filters)
            {
                string kind = data.materials[records[pair.Key].material].kind;
                if (kind != "stone" && kind != "wood" && kind != "wash" && kind != "ink")
                    continue;
                var sv = Read(pair.Key);
                if (sv.Max(q => q.y) - sv.Min(q => q.y) < .04f)
                    continue;
                Filter(pair.Key, q => Mathf.Abs(q.x - p.x) < .65f && Mathf.Abs(q.z - p.z) < .65f && q.y > -.25f && q.y < 2.3f);
            }

            foreach (var t in town.GetComponentsInChildren<Transform>(true))
                if (t.name == "Kasuga lantern · closed stone cap" && Vector2.Distance(new Vector2(t.position.x, t.position.z), new Vector2(p.x, p.z)) < .25f)
                    Hide(t.gameObject);
            foreach (var light in town.GetComponentsInChildren<Light>(true))
                if (Mathf.Abs(light.transform.position.x - p.x) < .3f && Mathf.Abs(light.transform.position.z - p.z) < .3f)
                    Hide(light.gameObject);
            foreach (var c in town.GetComponentsInChildren<CapsuleCollider>(true))
                if (c.name == "Trunk / rock collider" && Mathf.Abs(c.transform.position.x - p.x) < .1f && Mathf.Abs(c.transform.position.z - p.z) < .1f)
                    c.enabled = false;
            removed.Add(p);
        }

        static int ClearStreet()
        {
            int count = 0, id = 0;
            foreach (var a in data.assets)
            {
                int first = id;
                id += a.meshes.Length;
                if (a.meshes.Length == 0)
                    continue;
                bool foliage = a.meshes.Any(m => data.materials[m.material].kind == "leaves");
                if (!foliage)
                    continue;
                var v = Enumerable.Range(first, a.meshes.Length).SelectMany(i => Read(i)).ToArray();
                var b = new Bounds(v[0], Vector3.zero);
                foreach (var p in v)
                    b.Encapsulate(p);
                if (b.size.y < 2 || b.size.y > 16 || b.size.x > 24 || b.size.z > 24 || !Street(b))
                    continue;
                for (int i = first; i < id; i++)
                    HideSource(i);
                removed.Add(b.center);
                count++;
            }

            foreach (var t in town.GetComponentsInChildren<Transform>(true))
                if (t.name == "Cherry_A" || t.name == "Cherry_B" || t.name == "Maple_A" || t.name == "Pine_A")
                {
                    var rs = t.GetComponentsInChildren<Renderer>(true);
                    if (rs.Length == 0)
                        continue;
                    var b = rs[0].bounds;
                    foreach (var r in rs.Skip(1))
                        b.Encapsulate(r.bounds);
                    if (Street(b))
                    {
                        removed.Add(t.position);
                        Hide(t.gameObject);
                        count++;
                    }
                }

            // Some original cherry trees were batched into the shared TownV3 buffer,
            // not exported as a leaf asset group. Remove their referenced components
            // at central-road trunk locations; leave houses/porches outside the road.
            var trunks = data.world.obstacles.Where(c => c.r >= .4f && c.r < .8f && Mathf.Abs(c.x) < 3.4f && Mathf.Abs(c.z) < 18).ToArray();
            foreach (var c in trunks)
            {
                var p = new Vector3(c.x, 0, -c.z);
                removed.Add(p);
                foreach (var pair in filters)
                {
                    string kind = data.materials[records[pair.Key].material].kind;
                    if (kind != "leaves" && kind != "wood" && kind != "ink")
                        continue;
                    var v = Read(pair.Key);
                    var kill = new HashSet<int>();
                    foreach (var island in SurfaceIslands.Find(v, pair.Value.sharedMesh.triangles))
                    {
                        var b = new Bounds(v[island[0]], Vector3.zero);
                        foreach (int k in island)
                            b.Encapsulate(v[k]);
                        if (b.center.y > .5f && b.size.y > 1.4f && Mathf.Abs(b.center.x - p.x) < 1.4f && Mathf.Abs(b.center.z - p.z) < 1.4f)
                            foreach (int k in island)
                                kill.Add(k);
                    }

                    // Filter by referenced indices to retain all other source islands.
                    var ix = pair.Value.sharedMesh.triangles;
                    var keep = new List<int>();
                    for (int k = 0; k < ix.Length; k += 3)
                        if (!kill.Contains(ix[k]))
                            keep.AddRange(new[] { ix[k], ix[k + 1], ix[k + 2] });
                    if (keep.Count != ix.Length)
                    {
                        pair.Value.sharedMesh.triangles = keep.ToArray();
                        pair.Value.sharedMesh.RecalculateBounds();
                        EditorUtility.SetDirty(pair.Value.sharedMesh);
                    }
                }
            }

            foreach (var c in town.GetComponentsInChildren<CapsuleCollider>(true))
                if (c.name == "Trunk / rock collider" && removed.Any(p => Mathf.Abs(c.transform.position.x - p.x) < .4f && Mathf.Abs(c.transform.position.z - p.z) < .4f))
                    c.enabled = false;
            return count + trunks.Length;
        }

        static bool Street(Bounds b) => EnvironmentLayout.Street(b);
        static void Lantern(Vector3 p, string label)
        {
            p.y = Ground(p) - .04f;
            var t = Group(label, root, p);
            MeshObject("Carved stone pedestal", t, Lathe(new[] { new Vector2(0, 0), new Vector2(.43f, 0), new Vector2(.45f, .12f), new Vector2(.24f, .24f), new Vector2(.14f, .34f), new Vector2(.13f, .95f), new Vector2(.28f, 1.06f), new Vector2(0, 1.06f) }), stone, Vector3.zero);
            Box("Solid firebox", t, new Vector3(0, 1.28f, 0), new Vector3(.48f, .46f, .48f), stone);
            var lit = Colour("Lantern glow", new Color(1, .66f, .26f), 1.4f);
            for (int s = 0; s < 4; s++)
            {
                var face = Group("Inset amber window", t, new Vector3(Mathf.Sin(s * Mathf.PI / 2) * .244f, 1.29f, Mathf.Cos(s * Mathf.PI / 2) * .244f));
                face.localRotation = Quaternion.Euler(0, s * 90, 0);
                Box("Window paper", face, Vector3.zero, new Vector3(.27f, .29f, .015f), lit);
                for (int k = -1; k <= 1; k++)
                    Box("Window lattice", face, new Vector3(k * .09f, 0, .012f), new Vector3(.012f, .31f, .018f), cedar);
            }

            MeshObject("Watertight carved roof", t, Lathe(RevolvedGeometry.LanternRoof), stone, Vector3.zero);
            LightAt(t, new Vector3(0, 1.30f, 0), new Color(1, .62f, .25f), .65f, 3.2f);
        }

        static void Arena()
        {
            foreach (var p in new[]
            {
                new Vector3(20, 0, 11),
                new Vector3(32, 0, 11),
                new Vector3(39, 0, -1)
            }

            )
                RemoveLantern(p);
            for (int i = 0; i < 8; i++)
            {
                float a = i * Mathf.PI / 4;
                var p = new Vector3(35 + Mathf.Cos(a) * 19.1f, 0, Mathf.Sin(a) * 19.1f);
                if (p.x < 17 && Mathf.Abs(p.z) < 4)
                    continue;
                Lantern(p, "Arena perimeter lantern · " + i);
            }

            for (int id = 715; id <= 730; id++)
                HideSource(id); // Legacy thin brown brush arcs, not timber.
            var fence = Group("Arena · cut cedar boundary logs", root, Vector3.zero);
            for (int i = 0; i < 32; i++)
            {
                float a = i * Mathf.PI * 2 / 32, b = (i + 1) * Mathf.PI * 2 / 32;
                Vector3 Point(float angle) => EnvironmentLayout.ArenaPoint(angle);
                var p = Point(a);
                var q = Point(b);
                if (EnvironmentLayout.GateOpening(p) || EnvironmentLayout.GateOpening(q))
                    continue;
                p.y = Ground(p) + .16f;
                q.y = Ground(q) + .16f;
                var log = Rod("Arena · full cedar log " + i, fence, p, q, .235f, cedar);
                log.layer = 6;
                var col = log.AddComponent<BoxCollider>();
                col.size = new Vector3(2, 1, 2);
                log.AddComponent<VillageWorldSolid>();
                // Unit rod axes and caps rotate together: grain follows the timber.
                foreach (int side in new[]
                {
                    -1,
                    1
                }

                )
                {
                    var cap = MeshObject("Visible saw-cut growth rings", fence, EndCap(0, .235f), endgrain, side < 0 ? p : q);
                    cap.transform.localRotation = Quaternion.FromToRotation(Vector3.up, (q - p) * side);
                }

                if (i % 4 == 0)
                {
                    var peg = p;
                    peg.y -= .26f;
                    MeshObject("Cedar locking peg", fence, Lathe(new[] { new Vector2(0, 0), new Vector2(.12f, 0), new Vector2(.10f, .65f), new Vector2(0, .65f) }, 24), cedar, peg);
                }
            }
        }

        static void LightAt(Transform parent, Vector3 p, Color colour, float intensity, float range)
        {
            var l = Group("Warm practical light", parent, p).gameObject.AddComponent<Light>();
            l.type = LightType.Point;
            l.color = colour;
            l.intensity = intensity;
            l.range = range;
            l.shadows = LightShadows.None;
        }

        static void Market()
        {
            foreach (string path in new[]
            {
                WindflowerRenovation.RootName + "/Market · supported festival line",
                "Windflower · visual remake/Festival · seigaiha cloth, ofuda and tassels"
            }

            )
            {
                var old = town.Find(path);
                if (old)
                    Hide(old.gameObject);
            }

            var street = Group("Market · five vibrant festival spans", root, Vector3.zero);
            Color[] palette =
            {
                new Color(.78f, .12f, .09f),
                new Color(.06f, .33f, .43f),
                new Color(.87f, .52f, .08f),
                new Color(.41f, .16f, .48f),
                new Color(.16f, .49f, .34f)
            };
            var colors = palette.Select((c, i) => Colour("Festival silk " + i, c, .18f)).ToArray();
            foreach (var cloth in colors)
            {
                cloth.SetFloat("_Cull", 0);
                EditorUtility.SetDirty(cloth);
            }

            var shades = palette.Select((c, i) => Colour("Coloured luminous paper " + i, Color.Lerp(c, Color.white, .18f), .75f)).ToArray();
            var dark = Colour("Indigo twine", new Color(.08f, .10f, .11f), 0);
            var lampMesh = Lathe(new[] { new Vector2(0, -.32f), new Vector2(.12f, -.32f), new Vector2(.24f, -.23f), new Vector2(.29f, 0), new Vector2(.24f, .23f), new Vector2(.12f, .32f), new Vector2(0, .32f) }, 32);
            var ribMesh = Lathe(new[] { new Vector2(.28f, -.006f), new Vector2(.293f, -.006f), new Vector2(.293f, .006f), new Vector2(.28f, .006f), new Vector2(.28f, -.006f) }, 32);
            for (int span = 0; span < 5; span++)
            {
                float z = new[]
                {
                    -15f,
                    -8f,
                    -3f,
                    9f,
                    16f
                }[span];
                var line = Group("Supported span " + span, street, new Vector3(0, 0, z));
                for (int side = -1; side <= 1; side += 2)
                {
                    var p = new Vector3(side * 3.65f, 0, 0);
                    p.y = Ground(new Vector3(p.x, 0, z)) - .08f;
                    Rod("Cedar support", line, p, new Vector3(p.x, 3.9f, 0), .075f, cedar);
                }

                Vector3 Cable(float t) => new Vector3(Mathf.Lerp(-3.65f, 3.65f, t), 3.85f - .55f * Mathf.Sin(t * Mathf.PI), 0);
                for (int j = 0; j < 16; j++)
                    Rod("Tensioned cable", line, Cable(j / 16f), Cable((j + 1) / 16f), .012f, dark);
                for (int i = 0; i < 7; i++)
                {
                    int colour = (i + span * 2) % 5;
                    var anchor = Group("Swaying coloured lantern " + i, line, Cable((i + 1) / 8f));
                    Rod("Suspension", anchor, Vector3.zero, new Vector3(0, -.24f, 0), .009f, dark);
                    MeshObject("Coloured ribbed paper", anchor, lampMesh, shades[colour], new Vector3(0, -.55f, 0));
                    for (int rib = -2; rib <= 2; rib++)
                    {
                        var go = MeshObject("Bamboo rib", anchor, ribMesh, dark, new Vector3(0, -.55f + rib * .095f, 0));
                        float s = Mathf.Sqrt(1 - rib * rib * .09f);
                        go.transform.localScale = new Vector3(s, 1, s);
                    }

                    Box("Gold painted crest", anchor, new Vector3(0, -.55f, .285f), new Vector3(.11f, .18f, .012f), gold).transform.localRotation = Quaternion.Euler(0, 0, 45);
                    var sway = anchor.gameObject.AddComponent<HangingWind>();
                    sway.phase = span + i * .7f;
                    sway.amplitude = 3.4f;
                    if (i == 1 || i == 5)
                        LightAt(anchor, new Vector3(0, -.56f, 0), Color.Lerp(palette[colour], new Color(1, .72f, .40f), .8f), .95f, 4);
                }

                for (int i = 0; i < 12; i++)
                {
                    var flag = Group("Silk streamer " + i, line, Cable((i + .5f) / 12f) + new Vector3(0, 0, .05f));
                    var v = new List<Vector3>();
                    var ix = new List<int>();
                    for (int j = 0; j <= 6; j++)
                    {
                        float t = j / 6f;
                        v.Add(new Vector3(-.095f * (1 - t * .65f), -t * (.55f + (i % 3) * .13f), Mathf.Sin(t * 4 + i) * t * .08f));
                        v.Add(new Vector3(.095f * (1 - t * .65f), -t * (.55f + (i % 3) * .13f), Mathf.Sin(t * 4 + i) * t * .08f));
                        if (j < 6)
                        {
                            int k = j * 2;
                            ix.AddRange(new[] { k, k + 2, k + 1, k + 1, k + 2, k + 3 });
                        }
                    }

                    MeshObject("Coloured flowing silk", flag, MeshAsset(v.ToArray(), ix.ToArray()), colors[(i + span) % 5], Vector3.zero);
                    var sway = flag.gameObject.AddComponent<HangingWind>();
                    sway.phase = i + span;
                    sway.amplitude = 8;
                }
            }

            // Carts and displayed goods remain at the road edges, outside the clear central lane.
            for (int i = 0; i < 8; i++)
            {
                float x = i % 2 == 0 ? -3.25f : 3.25f, z = new[]
                {
                    -12f,
                    -6f,
                    11f,
                    17f
                }[i / 2];
                var p = new Vector3(x, 0, z);
                p.y = Ground(p);
                var cart = Group("Market street · produce and flower basket " + i, street, p);
                MeshObject("Woven cedar basket", cart, Lathe(new[] { new Vector2(0, 0), new Vector2(.31f, 0), new Vector2(.42f, .44f), new Vector2(.37f, .46f), new Vector2(.28f, .06f), new Vector2(0, .06f) }, 24), cedar, Vector3.zero);
                for (int item = 0; item < 8; item++)
                {
                    var fruit = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                    fruit.name = i % 2 == 0 ? "Persimmon display" : "Blossom arrangement";
                    fruit.transform.SetParent(cart, false);
                    fruit.transform.localPosition = new Vector3(Mathf.Sin(item * 2.4f) * .24f, .40f + (item % 3) * .07f, Mathf.Cos(item * 2.4f) * .24f);
                    fruit.transform.localScale = Vector3.one * .13f;
                    fruit.GetComponent<Renderer>().sharedMaterial = colors[(item + i) % 5];
                    UnityEngine.Object.DestroyImmediate(fruit.GetComponent<Collider>());
                }
            }

            var ps = Group("Warm market motes · bounded 48 particles", street, new Vector3(0, 2, 0)).gameObject.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.startLifetime = 5;
            main.startSpeed = .07f;
            main.startSize = .035f;
            main.startColor = new Color(1, .72f, .32f, .6f);
            main.maxParticles = 48;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            var emission = ps.emission;
            emission.rateOverTime = 7;
            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(5, 1.5f, 31);
            var r = ps.GetComponent<ParticleSystemRenderer>();
            var glow = new Texture2D(64, 64, TextureFormat.RGBA32, false);
            var pixels = new Color[64 * 64];
            for (int y = 0; y < 64; y++)
                for (int x = 0; x < 64; x++)
                {
                    float radius = new Vector2((x - 31.5f) / 31.5f, (y - 31.5f) / 31.5f).magnitude;
                    float alpha = Mathf.Pow(Mathf.Clamp01(1 - radius), 2);
                    pixels[y * 64 + x] = new Color(1, 1, 1, alpha);
                }

            glow.SetPixels(pixels);
            glow.Apply();
            glow.wrapMode = TextureWrapMode.Clamp;
            var mat = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            mat.SetTexture("_BaseMap", Save(glow, "SoftGlow.asset"));
            mat.SetFloat("_Surface", 1);
            mat.SetFloat("_ZWrite", 0);
            mat.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            mat.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            mat.renderQueue = 3000;
            r.sharedMaterial = Save(mat, "MarketMotes.mat");
            var fade = ps.colorOverLifetime;
            fade.enabled = true;
            var gradient = new Gradient();
            gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) }, new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(.65f, .2f), new GradientAlphaKey(.65f, .7f), new GradientAlphaKey(0, 1) });
            fade.color = gradient;
        }

        static void Surfaces()
        {
            foreach (var pair in filters)
            {
                string kind = data.materials[records[pair.Key].material].kind;
                var r = pair.Value.GetComponent<MeshRenderer>();
                if (!r)
                    continue;
                if (pair.Key == 751)
                    r.sharedMaterial = grass;
                else if (kind == "stone")
                    r.sharedMaterial = stone;
                else if (kind == "wood")
                {
                    var m = new Material(cedar);
                    if (pair.Value.sharedMesh.uv.Length == pair.Value.sharedMesh.vertexCount)
                    {
                        pair.Value.sharedMesh.RecalculateTangents();
                        EditorUtility.SetDirty(pair.Value.sharedMesh);
                    }

                    if (pair.Key == 795)
                        m.SetFloat("_Cull", 0);
                    if (ColorUtility.TryParseHtmlString("#" + data.materials[records[pair.Key].material].color, out var tint))
                    {
                        float largest = Mathf.Max(tint.r, Mathf.Max(tint.g, tint.b));
                        m.SetColor("_BaseColor", Color.Lerp(Color.white, new Color(tint.r / Mathf.Max(.01f, largest), tint.g / Mathf.Max(.01f, largest), tint.b / Mathf.Max(.01f, largest)), .55f));
                    }

                    r.sharedMaterial = Save(m, "SourceTimber-" + pair.Key + ".mat");
                }
            }

            foreach (var f in town.GetComponentsInChildren<MeshFilter>(true))
                if (f.name.StartsWith("Grounded stone "))
                {
                    var b = f.sharedMesh.bounds;
                    int seed = 0;
                    foreach (char ch in f.name)
                        seed = (seed * 31 + ch) & 255;
                    SeatedStoneGeometry.Build(seed, out var v, out var ix);
                    float minX = v.Min(p => p.x), maxX = v.Max(p => p.x), minZ = v.Min(p => p.z), maxZ = v.Max(p => p.z);
                    for (int i = 0; i < v.Length; i++)
                        v[i] = new Vector3(b.min.x + (v[i].x - minX) * b.size.x / (maxX - minX), b.min.y + v[i].y * b.size.y, b.min.z + (v[i].z - minZ) * b.size.z / (maxZ - minZ));
                    f.sharedMesh = MeshAsset(v, ix);
                    f.GetComponent<MeshRenderer>().sharedMaterial = stone;
                }

            // Connect the new surface work to the visible replacement houses/stalls,
            // not only to hidden legacy meshes. Never touch skinned residents or Amaterasu.
            foreach (var renderer in town.GetComponentsInChildren<MeshRenderer>(true))
            {
                if (renderer.transform.IsChildOf(root))
                    continue;
                var mats = renderer.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (!mats[i])
                        continue;
                    string path = AssetDatabase.GetAssetPath(mats[i]);
                    if (path == "Assets/Sunward/Generated/Remake/Oak.mat")
                    {
                        mats[i] = cedar;
                        changed = true;
                    }
                    else if (path == "Assets/Sunward/Generated/Remake/Stone.mat")
                    {
                        mats[i] = stone;
                        changed = true;
                    }
                    else if (path == "Assets/Sunward/Generated/Remake/Plaster.mat")
                    {
                        mats[i] = plaster;
                        changed = true;
                    }
                    else if (path == "Assets/Sunward/Generated/Remake/Roof.mat")
                    {
                        mats[i] = slate;
                        changed = true;
                    }
                }

                if (changed)
                    renderer.sharedMaterials = mats;
            }

            // Upgrade existing arena floor/path materials without changing combat collision.
            foreach (var pair in filters)
            {
                var v = Read(pair.Key);
                if (v.Length == 0)
                    continue;
                var b = new Bounds(v[0], Vector3.zero);
                foreach (var p in v)
                    b.Encapsulate(p);
                string kind = data.materials[records[pair.Key].material].kind;
                if (b.size.y < .02f && b.max.y < .2f && (kind == "stone" || kind == "grass"))
                    pair.Value.GetComponent<MeshRenderer>().sharedMaterial = kind == "grass" ? grass : earth;
            }
        }

        static void Shoppers()
        {
            var group = Group("Market · six ambient browsing residents", root, Vector3.zero);
            for (int i = 0; i < 6; i++)
            {
                var template = flow.npcObjects[i % flow.npcObjects.Length];
                if (!template)
                    continue;
                var go = UnityEngine.Object.Instantiate(template, group);
                go.name = "Ambient shopper " + (i + 1);
                foreach (var resident in go.GetComponents<VillageResident>())
                    UnityEngine.Object.DestroyImmediate(resident);
                float x = i % 2 == 0 ? -2.25f : 2.25f, z = -12 + (i / 2) * 12;
                var p = new Vector3(x, 0, z);
                p.y = Ground(p);
                go.transform.position = p;
                go.transform.rotation = Quaternion.Euler(0, i % 2 == 0 ? 0 : 180, 0);
                var walker = go.AddComponent<MarketWalker>();
                walker.game = flow;
                walker.phase = i * .6f;
                walker.route = new[]
                {
                    p + Vector3.forward * 1.3f,
                    p - Vector3.forward * 1.3f
                };
                var rig = go.GetComponent<ResidentLocomotion>();
                if (rig)
                {
                    rig.game = flow;
                    rig.stallkeeper = false;
                }

                var body = go.GetComponent<Rigidbody>();
                if (body)
                    body.isKinematic = true;
            }
        }

        static void Verify()
        {
            if (Mathf.Abs(flow.valley.homeBridgeSourceZ - 8) > .01f)
                throw new InvalidDataException("Bridge navigation not migrated.");
            if (!filters.TryGetValue(795, out var bridge) || Mathf.Abs(bridge.sharedMesh.bounds.center.z + 8) > .04f)
                throw new InvalidDataException("Bridge geometry does not match navigation.");
            if (root.GetComponentsInChildren<MarketWalker>().Length != 6)
                throw new InvalidDataException("Expected six ambient shoppers.");
            foreach (var o in hidden)
                if (o && o.activeSelf)
                    throw new InvalidDataException("Suppressed legacy object is active: " + o.name);
            foreach (var f in root.GetComponentsInChildren<MeshFilter>())
                MeshSafety.Validate(f.name, f.sharedMesh.vertices, f.sharedMesh.triangles);
            if (root.GetComponentsInChildren<Light>().Any(l => l.shadows != LightShadows.None))
                throw new InvalidDataException("Festival point-light shadow budget exceeded.");
        }
    }
}
