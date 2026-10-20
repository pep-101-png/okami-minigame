using UnityEditor;

namespace Sunward.Editor
{
    // Applied before Unity's default importers try to construct legacy FBX materials.
    // This policy only affects the copied Unity assets, never the source wolf.
    public sealed class SunwardImportPolicy : AssetPostprocessor
    {
        public override uint GetVersion() => 3;
        void OnPreprocessModel()
        {
            if (assetPath.StartsWith("Assets/Sunward/Models/Remake/"))
            {
                var staticModel = (ModelImporter)assetImporter;
                staticModel.materialImportMode = ModelImporterMaterialImportMode.None;
                staticModel.importAnimation = false;
                staticModel.isReadable = true;
                return;
            }

            if (assetPath != "Assets/Sunward/Models/Amaterasu.fbx")
                return;
            var model = (ModelImporter)assetImporter;
            model.materialImportMode = ModelImporterMaterialImportMode.None;
        }

        static bool repairQueued;
        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            if (System.Array.IndexOf(imported, WolfClipProcessor.Source) < 0 || repairQueued)
                return;
            repairQueued = true;
            EditorApplication.delayCall += RepairAfterImport;
        }

        static void RepairAfterImport()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorApplication.delayCall += RepairAfterImport;
                return;
            }

            repairQueued = false;
            if (!EditorApplication.isPlayingOrWillChangePlaymode && System.IO.File.Exists(WolfClipProcessor.Controller))
                WolfClipProcessor.RepairExisting();
        }

        void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith("Assets/Sunward/Textures/") || !assetPath.EndsWith(".png", System.StringComparison.OrdinalIgnoreCase))
                return;
            var texture = (TextureImporter)assetImporter;
            texture.textureType = TextureImporterType.Default;
            texture.textureShape = TextureImporterShape.Texture2D;
            bool normalData = (assetPath.Contains("/Art/") || assetPath.Contains("/Remake/")) && assetPath.EndsWith("-normal.png", System.StringComparison.OrdinalIgnoreCase);
            texture.sRGBTexture = !normalData;
            if (normalData)
                texture.textureCompression = TextureImporterCompression.Uncompressed;
            texture.wrapMode = UnityEngine.TextureWrapMode.Repeat;
            texture.filterMode = UnityEngine.FilterMode.Trilinear;
            texture.anisoLevel = 4;
            texture.npotScale = TextureImporterNPOTScale.None;
            if (assetPath.Contains("/Wolf-"))
                texture.textureCompression = TextureImporterCompression.Uncompressed;
        }
    }
}
