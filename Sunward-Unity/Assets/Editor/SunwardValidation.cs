using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class SunwardValidation
    {
        [MenuItem("Sunward/Validate Imported Project")]
        public static void Validate()
        {
            int checks = 0;
            void Need(bool ok, string what)
            {
                if (!ok)
                    throw new InvalidOperationException(what);
                checks++;
            }

            Need(File.Exists("Assets/Sunward/Scenes/Windflower.unity"), "Generated Windflower scene exists");
            foreach (string name in new[]
            {
                "Sunward/Surface Pigment",
                "Sunward/Brush River",
                "Sunward/Calligraphic Energy"
            }

            )
            {
                var shader = Shader.Find(name);
                Need(shader && !ShaderUtil.ShaderHasError(shader), "Shader compiled: " + name);
            }

            var fbx = AssetDatabase.LoadAllAssetsAtPath("Assets/Sunward/Models/Amaterasu.fbx");
            var clips = fbx.OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).ToArray();
            Need(clips.Length == 47, "All 47 imported animation clips retained");
            foreach (string n in new[]
            {
                "Idle_Natural",
                "Walk_Natural",
                "Jog_Natural",
                "Sprint_Fluid",
                "Sleep_Down",
                "Sleep_Loop",
                "Sleep_Up",
                "Thrust",
                "HeavyArc",
                "Disc1",
                "Jump_Double"
            }

            )
                Need(clips.Any(c => WolfClipProcessor.Clean(c.name) == n), "Animation: " + n);
            Need(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Sunward/Generated/Amaterasu.prefab"), "Original-wolf prefab");
            Need(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Sunward/Generated/TownV3.prefab"), "Latest V3 town prefab");
            Need(AssetDatabase.LoadAssetAtPath<WeaponDefinition>("Assets/Sunward/Generated/sundial.asset"), "Sundial weapon definition");
            var wolfPrefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Sunward/Generated/Amaterasu.prefab");
            foreach (var renderer in wolfPrefab.GetComponentsInChildren<Renderer>(true))
                foreach (var material in renderer.sharedMaterials)
                {
                    Need(material && material.shader && !ShaderUtil.ShaderHasError(material.shader), "Wolf shader: " + renderer.name);
                    if (material.name == "Wolf-OriginalDefault")
                        continue;
                    Need(material.GetTexture("_BaseMap") is Texture2D, "Original 2D fur map: " + renderer.name);
                    Need(material.GetFloat("_Cull") == 2, "Original ink-shell backface culling: " + renderer.name);
                }

            foreach (var path in AssetDatabase.FindAssets("t:Material", new[] { "Assets/Sunward/Generated" }).Select(AssetDatabase.GUIDToAssetPath))
            {
                var material = AssetDatabase.LoadAssetAtPath<Material>(path);
                foreach (string property in new[]
                {
                    "_BaseMap",
                    "_MainTex"
                }

                )
                    if (material.HasProperty(property) && material.GetTexture(property))
                        Need(material.GetTexture(property).dimension == UnityEngine.Rendering.TextureDimension.Tex2D, "2D texture binding: " + path + " / " + property);
            }

            foreach (string id in new[]
            {
                "spear",
                "sundial"
            }

            )
            {
                var weapon = AssetDatabase.LoadAssetAtPath<WeaponDefinition>("Assets/Sunward/Generated/" + id + ".asset");
                Need(weapon && weapon.visual && weapon.visual.GetComponentsInChildren<Renderer>(true).Length > 0, "Original weapon geometry: " + id);
                foreach (var strike in weapon.light.Concat(weapon.heavy).Concat(new[] { weapon.charged, weapon.chargedHeavy, weapon.air }))
                    Need(clips.Any(c => WolfClipProcessor.Clean(c.name) == strike.clip) && strike.start < strike.end && strike.end <= 1 && strike.duration > 0, "Playable attack: " + id + " / " + strike.clip);
            }

            foreach (var mesh in AssetDatabase.LoadAllAssetsAtPath("Assets/Sunward/Generated/ValleyMeshes.asset").OfType<Mesh>())
                Need(mesh.vertices.All(v => float.IsFinite(v.x) && float.IsFinite(v.y) && float.IsFinite(v.z)), "Finite terrain geometry: " + mesh.name);
            var p = new ProfileData();
            Need(ProgressionRules.Validate(p), "Fresh progression");
            Need(ProgressionRules.Buy(p, "vitality") && p.coins == 5 && ProgressionRules.MaxHp(p) == 112, "Permanent upgrade purchase");
            Need(!ProgressionRules.Buy(p, "unlock-sundial"), "Unaffordable purchase rejected");
            p.coins = 500;
            Need(ProgressionRules.Buy(p, "unlock-sundial") && p.equipped == "sundial", "Unlock and equip");
            p.defeats++;
            Need(p.owned.Contains("sundial"), "Defeat preserves ownership");
            if (EditorApplication.isPlaying)
            {
                var game = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
                Need(game && game.Player && game.Player.animationView.animator.isInitialized, "Playable scene and Animator initialised");
                Need(game.npcObjects.Length == 7, "Seven original village NPCs");
                foreach (var npc in game.npcObjects)
                    Need(VillageNavigation.Clear(game.valley.Data, npc.transform.position), "Resident clear of walls/water: " + npc.name);
                Need(UnityEngine.Object.FindFirstObjectByType<HomeWeaponRack>(), "Home weapon display state system");
                Need(game.Combat.enabled, "Arena equipment/combat state system");
                Need(game.spirits.Length == 6, "Six spirit definitions including boss");
                Need(game.valley.Data.terrain.heights.Length > 40000, "Sculpted V3 terrain loaded");
                Need(Valley.Depth(new Vector3(Valley.RiverX(0), 0, 0)) > .5f, "River centre has depth");
                Need(Valley.Depth(new Vector3(-23, 0, -12)) == 0, "Bridge is a valid crossing");
            }

            Debug.Log("Sunward validation complete · " + checks + " checks passed. Imports and wiring checked; visual review and playtesting still required. Follow Review/REPAIR-2.md.");
        }

        [MenuItem("Sunward/Validate Character Deformations")]
        public static void ValidateDeformations()
        {
            if (EditorApplication.isPlaying || AnimationMode.InAnimationMode())
                throw new InvalidOperationException("Exit Play Mode and animation preview before testing.");
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Sunward/Generated/Amaterasu.prefab");
            if (!prefab)
                throw new InvalidOperationException("Rebuild the Windflower scene first.");
            var copy = UnityEngine.Object.Instantiate(prefab);
            copy.hideFlags = HideFlags.HideAndDontSave;
            var baked = new Mesh();
            int samples = 0;
            try
            {
                var animator = copy.GetComponentInChildren<Animator>();
                animator.enabled = false;
                string[] names =
                {
                    "Idle_Natural",
                    "Walk_Natural",
                    "Jog_Natural",
                    "Sprint_Fluid",
                    "Sleep_Down",
                    "Sleep_Loop",
                    "Sleep_Up",
                    "HeavyArc",
                    "HeavyReturn",
                    "DiscHeavy",
                    "DiscCharged"
                };
                foreach (var clip in animator.runtimeAnimatorController.animationClips.Where(c => names.Contains(c.name)).Distinct())
                    foreach (float phase in new[]
                    {
                        0f,
                        .25f,
                        .5f,
                        .75f,
                        .999f
                    }

                    )
                    {
                        clip.SampleAnimation(animator.gameObject, clip.length * phase);
                        foreach (var renderer in copy.GetComponentsInChildren<SkinnedMeshRenderer>())
                        {
                            renderer.BakeMesh(baked);
                            if (baked.vertices.Any(v => !float.IsFinite(v.x) || !float.IsFinite(v.y) || !float.IsFinite(v.z)))
                                throw new InvalidOperationException("Invalid skinning: " + clip.name + " / " + renderer.name + " / " + phase);
                            if (baked.bounds.size.magnitude > 100)
                                throw new InvalidOperationException("Exploded mesh bounds: " + clip.name + " / " + renderer.name);
                            samples++;
                        }
                    }
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(baked);
                UnityEngine.Object.DestroyImmediate(copy);
            }

            Debug.Log("Character deformation sampling passed · " + samples + " baked meshes. This catches invalid vertices/explosions, not all clipping or visual defects. Inspect sleep and both heavy combos in Play Mode.");
        }
    }
}
