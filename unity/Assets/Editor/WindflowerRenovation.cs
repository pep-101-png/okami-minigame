using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class WindflowerRenovation
    {
        const string Folder = "Assets/Sunward/Generated/Renovation/";
        public const string RootName = "Windflower · village renovation";
        static int serial;
        static readonly Dictionary<string, Mesh> latheCache = new Dictionary<string, Mesh>();
        static GameFlow flow;
        static WorldData world;
        static Transform root;
        static Material wood, stone, paper, indigo, vermilion, brass, green, fruit, glass;
        static Dictionary<string, string> sourceKinds;
        static T Save<T>(T asset, string name)
            where T : UnityEngine.Object
        {
            string path = Folder + name;
            asset.name = Path.GetFileNameWithoutExtension(name);
            var old = AssetDatabase.LoadAssetAtPath<T>(path);
            if (old)
            {
                EditorUtility.CopySerialized(asset, old);
                UnityEngine.Object.DestroyImmediate(asset);
                EditorUtility.SetDirty(old);
                return old;
            }

            AssetDatabase.CreateAsset(asset, path);
            return asset;
        }

        static Material Paint(string name, Color color, string family = null, bool emissive = false)
        {
            var m = new Material(Shader.Find(emissive ? "Universal Render Pipeline/Lit" : "Sunward/Surface Pigment"));
            m.SetColor("_BaseColor", color);
            m.enableInstancing = true;
            if (family != null)
                WindflowerArt.Apply(m, new PaintData { kind = family, texture = -1 });
            if (emissive)
            {
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", color * .55f);
            }

            return Save(m, name + ".mat");
        }

        static Transform Group(string name, Vector3 p, Transform parent = null)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent ? parent : root, false);
            t.localPosition = p;
            return t;
        }

        static GameObject Box(string name, Vector3 p, Vector3 size, Material mat, Transform parent = null, bool solid = false)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent ? parent : root, false);
            go.transform.localPosition = p;
            go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            if (solid)
            {
                go.layer = 6;
                go.AddComponent<VillageWorldSolid>();
            }
            else
                UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
            return go;
        }

        static Mesh LatheMesh(Vector2[] profile, int sides = 32)
        {
            RevolvedGeometry.Build(profile, sides, out var v, out var uv, out var tri);
            var mesh = new Mesh
            {
                vertices = v,
                uv = uv,
                triangles = tri,
                colors = Enumerable.Repeat(Color.white, v.Length).ToArray()
            };
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        static GameObject MeshObject(string name, Mesh mesh, Vector3 p, Material mat, Transform parent = null)
        {
            MeshSafety.Validate(name, mesh.vertices, mesh.triangles);
            if (!AssetDatabase.Contains(mesh))
                mesh = Save(mesh, "Detail-" + (serial++) + ".asset");
            var go = new GameObject(name);
            go.transform.SetParent(parent ? parent : root, false);
            go.transform.localPosition = p;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = mat;
            return go;
        }

        static GameObject Lathe(string name, Vector3 p, Vector2[] profile, Material mat, Transform parent = null)
        {
            string key = string.Join(";", profile.Select(v => v.x.ToString("R", System.Globalization.CultureInfo.InvariantCulture) + "," + v.y.ToString("R", System.Globalization.CultureInfo.InvariantCulture)));
            if (!latheCache.TryGetValue(key, out var mesh))
                mesh = LatheMesh(profile);
            var go = MeshObject(name, mesh, p, mat, parent);
            latheCache[key] = go.GetComponent<MeshFilter>().sharedMesh;
            return go;
        }

        static GameObject Cylinder(string name, Vector3 p, float radius, float height, Material mat, Transform parent = null) => Lathe(name, p, new[] { new Vector2(0, -height / 2), new Vector2(radius, -height / 2), new Vector2(radius, height / 2), new Vector2(0, height / 2) }, mat, parent);
        static void Beam(string name, Vector3 a, Vector3 b, float radius, Material mat, Transform parent = null)
        {
            var go = Cylinder(name, (a + b) * .5f, radius, Vector3.Distance(a, b), mat, parent);
            go.transform.localRotation = Quaternion.FromToRotation(Vector3.up, (b - a).normalized);
        }

        static float Height(float x, float z) => Valley.SurfaceHeight(world.terrain, new Vector3(x, 0, z));
        static void Ring(string name, Vector3 center, float radius, float thickness, Material mat, Transform parent = null)
        {
            var p = new Vector2[13];
            for (int i = 0; i <= 12; i++)
            {
                float a = i / 12f * Mathf.PI * 2;
                p[i] = new Vector2(radius + Mathf.Cos(a) * thickness, Mathf.Sin(a) * thickness);
            }

            var go = Lathe(name, center, p, mat, parent);
            go.transform.localRotation = Quaternion.Euler(90, 0, 0);
        }

        static void WarmLight(Vector3 p, float intensity, float range)
        {
            var light = Group("Warm paper glow", p).gameObject.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = new Color(1, .72f, .38f);
            light.intensity = intensity;
            light.range = range;
            light.shadows = LightShadows.None;
        }

        public static void Apply(GameFlow game, GameObject town, ValleyData data)
        {
            Directory.CreateDirectory(Folder);
            AssetDatabase.Refresh();
            flow = game;
            world = data.world;
            serial = 0;
            latheCache.Clear();
            var old = town.transform.Find(RootName);
            if (old)
            {
                // These are persistent gameplay references, not disposable decoration.
                foreach (var slot in game.Shelf.slots)
                    if (slot && slot.IsChildOf(old))
                        slot.SetParent(town.transform, true);
                UnityEngine.Object.DestroyImmediate(old.gameObject);
            }

            root = new GameObject(RootName).transform;
            root.SetParent(town.transform, false);
            wood = Paint("Joinery", new Color(.64f, .43f, .27f), "wood");
            stone = Paint("Weathered stone", new Color(.77f, .80f, .72f), "stone");
            paper = Paint("Warm rice paper", new Color(.94f, .85f, .66f));
            indigo = Paint("Indigo cloth", new Color(.30f, .43f, .53f));
            vermilion = Paint("Vermilion cloth", new Color(.66f, .30f, .23f));
            brass = Paint("Aged bronze", new Color(.59f, .52f, .30f));
            green = Paint("Celadon pottery", new Color(.48f, .67f, .59f));
            fruit = Paint("Harvest persimmons", new Color(.91f, .49f, .18f));
            glass = Paint("Mirror jade", new Color(.40f, .72f, .69f), null, true);
            sourceKinds = new Dictionary<string, string>();
            int sourceID = 0;
            foreach (var a in data.assets)
                foreach (var m in a.meshes)
                    sourceKinds["Valley-" + (sourceID++)] = data.materials[m.material].kind;
            ReplaceLegacy(town, data);
            Home(town);
            Mill();
            Decorations();
            Market();
            GroundAccents();
            Lanterns();
            Wind(town, data);
            Residents();
            foreach (var renderer in root.GetComponentsInChildren<MeshRenderer>())
                if (!renderer.GetComponentInParent<WaterMillMotion>() && !renderer.GetComponentInParent<HangingWind>())
                    GameObjectUtility.SetStaticEditorFlags(renderer.gameObject, StaticEditorFlags.BatchingStatic);
            game.Player.GetComponent<CharacterController>().skinWidth = .025f;
            if (!game.Player.GetComponent<WolfBodyCollision>())
                game.Player.gameObject.AddComponent<WolfBodyCollision>();
            var camera = Camera.main;
            if (camera)
                camera.nearClipPlane = .08f;
            AssetDatabase.SaveAssets();
            Debug.Log("Village renovation connected to Windflower: new home zones, skinned resident rigs, river mill, supported ornaments, closed lantern roofs, market merchandise/audio and tree wind. Native visual/physics checks still required.");
        }

        static void ReplaceLegacy(GameObject town, ValleyData data)
        {
            var filters = town.GetComponentsInChildren<MeshFilter>(true).Where(f => f.sharedMesh && f.sharedMesh.name.StartsWith("Valley-")).ToDictionary(f => f.sharedMesh.name);
            int id = 0;
            foreach (var asset in data.assets)
            {
                var ids = new List<int>();
                foreach (var record in asset.meshes)
                    ids.Add(id++);
                if (asset.name != "TownV3")
                    continue;
                foreach (int n in ids)
                {
                    if (!filters.TryGetValue("Valley-" + n, out var filter))
                        throw new InvalidDataException("Missing live Windflower mesh Valley-" + n);
                    // IDs identify the frozen V3 export; reject a mismatched scene/catalog.
                    if (n == 343 && Mathf.Abs(filter.GetComponent<Renderer>().bounds.center.x + 12.45f) > .1f)
                        throw new InvalidDataException("Old wheel provenance does not match V3; no replacement applied.");
                    if (n == 892 && Mathf.Abs(filter.sharedMesh.bounds.size.x - 28) > .1f)
                        throw new InvalidDataException("Old festival rope provenance does not match V3.");
                    int materialID = asset.meshes[ids.IndexOf(n)].material;
                    bool banner = materialID == 106 || materialID == 107;
                    if ((n >= 343 && n <= 347) || n == 892 || (n >= 893 && n <= 906))
                        filter.GetComponent<Renderer>().enabled = false;
                    if (n >= 600 && n <= 632 || n >= 348 && n <= 390 || n >= 484 && n <= 599 || banner)
                    {
                        var mesh = filter.sharedMesh;
                        var v = mesh.vertices;
                        var ix = mesh.triangles;
                        var keep = new List<int>();
                        var material = filter.GetComponent<Renderer>().sharedMaterial;
                        for (int t = 0; t < ix.Length; t += 3)
                        {
                            bool home = true, beam = true, stall = true, flags = banner;
                            for (int k = 0; k < 3; k++)
                            {
                                var p = filter.transform.TransformPoint(v[ix[t + k]]);
                                home &= p.x > -38.8f && p.x < -29.2f && p.z > -19.8f && p.z < -12.2f && p.y > .13f && p.y < 2.7f;
                                beam &= p.x > -20.6f && p.x < -12.7f && Mathf.Abs(p.z - 5) < .38f && p.y > -.5f && p.y < 1.5f;
                                stall &= Mathf.Abs(Mathf.Abs(p.x) - 4.8f) < 1.55f && Mathf.Abs(p.z) < 1.15f && p.y > .06f && p.y < 3.2f;
                                flags &= p.x > -32 && p.x < -2 && Mathf.Abs(p.z + 7) < .5f && p.y > 2.3f;
                            }

                            if (!home && !beam && !stall && !flags)
                            {
                                keep.Add(ix[t]);
                                keep.Add(ix[t + 1]);
                                keep.Add(ix[t + 2]);
                            }
                        }

                        if (keep.Count != ix.Length)
                        {
                            mesh.triangles = keep.ToArray();
                            mesh.RecalculateBounds();
                            EditorUtility.SetDirty(mesh);
                        }
                    }
                }
            }

            foreach (var collider in town.GetComponentsInChildren<CapsuleCollider>(true))
                if (collider.name == "Trunk / rock collider" && Mathf.Abs(collider.transform.position.x + 12.45f) < .05f && Mathf.Abs(collider.transform.position.z - 5) < .05f)
                    collider.enabled = false;
            // The obsolete aqueduct collider no longer matches the redesigned mill.
            foreach (var col in town.GetComponentsInChildren<BoxCollider>(true))
                if (col.name == "Building / rail collider" && Mathf.Abs(col.transform.position.x + 16.7f) < .1f && Mathf.Abs(col.transform.position.z - 5) < .1f)
                    col.enabled = false;
        }

        static void Home(GameObject town)
        {
            var existing = town.GetComponent<HomeWeaponRack>();
            if (existing)
            {
                if (existing.displays)
                    UnityEngine.Object.DestroyImmediate(existing.displays);
                UnityEngine.Object.DestroyImmediate(existing);
            }

            var home = Group("Home · sleeping west / mirror east / open centre", Vector3.zero);
            var tatami = Paint("Woven tatami", new Color(.73f, .70f, .48f), "plaster");
            for (int x = 0; x < 3; x++)
                for (int z = 0; z < 3; z++)
                    Box("Bound tatami", new Vector3(-36.5f + x * 2.1f, .10f, -18.7f + z * 1.9f), new Vector3(2.03f, .035f, 1.83f), tatami, home);
            var bed = Box("Low futon · sleep zone", HomeLayout.Bed + Vector3.down * .035f, new Vector3(3.4f, .10f, 1.65f), vermilion, home, true);
            Box("Futon pillow", HomeLayout.Bed + new Vector3(-1.05f, .07f, 0), new Vector3(.62f, .12f, 1.12f), paper, home);
            // East-wall memory mirror faces into the room; nothing shares its footprint.
            var mirror = Group("Accessible memory mirror", HomeLayout.Mirror, home);
            mirror.localRotation = Quaternion.Euler(0, -90, 0);
            Ring("Carved bronze mirror rim", new Vector3(0, 1.3f, 0), .54f, .055f, brass, mirror);
            var disk = Cylinder("Solid polished jade mirror", new Vector3(0, 1.3f, .015f), .50f, .025f, glass, mirror);
            disk.transform.localRotation = Quaternion.Euler(90, 0, 0);
            for (int s = -1; s <= 1; s += 2)
                Box("Mirror stand", new Vector3(s * .36f, .48f, .06f), new Vector3(.10f, .94f, .12f), wood, mirror);
            Box("Mirror foot", new Vector3(0, .05f, .08f), new Vector3(1.05f, .1f, .48f), wood, mirror);
            var rack = Group("Home · separate wall-mounted weapon displays", Vector3.zero, home);
            Box("Spear lacquer backing", new Vector3(-38.65f, 1.60f, -15.9f), new Vector3(.12f, .62f, 3.1f), wood, rack);
            for (int i = 0; i < 2; i++)
                Box("Spear padded hook", new Vector3(-38.39f, 1.50f, -16.9f + i * 2), new Vector3(.45f, .09f, .12f), brass, rack);
            PlaceWeapon(flow.Combat.spear.visual, rack, new Vector3(-38.30f, 1.60f, -15.9f), Vector3.forward, 2.9f, false);
            Box("Disc lacquer backing", new Vector3(-38.65f, 1.65f, -18.45f), new Vector3(.12f, 1.50f, 1.4f), wood, rack);
            Box("Disc support", new Vector3(-38.4f, 1.0f, -18.45f), new Vector3(.4f, .09f, .55f), brass, rack);
            PlaceWeapon(flow.Combat.sundial.visual, rack, new Vector3(-38.25f, 1.65f, -18.45f), Vector3.right, 1.25f, true);
            Box("Weapon storage collision", new Vector3(-38.48f, 1.05f, -17.1f), new Vector3(.48f, 2.1f, 4.9f), wood, home, true).GetComponent<Renderer>().enabled = false;
            Box("Mirror stand collision", HomeLayout.Mirror + Vector3.up * .75f, new Vector3(.40f, 1.5f, 1.15f), wood, home, true).GetComponent<Renderer>().enabled = false;
            var equipment = town.AddComponent<HomeWeaponRack>();
            equipment.game = flow;
            equipment.displays = rack.gameObject;
            var shelf = Group("East-wall collectible alcove", new Vector3(-29.7f, .13f, -17.8f), home);
            Box("Shelf back", new Vector3(.2f, .9f, 0), new Vector3(.08f, 1.8f, 2.75f), wood, shelf);
            for (int row = 0; row < 3; row++)
                Box("Display shelf", new Vector3(0, .35f + row * .62f, 0), new Vector3(.65f, .07f, 2.75f), wood, shelf);
            for (int end = -1; end <= 1; end += 2)
                Box("Shelf upright", new Vector3(0, .9f, end * 1.37f), new Vector3(.65f, 1.8f, .07f), wood, shelf);
            for (int i = 0; i < 6; i++)
            {
                var slot = flow.Shelf.slots[i];
                slot.SetParent(shelf, false);
                slot.localPosition = new Vector3(-.1f, .40f + (i / 3) * .62f, -.9f + (i % 3) * .9f);
            }

            WarmLight(new Vector3(-30.8f, 2.1f, -14.2f), .8f, 4);
            WarmLight(new Vector3(-36.6f, 2.4f, -14.2f), .7f, 4);
            // Furniture collisions stay away from the entry and central two-metre aisle.
            Box("Shelf collision", new Vector3(-29.65f, .85f, -17.8f), new Vector3(.65f, 1.6f, 2.75f), wood, home, true).GetComponent<Renderer>().enabled = false;
        }

        static void PlaceWeapon(GameObject prefab, Transform parent, Vector3 center, Vector3 axis, float size, bool flat)
        {
            var go = UnityEngine.Object.Instantiate(prefab, parent);
            go.name = flat ? "Sundial · dedicated wall cradle" : "Spear · dedicated wall hooks";
            go.transform.localPosition = Vector3.zero;
            go.transform.localRotation = Quaternion.identity;
            go.transform.localScale = Vector3.one;
            Bounds bounds = new Bounds();
            bool first = true;
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                if (first)
                {
                    bounds = r.bounds;
                    first = false;
                }
                else
                    bounds.Encapsulate(r.bounds);
            }

            Vector3 s = bounds.size;
            Vector3 source = flat ? (s.x < s.y && s.x < s.z ? Vector3.right : s.y < s.z ? Vector3.up : Vector3.forward) : (s.x > s.y && s.x > s.z ? Vector3.right : s.y > s.z ? Vector3.up : Vector3.forward);
            go.transform.rotation = Quaternion.FromToRotation(source, axis);
            go.transform.localScale = Vector3.one * (size / Mathf.Max(.001f, Mathf.Max(s.x, Mathf.Max(s.y, s.z))));
            first = true;
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                if (first)
                {
                    bounds = r.bounds;
                    first = false;
                }
                else
                    bounds.Encapsulate(r.bounds);
            }

            go.transform.position += center - bounds.center;
            foreach (var c in go.GetComponentsInChildren<Collider>())
                UnityEngine.Object.DestroyImmediate(c);
        }

        static void Mill()
        {
            float z = 5, x = Valley.RiverX(-z) + 1.35f; // East side of the real curved river, paddles enter its surface.
            var mill = Group("River-driven rice mill · supported short transmission", new Vector3(x, 1.14f, z));
            var wheel = Group("Bucket wheel · X axle", Vector3.zero, mill);
            for (int side = -1; side <= 1; side += 2)
            {
                var ring = Group("Joined wheel rim", new Vector3(side * .30f, 0, 0), wheel);
                ring.localRotation = Quaternion.Euler(0, 0, 90);
                Lathe("Oak outer rim", Vector3.zero, new[] { new Vector2(1.43f, -.07f), new Vector2(1.58f, -.07f), new Vector2(1.58f, .07f), new Vector2(1.43f, .07f), new Vector2(1.43f, -.07f) }, wood, ring);
                for (int i = 0; i < 8; i++)
                {
                    float a = i * Mathf.PI / 4;
                    Beam("Radial mortised spoke", new Vector3(side * .30f, 0, 0), new Vector3(side * .30f, Mathf.Cos(a) * 1.47f, Mathf.Sin(a) * 1.47f), .055f, wood, wheel);
                }
            }

            for (int i = 0; i < 16; i++)
            {
                float a = i * Mathf.PI * 2 / 16;
                var paddle = Box("Water-catching paddle", new Vector3(0, Mathf.Cos(a) * 1.47f, Mathf.Sin(a) * 1.47f), new Vector3(.76f, .10f, .34f), wood, wheel);
                paddle.transform.localRotation = Quaternion.Euler(a * Mathf.Rad2Deg, 0, 0);
            }

            var shaft = Group("Axle · supported at both bearings", new Vector3(.95f, 0, 0), mill);
            Cylinder("Octagonal drive axle", Vector3.zero, .11f, 2.7f, wood, shaft);
            for (int k = 0; k < 2; k++)
            {
                float bx = k == 0 ? .65f : 2.35f;
                for (int s = -1; s <= 1; s += 2)
                    Beam("Braced bearing trestle", new Vector3(bx, Height(x + bx, z + s * .55f) - 1.14f - .12f, s * .55f), new Vector3(bx, -.05f, 0), .10f, wood, mill);
                Box("Bearing block", new Vector3(bx, -.03f, 0), new Vector3(.28f, .38f, .43f), stone, mill);
            }

            var gear = Group("Crown driving pegs", new Vector3(2.40f, 0, 0), mill);
            var disc = Cylinder("Drive gear plate", Vector3.zero, .43f, .10f, wood, gear);
            disc.transform.localRotation = Quaternion.Euler(0, 0, 90);
            for (int i = 0; i < 12; i++)
            {
                float a = i * Mathf.PI / 6;
                Box("Crown gear peg", new Vector3(.14f, Mathf.Cos(a) * .36f, Mathf.Sin(a) * .36f), new Vector3(.25f, .09f, .09f), wood, gear);
            }

            var spindle = Group("Vertical driven gear", new Vector3(2.90f, -.25f, 0), mill);
            Cylinder("Driven gear", Vector3.zero, .43f, .10f, wood, spindle);
            for (int i = 0; i < 12; i++)
            {
                float a = i * Mathf.PI / 6;
                var tooth = Box("Driven tooth", new Vector3(Mathf.Cos(a) * .39f, 0, Mathf.Sin(a) * .39f), new Vector3(.10f, .22f, .10f), wood, spindle);
            }

            Cylinder("Vertical spindle", new Vector3(0, .43f, 0), .07f, .95f, wood, spindle);
            var grind = Group("Rotating upper millstone", new Vector3(2.9f, .2f, 0), mill);
            Cylinder("Upper stone", Vector3.zero, .62f, .15f, stone, grind);
            Cylinder("Fixed lower millstone", new Vector3(2.9f, .03f, 0), .65f, .16f, stone, mill);
            float baseY = Height(x + 2.9f, z) - 1.14f;
            Box("Mill mechanism collision", new Vector3(2.9f, baseY + .78f, 0), new Vector3(1.4f, 1.55f, 1.4f), wood, mill, true).GetComponent<Renderer>().enabled = false;
            Box("Mill annex deck", new Vector3(2.9f, baseY + .08f, 0), new Vector3(2.5f, .16f, 2.9f), wood, mill);
            for (int sx = -1; sx <= 1; sx += 2)
                for (int sz = -1; sz <= 1; sz += 2)
                    Box("Annex roof post", new Vector3(2.9f + sx * 1.12f, baseY + 1.25f, sz * 1.3f), new Vector3(.14f, 2.5f, .14f), wood, mill);
            Canopy("River-mill shelter", new Vector3(2.9f, baseY + 2.55f, 0), 3.0f, 3.3f, indigo, mill);
            var motion = mill.gameObject.AddComponent<WaterMillMotion>();
            motion.game = flow;
            motion.wheel = wheel;
            motion.shaft = shaft;
            motion.pinion = gear;
            motion.spindle = spindle;
            motion.millstone = grind;
            var spray = Group("Paddle spray", new Vector3(x, -.30f, z)).gameObject.AddComponent<ParticleSystem>();
            var main = spray.main;
            main.startLifetime = .45f;
            main.startSpeed = .7f;
            main.startSize = .035f;
            main.maxParticles = 28;
            main.startColor = new Color(.80f, .92f, .87f, .6f);
            main.gravityModifier = .6f;
            var emission = spray.emission;
            emission.rateOverTime = 18;
            var shape = spray.shape;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 28;
            shape.radius = .22f;
            var particleMat = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            particleMat.SetColor("_BaseColor", new Color(.84f, .94f, .9f, .6f));
            var dab = new Texture2D(32, 32, TextureFormat.RGBA32, false, true);
            dab.wrapMode = TextureWrapMode.Clamp;
            var pixels = new Color[1024];
            for (int py = 0; py < 32; py++)
                for (int px = 0; px < 32; px++)
                {
                    float dx = (px - 15.5f) / 15.5f, dy = (py - 15.5f) / 15.5f;
                    pixels[py * 32 + px] = new Color(1, 1, 1, Mathf.Clamp01(1 - dx * dx - dy * dy) * .8f);
                }

            dab.SetPixels(pixels);
            dab.Apply();
            particleMat.SetTexture("_BaseMap", Save(dab, "SprayDab.asset"));
            particleMat.SetFloat("_Surface", 1);
            particleMat.SetFloat("_SrcBlend", 5);
            particleMat.SetFloat("_DstBlend", 10);
            particleMat.SetFloat("_ZWrite", 0);
            particleMat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            particleMat.renderQueue = 3000;
            spray.transform.rotation = Quaternion.Euler(-65, 0, 0);
            spray.GetComponent<ParticleSystemRenderer>().sharedMaterial = Save(particleMat, "MillSpray.mat");
            motion.spray = spray;
        }

        static void Canopy(string name, Vector3 p, float width, float depth, Material mat, Transform parent = null)
        {
            const int W = 20, D = 10;
            var v = new Vector3[(W + 1) * (D + 1)];
            var uv = new Vector2[v.Length];
            var ix = new List<int>();
            for (int j = 0; j <= D; j++)
                for (int i = 0; i <= W; i++)
                {
                    float u = i / (float)W, t = j / (float)D;
                    int k = j * (W + 1) + i;
                    v[k] = new Vector3((u - .5f) * width, Mathf.Sin(t * Mathf.PI) * .26f - Mathf.Sin(u * Mathf.PI) * .08f, (t - .5f) * depth);
                    uv[k] = new Vector2(u, t);
                    if (i < W && j < D)
                        ix.AddRange(new[] { k, k + W + 1, k + 1, k + 1, k + W + 1, k + W + 2 });
                }

            // Solid thickness: duplicate reversed underside, plus stitched edges.
            int count = v.Length;
            var verts = v.Concat(v.Select(a => a - Vector3.up * .035f)).ToArray();
            var tex = uv.Concat(uv).ToArray();
            var tris = new List<int>(ix);
            for (int i = 0; i < ix.Count; i += 3)
                tris.AddRange(new[] { ix[i + 2] + count, ix[i + 1] + count, ix[i] + count });
            for (int j = 0; j <= D; j++)
                for (int i = 0; i <= W; i++)
                {
                    int a = j * (W + 1) + i;
                    if (j == 0 && i < W)
                        Edge(a, a + 1);
                    if (j == D && i < W)
                        Edge(a + 1, a);
                    if (i == 0 && j < D)
                        Edge(a + W + 1, a);
                    if (i == W && j < D)
                        Edge(a, a + W + 1);
                }

            void Edge(int a, int b)
            {
                tris.AddRange(new[] { a, b, a + count, b, b + count, a + count });
            }

            var mesh = new Mesh
            {
                vertices = verts,
                uv = tex,
                triangles = tris.ToArray(),
                colors = Enumerable.Repeat(Color.white, verts.Length).ToArray()
            };
            mesh.RecalculateNormals();
            MeshObject(name, mesh, p, mat, parent);
        }

        static void Decorations()
        {
            var line = Group("Market · supported festival line", Vector3.zero);
            Vector3 a = new Vector3(-7, Height(-7, -2.3f) + 3.45f, -2.3f), b = new Vector3(7, Height(7, -2.3f) + 3.45f, -2.3f);
            foreach (var p in new[]
            {
                a,
                b
            }

            )
            {
                Beam("Festival cedar support", new Vector3(p.x, Height(p.x, p.z) - .12f, p.z), p + Vector3.up * .14f, .095f, wood, line);
                Beam("Post knee brace", p - Vector3.up * .7f, p + Vector3.right * (p.x < 0 ? .45f : -.45f), .04f, wood, line);
            }

            Vector3 Point(float t) => Vector3.Lerp(a, b, t) - Vector3.up * (Mathf.Sin(t * Mathf.PI) * .43f);
            for (int i = 0; i < 40; i++)
                Beam("Sagging tied rope", Point(i / 40f), Point((i + 1) / 40f), .018f, wood, line);
            for (int i = 0; i < 9; i++)
            {
                float u = (i + 1) / 10f;
                var anchor = Group("Tied ornament anchor", Point(u), line);
                var sway = anchor.gameObject.AddComponent<HangingWind>();
                sway.phase = i * 1.7f;
                sway.amplitude = 1.7f;
                Beam("Tied pendant cord", Vector3.zero, Vector3.down * .22f, .008f, wood, anchor);
                if (i % 2 == 0)
                    PaperLantern(new Vector3(0, -.45f, 0), anchor);
                else
                    Box("Folded festival paper", new Vector3(0, -.38f, 0), new Vector3(.16f, .31f, .015f), paper, anchor);
            }
        }

        static void PaperLantern(Vector3 p, Transform parent)
        {
            Lathe("Ribbed paper lantern", p, new[] { new Vector2(0, -.26f), new Vector2(.10f, -.26f), new Vector2(.19f, -.19f), new Vector2(.23f, 0), new Vector2(.19f, .19f), new Vector2(.10f, .26f), new Vector2(0, .26f) }, paper, parent);
            for (int i = 0; i < 7; i++)
            {
                float y = -.23f + i * .076f, r = .12f + .10f * Mathf.Sin(i / 6f * Mathf.PI);
                var ring = Group("Bamboo lantern rib", p + Vector3.up * y, parent);
                ring.localRotation = Quaternion.Euler(90, 0, 0);
                Ring("Binding", Vector3.zero, r, .005f, wood, ring);
            }
        }

        static void Market()
        {
            var market = Group("Market · crafted stalls and arranged goods", Vector3.zero);
            for (int stall = 0; stall < 2; stall++)
            {
                float x = stall == 0 ? -4.8f : 4.8f;
                var s = Group(stall == 0 ? "Hana · produce and flowers" : "Taro · tea and pottery", new Vector3(x, Height(x, 0), 0), market);
                Box("Stall counter", new Vector3(0, .42f, 0), new Vector3(2.5f, .78f, 1.3f), wood, s, true);
                for (int i = 0; i < 6; i++)
                    Box("Joined counter planks", new Vector3(-1.05f + i * .42f, .84f, 0), new Vector3(.40f, .07f, 1.45f), wood, s);
                foreach (float sx in new[]
                {
                    -1.26f,
                    1.26f
                }

                )
                {
                    Box("Canopy upright", new Vector3(sx, 1.14f, .54f), new Vector3(.12f, 2.28f, .12f), wood, s);
                    Beam("Canopy brace", new Vector3(sx, 1.65f, .54f), new Vector3(sx * .65f, 2.18f, .54f), .035f, wood, s);
                }

                Canopy("Layered painted cloth canopy", new Vector3(0, 2.28f, 0), 3, 2.1f, stall == 0 ? vermilion : indigo, s);
                for (int i = 0; i < 5; i++)
                    Box("Cloth valance", new Vector3(-1.15f + i * .57f, 2.13f, -1.05f), new Vector3(.54f, .29f, .025f), i % 2 == 0 ? paper : stall == 0 ? vermilion : indigo, s);
                Box("Hanging shop crest sign", new Vector3(.78f, 1.69f, -.88f), new Vector3(.5f, .55f, .05f), wood, s);
                // Original painted sun crest, visibly attached to the sign board.
                var crest = Box("Painted crest", new Vector3(.78f, 1.69f, -.914f), new Vector3(.44f, .48f, .008f), paper, s);
                var cm = new Material(paper);
                cm.SetTexture("_BaseMap", WindflowerArt.Load("noren"));
                crest.GetComponent<Renderer>().sharedMaterial = Save(cm, "StallCrest-" + stall + ".mat");
                Beam("Lantern hanging hook", new Vector3(-1.2f, 2.18f, -.45f), new Vector3(-1.2f, 2.18f, -.85f), .025f, wood, s);
                Beam("Lantern cord", new Vector3(-1.2f, 2.18f, -.85f), new Vector3(-1.2f, 1.98f, -.85f), .008f, wood, s);
                PaperLantern(new Vector3(-1.2f, 1.73f, -.85f), s);
                for (int tray = 0; tray < 2; tray++)
                {
                    float tx = tray == 0 ? -.62f : .45f;
                    Box("Merchandise tray", new Vector3(tx, .92f, -.1f), new Vector3(.85f, .08f, .65f), wood, s);
                    if (stall == 0)
                        for (int j = 0; j < 6; j++)
                        {
                            float px = tx - .26f + (j % 3) * .25f, pz = -.30f + (j / 3) * .30f;
                            var produce = Lathe("Harvest produce", new Vector3(px, 1.03f, pz), new[] { new Vector2(0, -.09f), new Vector2(.09f, -.07f), new Vector2(.12f, .01f), new Vector2(.085f, .10f), new Vector2(0, .11f) }, j % 2 == 0 ? fruit : green, s);
                        }
                    else
                        for (int j = 0; j < 3; j++)
                            Lathe("Celadon tea vessel", new Vector3(tx - .25f + j * .25f, .96f, -.08f), new[] { new Vector2(0, 0), new Vector2(.07f, 0), new Vector2(.11f, .04f), new Vector2(.10f, .19f), new Vector2(.06f, .22f), new Vector2(.065f, .24f), new Vector2(.045f, .24f), new Vector2(.04f, .20f), new Vector2(.075f, .17f), new Vector2(.075f, .05f), new Vector2(0, .04f) }, green, s);
                }

                Box("Rear merchandise shelf", new Vector3(0, 1.12f, .56f), new Vector3(1.9f, .06f, .35f), wood, s);
                for (int j = 0; j < 3; j++)
                    Lathe("Stored basket", new Vector3(-.65f + j * .65f, 1.16f, .56f), new[] { new Vector2(0, 0), new Vector2(.13f, 0), new Vector2(.20f, .24f), new Vector2(.18f, .26f), new Vector2(.16f, .23f), new Vector2(.11f, .04f), new Vector2(0, .04f) }, paper, s);
                WarmLight(new Vector3(x, 1.8f, -.5f), .5f, 3.5f);
            }

            var audio = market.gameObject.AddComponent<MarketSoundscape>();
            audio.game = flow;
            audio.music = market.gameObject.AddComponent<AudioSource>();
            audio.music.clip = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Sunward/Audio/market-pentatonic.wav");
            audio.music.loop = true;
            audio.music.playOnAwake = true;
            audio.music.volume = 0;
            audio.music.spatialBlend = 0;
            audio.market = market.gameObject.AddComponent<AudioSource>();
            audio.market.clip = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Sunward/Audio/market-ambience.wav");
            audio.market.loop = true;
            audio.market.playOnAwake = true;
            audio.market.volume = 0;
            audio.market.spatialBlend = 1;
            audio.market.minDistance = 8;
            audio.market.maxDistance = 35;
            if (!audio.music.clip || !audio.market.clip)
                throw new InvalidDataException("Missing original market music/Foley WAVs.");
        }

        static void GroundAccents()
        {
            var v = new List<Vector3>();
            var uv = new List<Vector2>();
            var colors = new List<Color>();
            var ix = new List<int>();
            void Triangle(Vector3 a, Vector3 b, Vector3 c, Color color)
            {
                int n = v.Count;
                v.AddRange(new[] { a, b, c, c, b, a });
                uv.AddRange(new[] { Vector2.zero, new Vector2(.5f, 1), new Vector2(1, 0), new Vector2(1, 0), new Vector2(.5f, 1), Vector2.zero });
                colors.AddRange(new[] { color * .8f, color, color * .95f, color * .95f, color, color * .8f });
                ix.AddRange(new[] { n, n + 1, n + 2, n + 3, n + 4, n + 5 });
            }

            for (int blade = 0; blade < 9; blade++)
            {
                float a = blade * 2.4f;
                var foot = new Vector3(Mathf.Sin(a) * .27f, 0, Mathf.Cos(a) * .27f);
                var side = new Vector3(Mathf.Cos(a), 0, -Mathf.Sin(a)) * .035f;
                var mid = foot + new Vector3(Mathf.Sin(a) * .06f, .18f + (blade % 3) * .03f, Mathf.Cos(a) * .06f);
                var tip = mid + new Vector3(Mathf.Sin(a) * .10f, .13f, Mathf.Cos(a) * .10f);
                var color = new Color(.36f + .025f * (blade % 3), .52f, .29f);
                Triangle(foot - side, mid, foot + side, color);
                Triangle(mid - side * .65f, tip, mid + side * .65f, color);
            }

            for (int flower = 0; flower < 4; flower++)
            {
                float a = flower * 2.4f;
                var foot = new Vector3(Mathf.Sin(a) * .24f, 0, Mathf.Cos(a) * .24f);
                var top = foot + Vector3.up * (.34f + flower * .045f);
                Triangle(foot - Vector3.right * .008f, top, foot + Vector3.right * .008f, new Color(.37f, .52f, .31f));
                for (int petal = 0; petal < 5; petal++)
                {
                    float ang = petal * Mathf.PI * 2 / 5;
                    var axis = new Vector3(Mathf.Sin(ang), .10f, Mathf.Cos(ang));
                    var side = new Vector3(axis.z, 0, -axis.x) * .035f;
                    var end = top + axis * .09f;
                    var tint = flower % 2 == 0 ? new Color(.97f, .70f, .65f) : new Color(.94f, .90f, .70f);
                    Triangle(top, end - side, end + side, tint);
                    Triangle(end - side, end + axis * .035f, end + side, tint);
                }
            }

            var mesh = new Mesh
            {
                vertices = v.ToArray(),
                uv = uv.ToArray(),
                colors = colors.ToArray(),
                triangles = ix.ToArray()
            };
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            mesh = Save(mesh, "Wildflower-clump.asset");
            var mat = Paint("Wildflower pigments", Color.white);
            mat.SetFloat("_Wind", .35f);
            mat.SetFloat("_SurfaceKind", 4);
            EditorUtility.SetDirty(mat);
            var garden = Group("Road-edge wildflower planting", Vector3.zero);
            for (int side = -1; side <= 1; side += 2)
                for (int i = 0; i < 12; i++)
                {
                    var p = new Vector3(side * (3.35f + .22f * Mathf.Sin(i * 2.1f)), 0, -18 + i * 3.2f);
                    if (!VillageNavigation.Clear(world, p, .30f) || LanternPlaces.Any(l => new Vector2(p.x - l.x, p.z - l.y).sqrMagnitude < .9f))
                        continue;
                    p.y = Height(p.x, p.z) - .015f;
                    var go = MeshObject("Painted wildflower verge", mesh, p, mat, garden);
                    go.transform.localRotation = Quaternion.Euler(0, i * 47, 0);
                }
        }

        static readonly Vector2[] LanternPlaces =
        {
            new Vector2(-3.9f, 20),
            new Vector2(3.9f, 20),
            new Vector2(-3.9f, -19),
            new Vector2(3.9f, -19),
            new Vector2(15, 3.8f),
            new Vector2(15, -3.8f),
            new Vector2(-29, -11),
            new Vector2(-39, -11),
            new Vector2(-32, 16),
            new Vector2(-42, -18),
            new Vector2(-17, -11),
            new Vector2(-17, 15)
        };
        static void Lanterns()
        {
            foreach (var p in LanternPlaces)
            {
                var t = Group("Kasuga lantern · closed stone cap", new Vector3(p.x, Height(p.x, p.y) - .05f, p.y));
                Lathe("Carved pedestal", Vector3.zero, new[] { new Vector2(0, 0), new Vector2(.43f, 0), new Vector2(.44f, .10f), new Vector2(.30f, .18f), new Vector2(.18f, .24f), new Vector2(.13f, .91f), new Vector2(.26f, 1.02f), new Vector2(0, 1.05f) }, stone, t);
                Box("Lantern solid fire chamber", new Vector3(0, 1.25f, 0), new Vector3(.46f, .47f, .46f), stone, t);
                for (int side = 0; side < 4; side++)
                {
                    var face = Group("Recessed warm window", new Vector3(Mathf.Sin(side * Mathf.PI / 2) * .238f, 1.28f, Mathf.Cos(side * Mathf.PI / 2) * .238f), t);
                    face.localRotation = Quaternion.Euler(0, side * 90, 0);
                    Box("Lit rice paper", Vector3.zero, new Vector3(.25f, .28f, .012f), paper, face);
                }

                Lathe("Solid weathered stone roof", Vector3.zero, RevolvedGeometry.LanternRoof, stone, t);
                WarmLight(t.position + Vector3.up * 1.28f, .26f, 2.8f);
            }

            // Remove the old open-bottom caps/chambers by location, not by making
            // their material double-sided. Their replacements above have real caps.
            foreach (var filter in root.parent.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!filter.sharedMesh || !filter.sharedMesh.name.StartsWith("Valley-"))
                    continue;
                if (!sourceKinds.TryGetValue(filter.sharedMesh.name, out string kind) || (kind != "wood" && kind != "stone" && kind != "wash"))
                    continue;
                var m = filter.sharedMesh;
                var v = m.vertices;
                var ix = m.triangles;
                var keep = new List<int>();
                for (int k = 0; k < ix.Length; k += 3)
                {
                    bool remove = false;
                    foreach (var p in LanternPlaces)
                    {
                        bool inside = true;
                        float ground = Height(p.x, p.y);
                        for (int j = 0; j < 3; j++)
                        {
                            var a = filter.transform.TransformPoint(v[ix[k + j]]);
                            inside &= Mathf.Abs(a.x - p.x) < .62f && Mathf.Abs(a.z - p.y) < .62f && a.y > ground + .07f && a.y < ground + 2.2f;
                        }

                        if (inside)
                        {
                            remove = true;
                            break;
                        }
                    }

                    if (!remove)
                    {
                        keep.Add(ix[k]);
                        keep.Add(ix[k + 1]);
                        keep.Add(ix[k + 2]);
                    }
                }

                if (keep.Count != ix.Length)
                {
                    m.triangles = keep.ToArray();
                    m.RecalculateBounds();
                    EditorUtility.SetDirty(m);
                }
            }
        }

        static void Wind(GameObject town, ValleyData data)
        {
            var filters = town.GetComponentsInChildren<MeshFilter>(true).Where(f => f.sharedMesh && f.sharedMesh.name.StartsWith("Valley-")).ToDictionary(f => f.sharedMesh.name);
            int id = 0, count = 0;
            foreach (var group in data.assets)
            {
                int first = id;
                id += group.meshes.Length;
                if (group.name != "TownV3" || !group.meshes.Any(m => data.materials[m.material].kind == "leaves"))
                    continue;
                Bounds bounds = new Bounds();
                bool init = false;
                for (int i = 0; i < group.meshes.Length; i++)
                    if (filters.TryGetValue("Valley-" + (first + i), out var f))
                    {
                        if (!init)
                        {
                            bounds = f.GetComponent<Renderer>().bounds;
                            init = true;
                        }
                        else
                            bounds.Encapsulate(f.GetComponent<Renderer>().bounds);
                    }

                for (int i = 0; i < group.meshes.Length; i++)
                {
                    if (!filters.TryGetValue("Valley-" + (first + i), out var f))
                        continue;
                    string kind = data.materials[group.meshes[i].material].kind;
                    if (kind != "wood" && kind != "leaves")
                        continue;
                    // Scene-owned material copies serialize tree-specific wind values.
                    var r = f.GetComponent<Renderer>();
                    var m = new Material(r.sharedMaterial);
                    m.SetFloat("_TreeWind", kind == "wood" ? .35f : 1);
                    m.SetFloat("_TreeBaseY", bounds.min.y);
                    m.SetFloat("_TreePhase", bounds.center.x * .37f + bounds.center.z * .29f);
                    r.sharedMaterial = Save(m, "TreeWind-" + (first + i) + ".mat");
                    count++;
                }
            }

            Debug.Log("Tree-specific wind assigned to " + count + " live foliage/branch renderers; trunks anchored by height.");
        }

        static void Residents()
        {
            for (int i = 0; i < flow.npcObjects.Length; i++)
            {
                var npc = flow.npcObjects[i];
                Vector3 desired = i < 2 ? new Vector3(i == 0 ? -4.8f : 4.8f, 0, 1.42f) : npc.transform.position;
                if (!VillageNavigation.FindSafe(world, desired, out var safe))
                    throw new InvalidDataException("No safe resident position " + npc.name);
                npc.transform.position = safe;
                if (i < 2)
                    npc.transform.rotation = Quaternion.Euler(0, 180, 0);
                ResidentRigAuthoring.Build(npc, flow, i);
            }
        }
    }
}
