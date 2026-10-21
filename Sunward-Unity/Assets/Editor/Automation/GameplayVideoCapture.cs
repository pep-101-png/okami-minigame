using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
namespace Sunward.Editor.Automation
{
    [InitializeOnLoad]
    public static class GameplayVideoCapture
    {
        const string Pending = "SunwardGameplayVideoPending";
        static readonly System.Diagnostics.Stopwatch timer = System.Diagnostics.Stopwatch.StartNew();
        static GameplayVideoCapture()
        {
            if (AutomationIsolation.Enabled && SessionState.GetBool(Pending,false)) EditorApplication.update += Attach;
        }
        public static void Run()
        {
            _ = BatchValidation.Output;
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) { Fail("No graphics device; no gameplay video was rendered."); return; }
            SessionState.SetBool(Pending,true);
            EditorSceneManager.OpenScene(BatchValidation.ScenePath,OpenSceneMode.Single);
            EditorApplication.update -= Attach; EditorApplication.update += Attach;
            EditorApplication.EnterPlaymode();
        }
        static void Attach()
        {
            if (timer.Elapsed.TotalSeconds > 120) { Fail("Video Play Mode startup timed out."); return; }
            if (!EditorApplication.isPlaying || !Application.isPlaying) return;
            EditorApplication.update -= Attach;
            SessionState.SetBool(Pending,false);
            var host = new GameObject("Sunward isolated gameplay video driver");
            UnityEngine.Object.DontDestroyOnLoad(host);
            var driver = host.AddComponent<VideoCaptureDriver>();
            host.AddComponent<VideoFrameWriter>().driver = driver;
            driver.Initialize();
        }
        static void Fail(string error)
        {
            EditorApplication.update -= Attach; SessionState.SetBool(Pending,false);
            try { File.WriteAllText(Path.Combine(BatchValidation.Output,"video-capture.json"),JsonUtility.ToJson(new VideoCaptureDriver.Campaign { status="unavailable", error=error },true)); }
            finally { EditorApplication.Exit(2); }
        }
    }
}
