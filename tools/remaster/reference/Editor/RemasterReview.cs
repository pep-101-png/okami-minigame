using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Sunward.Remaster.Editor
{
    // Explicit review commands only. No import callback, startup hook, build or save migration.
    public static class RemasterReview
    {
        public const string Root = "Assets/OkamiRemaster/Village";
        public const string Scene = Root + "/Demo/Scenes/VillageDemo.unity";

        [MenuItem("Sunward/Remaster/Open Village Review Scene")]
        public static void OpenVillage()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("Exit Play Mode before opening the separate village review scene.");
                return;
            }
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(Scene, OpenSceneMode.Single);
        }

        [Serializable] sealed class ReviewReport
        {
            public string scope = "Editor asset/reference checks only. Gameplay, motion and visual approval remain pending.";
            public string utc, unity, graphicsDevice;
            public string[] errors;
            public int materialsChecked, shadersChecked;
            public bool passedAssetChecks;
            public bool gameplayValidated = false;
        }

        [MenuItem("Sunward/Remaster/Validate Village Assets")]
        public static void ValidateVillageAssets()
        {
            ReviewReport report = new ReviewReport
            {
                utc = DateTime.UtcNow.ToString("o"), unity = Application.unityVersion,
                graphicsDevice = SystemInfo.graphicsDeviceType.ToString()
            };
            List<string> errors = new List<string>();
            if (!(UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset))
                errors.Add("The active renderer is not URP; the review shaders target Sunward's URP pipeline.");
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(Scene) == null) errors.Add("Village review scene is missing.");
            foreach (string guid in AssetDatabase.FindAssets("t:Material", new[] { Root }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
                ++report.materialsChecked;
                if (material == null || material.shader == null) { errors.Add("Missing shader: " + path); continue; }
                if (!material.shader.name.StartsWith("VillageDemo/", StringComparison.Ordinal)) errors.Add("Unexpected shader: " + path);
                foreach (string property in material.GetTexturePropertyNames())
                    if (property == "_MainTex" && material.GetTexture(property) == null) errors.Add("Missing painted texture: " + path);
            }
            foreach (string guid in AssetDatabase.FindAssets("t:Shader", new[] { Root }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                Shader shader = AssetDatabase.LoadAssetAtPath<Shader>(path);
                ++report.shadersChecked;
                if (shader == null || ShaderUtil.ShaderHasError(shader)) errors.Add("Shader import/compile error: " + path);
                // Messages cover compiled variants only; this is not full platform/variant coverage.
                if (shader != null)
                    foreach (var message in ShaderUtil.GetShaderMessages(shader))
                        if (message.severity.ToString() == "Error") errors.Add(path + ": " + message.message);
            }
            foreach (string key in new[] { "DemoGeometry/VillageWorld", "DemoGeometry/VillageHomes", "DemoGeometry/CollisionProxies", "DemoGeometry/StairRamps", "DemoGeometry/BlossomTrees", "Farm/Animals", "Farm/Layout" })
                if (Resources.Load<TextAsset>(key) == null) errors.Add("Missing resource: " + key);
            foreach (string key in new[] { "Farm/AnimalPaint", "Farm/HeartPaint", "Farm/PetalPaint0", "Farm/PetalPaint1", "Farm/PetalPaint2" })
                if (Resources.Load<Material>(key) == null) errors.Add("Missing material resource: " + key);
            if (Resources.Load<AudioClip>("Farm/PettingChime") == null) errors.Add("Missing petting chime.");
            report.errors = errors.ToArray(); report.passedAssetChecks = errors.Count == 0;
            string directory = Path.Combine("Library", "SunwardRemaster"); Directory.CreateDirectory(directory);
            string output = Path.Combine(directory, "village-asset-validation.json");
            File.WriteAllText(output, JsonUtility.ToJson(report, true));
            string summary = "Village asset checks: " + (report.passedAssetChecks ? "passed" : "failed") + ". " + output + ". Runtime/visual validation is still required.";
            if (report.passedAssetChecks) Debug.Log(summary); else Debug.LogError(summary + "\n" + string.Join("\n", errors));
        }
    }
}
