using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Sunward.Editor.Automation
{
    [InitializeOnLoad]
    public static class GameplayCapture
    {
        const string Pending = "SunwardAutomationGameplayPending";
        static readonly System.Diagnostics.Stopwatch timer = System.Diagnostics.Stopwatch.StartNew();
        static int firstFrame = -1;
        [Serializable] public class Report
        {
            public string status = "unavailable_or_failed", error, graphics, file;
            public string scope = "Actual Windflower Play Mode camera after 30 fixed-time frames with isolated fresh save and input disabled. Camera render only; no UI, combat or artistic approval.";
            public int frame;
        }
        static GameplayCapture()
        {
            if (AutomationIsolation.Enabled && SessionState.GetBool(Pending,false)) EditorApplication.update += Tick;
        }
        public static void Run()
        {
            _ = BatchValidation.Output;
            EditorSceneManager.OpenScene(BatchValidation.ScenePath,OpenSceneMode.Single);
            SessionState.SetBool(Pending,true);
            EditorApplication.update -= Tick; EditorApplication.update += Tick;
            EditorApplication.EnterPlaymode();
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Pending,false)) return;
            if (timer.Elapsed.TotalSeconds > 120) { Finish(new Report { error = "Play Mode startup/capture timed out." }); return; }
            if (!EditorApplication.isPlaying || !Application.isPlaying) return;
            try {
                if (firstFrame < 0) {
                    firstFrame=Time.frameCount; Time.captureDeltaTime=1f/60f; UnityEngine.Random.InitState(0);
                    foreach (var device in InputSystem.devices) InputSystem.DisableDevice(device);
                }
                if (Time.frameCount - firstFrame < 30) return;
                var report=new Report { graphics=SystemInfo.graphicsDeviceType.ToString(),frame=Time.frameCount };
                if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) throw new NotSupportedException("No graphics device.");
                var camera=Camera.main;
                if (!camera || !UnityEngine.Object.FindFirstObjectByType<Sunward.GameFlow>()) throw new Exception("Live camera or GameFlow missing.");
                RenderTexture previous=RenderTexture.active;
                var rt=new RenderTexture(1280,720,24,RenderTextureFormat.ARGB32); rt.Create();
                var image=new Texture2D(1280,720,TextureFormat.RGB24,false);
                try {
                    var request=new UniversalRenderPipeline.SingleCameraRequest { destination=rt };
                    if (!RenderPipeline.SupportsRenderRequest(camera,request)) throw new NotSupportedException("URP render request unavailable.");
                    RenderPipeline.SubmitRenderRequest(camera,request); RenderTexture.active=rt;
                    image.ReadPixels(new Rect(0,0,1280,720),0,0); image.Apply();
                    var pixels=image.GetPixels32(); int variation=0; var first=pixels[0];
                    foreach (var pixel in pixels) variation=Math.Max(variation,Math.Max(Math.Abs(pixel.r-first.r),Math.Max(Math.Abs(pixel.g-first.g),Math.Abs(pixel.b-first.b))));
                    if (variation<3) throw new Exception("Nearly uniform capture; usable rendering not established.");
                    string folder=Path.Combine(BatchValidation.Output,"screenshots"); Directory.CreateDirectory(folder);
                    report.file="gameplay-live-camera.png"; File.WriteAllBytes(Path.Combine(folder,report.file),image.EncodeToPNG()); report.status="rendered_unreviewed";
                } finally { RenderTexture.active=previous; rt.Release(); UnityEngine.Object.DestroyImmediate(rt); UnityEngine.Object.DestroyImmediate(image); }
                Finish(report);
            } catch (Exception e) { Finish(new Report { error=e.ToString() }); }
        }
        static void Finish(Report report)
        {
            SessionState.SetBool(Pending,false); EditorApplication.update -= Tick;
            File.WriteAllText(Path.Combine(BatchValidation.Output,"gameplay-capture.json"),JsonUtility.ToJson(report,true));
            EditorApplication.Exit(report.status=="rendered_unreviewed"?0:2);
        }
    }
}
