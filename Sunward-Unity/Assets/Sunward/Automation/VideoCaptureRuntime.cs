#if UNITY_EDITOR
using System;
using System.IO;
using UnityEngine;
namespace Sunward.Editor.Automation
{
    // These editor-only behaviours live outside Editor so Unity can attach them in Play Mode.
    // The entire implementation is excluded from player builds; no saved scene uses them.
    public static class VideoCaptureRuntime
    {
        public const string ScenePath="Assets/Sunward/Scenes/Windflower.unity";
        public static string Output {
            get {
                if (Environment.GetEnvironmentVariable("SUNWARD_AUTOMATION_READONLY")!="1" || !File.Exists(Path.Combine(Application.dataPath,"..",".sunward-automation-snapshot"))) throw new InvalidOperationException("Isolated automation snapshot required.");
                string path=Environment.GetEnvironmentVariable("SUNWARD_AUTOMATION_OUTPUT");
                if (string.IsNullOrWhiteSpace(path)||!Path.IsPathRooted(path)) throw new InvalidOperationException("Absolute video output required.");
                Directory.CreateDirectory(path);return path;
            }
        }
    }
}
#endif
