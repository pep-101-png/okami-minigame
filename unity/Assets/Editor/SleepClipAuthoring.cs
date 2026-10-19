using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    // Unity-space FK bake: preserves every bone's rest translation/scale except
    // root hips translation. Analytic limb rotation never stretches a segment.
    public static class SleepClipAuthoring
    {
        static string Normal(string s) => s.Replace(".", "");
        static Transform Bone(Transform root, string name) => root.GetComponentsInChildren<Transform>(true).Single(t => Normal(t.name) == Normal(name));
        public static void Apply(AnimationClip clip, GameObject source)
        {
            if (clip.name != "Sleep_Down" && clip.name != "Sleep_Loop" && clip.name != "Sleep_Up")
                return;
            foreach (var binding in AnimationUtility.GetCurveBindings(clip))
                if (binding.type == typeof(Transform) && binding.path.Split('/').Last().StartsWith("DEF_") && (binding.propertyName.StartsWith("m_LocalPosition") || binding.propertyName.StartsWith("m_LocalRotation") || binding.propertyName.StartsWith("m_LocalScale") || binding.propertyName.Contains("Euler")))
                    AnimationUtility.SetEditorCurve(clip, binding, null);
            var model = UnityEngine.Object.Instantiate(source);
            model.hideFlags = HideFlags.HideAndDontSave;
            try
            {
                var animator = model.GetComponent<Animator>();
                if (animator)
                    UnityEngine.Object.DestroyImmediate(animator);
                model.transform.localScale = Vector3.one * .34f;
                Bone(model.transform, "WOLF_RIG").localScale = Vector3.one;
                // Match MakeWolf's facing correction without modifying the source.
                Vector3 front = Bone(model.transform, "DEF_head").position - Bone(model.transform, "DEF_chest").position;
                front.y = 0;
                model.transform.rotation = Quaternion.FromToRotation(front.normalized, Vector3.forward) * model.transform.rotation;
                var bones = model.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("DEF_")).ToArray();
                var pos = bones.Select(t => t.localPosition).ToArray();
                var rot = bones.Select(t => t.localRotation).ToArray();
                var scales = bones.Select(t => t.localScale).ToArray();
                var paths = bones.Select(t => AnimationUtility.CalculateTransformPath(t, model.transform)).ToArray();
                var curves = new Dictionary<string, AnimationCurve[]>();
                foreach (string path in paths)
                    curves[path] = Enumerable.Range(0, 10).Select(_ => new AnimationCurve()).ToArray();
                var hips = Bone(model.transform, "DEF_hips");
                float drop = Mathf.Max(0, hips.position.y - .43f);
                var pawRest = new Dictionary<string, Vector3>();
                var pawRot = new Dictionary<string, Quaternion>();
                var tipRot = new Dictionary<string, Quaternion>();
                var tipOffset = new Dictionary<string, Vector3>();
                foreach (string kind in new[]
                {
                    "front",
                    "rear"
                }

                )
                    foreach (string side in new[]
                    {
                        "L",
                        "R"
                    }

                    )
                    {
                        string key = kind + side;
                        var paw = Bone(model.transform, "DEF_" + kind + "_paw." + side);
                        pawRest[key] = paw.position;
                        pawRot[key] = paw.rotation;
                        var tip = Bone(model.transform, "DEF_" + kind + (kind == "front" ? "_paw." : "_hock.") + side);
                        tipRot[key] = tip.rotation;
                        tipOffset[key] = tip.position - paw.position;
                    }

                const int samples = 61;
                float duration = clip.name == "Sleep_Loop" ? 4f : 2f;
                for (int frame = 0; frame < samples; frame++)
                {
                    for (int i = 0; i < bones.Length; i++)
                    {
                        bones[i].localPosition = pos[i];
                        bones[i].localRotation = rot[i];
                        bones[i].localScale = scales[i];
                    }

                    float t = frame / (float)(samples - 1);
                    float q = clip.name == "Sleep_Loop" ? 1 : Mathf.SmoothStep(0, 1, clip.name == "Sleep_Up" ? 1 - t : t);
                    hips.position -= Vector3.up * (drop * q);
                    foreach (string n in new[]
                    {
                        "DEF_spine_mid",
                        "DEF_chest",
                        "DEF_neck_base",
                        "DEF_neck_upper",
                        "DEF_head"
                    }

                    )
                    {
                        var b = Bone(model.transform, n);
                        float degrees = n == "DEF_head" ? 12 : n.Contains("neck") ? 18 : 2;
                        b.rotation = Quaternion.AngleAxis(degrees * q, Vector3.right) * b.rotation;
                    }

                    var tail = Bone(model.transform, "DEF_tail_01");
                    tail.rotation = Quaternion.AngleAxis(8 * q, Vector3.right) * Quaternion.AngleAxis(12 * q, Vector3.up) * tail.rotation;
                    if (clip.name == "Sleep_Loop")
                        hips.position += Vector3.up * (Mathf.Cos(t * Mathf.PI * 2) - 1) * .004f;
                    foreach (string kind in new[]
                    {
                        "front",
                        "rear"
                    }

                    )
                        foreach (string side in new[]
                        {
                            "L",
                            "R"
                        }

                        )
                        {
                            var upper = Bone(model.transform, "DEF_" + kind + "_upper." + side);
                            var lower = Bone(model.transform, "DEF_" + kind + "_lower." + side);
                            var tip = Bone(model.transform, "DEF_" + kind + (kind == "front" ? "_paw." : "_hock.") + side);
                            var paw = Bone(model.transform, "DEF_" + kind + "_paw." + side);
                            string key = kind + side;
                            Vector3 target = pawRest[key] + Vector3.forward * (kind == "front" ? .65f : .45f) * q;
                            // Keep the original paw/toe clearance; lowering paw bones
                            // to a common height buries the front toes in the futon.
                            target.y = pawRest[key].y;
                            Vector3 offset = tipOffset[key];
                            Vector3 end = target + offset;
                            Vector3 start = upper.position;
                            float a = Vector3.Distance(start, lower.position), b = Vector3.Distance(lower.position, tip.position);
                            Vector3 axis = (end - start).normalized;
                            LimbArc.Solve(a, b, Vector3.Distance(start, end), out float x, out float h, out float d);
                            Vector3 restPlane = Vector3.ProjectOnPlane(lower.position - start, axis).normalized;
                            Vector3 folded = Vector3.ProjectOnPlane(Vector3.down * .9f + (kind == "front" ? Vector3.back : Vector3.forward) * .1f + Vector3.right * (side == "L" ? .18f : -.18f), axis).normalized;
                            Vector3 plane = Vector3.Slerp(restPlane, folded, q).normalized;
                            Vector3 center = start + axis * x;
                            Vector3 joint = center + plane * h;
                            if (joint.y < .14f && h > .0001f)
                            {
                                Vector3 upright = Vector3.ProjectOnPlane(Vector3.up, axis).normalized;
                                Vector3 lateral = Vector3.Cross(axis, upright).normalized;
                                if (Vector3.Dot(lateral, Vector3.right) * (side == "L" ? 1 : -1) < 0)
                                    lateral = -lateral;
                                float c = Mathf.Clamp((.14f - center.y) / Mathf.Max(.00001f, h * upright.y), -1, 1);
                                plane = upright * c + lateral * Mathf.Sqrt(Mathf.Max(0, 1 - c * c));
                                joint = center + plane * h;
                            }

                            upper.rotation = Quaternion.FromToRotation(lower.position - start, joint - start) * upper.rotation;
                            lower.rotation = Quaternion.FromToRotation(tip.position - lower.position, (start + axis * d) - lower.position) * lower.rotation;
                            tip.rotation = tipRot[key];
                            paw.rotation = pawRot[key];
                        }

                    for (int i = 0; i < bones.Length; i++)
                    {
                        var p = bones[i].localPosition;
                        var r = bones[i].localRotation;
                        var v = bones[i].localScale;
                        var c = curves[paths[i]];
                        if (frame > 0)
                        {
                            float dot = c[3].keys[frame - 1].value * r.x + c[4].keys[frame - 1].value * r.y + c[5].keys[frame - 1].value * r.z + c[6].keys[frame - 1].value * r.w;
                            if (dot < 0)
                                r = new Quaternion(-r.x, -r.y, -r.z, -r.w);
                        }

                        float[] values =
                        {
                            p.x,
                            p.y,
                            p.z,
                            r.x,
                            r.y,
                            r.z,
                            r.w,
                            v.x,
                            v.y,
                            v.z
                        };
                        for (int k = 0; k < 10; k++)
                        {
                            if (!float.IsFinite(values[k]))
                                throw new InvalidOperationException("Invalid sleep FK sample " + bones[i].name);
                            c[k].AddKey(t * duration, values[k]);
                        }

                        if (bones[i] != hips && Vector3.Distance(bones[i].localPosition, pos[i]) > .0001f)
                            throw new InvalidOperationException("Sleep stretched bone: " + bones[i].name);
                        if (Vector3.Distance(bones[i].localScale, scales[i]) > .0001f)
                            throw new InvalidOperationException("Sleep scaled bone: " + bones[i].name);
                    }
                }

                string[] properties =
                {
                    "m_LocalPosition.x",
                    "m_LocalPosition.y",
                    "m_LocalPosition.z",
                    "m_LocalRotation.x",
                    "m_LocalRotation.y",
                    "m_LocalRotation.z",
                    "m_LocalRotation.w",
                    "m_LocalScale.x",
                    "m_LocalScale.y",
                    "m_LocalScale.z"
                };
                foreach (var entry in curves)
                    for (int k = 0; k < properties.Length; k++)
                    {
                        var curve = entry.Value[k];
                        for (int key = 0; key < curve.length; key++)
                        {
                            AnimationUtility.SetKeyLeftTangentMode(curve, key, AnimationUtility.TangentMode.Linear);
                            AnimationUtility.SetKeyRightTangentMode(curve, key, AnimationUtility.TangentMode.Linear);
                        }

                        AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(entry.Key, typeof(Transform), properties[k]), curve);
                    }

                var settings = AnimationUtility.GetAnimationClipSettings(clip);
                settings.startTime = 0;
                settings.stopTime = duration;
                settings.loopTime = clip.name == "Sleep_Loop";
                AnimationUtility.SetAnimationClipSettings(clip, settings);
                Debug.Log("Authored " + clip.name + ": fixed local limb lengths/scales; 61 FK samples. Native deformation/visual review required.");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(model);
            }
        }
    }
}
