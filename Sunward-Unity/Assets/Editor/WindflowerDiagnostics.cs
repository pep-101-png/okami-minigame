using System;
using System.Linq;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class WindflowerDiagnostics
    {
        static string Hierarchy(Transform t) => t.parent ? Hierarchy(t.parent) + "/" + t.name : t.name;
        [MenuItem("Sunward/Diagnose Invalid Mesh Bounds")]
        public static void BoundsAudit()
        {
            int bad = 0, checkedMeshes = 0;
            foreach (var renderer in Resources.FindObjectsOfTypeAll<Renderer>().Where(r => r.gameObject.scene.IsValid()))
            {
                var bounds = renderer.bounds;
                if (!MeshSafety.Finite(bounds.center) || !MeshSafety.Finite(bounds.size) || !MeshSafety.Finite(renderer.transform.lossyScale))
                {
                    Debug.LogError("Invalid renderer bounds: " + Hierarchy(renderer.transform) + " bounds=" + bounds + " scale=" + renderer.transform.lossyScale, renderer);
                    bad++;
                }

                var skin = renderer as SkinnedMeshRenderer;
                var filter = renderer.GetComponent<MeshFilter>();
                var mesh = skin ? skin.sharedMesh : filter ? filter.sharedMesh : null;
                if (!mesh)
                    continue;
                if (!MeshSafety.Finite(mesh.bounds.center) || !MeshSafety.Finite(mesh.bounds.size))
                {
                    Debug.LogError("Invalid mesh bounds: " + Hierarchy(renderer.transform) + " mesh='" + mesh.name + "' asset=" + AssetDatabase.GetAssetPath(mesh), renderer);
                    bad++;
                }

                if (mesh.isReadable)
                {
                    try
                    {
                        MeshSafety.Validate(Hierarchy(renderer.transform) + " / " + mesh.name, mesh.vertices, mesh.triangles);
                        checkedMeshes++;
                    }
                    catch (Exception error)
                    {
                        Debug.LogException(error, renderer);
                        bad++;
                    }
                }
            }

            if (bad > 0)
                throw new InvalidDataException(bad + " invalid mesh/renderer inputs identified above. These were not attributed automatically to the wolf scale.");
            Debug.Log("Loaded-scene bounds audit: " + checkedMeshes + " readable meshes checked, no invalid bounds found now. For a transient error reproduce it, then run this audit again.");
        }

        [MenuItem("Sunward/Verify Windflower Connections")]
        public static void Connections()
        {
            var home = UnityEngine.Object.FindFirstObjectByType<HomeCutaway>();
            var game = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
            if (!home || !game || !game.Combat)
                throw new InvalidDataException("Open the playable Windflower scene first.");
            var families = new HashSet<string>();
            int assigned = 0, water = 0;
            foreach (var renderer in Resources.FindObjectsOfTypeAll<Renderer>().Where(r => r.gameObject.scene == home.gameObject.scene))
                foreach (var material in renderer.sharedMaterials)
                {
                    if (material && AssetDatabase.GetAssetPath(material).StartsWith("Assets/OkamiRemaster/", System.StringComparison.Ordinal))
                    {
                        if (!material.shader || ShaderUtil.ShaderHasError(material.shader))
                            throw new InvalidDataException("Recovered scene material shader failed: " + Hierarchy(renderer.transform));
                    }
                    if (material && material.shader && material.shader.name.StartsWith("Sunward/Brush River", System.StringComparison.Ordinal))
                    {
                        if (!(material.GetTexture("_FlowMap") is Texture2D) || !(material.GetTexture("_FlowNormal") is Texture2D))
                            throw new InvalidDataException("Live river is missing painted current maps: " + Hierarchy(renderer.transform));
                        water++;
                    }

                    if (!material || !material.HasProperty("_ArtStrength") || material.GetFloat("_ArtStrength") <= .01f)
                        continue;
                    var texture = material.GetTexture("_DetailMap");
                    var normal = material.GetTexture("_DetailNormal");
                    if (!(texture is Texture2D) || !(normal is Texture2D))
                        throw new InvalidDataException("Artwork not assigned to actual scene renderer: " + Hierarchy(renderer.transform));
                    string asset = AssetDatabase.GetAssetPath(texture);
                    string family;
                    if (asset.StartsWith(WindflowerArt.Root))
                        family = Path.GetFileNameWithoutExtension(asset).Replace("Paint-", "");
                    else if (asset.StartsWith("Assets/Sunward/Textures/VillageFinish/"))
                    {
                        string painting = Path.GetFileNameWithoutExtension(asset);
                        family = painting == "Bark" ? "wood" : painting.StartsWith("Rock-") ? "stone" : "";
                        if (family == "") throw new InvalidDataException("Unexpected village-finish painting: " + asset);
                    }
                    else if (asset.StartsWith("Assets/Sunward/Textures/InkWorld/"))
                    {
                        string painting = Path.GetFileNameWithoutExtension(asset);
                        switch (painting)
                        {
                            case "Timber": family = "wood"; break;
                            case "Cliff": family = "stone"; break;
                            case "Roof":
                            case "RoofIndigo": family = "roof"; break;
                            case "Plaster": family = "plaster"; break;
                            case "Meadow": family = "meadow"; break;
                            case "Path": family = "path"; break;
                            default: throw new InvalidDataException("Unexpected ink-world painting: " + asset);
                        }
                    }
                    else if (asset.StartsWith("Assets/OkamiRemaster/Windflower/Textures/", System.StringComparison.Ordinal))
                    {
                        string painting = Path.GetFileNameWithoutExtension(asset).Replace("Recovered-", "");
                        switch (painting)
                        {
                            case "Timber":
                            case "Bark": family = "wood"; break;
                            case "Cliff": family = "stone"; break;
                            case "Roof":
                            case "RoofIndigo": family = "roof"; break;
                            case "Plaster": family = "plaster"; break;
                            case "Meadow": family = "meadow"; break;
                            case "Path": family = "path"; break;
                            default: throw new InvalidDataException("Unexpected recovered painting: " + asset);
                        }
                    }
                    else throw new InvalidDataException("Unexpected environment-art source: " + asset);
                    families.Add(family);
                    assigned++;
                }

            foreach (string family in new[]
            {
                "wood",
                "roof",
                "stone",
                "plaster",
                "meadow"
            }

            )
                if (!families.Contains(family))
                    throw new InvalidDataException("No live Windflower renderer uses new " + family + " artwork. Apply the artwork update first.");
            if (water == 0)
                throw new InvalidDataException("No live Windflower river uses the current shader/maps.");
            var animator = game.Player.animationView.animator;
            if (animator.runtimeAnimatorController.animationClips.Distinct().Count() != 47 || animator.runtimeAnimatorController.animationClips.Any(c => !AssetDatabase.GetAssetPath(c).StartsWith(WolfClipProcessor.Folder)))
                throw new InvalidDataException("Playable wolf still uses raw or missing clips.");
            if (!game.Combat.spear || !game.Combat.sundial || !game.Combat.headSocket)
                throw new InvalidDataException("Playable combat weapon/socket reference is missing.");
            if (!home.GetComponent<HomeWeaponRack>() || !home.GetComponent<HomeWeaponRack>().displays)
                throw new InvalidDataException("Home weapon display is disconnected.");
            if (!home.transform.Find("Windflower · painted architectural details"))
                throw new InvalidDataException("Architectural details are not in Windflower.");
            Debug.Log("Windflower connections verified: " + assigned + " renderer/material assignments use new artwork; 47 processed clips, both weapons, mouth socket, wall display and architectural details are linked. Rendering/Play Mode review is still required.");
        }
    }
}
