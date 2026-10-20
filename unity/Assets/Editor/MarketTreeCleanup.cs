using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Sunward;

namespace Sunward.Editor
{
    [InitializeOnLoad]
    public static class MarketTreeCleanup
    {
        const string ScenePath = "Assets/Sunward/Scenes/Windflower.unity";
        const string Marker = "Market · misplaced tree removal";
        static MarketTreeCleanup()
        {
            EditorApplication.delayCall += Automatic;
            EditorSceneManager.sceneOpened += (s, m) => EditorApplication.delayCall += Automatic;
            EditorSceneManager.activeSceneChangedInEditMode += (a, b) => EditorApplication.delayCall += Automatic;
        }

        static void Automatic()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorApplication.delayCall += Automatic;
                return;
            }

            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorSceneManager.GetActiveScene().path != ScenePath)
                return;
            // No previous environment-version marker can suppress this scan.
            // In particular, look at ALL scene roots, not just the generated town.
            if (Candidates(EditorSceneManager.GetActiveScene()).Count == 0)
                return;
            try
            {
                Apply();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        static List<GameObject> Candidates(Scene scene)
        {
            var result = new HashSet<GameObject>();
            foreach (var sceneRoot in scene.GetRootGameObjects())
                foreach (var filter in sceneRoot.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (!filter.gameObject.activeInHierarchy || !filter.sharedMesh)
                        continue;
                    Transform owner = filter.transform;
                    bool named = MarketTreeRules.TreeMesh(filter.sharedMesh.name), namedOwner = false;
                    for (var p = filter.transform; p; p = p.parent)
                        if (MarketTreeRules.TreeOwner(p.name))
                        {
                            if (!namedOwner || MarketTreeRules.KnownFamily(p.name))
                            {
                                owner = p;
                                namedOwner = true;
                            }

                            named = true;
                        }

                    if (!named)
                        continue;
                    var renderers = owner.GetComponentsInChildren<Renderer>(true);
                    if (renderers.Length == 0)
                        continue;
                    var b = renderers[0].bounds;
                    foreach (var r in renderers.Skip(1))
                        b.Encapsulate(r.bounds);
                    if (MarketTreeRules.InMarket(owner.position, b))
                        result.Add(owner.gameObject);
                }

            return result.Where(go => !result.Any(parent => parent != go && go.transform.IsChildOf(parent.transform))).ToList();
        }

        [MenuItem("Sunward/Remove Misplaced Market Tree")]
        public static void Apply()
        {
            var scene = EditorSceneManager.GetActiveScene();
            if (EditorApplication.isPlayingOrWillChangePlaymode || scene.path != ScenePath)
                throw new InvalidOperationException("Open Windflower outside Play Mode.");
            var matches = Candidates(scene);
            if (matches.Count == 0)
            {
                Debug.LogWarning("Market tree scan found no recognised active tree. Removal is NOT confirmed for an unrecognised object. Select the remaining tree and report its Hierarchy name.");
                return;
            }

            Directory.CreateDirectory("Review/LocalBackups");
            EditorSceneManager.SaveScene(scene);
            File.Copy(ScenePath, "Review/LocalBackups/Windflower-before-market-tree-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + ".unity", true);
            var marker = scene.GetRootGameObjects().FirstOrDefault(go => go.name == Marker);
            if (!marker)
            {
                marker = new GameObject(Marker);
                SceneManager.MoveGameObjectToScene(marker, scene);
            }

            var state = marker.GetComponent<EnvironmentReviewState>();
            if (!state)
                state = marker.AddComponent<EnvironmentReviewState>();
            var hidden = (state.suppressed ?? Array.Empty<GameObject>()).Where(go => go).ToList();
            var positions = (state.removedObstacles ?? Array.Empty<Vector3>()).ToList();
            var report = new List<string>
            {
                "Scene-wide market tree cleanup. No geometry, material or game rebuild.",
                "Matched actual meshes/owners; not dependent on material colours or the town parent."
            };
            foreach (var tree in matches)
            {
                string path = tree.name;
                for (var p = tree.transform.parent; p; p = p.parent)
                    path = p.name + "/" + path;
                var meshes = tree.GetComponentsInChildren<MeshFilter>(true).Where(f => f.sharedMesh).Select(f => f.sharedMesh.name);
                string line = path + " | position " + tree.transform.position + " | meshes " + string.Join(", ", meshes);
                report.Add(line);
                positions.Add(tree.transform.position);
                hidden.Add(tree);
                Undo.RecordObject(tree, "Remove misplaced market tree");
                tree.SetActive(false);
                EditorUtility.SetDirty(tree);
                Debug.Log("Removed market tree instance: " + line, tree);
            }

            // Independent source-world colliders are not always children of a tree.
            foreach (var sceneRoot in scene.GetRootGameObjects())
                foreach (var c in sceneRoot.GetComponentsInChildren<CapsuleCollider>(true))
                    if (c.name == "Trunk / rock collider" && positions.Any(p => Mathf.Abs(p.x - c.transform.position.x) < .4f && Mathf.Abs(p.z - c.transform.position.z) < .4f))
                    {
                        Undo.RecordObject(c, "Remove tree collision");
                        c.enabled = false;
                        EditorUtility.SetDirty(c);
                    }

            state.suppressed = hidden.Distinct().ToArray();
            state.removedObstacles = positions.Distinct().ToArray();
            state.complete = true;
            EditorUtility.SetDirty(state);
            if (Candidates(scene).Count != 0)
                throw new InvalidDataException("A recognised market tree is still active; scene was not marked repaired.");
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            File.WriteAllLines("Review/market-tree-removal.txt", report);
            Debug.Log("Market tree removal saved: " + matches.Count + " instance(s). Exact names are listed above and in Review/market-tree-removal.txt. No other environment rebuild was run.");
        }
    }
}
