using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class WolfClipProcessor
    {
        public const string Source = "Assets/Sunward/Models/Amaterasu.fbx";
        public const string Folder = "Assets/Sunward/Generated/Animations";
        public const string Controller = "Assets/Sunward/Generated/Amaterasu.controller";
        public static string Clean(string name) => name.Substring(name.LastIndexOf('|') + 1).Replace("_WOLF_RIG", "");
        public static AnimationClip[] Prepare()
        {
            Directory.CreateDirectory(Folder);
            AssetDatabase.Refresh();
            var source = AssetDatabase.LoadAllAssetsAtPath(Source).OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).ToArray();
            if (source.Length != 47)
                throw new InvalidDataException("Expected all 47 Amaterasu clips, found " + source.Length);
            var result = new List<AnimationClip>();
            int removed = 0;
            foreach (var original in source)
            {
                var copy = UnityEngine.Object.Instantiate(original);
                copy.name = Clean(original.name);
                copy.hideFlags = HideFlags.None;
                copy.legacy = false;
                foreach (var binding in AnimationUtility.GetCurveBindings(copy))
                {
                    if (binding.type != typeof(Transform) || !WolfScaleRules.IsContainerScale(binding.path, binding.propertyName))
                        continue;
                    var curve = AnimationUtility.GetEditorCurve(copy, binding);
                    if (curve.keys.Any(k => !float.IsFinite(k.value)))
                        throw new InvalidDataException("Non-finite source container scale: " + copy.name + " / " + binding.path);
                    AnimationUtility.SetEditorCurve(copy, binding, null);
                    removed++;
                }

                if (AnimationUtility.GetCurveBindings(copy).Any(b => b.type == typeof(Transform) && WolfScaleRules.IsContainerScale(b.path, b.propertyName)))
                    throw new InvalidDataException("Container scale survived processing: " + copy.name);
                string path = Folder + "/" + copy.name + ".anim";
                var saved = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
                if (saved)
                {
                    EditorUtility.CopySerialized(copy, saved);
                    UnityEngine.Object.DestroyImmediate(copy);
                }
                else
                {
                    AssetDatabase.CreateAsset(copy, path);
                    saved = copy;
                }

                EditorUtility.SetDirty(saved);
                result.Add(saved);
            }

            AssetDatabase.SaveAssets();
            Debug.Log("Prepared " + result.Count + " native Amaterasu clip copies; removed " + removed + " container-only scale bindings. Source FBX and all bone channels preserved.");
            return result.ToArray();
        }

        [MenuItem("Sunward/Repair Amaterasu Animation Scale")]
        public static void RepairExisting()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Stop Play Mode before repairing animation assets.");
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(Controller);
            if (!controller)
            {
                Debug.Log("No generated Animator yet. Create Windflower once; its builder processes the clips automatically.");
                return;
            }

            string backup = "Assets/Sunward/Generated/Amaterasu-SourceClips.controller";
            if (!File.Exists(backup))
                AssetDatabase.CopyAsset(Controller, backup);
            var clips = Prepare().ToDictionary(c => c.name);
            foreach (var child in controller.layers[0].stateMachine.states)
            {
                if (!clips.TryGetValue(child.state.name, out var clip))
                    throw new InvalidDataException("Unmapped Animator state: " + child.state.name);
                child.state.motion = clip;
                EditorUtility.SetDirty(child.state);
            }

            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();
            ValidateScale();
            foreach (var view in UnityEngine.Object.FindObjectsByType<WolfAnimation>())
            {
                if (!view.animator || view.animator.runtimeAnimatorController != controller)
                    continue;
                Undo.RecordObject(view.animator, "Enable repaired wolf Animator");
                view.animator.enabled = true;
                EditorUtility.SetDirty(view.animator);
                foreach (var transform in view.animator.GetComponentsInChildren<Transform>(true))
                {
                    if (transform != view.animator.transform && transform.name != "WOLF_RIG")
                        continue;
                    if ((transform.localScale - Vector3.one * 100).sqrMagnitude < .001f)
                    {
                        Undo.RecordObject(transform, "Restore authored rig container scale once");
                        transform.localScale = transform == view.animator.transform ? Vector3.one * .34f : Vector3.one;
                        EditorUtility.SetDirty(transform);
                    }
                }
            }

            Debug.Log("Animator now uses processed native clips. No scale is forced by a runtime script. The source-clip controller is preserved for rollback.");
        }

        [MenuItem("Sunward/Validate Amaterasu Scale and Transitions")]
        public static void ValidateScale()
        {
            if (EditorApplication.isPlaying)
                throw new InvalidOperationException("Run this check outside Play Mode.");
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Sunward/Generated/Amaterasu.prefab");
            if (!prefab)
                throw new InvalidOperationException("Generate the Amaterasu prefab first.");
            var instance = UnityEngine.Object.Instantiate(prefab);
            instance.hideFlags = HideFlags.HideAndDontSave;
            int samples = 0;
            try
            {
                var animator = instance.GetComponentInChildren<Animator>();
                animator.runtimeAnimatorController = AssetDatabase.LoadAssetAtPath<AnimatorController>(Controller);
                var containers = animator.GetComponentsInChildren<Transform>(true).Where(t => t == animator.transform || t.name == "WOLF_RIG").ToArray();
                // Compare against authored values, never a snapshot that might already
                // contain the very 100x fault being tested.
                var rest = containers.Select(t => t == animator.transform ? Vector3.one * .34f : Vector3.one).ToArray();
                var clips = animator.runtimeAnimatorController.animationClips.Distinct().ToArray();
                if (clips.Length != 47)
                    throw new InvalidDataException("Controller must retain all 47 actions.");
                void Check(string label)
                {
                    for (int i = 0; i < containers.Length; i++)
                        if (!MeshSafety.Finite(containers[i].localScale) || (containers[i].localScale - rest[i]).sqrMagnitude > .00001f)
                            throw new InvalidDataException("Animated container scale changed in " + label + " / " + containers[i].name + ": " + containers[i].localScale);
                    samples++;
                }

                animator.Rebind();
                animator.Update(0);
                Check("initial Animator enable");
                foreach (var clip in clips)
                {
                    if (!AssetDatabase.GetAssetPath(clip).StartsWith(Folder + "/"))
                        throw new InvalidDataException("Controller still references raw FBX action: " + clip.name);
                    for (int frame = 0; frame <= 12; frame++)
                    {
                        animator.Play(clip.name, 0, frame / 12f);
                        animator.Update(0);
                        Check(clip.name + " phase " + frame);
                    }
                }

                string[] cycle =
                {
                    "Idle_Natural",
                    "Walk_Natural",
                    "Jog_Natural",
                    "Sprint_Fluid",
                    "Jump_Sprint",
                    "Air_Fall",
                    "Land_Heavy",
                    "Dodge_Left",
                    "HeavyArc",
                    "HeavyReturn",
                    "DiscHeavy",
                    "Sleep_Down",
                    "Sleep_Loop",
                    "Sleep_Up",
                    "Idle_Natural"
                };
                foreach (var state in cycle)
                {
                    animator.CrossFadeInFixedTime(state, .12f, 0, 0);
                    for (int f = 0; f < 12; f++)
                    {
                        animator.Update(1 / 60f);
                        Check("transition " + state);
                    }
                }
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(instance);
            }

            Debug.Log("Amaterasu scale validation passed: " + samples + " Animator samples, all 47 actions and representative transitions. Review movement/skinning visually in Play Mode too.");
        }
    }
}
