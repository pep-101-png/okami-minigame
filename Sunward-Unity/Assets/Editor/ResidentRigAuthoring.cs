using System;
using System.Linq;
using System.IO;
using UnityEditor;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class ResidentRigAuthoring
    {
        const string Folder = "Assets/Sunward/Generated/Renovation/";
        static Transform Joint(Transform parent, string name, Vector3 p)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = p;
            return t;
        }

        public static void Build(GameObject npc, GameFlow game, int index, GameObject visualSource = null)
        {
            var old = npc.transform.Find("Resident · articulated skeleton");
            if (old)
                UnityEngine.Object.DestroyImmediate(old.gameObject);
            var filters = (visualSource ? visualSource : npc).GetComponentsInChildren<MeshFilter>(true);
            var root = Joint(npc.transform, "Resident · articulated skeleton", Vector3.zero);
            var hips = Joint(root, "Hips", new Vector3(0, .74f, 0));
            var spine = Joint(hips, "Spine", new Vector3(0, .46f, 0));
            var head = Joint(spine, "Head", new Vector3(0, .48f, 0));
            var bones = new Transform[13];
            bones[0] = hips;
            bones[1] = spine;
            bones[2] = head;
            var thighs = new Transform[2];
            var shins = new Transform[2];
            var feet = new Transform[2];
            var arms = new Transform[2];
            var forearms = new Transform[2];
            for (int i = 0; i < 2; i++)
            {
                string side = i == 0 ? "L" : "R";
                float sign = i == 0 ? -1 : 1;
                thighs[i] = Joint(hips, "Thigh." + side, new Vector3(sign * .14f, 0, 0));
                shins[i] = Joint(thighs[i], "Shin." + side, new Vector3(0, -.34f, 0));
                feet[i] = Joint(shins[i], "Foot." + side, new Vector3(0, -.335f, 0));
                arms[i] = Joint(spine, "Arm." + side, new Vector3(sign * .27f, .22f, 0));
                forearms[i] = Joint(arms[i], "Forearm." + side, new Vector3(sign * .16f, -.24f, 0));
                int k = i == 0 ? 3 : 6;
                bones[k] = thighs[i];
                bones[k + 1] = shins[i];
                bones[k + 2] = feet[i];
                bones[i == 0 ? 9 : 11] = arms[i];
                bones[i == 0 ? 10 : 12] = forearms[i];
            }

            int meshIndex = 0;
            foreach (var filter in filters)
            {
                var renderer = filter.GetComponent<MeshRenderer>();
                if (!renderer || !filter.sharedMesh)
                    continue;
                var mesh = UnityEngine.Object.Instantiate(filter.sharedMesh);
                mesh.name = "Resident-" + index + "-" + meshIndex;
                var vertices = mesh.vertices;
                var normals = mesh.normals;
                var toLocal = npc.transform.worldToLocalMatrix * filter.transform.localToWorldMatrix;
                Quaternion facing = visualSource ? Quaternion.identity : Quaternion.Euler(0, 180, 0);
                var weights = new BoneWeight[vertices.Length];
                for (int v = 0; v < vertices.Length; v++)
                {
                    vertices[v] = facing * toLocal.MultiplyPoint3x4(vertices[v]);
                    if (normals.Length == vertices.Length)
                        normals[v] = facing * toLocal.MultiplyVector(normals[v]).normalized;
                    var p = vertices[v];
                    int a, b;
                    float w;
                    if (p.y > 1.58f)
                    {
                        a = 2;
                        b = 1;
                        w = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(1.58f, 1.70f, p.y));
                    }
                    else if (Mathf.Abs(p.x) > .29f && p.y > .80f && p.y < 1.58f)
                    {
                        a = p.x < 0 ? 9 : 11;
                        b = a + 1;
                        w = Mathf.InverseLerp(.95f, 1.4f, p.y);
                    }
                    else if (p.y > .85f)
                    {
                        a = 1;
                        b = 0;
                        w = Mathf.InverseLerp(.85f, 1.2f, p.y);
                    }
                    else if (p.y > .63f)
                    {
                        a = 0;
                        b = p.x < 0 ? 3 : 6;
                        w = Mathf.InverseLerp(.63f, .85f, p.y);
                    }
                    else
                    {
                        int leg = p.x < 0 ? 3 : 6;
                        a = p.y < .13f ? leg + 2 : leg + 1;
                        b = leg;
                        w = p.y < .13f ? 1 : 1 - Mathf.InverseLerp(.30f, .63f, p.y);
                    }

                    weights[v] = new BoneWeight
                    {
                        boneIndex0 = a,
                        weight0 = w,
                        boneIndex1 = b,
                        weight1 = 1 - w
                    };
                }

                mesh.vertices = vertices;
                mesh.normals = normals;
                mesh.boneWeights = weights;
                mesh.bindposes = bones.Select(b => b.worldToLocalMatrix * root.localToWorldMatrix).ToArray();
                mesh.RecalculateBounds();
                string path = Folder + "Resident-" + index + "-" + (meshIndex++) + ".asset";
                var saved = AssetDatabase.LoadAssetAtPath<Mesh>(path);
                if (saved)
                {
                    EditorUtility.CopySerialized(mesh, saved);
                    UnityEngine.Object.DestroyImmediate(mesh);
                    EditorUtility.SetDirty(saved);
                }
                else
                {
                    AssetDatabase.CreateAsset(mesh, path);
                    saved = mesh;
                }

                var skin = new GameObject("Skinned · " + filter.name).AddComponent<SkinnedMeshRenderer>();
                skin.transform.SetParent(root, false);
                skin.sharedMesh = saved;
                skin.sharedMaterials = renderer.sharedMaterials;
                skin.bones = bones;
                skin.rootBone = hips;
                skin.localBounds = new Bounds(new Vector3(0, 1.1f, 0), new Vector3(1.8f, 2.8f, 1.4f));
                skin.quality = SkinQuality.Bone4;
                renderer.enabled = false;
            }

            var pose = npc.GetComponent<ResidentLocomotion>();
            if (!pose)
                pose = npc.AddComponent<ResidentLocomotion>();
            pose.game = game;
            pose.hips = hips;
            pose.spine = spine;
            pose.head = head;
            pose.thighs = thighs;
            pose.shins = shins;
            pose.feet = feet;
            pose.arms = arms;
            pose.forearms = forearms;
            pose.stallkeeper = index < 2;
            pose.footstep = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Sunward/Audio/resident-footstep.wav");
            var source = npc.GetComponent<AudioSource>();
            if (!source)
                source = npc.AddComponent<AudioSource>();
            source.playOnAwake = false;
            source.spatialBlend = 1;
            source.minDistance = 1;
            source.maxDistance = 12;
            pose.stepSource = source;
            var resident = npc.GetComponent<VillageResident>();
            resident.stallkeeper = index < 2;
            if (index == 2)
                resident.route = new[]
                {
                    new Vector3(-1.7f, 0, 8),
                    new Vector3(-1.7f, 0, 3),
                    new Vector3(1.7f, 0, 3),
                    new Vector3(1.7f, 0, 8),
                    npc.transform.position
                };
            if (index == 3)
                resident.route = new[]
                {
                    new Vector3(-1.8f, 0, -3),
                    new Vector3(1.8f, 0, -3),
                    new Vector3(1.8f, 0, 3),
                    new Vector3(-1.8f, 0, 3)
                };
            EditorUtility.SetDirty(pose);
            EditorUtility.SetDirty(resident);
        }
    }
}
