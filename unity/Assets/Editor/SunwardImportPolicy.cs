using UnityEditor;

namespace Sunward.Editor
{
    // Applied before Unity's default importers try to construct legacy FBX materials.
    // This policy only affects the copied Unity assets, never the source wolf.
    public sealed class SunwardImportPolicy : AssetPostprocessor
    {
        public override uint GetVersion() => 1;

        void OnPreprocessModel()
        {
            if (assetPath != "Assets/Sunward/Models/Amaterasu.fbx") return;
            var model = (ModelImporter)assetImporter;
            model.materialImportMode = ModelImporterMaterialImportMode.None;
        }

        void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith("Assets/Sunward/Textures/") ||
                !assetPath.EndsWith(".png", System.StringComparison.OrdinalIgnoreCase)) return;
            var texture = (TextureImporter)assetImporter;
            texture.textureType = TextureImporterType.Default;
            texture.textureShape = TextureImporterShape.Texture2D;
            texture.sRGBTexture = true;
        }
    }
}
