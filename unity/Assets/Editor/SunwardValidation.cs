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
            void Need(bool ok, string what)
            {
                if (!ok)
                    throw new InvalidOperationException(what);
                Debug.Log("PASS · " + what);
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
            Need(clips.Length >= 44, "44 imported animation clips");
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
                Need(clips.Any(c => c.name == n), "Animation: " + n);
            Need(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Sunward/Generated/Amaterasu.prefab"), "Original-wolf prefab");
            Need(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Sunward/Generated/TownV3.prefab"), "Latest V3 town prefab");
            Need(AssetDatabase.LoadAssetAtPath<WeaponDefinition>("Assets/Sunward/Generated/sundial.asset"), "Sundial weapon definition");
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
                Need(game.spirits.Length == 6, "Six spirit definitions including boss");
                Need(game.valley.Data.terrain.heights.Length > 40000, "Sculpted V3 terrain loaded");
                Need(Valley.Depth(new Vector3(Valley.RiverX(0), 0, 0)) > .5f, "River centre has depth");
                Need(Valley.Depth(new Vector3(-23, 0, -12)) == 0, "Bridge is a valid crossing");
            }

            Debug.Log("Sunward validation complete. This checks imports and wiring, not visual approval or combat balance. Follow the play checklist in README.md.");
        }
    }
}
