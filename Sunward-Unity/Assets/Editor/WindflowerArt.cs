using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class WindflowerArt
    {
        public const string Root = "Assets/Sunward/Textures/Art/";
        public static string Family(PaintData data) => SurfaceArtRules.Family(data);
        public static Texture2D Load(string family, bool normal = false)
        {
            string path = Root + "Paint-" + family + (normal ? "-normal" : "") + ".png";
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (!texture)
                throw new InvalidDataException("Missing connected Windflower artwork: " + path);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            if (importer.textureShape != TextureImporterShape.Texture2D || importer.sRGBTexture == normal)
                throw new InvalidDataException("Wrong colour space/type for " + path + ". Reimport its Art folder.");
            return texture;
        }

        public static void Apply(Material material, PaintData data)
        {
            string family = Family(data);
            if (family == null)
                return;
            material.SetTexture("_DetailMap", Load(family));
            material.SetTexture("_DetailNormal", Load(family, true));
            material.SetFloat("_ArtStrength", family == "plaster" ? .55f : .86f);
            material.SetFloat("_ArtTiling", family == "roof" ? .45f : family == "wood" ? .55f : family == "meadow" ? .18f : .35f);
            material.SetFloat("_NormalStrength", family == "stone" ? .48f : family == "roof" ? .65f : .25f);
            material.SetFloat("_TerrainBlend", data.kind == "landscape" ? 1 : 0);
            if (data.kind == "landscape")
            {
                material.SetTexture("_PathMap", Load("path"));
                material.SetTexture("_PathNormal", Load("path", true));
            }
        }
    }
}
