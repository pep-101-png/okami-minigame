using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Unity.Cinemachine;
using Sunward;

namespace Sunward.Editor
{
    [InitializeOnLoad]
    public static class SunwardProjectBuilder
    {
        const string Root = "Assets/Sunward/", Generated = Root + "Generated/", ScenePath = Root + "Scenes/Windflower.unity";
        static SunwardProjectBuilder()
        {
            EditorApplication.delayCall += InitialiseWhenReady;
        }

        static void InitialiseWhenReady()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorApplication.delayCall += InitialiseWhenReady;
                return;
            }

            if (!EditorApplication.isPlayingOrWillChangePlaymode && !File.Exists(ScenePath) && !SessionState.GetBool("SunwardBuildAttempted", false))
            {
                SessionState.SetBool("SunwardBuildAttempted", true);
                try
                {
                    Build();
                }
                catch (Exception e)
                {
                    Debug.LogException(e);
                    Debug.LogError("Sunward initial scene build failed. Read the first Console error, then use Sunward > Create or Rebuild V3 Scene. The Three.js game is untouched.");
                }
            }
        }

        [MenuItem("Sunward/Create or Rebuild V3 Scene")]
        public static void Build()
        {
            if (EditorApplication.isPlaying)
                throw new InvalidOperationException("Exit Play Mode before rebuilding.");
            if (!Directory.Exists(Generated))
                Directory.CreateDirectory(Generated);
            Directory.CreateDirectory(Root + "Scenes");
            AssetDatabase.Refresh();
            ConfigurePipeline();
            var data = JsonUtility.FromJson<ValleyData>(File.ReadAllText(Root + "Data/Valley.json"));
            var materials = MakeMaterials(data.materials);
            var prefabs = MakePrefabs(data, materials);
            var wolf = MakeWolf();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var town = (GameObject)PrefabUtility.InstantiatePrefab(prefabs["TownV3"]);
            town.name = "V3 · preserved painted valley";
            var logic = new GameObject("Sunward · game systems");
            var valley = logic.AddComponent<Valley>();
            valley.source = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "Data/Valley.json");
            var flow = logic.AddComponent<GameFlow>();
            flow.valley = valley;
            flow.Fx = logic.AddComponent<PaintedEffects>();
            flow.Fx.ink = Energy("Impact", new Color(.93f, .88f, .75f, 1), false);
            flow.Audio = logic.AddComponent<ValleyAudio>();
            flow.Audio.bark = AssetDatabase.LoadAssetAtPath<AudioClip>(Root + "Audio/bark.ogg");
            flow.Audio.growl = AssetDatabase.LoadAssetAtPath<AudioClip>(Root + "Audio/wolf-growl-1.ogg");
            flow.Audio.hit = AssetDatabase.LoadAssetAtPath<AudioClip>(Root + "Audio/wolf-hit-1.ogg");
            flow.Audio.howl = AssetDatabase.LoadAssetAtPath<AudioClip>(Root + "Audio/wolf-howl.ogg");
            flow.barrierMaterial = Energy("ArenaInk", new Color(.38f, .42f, .34f, .80f), true);
            flow.projectileMaterial = Energy("Projectile", new Color(.39f, .24f, .42f, 1), false);
            var player = (GameObject)PrefabUtility.InstantiatePrefab(wolf);
            player.name = "Amaterasu";
            player.layer = 7;
            player.transform.position = new Vector3(-34, 0, -22);
            var motor = player.AddComponent<WolfMotor>();
            motor.game = flow;
            motor.valley = valley;
            flow.Player = motor;
            var cc = player.GetComponent<CharacterController>();
            cc.radius = .38f;
            cc.height = 1.20f;
            cc.center = Vector3.up * .65f;
            cc.stepOffset = .34f;
            cc.slopeLimit = 48;
            cc.skinWidth = .025f;
            motor.animationView = player.AddComponent<WolfAnimation>();
            motor.animationView.animator = player.GetComponentInChildren<Animator>();
            motor.animationView.animator.applyRootMotion = false;
            var combat = player.AddComponent<WolfCombat>();
            flow.Combat = combat;
            combat.game = flow;
            combat.motor = motor;
            combat.spear = Weapon("spear", prefabs["Spear"]);
            combat.sundial = Weapon("sundial", prefabs["Sundial"]);
            combat.headSocket = Socket(player, "Mouth weapon", Find(player, "DEF_head"), new Vector3(0, 1.428f, 1.4144f));
            combat.headSocket.Rotate(0, 180, 0, Space.Self);
            combat.backSocket = Socket(player, "Back weapon", Find(player, "DEF_chest"), new Vector3(0, 1.428f, .034f));
            combat.backSocket.Rotate(28.6f, 0, 0, Space.Self);
            var cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            var cam = cameraObject.AddComponent<Camera>();
            cam.fieldOfView = 38;
            cam.farClipPlane = 280;
            cam.backgroundColor = new Color(.86f, .89f, .84f);
            cameraObject.AddComponent<AudioListener>();
            cameraObject.AddComponent<CinemachineBrain>();
            cameraObject.AddComponent<UniversalAdditionalCameraData>();
            motor.view = cam.transform;
            var cutaway = town.AddComponent<HomeCutaway>();
            cutaway.player = motor;
            cutaway.roof = town.GetComponentsInChildren<Renderer>().Where(r => r.name.StartsWith("HomeRoof")).ToArray();
            var orbit = new GameObject("Cinemachine · painted valley camera").AddComponent<OrbitCamera>();
            orbit.target = motor;
            orbit.virtualCamera = orbit.gameObject.AddComponent<CinemachineCamera>();
            orbit.virtualCamera.Lens.FieldOfView = 38;
            orbit.virtualCamera.Lens.FarClipPlane = 280;
            flow.Home = logic.AddComponent<HomeRest>();
            flow.Home.game = flow;
            flow.Shelf = logic.AddComponent<CollectibleShelf>();
            flow.Shelf.game = flow;
            flow.Shelf.slots = new Transform[6];
            for (int i = 0; i < 6; i++)
            {
                var slot = new GameObject("Collectible slot " + (i + 1)).transform;
                slot.SetParent(town.transform);
                slot.position = new Vector3(-31.1f - .87f + (i % 3) * .87f, .43f + (i / 3) * .64f, -12.54f);
                flow.Shelf.slots[i] = slot;
            }

            logic.AddComponent<WaterContact>().game = flow;
            var growth = player.AddComponent<DivineGrowth>();
            growth.game = flow;
            growth.player = motor;
            growth.ink = flow.Fx.ink;
            flow.npcData = data.world.npcs;
            flow.npcObjects = new GameObject[flow.npcData.Length];
            for (int i = 0; i < flow.npcData.Length; i++)
            {
                var n = data.world.npcs[i];
                var obj = (GameObject)PrefabUtility.InstantiatePrefab(prefabs[n.asset]);
                obj.name = n.name;
                obj.transform.position = new Vector3(n.position[0], n.position[1], n.position[2]);
                var col = obj.AddComponent<CapsuleCollider>();
                col.radius = .38f;
                col.height = 1.7f;
                col.center = Vector3.up * .85f;
                obj.layer = 6;
                flow.npcObjects[i] = obj;
            }

            flow.spirits = EnemyDefinitions(prefabs);
            Collisions(data.world, town);
            logic.AddComponent<PerformanceHUD>();
            var ui = logic.AddComponent<ScrollUI>();
            ui.game = flow;
            var sun = new GameObject("Soft afternoon wash").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1, .96f, .86f);
            sun.intensity = 1.2f;
            sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(42, -38, 0);
            var warm = new GameObject("Home · warm lantern wash").AddComponent<Light>();
            warm.type = LightType.Point;
            warm.transform.position = new Vector3(-34, 2.2f, -14);
            warm.color = new Color(1, .73f, .43f);
            warm.intensity = 1.6f;
            warm.range = 8;
            warm.shadows = LightShadows.None;
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.66f, .74f, .73f);
            RenderSettings.ambientEquatorColor = new Color(.57f, .64f, .58f);
            RenderSettings.ambientGroundColor = new Color(.36f, .42f, .38f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(.79f, .85f, .80f);
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = .0043f;
            player.transform.position = new Vector3(-34, Sample(data.world.terrain, -34, 22), -22);
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(ScenePath, true)
            };
            EditorUserBuildSettings.selectedBuildTargetGroup = BuildTargetGroup.Standalone;
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = player;
            Debug.Log("Sunward V3 scene generated. Open Assets/Sunward/Scenes/Windflower and press Play. Runtime verification is required.");
        }

        static float Sample(Sunward.TerrainData t, float x, float z)
        {
            float fx = Mathf.Clamp((x - t.minX) / t.step, 0, t.nx - 1.001f), fz = Mathf.Clamp((z - t.minZ) / t.step, 0, t.nz - 1.001f);
            int i = (int)fx, j = (int)fz;
            return Mathf.Lerp(Mathf.Lerp(t.heights[j * t.nx + i], t.heights[j * t.nx + i + 1], fx - i), Mathf.Lerp(t.heights[(j + 1) * t.nx + i], t.heights[(j + 1) * t.nx + i + 1], fx - i), fz - j);
        }

        static T SaveAsset<T>(T obj, string name)
            where T : UnityEngine.Object
        {
            string path = Generated + name;
            var old = AssetDatabase.LoadAssetAtPath<T>(path);
            if (old)
            {
                EditorUtility.CopySerialized(obj, old);
                UnityEngine.Object.DestroyImmediate(obj);
                return old;
            }

            AssetDatabase.CreateAsset(obj, path);
            return obj;
        }

        static void ConfigurePipeline()
        {
            var renderer = SaveAsset(ScriptableObject.CreateInstance<UniversalRendererData>(), "ValleyRenderer.asset");
            var pipeline = UniversalRenderPipelineAsset.Create(renderer);
            pipeline.renderScale = 1;
            pipeline.msaaSampleCount = 2;
            pipeline.shadowDistance = 45;
            pipeline = SaveAsset(pipeline, "ValleyURP.asset");
            var pipelineSettings = new SerializedObject(pipeline);
            pipelineSettings.FindProperty("m_SoftShadowsSupported").boolValue = true;
            pipelineSettings.FindProperty("m_MainLightShadowmapResolution").intValue = 2048;
            pipelineSettings.ApplyModifiedProperties();
            GraphicsSettings.defaultRenderPipeline = pipeline;
            QualitySettings.renderPipeline = pipeline;
            PlayerSettings.companyName = "Sunward";
            PlayerSettings.productName = "Sunward - Amaterasu";
            PlayerSettings.defaultScreenWidth = 1600;
            PlayerSettings.defaultScreenHeight = 900;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            var settingsObjects = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset");
            if (settingsObjects.Length > 0)
            {
                var settings = new SerializedObject(settingsObjects[0]);
                var activeInput = settings.FindProperty("activeInputHandler");
                if (activeInput != null && activeInput.intValue != 1)
                {
                    activeInput.intValue = 1;
                    settings.ApplyModifiedProperties();
                }
            }

            var tags = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
            var layers = tags.FindProperty("layers");
            layers.GetArrayElementAtIndex(6).stringValue = "World";
            layers.GetArrayElementAtIndex(7).stringValue = "Player";
            layers.GetArrayElementAtIndex(8).stringValue = "Enemy";
            tags.ApplyModifiedProperties();
        }

        static Material[] MakeMaterials(PaintData[] data)
        {
            var initialized = new HashSet<string>();
            var result = new Material[data.Length];
            for (int i = 0; i < data.Length; i++)
            {
                var d = data[i];
                var shader = Shader.Find(d.kind == "water" ? "Sunward/Brush River" : "Sunward/Surface Pigment");
                if (!shader)
                    throw new InvalidDataException("Sunward shaders did not import");
                var m = new Material(shader)
                {
                    name = d.name,
                    enableInstancing = true
                };
                ColorUtility.TryParseHtmlString("#" + d.color, out var c);
                c.a = d.opacity;
                m.SetColor("_BaseColor", c);
                if (d.texture >= 0)
                {
                    string path = Root + "Textures/map-" + d.texture + ".png";
                    var imp = AssetImporter.GetAtPath(path) as TextureImporter;
                    if (imp != null && initialized.Add(path))
                    {
                        imp.textureType = TextureImporterType.Default;
                        imp.textureShape = TextureImporterShape.Texture2D;
                        imp.sRGBTexture = true;
                        imp.alphaIsTransparency = d.transparent;
                        imp.wrapMode = TextureWrapMode.Repeat;
                        imp.SaveAndReimport();
                    }

                    var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                    if (!texture) throw new InvalidDataException("Expected a 2D map: " + path);
                    m.SetTexture("_BaseMap", texture);
                }

                if (d.kind != "water")
                {
                    m.SetFloat("_Cutoff", Mathf.Max(.005f, d.cutout));
                    m.SetFloat("_Pigment", d.kind == "landscape" ? .12f : .22f);
                    m.SetFloat("_Wind", d.kind == "leaves" || d.kind == "grass-blade" ? 1 : 0);
                    m.SetFloat("_Cull", d.side == 2 ? 0 : d.side == 1 ? 1 : 2);
                    if (d.transparent)
                    {
                        m.SetFloat("_SrcBlend", 5);
                        m.SetFloat("_DstBlend", 10);
                        m.SetFloat("_ZWrite", 0);
                        m.renderQueue = 3000;
                    }
                    else
                        m.renderQueue = 2000;
                }

                result[i] = SaveAsset(m, "Paint-" + i + ".mat");
            }

            return result;
        }

        static Dictionary<string, GameObject> MakePrefabs(ValleyData data, Material[] materials)
        {
            var roots = new Dictionary<string, GameObject>();
            string meshPath = Generated + "ValleyMeshes.asset";
            AssetDatabase.DeleteAsset(meshPath);
            var container = new Mesh()
            {
                name = "Valley mesh catalogue"
            };
            AssetDatabase.CreateAsset(container, meshPath);
            using (var stream = File.OpenRead(Root + "Data/Valley.bytes"))
            using (var reader = new BinaryReader(stream))
            {
                int id = 0;
                foreach (var asset in data.assets)
                {
                    if (!roots.TryGetValue(asset.name, out var root))
                    {
                        root = new GameObject(asset.name);
                        roots.Add(asset.name, root);
                    }

                    foreach (var record in asset.meshes)
                    {
                        stream.Position = record.offset;
                        int nv = reader.ReadInt32(), ni = reader.ReadInt32();
                        if (nv != record.vertices || ni != record.indices)
                            throw new InvalidDataException("Valley mesh descriptor mismatch");
                        var v = new Vector3[nv];
                        var n = new Vector3[nv];
                        var uv = new Vector2[nv];
                        var color = new Color[nv];
                        for (int i = 0; i < nv; i++)
                        {
                            v[i] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
                            n[i] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
                            uv[i] = new Vector2(reader.ReadSingle(), reader.ReadSingle());
                            color[i] = new Color(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
                        }

                        var indices = new int[ni];
                        for (int i = 0; i < ni; i++)
                            indices[i] = reader.ReadInt32();
                        var mesh = new Mesh()
                        {
                            name = "Valley-" + id++,
                            indexFormat = IndexFormat.UInt32
                        };
                        mesh.vertices = v;
                        mesh.normals = n;
                        mesh.uv = uv;
                        mesh.colors = color;
                        mesh.triangles = indices;
                        mesh.RecalculateBounds();
                        AssetDatabase.AddObjectToAsset(mesh, container);
                        var child = new GameObject(record.name + "-" + id);
                        child.transform.SetParent(root.transform, false);
                        child.AddComponent<MeshFilter>().sharedMesh = mesh;
                        var r = child.AddComponent<MeshRenderer>();
                        r.sharedMaterial = materials[record.material];
                        r.shadowCastingMode = data.materials[record.material].transparent ? ShadowCastingMode.Off : ShadowCastingMode.On;
                        r.receiveShadows = true;
                        if (asset.name == "TownV3")
                        {
                            GameObjectUtility.SetStaticEditorFlags(child, StaticEditorFlags.BatchingStatic);
                            if (record.vertices > 45000 && data.materials[record.material].kind == "landscape")
                            {
                                child.layer = 6;
                                child.AddComponent<MeshCollider>().sharedMesh = mesh;
                            }
                        }
                    }
                }
            }

            AssetDatabase.SaveAssets();
            var result = new Dictionary<string, GameObject>();
            foreach (var pair in roots)
            {
                result[pair.Key] = PrefabUtility.SaveAsPrefabAsset(pair.Value, Generated + pair.Key + ".prefab");
                UnityEngine.Object.DestroyImmediate(pair.Value);
            }

            return result;
        }

        [Serializable]
        class WolfReport
        {
            public WolfMaterial[] materials;
            public WolfMeshMaterials[] meshMaterials;
        }

        [Serializable]
        class WolfMaterial
        {
            public string name;
            public string[] images;
            public float[] color;
            public float metallic, roughness;
        }

        [Serializable]
        class WolfMeshMaterials
        {
            public string name;
            public string[] materials;
        }

        static string CleanClip(string name)
        {
            int bar = name.LastIndexOf('|');
            if (bar >= 0)
                name = name.Substring(bar + 1);
            return name.Replace("_WOLF_RIG", "");
        }

        static GameObject MakeWolf()
        {
            string path = Root + "Models/Amaterasu.fbx";
            var importer = (ModelImporter)AssetImporter.GetAtPath(path);
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            importer.importAnimation = true;
            importer.optimizeGameObjects = false;
            importer.importNormals = ModelImporterNormals.Import;
            importer.animationCompression = ModelImporterAnimationCompression.Off;
            // Material conversion is intentionally disabled. Legacy FBX conversion can bind
            // a Cube texture to _MainTex before our final material assignment runs.
            // Keep rig/mesh/animation import, then bind the original 2D maps by mesh name.
            importer.materialImportMode = ModelImporterMaterialImportMode.None;
            var clips = importer.defaultClipAnimations;
            foreach (var c in clips)
            {
                c.name = CleanClip(c.name);
                c.loopTime = c.name.StartsWith("Idle") || c.name.StartsWith("Walk") || c.name.StartsWith("Jog") || c.name.StartsWith("Sprint") || c.name == "Air_Fall" || c.name == "Sleep_Loop";
                c.lockRootRotation = true;
                c.lockRootPositionXZ = true;
                c.lockRootHeightY = false;
            }

            importer.clipAnimations = clips;
            importer.SaveAndReimport();
            var report = JsonUtility.FromJson<WolfReport>(File.ReadAllText("Review/wolf-export.json"));
            var wolfMaterials = new Dictionary<string, Material>();
            foreach (var entry in report.materials)
            {
                var m = new Material(Shader.Find("Universal Render Pipeline/Lit"))
                {
                    name = entry.name
                };
                var c = entry.color != null && entry.color.Length == 4 ? new Color(entry.color[0], entry.color[1], entry.color[2], entry.color[3]) : Color.white;
                m.SetColor("_BaseColor", c);
                m.SetFloat("_Metallic", entry.metallic);
                m.SetFloat("_Smoothness", 1 - entry.roughness);
                m.SetFloat("_Cull", 0);
                if (entry.images != null && entry.images.Length > 0)
                {
                    string image = entry.images[0].Split('.')[0];
                    string texturePath = Root + "Textures/Wolf-" + image + ".png";
                    var texImporter = AssetImporter.GetAtPath(texturePath) as TextureImporter;
                    if (texImporter != null)
                    {
                        texImporter.textureType = TextureImporterType.Default;
                        texImporter.textureShape = TextureImporterShape.Texture2D;
                        texImporter.sRGBTexture = true;
                        texImporter.textureCompression = TextureImporterCompression.Uncompressed;
                        texImporter.SaveAndReimport();
                    }

                    var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
                    if (!tex)
                        throw new InvalidDataException("Missing original wolf map: " + image);
                    m.SetTexture("_BaseMap", tex);
                }

                wolfMaterials[entry.name] = SaveAsset(m, "Wolf-" + entry.name + ".mat");
            }

            var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            var root = new GameObject("Amaterasu");
            var visual = UnityEngine.Object.Instantiate(model, root.transform);
            visual.name = "Original Amaterasu · geometry untouched";
            visual.transform.localScale = Vector3.one * .34f;
            if (report.meshMaterials == null || report.meshMaterials.Length == 0)
                throw new InvalidDataException("Missing original mesh/material bindings in Review/wolf-export.json");
            var bindings = report.meshMaterials.ToDictionary(entry => entry.name);
            var fallback = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "Original glTF default" };
            fallback.SetColor("_BaseColor", Color.white);
            fallback.SetFloat("_Metallic", 1);
            fallback.SetFloat("_Smoothness", 0);
            fallback = SaveAsset(fallback, "Wolf-OriginalDefault.mat");
            foreach (var renderer in visual.GetComponentsInChildren<Renderer>())
            {
                if (!bindings.TryGetValue(renderer.name, out var binding))
                    throw new InvalidDataException("Unmapped original wolf renderer: " + renderer.name);
                var skinned = renderer as SkinnedMeshRenderer;
                var filter = renderer.GetComponent<MeshFilter>();
                var mesh = skinned ? skinned.sharedMesh : filter ? filter.sharedMesh : null;
                int slots = mesh ? mesh.subMeshCount : 1;
                if (binding.materials == null || binding.materials.Length == 0)
                    renderer.sharedMaterials = Enumerable.Repeat(fallback, slots).ToArray();
                else
                {
                    if (binding.materials.Length != slots)
                        throw new InvalidDataException("Original wolf material-slot mismatch: " + renderer.name + " (" + binding.materials.Length + " source / " + slots + " imported)");
                    renderer.sharedMaterials = binding.materials.Select(name =>
                    {
                        if (!wolfMaterials.TryGetValue(name, out var material))
                            throw new InvalidDataException("Missing original wolf material: " + name);
                        return material;
                    }).ToArray();
                }
                renderer.shadowCastingMode = ShadowCastingMode.On;
            }

            var head = Find(root, "DEF_head");
            var chest = Find(root, "DEF_chest");
            if (head && chest)
            {
                Vector3 front = head.position - chest.position;
                front.y = 0;
                if (front.sqrMagnitude > .001f)
                    visual.transform.rotation = Quaternion.FromToRotation(front.normalized, Vector3.forward) * visual.transform.rotation;
            }

            var animator = visual.GetComponent<Animator>();
            if (!animator)
                animator = visual.AddComponent<Animator>();
            string ac = Generated + "Amaterasu.controller";
            AssetDatabase.DeleteAsset(ac);
            var controller = AnimatorController.CreateAnimatorControllerAtPath(ac);
            var sm = controller.layers[0].stateMachine;
            var actions = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).ToArray();
            var names = new HashSet<string>();
            foreach (var clip in actions)
            {
                string name = CleanClip(clip.name);
                if (!names.Add(name))
                    continue;
                clip.name = name;
                var state = sm.AddState(name);
                state.motion = clip;
                if (name == "Idle_Natural")
                    sm.defaultState = state;
            }

            foreach (string required in new[]
            {
                "Idle_Natural",
                "Walk_Natural",
                "Jog_Natural",
                "Sprint_Fluid",
                "Sleep_Down",
                "Sleep_Loop",
                "Sleep_Up",
                "Thrust",
                "Disc1"
            }

            )
                if (!names.Contains(required))
                    throw new InvalidDataException("Missing wolf animation: " + required);
            animator.runtimeAnimatorController = controller;
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            var result = PrefabUtility.SaveAsPrefabAsset(root, Generated + "Amaterasu.prefab");
            UnityEngine.Object.DestroyImmediate(root);
            return result;
        }

        static Transform Find(GameObject root, string name) => root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name || t.name == name.Replace(".", ""));
        static Transform Socket(GameObject root, string name, Transform bone, Vector3 localWorldPoint)
        {
            if (!bone)
                throw new InvalidDataException("Missing attachment bone: " + name);
            var socket = new GameObject(name).transform;
            socket.SetParent(bone, false);
            socket.position = root.transform.TransformPoint(localWorldPoint);
            socket.rotation = root.transform.rotation;
            socket.localScale = Vector3.one / .34f;
            return socket;
        }

        static Strike Strike(string name, float duration, float damage, float range, float arc, float lunge = 2) => new Strike()
        {
            clip = name,
            duration = duration,
            damage = damage,
            range = range,
            arc = arc,
            lunge = lunge,
            start = .32f,
            end = .62f,
            stagger = .45f
        };
        static WeaponDefinition Weapon(string id, GameObject model)
        {
            var w = ScriptableObject.CreateInstance<WeaponDefinition>();
            w.id = id;
            w.title = id == "spear" ? "Reed spear" : "Sundial Flame";
            w.visual = model;
            if (id == "spear")
            {
                w.light = new[]
                {
                    Strike("Thrust", .40f, 1, 3.3f, .8f, 3.2f),
                    Strike("Sweep", .48f, 2, 3.15f, .32f, 1.3f),
                    Strike("Finish", .66f, 3, 3.8f, .82f, 8.5f)
                };
                w.heavy = new[]
                {
                    Strike("HeavyArc", .66f, 3.3f, 3.5f, .2f),
                    Strike("HeavyReturn", .72f, 4, 3.8f, .2f)
                };
                w.charged = Strike("ChargedThrust", .65f, 4.5f, 4, .8f, 5);
                w.chargedHeavy = Strike("ChargedHeavy", .9f, 6, 4, .1f, 4);
            }
            else
            {
                w.light = new[]
                {
                    Strike("Disc1", .36f, 1.4f, 2.65f, -1, 1.5f),
                    Strike("Disc2", .48f, 2.1f, 2.9f, -1, 2),
                    Strike("Disc3", .66f, 3.8f, 3.35f, -1, 2.4f)
                };
                w.heavy = new[]
                {
                    Strike("DiscHeavy", .65f, 4, 3.2f, -1),
                    Strike("DiscHeavy", .75f, 4.5f, 3.5f, -1)
                };
                w.charged = Strike("DiscCharged", .8f, 5, 3.8f, -1);
                w.chargedHeavy = Strike("DiscCharged", 1, 6, 4.2f, -1);
            }

            w.air = Strike("AirStrike", .72f, 4.5f, 3.8f, -1, 1);
            return SaveAsset(w, id + ".asset");
        }

        static EnemyDefinition[] EnemyDefinitions(Dictionary<string, GameObject> models)
        {
            string[] ids =
            {
                "wisp",
                "reed",
                "heavy",
                "ranged",
                "elite",
                "boss"
            }, titles =
            {
                "Ashwing",
                "Reed sentinel",
                "Stonejaw",
                "Paper kite",
                "Crimson oathkeeper",
                "KUROGANE · THE HOLLOW BELL"
            };
            float[] hp =
            {
                7,
                11,
                27,
                12,
                32,
                145
            }, damage =
            {
                9,
                13,
                23,
                12,
                21,
                28
            }, speed =
            {
                3.5f,
                2.2f,
                1.4f,
                1.9f,
                2.8f,
                1.65f
            }, scale =
            {
                .76f,
                1,
                1.65f,
                1,
                1.25f,
                2.75f
            }, windup =
            {
                .42f,
                .67f,
                1.08f,
                .9f,
                .48f,
                1.1f
            };
            int[] reward =
            {
                8,
                10,
                18,
                13,
                23,
                45
            }, xp =
            {
                8,
                11,
                17,
                14,
                23,
                55
            };
            var list = new List<EnemyDefinition>();
            for (int i = 0; i < ids.Length; i++)
            {
                var d = ScriptableObject.CreateInstance<EnemyDefinition>();
                d.id = ids[i];
                d.title = titles[i];
                d.hp = hp[i];
                d.damage = damage[i];
                d.speed = speed[i];
                d.scale = scale[i];
                d.windup = windup[i];
                d.reward = reward[i];
                d.xp = xp[i];
                d.visual = models["Enemy-" + ids[i]];
                list.Add(SaveAsset(d, "Spirit-" + ids[i] + ".asset"));
            }

            return list.ToArray();
        }

        static void Collisions(WorldData w, GameObject town)
        {
            var root = new GameObject("V3 · physical walls and river crossings");
            root.transform.SetParent(town.transform, false);
            foreach (var b in w.boxes)
            {
                var go = new GameObject("Building / rail collider");
                go.layer = 6;
                go.transform.SetParent(root.transform, false);
                go.transform.position = new Vector3(b.x, 1.6f, -b.z);
                var col = go.AddComponent<BoxCollider>();
                col.size = new Vector3(b.halfX * 2, 3.2f, b.halfZ * 2);
            }

            foreach (var o in w.obstacles)
            {
                var go = new GameObject("Trunk / rock collider");
                go.layer = 6;
                go.transform.SetParent(root.transform, false);
                go.transform.position = new Vector3(o.x, .5f, -o.z);
                var c = go.AddComponent<CapsuleCollider>();
                c.radius = o.r;
                c.height = 1.0f;
            }

            foreach (float z in new[]
            {
                12f,
                -14f
            }

            )
            {
                var v = new Vector3[50];
                var ix = new int[24 * 6];
                for (int i = 0; i <= 24; i++)
                {
                    float x = -27.8f + i * .4f, h = Valley.BridgeHeight(i / 24f);
                    v[i * 2] = new Vector3(x, h, -z - 1.26f);
                    v[i * 2 + 1] = new Vector3(x, h, -z + 1.26f);
                    if (i < 24)
                    {
                        int k = i * 2, n = i * 6;
                        ix[n] = k;
                        ix[n + 1] = k + 1;
                        ix[n + 2] = k + 2;
                        ix[n + 3] = k + 1;
                        ix[n + 4] = k + 3;
                        ix[n + 5] = k + 2;
                    }
                }

                for (int vertex = 0; vertex < v.Length; vertex++)
                    if (float.IsNaN(v[vertex].y) || float.IsInfinity(v[vertex].y))
                        throw new InvalidDataException("Non-finite bridge collision height at vertex " + vertex);
                var mesh = new Mesh()
                {
                    name = "Arched bridge collision · " + z,
                    vertices = v,
                    triangles = ix
                };
                mesh.RecalculateNormals();
                var go = new GameObject("Arched bridge collision");
                go.layer = 6;
                go.transform.SetParent(root.transform, false);
                go.AddComponent<MeshCollider>().sharedMesh = mesh;
            }
        }

        static Material Energy(string name, Color color, bool barrier)
        {
            var mat = new Material(Shader.Find("Sunward/Calligraphic Energy"))
            {
                name = name
            };
            mat.SetColor("_BaseColor", color);
            mat.SetFloat("_Barrier", barrier ? 1 : 0);
            return SaveAsset(mat, name + ".mat");
        }

        [MenuItem("Sunward/Build Windows x64")]
        public static void BuildWindows()
        {
            if (!File.Exists(ScenePath))
                Build();
            string path = "Builds/Windows/Sunward.exe";
            Directory.CreateDirectory("Builds/Windows");
            var report = BuildPipeline.BuildPlayer(new[] { ScenePath }, path, BuildTarget.StandaloneWindows64, BuildOptions.None);
            if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
                throw new Exception("Windows build failed. Check the Console and installed Windows Build Support module.");
            Debug.Log("Windows build: " + Path.GetFullPath(path));
        }
    }
}
