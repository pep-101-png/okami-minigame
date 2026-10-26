using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace SunwardVillageDemo.Editor
{
    public static class DemoBuild
    {
        public const string ScenePath = "Assets/Demo/Scenes/VillageDemo.unity";
        static string ProjectRoot { get { return Path.GetFullPath(Path.Combine(Application.dataPath, "..")); } }
        static void RequireSeparateDemo()
        {
            if (!File.Exists(Path.Combine(ProjectRoot, ".sunward-village-demo")) || PlayerSettings.productName != "Sunward Village Demo")
                throw new BuildFailedException("This builder runs only in the separate Sunward Village Demo project.");
        }
        [MenuItem("Village Demo/Open village scene")]
        public static void OpenScene() { RequireSeparateDemo(); EditorSceneManager.OpenScene(ScenePath); }
        [MenuItem("Village Demo/Build Windows player")]
        public static void BuildWindows()
        {
            RequireSeparateDemo();
            if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64))
                throw new BuildFailedException("Windows Standalone build support is missing from this Unity installation. Add it in Unity Hub.");
            string output = Path.Combine(ProjectRoot, "Build", "SunwardVillageDemo.exe"); Directory.CreateDirectory(Path.GetDirectoryName(output));
            BuildPlayerOptions options = new BuildPlayerOptions(); options.scenes = new[] { ScenePath }; options.locationPathName = output;
            options.target = BuildTarget.StandaloneWindows64; options.options = BuildOptions.None;
            BuildReport report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded) throw new BuildFailedException("Demo build failed: " + report.summary.result);
            Debug.Log("DEMO BUILD SUCCEEDED: " + output);
        }
        [InitializeOnLoadMethod]
        static void OpenFirstScene()
        {
            if (Application.isBatchMode || !File.Exists(Path.Combine(ProjectRoot, ".sunward-village-demo"))) return;
            EditorApplication.update += OpenWhenReady;
        }
        static void OpenWhenReady()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating) return;
            EditorApplication.update -= OpenWhenReady;
            if (string.IsNullOrEmpty(UnityEngine.SceneManagement.SceneManager.GetActiveScene().path)) EditorSceneManager.OpenScene(ScenePath);
            SceneView view = SceneView.lastActiveSceneView;
            if (view != null) view.LookAt(new Vector3(0, 2, 6), Quaternion.Euler(40, -30, 0), 42);
        }
    }
}
