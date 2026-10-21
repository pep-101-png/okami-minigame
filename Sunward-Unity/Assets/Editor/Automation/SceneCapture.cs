using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Sunward.Editor.Automation
{
    public static class SceneCapture
    {
        [Serializable] public class View { public string name, status, detail, file; public Vector3 cameraPosition, focus; }
        [Serializable] public class Report
        {
            public string status = "running", device, unityVersion;
            public string scope = "Windflower edit-mode scene renders and fixed animation samples; no Play Mode, motion quality or artistic approval";
            public List<View> views = new List<View>();
        }
        static Report report;
        static Camera camera;
        static string output;
        static System.Diagnostics.Stopwatch startup;
        public static void Run()
        {
            _ = BatchValidation.Output;
            EditorSceneManager.OpenScene(BatchValidation.ScenePath, OpenSceneMode.Single);
            startup = System.Diagnostics.Stopwatch.StartNew();
            EditorApplication.update -= WaitForPipeline;
            EditorApplication.update += WaitForPipeline;
        }
        static void WaitForPipeline()
        {
            if (RenderPipelineManager.currentPipeline == null && SystemInfo.graphicsDeviceType != GraphicsDeviceType.Null && startup.Elapsed.TotalSeconds < 30) {
                EditorApplication.QueuePlayerLoopUpdate(); SceneView.RepaintAll(); return;
            }
            EditorApplication.update -= WaitForPipeline;
            CaptureNow();
        }
        static void CaptureNow()
        {
            report = new Report { device = SystemInfo.graphicsDeviceType.ToString(), unityVersion = Application.unityVersion };
            int code = 2;
            try {
                output = Path.Combine(BatchValidation.Output, "screenshots"); Directory.CreateDirectory(output);
                if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) throw new NotSupportedException("No graphics device; screenshots were NOT rendered.");
                EditorSceneManager.OpenScene(BatchValidation.ScenePath, OpenSceneMode.Single);
                var original = Camera.main;
                if (!original) throw new Exception("Gameplay camera missing.");
                camera = new GameObject("Automation temporary capture camera").AddComponent<Camera>();
                camera.CopyFrom(original); camera.transform.SetPositionAndRotation(original.transform.position, original.transform.rotation);
                camera.enabled = false;
                var data = camera.GetUniversalAdditionalCameraData();
                var originalData = original.GetComponent<UniversalAdditionalCameraData>();
                if (originalData) EditorUtility.CopySerialized(originalData, data);
                Capture("gameplay-camera-editmode", null, Vector3.zero);
                var wolf = UnityEngine.Object.FindFirstObjectByType<Sunward.WolfAnimation>();
                if (!wolf || !wolf.animator) throw new Exception("Existing scene Amaterasu/Animator missing.");
                Bounds bounds = BoundsOf(wolf.gameObject);
                Capture("amaterasu-front", bounds, new Vector3(.3f,.2f,1));
                Capture("amaterasu-side", bounds, new Vector3(1,.15f,.2f));
                foreach (string state in new[] { "Idle_Natural", "Walk_Natural", "Sprint_Fluid", "Thrust" }) {
                    var clip = wolf.animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == state);
                    if (!clip) { report.views.Add(new View { name = state, status = "failed", detail = "Existing clip missing" }); continue; }
                    AnimationMode.StartAnimationMode();
                    try {
                        AnimationMode.BeginSampling();
                        try { AnimationMode.SampleAnimationClip(wolf.animator.gameObject, clip, clip.length * .25f); }
                        finally { AnimationMode.EndSampling(); }
                        Capture("pose-" + state + "-quarter", BoundsOf(wolf.gameObject), new Vector3(1,.25f,.35f));
                    } finally { AnimationMode.StopAnimationMode(); }
                }
                CaptureTarget("architecture", "house|roof|shoji", false);
                CaptureTarget("vegetation-terrain", "pine|cherry|maple|tree|terrain", false);
                CaptureTarget("river-water", "Brush River|Garden Pond", true);
                Capture("lighting-shadows-wide", new Bounds(wolf.transform.position + Vector3.up * 2, new Vector3(24,8,24)), new Vector3(1,1,1));
                report.status = report.views.Count >= 10 && report.views.All(v => v.status == "rendered_unreviewed") ? "passed" : "incomplete";
                code = report.status == "passed" ? 0 : 2;
            } catch (Exception e) { report.status = "unavailable_or_failed"; report.views.Add(new View { name = "capture", status = "failed", detail = e.ToString() }); Debug.LogException(e); }
            finally {
                if (AnimationMode.InAnimationMode()) AnimationMode.StopAnimationMode();
                if (camera) UnityEngine.Object.DestroyImmediate(camera.gameObject);
                try { File.WriteAllText(Path.Combine(BatchValidation.Output, "capture.json"), JsonUtility.ToJson(report, true)); }
                finally { EditorApplication.Exit(code); }
            }
        }
        static Bounds BoundsOf(GameObject root)
        {
            var renderers = root.GetComponentsInChildren<Renderer>(true).Where(r => r.enabled && r.gameObject.activeInHierarchy).ToArray();
            if (renderers.Length == 0) throw new Exception("No visible renderers: " + root.name);
            var b = renderers[0].bounds; foreach (var r in renderers.Skip(1)) b.Encapsulate(r.bounds); return b;
        }
        static void CaptureTarget(string name, string pattern, bool shader)
        {
            var selected = UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)
                .Where(r => r.enabled && r.gameObject.activeInHierarchy &&
                    System.Text.RegularExpressions.Regex.IsMatch(shader ? string.Join(" ", r.sharedMaterials.Where(m => m && m.shader).Select(m => m.shader.name)) : r.name, pattern, System.Text.RegularExpressions.RegexOptions.IgnoreCase))
                .OrderBy(r => Hierarchy(r.transform), StringComparer.Ordinal).FirstOrDefault();
            if (!selected) { report.views.Add(new View { name = name, status = "not_captured", detail = "No matching existing scene target" }); return; }
            Capture(name, BoundsOf(selected.gameObject), new Vector3(1,.65f,1));
        }
        static string Hierarchy(Transform t) => t.parent ? Hierarchy(t.parent) + "/" + t.name : t.name;
        static void Capture(string name, Bounds? subject, Vector3 direction)
        {
            var view = new View { name = name, status = "failed" }; report.views.Add(view);
            RenderTexture rt = null; Texture2D image = null; var previous = RenderTexture.active;
            try {
                if (subject.HasValue) {
                    var b = subject.Value; view.focus = b.center;
                    float radius = Mathf.Max(.5f, b.extents.magnitude);
                    float distance = radius / Mathf.Sin(camera.fieldOfView * Mathf.Deg2Rad * .5f) * 1.15f;
                    camera.transform.SetPositionAndRotation(b.center + direction.normalized * distance, Quaternion.LookRotation(-direction.normalized));
                }
                view.cameraPosition = camera.transform.position;
                rt = new RenderTexture(1280,720,24,RenderTextureFormat.ARGB32); rt.Create();
                var request = new UniversalRenderPipeline.SingleCameraRequest { destination = rt };
                if (!RenderPipeline.SupportsRenderRequest(camera, request)) throw new NotSupportedException("URP render request not supported in this environment.");
                Shader.SetGlobalVector("_Time", Vector4.zero);
                RenderPipeline.SubmitRenderRequest(camera, request);
                RenderTexture.active = rt;
                image = new Texture2D(1280,720,TextureFormat.RGB24,false);
                image.ReadPixels(new Rect(0,0,1280,720),0,0); image.Apply();
                var pixels = image.GetPixels32(); int variation = 0; var first = pixels[0];
                foreach (var p in pixels) variation = Math.Max(variation, Math.Max(Math.Abs(p.r-first.r), Math.Max(Math.Abs(p.g-first.g), Math.Abs(p.b-first.b))));
                if (variation < 3) throw new Exception("Capture is nearly uniform; cannot claim a usable render.");
                view.file = name + ".png"; File.WriteAllBytes(Path.Combine(output,view.file),UnityEngine.ImageConversion.EncodeToPNG(image));
                view.status = "rendered_unreviewed";
            } catch (Exception e) { view.detail = e.ToString(); }
            finally { RenderTexture.active = previous; if (rt) { rt.Release(); UnityEngine.Object.DestroyImmediate(rt); } if (image) UnityEngine.Object.DestroyImmediate(image); }
        }
    }
}
