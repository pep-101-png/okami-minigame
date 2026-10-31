using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Sunward.Editor.Automation
{
    public static class BatchValidation
    {
        public const string ScenePath = "Assets/Sunward/Scenes/Windflower.unity";
        [Serializable] public class Check { public string name, status, detail; }
        [Serializable] public class Report
        {
            public string status = "running", unityVersion, scene = ScenePath;
            public string scope = "Editor import/compilation/static validation; not a Play Mode or visual approval";
            public List<Check> checks = new List<Check>();
            public List<string> logErrors = new List<string>();
        }
        public static string Output
        {
            get
            {
                if (!File.Exists(".sunward-automation-snapshot")) throw new InvalidOperationException("Runner snapshot marker required; never invoke against the live project.");
                if (!AutomationIsolation.Enabled) throw new InvalidOperationException("Automation entry points require an isolated runner snapshot.");
                string path = Environment.GetEnvironmentVariable("SUNWARD_AUTOMATION_OUTPUT");
                if (string.IsNullOrWhiteSpace(path) || !Path.IsPathRooted(path)) throw new InvalidOperationException("Absolute output path required.");
                Directory.CreateDirectory(path);
                return path;
            }
        }
        static void CheckOne(Report report, string name, Action action)
        {
            Debug.Log("SUNWARD CHECK START: " + name);
            try { action(); report.checks.Add(new Check { name = name, status = "passed" }); }
            catch (Exception e) { report.checks.Add(new Check { name = name, status = "failed", detail = e.ToString() }); Debug.LogException(e); }
        }
        public static void Run()
        {
            var report = new Report { unityVersion = Application.unityVersion };
            int code = 1;
            Application.LogCallback logger = (message, trace, type) => {
                if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert) report.logErrors.Add(message + "\n" + trace);
            };
            Application.logMessageReceived += logger;
            try
            {
                _ = Output;
                CheckOne(report, "version", () => { if (Application.unityVersion != "6000.6.6f1") throw new Exception("Wrong editor version."); });
                CheckOne(report, "Windflower scene", () => {
                    if (!File.Exists(ScenePath)) throw new FileNotFoundException(ScenePath);
                    EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
                    if (!UnityEngine.Object.FindFirstObjectByType<Sunward.GameFlow>()) throw new Exception("Playable GameFlow missing.");
                });
                CheckOne(report, "missing scripts/references", CheckReferences);
                CheckOne(report, "scene dependencies", () => {
                    foreach (string path in AssetDatabase.GetDependencies(ScenePath, true))
                        if (path.StartsWith("Assets/") && !File.Exists(path)) throw new FileNotFoundException("Missing scene dependency", path);
                });
                CheckOne(report, "serialized asset GUID references", () => {
                    var extensions = new HashSet<string> { ".unity", ".prefab", ".mat", ".controller" };
                    foreach (string path in Directory.EnumerateFiles("Assets/Sunward", "*", SearchOption.AllDirectories).Where(p => extensions.Contains(Path.GetExtension(p))))
                        foreach (System.Text.RegularExpressions.Match match in System.Text.RegularExpressions.Regex.Matches(File.ReadAllText(path), @"guid:\s*([0-9a-f]{32})")) {
                            string guid = match.Groups[1].Value;
                            if (!guid.StartsWith("0000000000000000") && string.IsNullOrEmpty(AssetDatabase.GUIDToAssetPath(guid))) throw new Exception("Unresolved GUID " + guid + " in " + path);
                        }
                });
                CheckOne(report, "material shaders", () => {
                    foreach (string guid in AssetDatabase.FindAssets("t:Material", new[] { "Assets/Sunward", "Assets/OkamiRemaster/Original", "Assets/OkamiRemaster/Player" })) {
                        var material = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                        if (!material || !material.shader || material.shader.name == "Hidden/InternalErrorShader" || ShaderUtil.ShaderHasError(material.shader))
                            throw new Exception("Missing/broken shader: " + AssetDatabase.GUIDToAssetPath(guid));
                    }
                    foreach (string guid in AssetDatabase.FindAssets("t:Shader", new[] { "Assets/Sunward", "Assets/OkamiRemaster/Original", "Assets/OkamiRemaster/Player" })) {
                        var shader = AssetDatabase.LoadAssetAtPath<Shader>(AssetDatabase.GUIDToAssetPath(guid));
                        if (!shader || ShaderUtil.ShaderHasError(shader)) throw new Exception("Shader import errors: " + AssetDatabase.GUIDToAssetPath(guid));
                    }
                });
                CheckOne(report, "Amaterasu 74-bone hierarchy / 47 clips", () => {
                    const string source = "Assets/Sunward/Models/Amaterasu.fbx";
                    var model = AssetDatabase.LoadAssetAtPath<GameObject>(source);
                    if (!model) throw new Exception("Amaterasu source missing.");
                    var rig = model.GetComponentsInChildren<Transform>(true).Single(t => t.name == "WOLF_RIG");
                    if (rig.GetComponentsInChildren<Transform>(true).Count(t => t.name.StartsWith("CTRL_") || t.name.StartsWith("DEF_") || t.name.StartsWith("MCH_")) != 74) throw new Exception("Expected 74 rig bones; inspect import hierarchy before changing the baseline.");
                    if (AssetDatabase.LoadAllAssetsAtPath(source).OfType<AnimationClip>().Count(c => !c.name.StartsWith("__preview__")) != 47) throw new Exception("Expected 47 source clips.");
                    if (AssetDatabase.FindAssets("t:AnimationClip", new[] { WolfClipProcessor.Folder }).Length != 47) throw new Exception("Expected 47 native animation assets.");
                });
                // Existing validators are reused; builders/repair methods are NEVER invoked.
                CheckOne(report, "existing imported-project checks", SunwardValidation.Validate);
                CheckOne(report, "existing animation-scale checks", WolfClipProcessor.ValidateScale);
                CheckOne(report, "existing scene connection checks", WindflowerDiagnostics.Connections);
                CheckOne(report, "existing scene bounds checks", WindflowerDiagnostics.BoundsAudit);
                CheckOne(report, "existing village checks", VillageOverhaulValidation.Validate);
                report.status = report.checks.All(c => c.status == "passed") && report.logErrors.Count == 0 ? "passed" : "failed";
                code = report.status == "passed" ? 0 : 1;
            }
            catch (Exception e) { report.status = "failed"; report.checks.Add(new Check { name = "entry", status = "failed", detail = e.ToString() }); Debug.LogException(e); }
            finally
            {
                Application.logMessageReceived -= logger;
                try { File.WriteAllText(Path.Combine(Output, "validation.json"), JsonUtility.ToJson(report, true)); }
                finally { EditorApplication.Exit(code); }
            }
        }
        [Serializable] public class BuildSummary { public string status, result, platform, error; public ulong bytes; public int errors, warnings; }
        public static void Build()
        {
            var summary = new BuildSummary { status = "failed", platform = "StandaloneWindows64" };
            int code = 1;
            try {
                string directory = Path.Combine(Output, "build"); Directory.CreateDirectory(directory);
                if (!File.Exists(ScenePath)) throw new FileNotFoundException(ScenePath);
                var build = BuildPipeline.BuildPlayer(new[] { ScenePath }, Path.Combine(directory, "Sunward.exe"), BuildTarget.StandaloneWindows64, BuildOptions.Development);
                summary.result = build.summary.result.ToString(); summary.bytes = build.summary.totalSize;
                summary.errors = (int)build.summary.totalErrors; summary.warnings = (int)build.summary.totalWarnings;
                if (build.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded) { summary.status = "passed"; code = 0; }
            } catch (Exception e) { summary.error = e.ToString(); Debug.LogException(e); }
            finally { try { File.WriteAllText(Path.Combine(Output,"build-summary.json"),JsonUtility.ToJson(summary,true)); } finally { EditorApplication.Exit(code); } }
        }
        static void CheckReferences()
        {
            foreach (var go in Resources.FindObjectsOfTypeAll<GameObject>().Where(g => g.scene.IsValid())) CheckObject(go);
            foreach (string guid in AssetDatabase.FindAssets("t:Prefab", new[] { "Assets/Sunward" })) {
                var root = AssetDatabase.LoadAssetAtPath<GameObject>(AssetDatabase.GUIDToAssetPath(guid));
                if (!root) throw new Exception("Missing prefab " + guid);
                foreach (var t in root.GetComponentsInChildren<Transform>(true)) CheckObject(t.gameObject);
            }
        }
        static void CheckObject(GameObject go)
        {
            if (GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(go) > 0) throw new Exception("Missing script: " + go.name);
            foreach (var component in go.GetComponents<Component>()) {
                if (!component) throw new Exception("Missing component: " + go.name);
                using (var serialized = new SerializedObject(component)) {
                    var property = serialized.GetIterator();
                    while (property.Next(true))
                        if (property.propertyType == SerializedPropertyType.ObjectReference && property.objectReferenceValue == null && property.objectReferenceEntityIdValue != EntityId.None)
                            throw new Exception("Broken reference: " + go.name + "/" + property.propertyPath);
                }
            }
        }
    }
}
