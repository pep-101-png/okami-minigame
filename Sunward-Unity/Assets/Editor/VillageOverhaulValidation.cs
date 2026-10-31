using System;
using System.Linq;
using UnityEditor;
using UnityEngine;
using Sunward;

namespace Sunward.Editor
{
    public static class VillageOverhaulValidation
    {
        [MenuItem("Sunward/Validate Village Overhaul")]
        public static void Validate()
        {
            var game = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
            if (!game)
                throw new InvalidOperationException("Open Windflower first.");
            if (game.npcObjects.All(n => n && n.GetComponent<Sunward.Remaster.OriginalActor>()))
            {
                OriginalRemakeValidation.Validate();
                return;
            }
            var home = UnityEngine.Object.FindFirstObjectByType<HomeCutaway>();
            var renovation = home.transform.Find(WindflowerRenovation.RootName);
            if (!renovation)
                throw new InvalidOperationException("Run Apply Windflower Repair and Artwork Update first.");
            if (!game.Player.GetComponent<WolfBodyCollision>())
                throw new InvalidOperationException("Wolf body sweep missing.");
            var mill = renovation.GetComponentInChildren<WaterMillMotion>();
            if (!mill || !mill.wheel || !mill.shaft || !mill.pinion || !mill.spindle || !mill.millstone || !mill.spray)
                throw new InvalidOperationException("Mill transmission/splash connections missing.");
            var audio = renovation.GetComponentInChildren<MarketSoundscape>();
            if (!audio || !audio.music || !audio.music.clip || !audio.market || !audio.market.clip)
                throw new InvalidOperationException("Market audio disconnected.");
            int skins = 0;
            foreach (var npc in game.npcObjects)
            {
                var pose = npc.GetComponent<ResidentLocomotion>();
                if (!pose || pose.thighs.Length != 2 || pose.shins.Any(t => !t) || pose.feet.Any(t => !t) || !pose.stepSource || !pose.footstep)
                    throw new InvalidOperationException("Resident rig/footstep disconnected: " + npc.name);
                foreach (var skin in pose.GetComponentsInChildren<SkinnedMeshRenderer>())
                {
                    if (skin.bones.Length != 13 || skin.sharedMesh.boneWeights.Length != skin.sharedMesh.vertexCount)
                        throw new InvalidOperationException("Skin weight count incorrect: " + skin.name);
                    foreach (var w in skin.sharedMesh.boneWeights)
                        if (Mathf.Abs(w.weight0 + w.weight1 + w.weight2 + w.weight3 - 1) > .001f)
                            throw new InvalidOperationException("Unweighted NPC vertex: " + skin.name);
                    skins++;
                }
            }

            var rack = home.GetComponent<HomeWeaponRack>();
            if (!rack || !rack.displays || rack.displays.GetComponentsInChildren<Renderer>().Length < 4)
                throw new InvalidOperationException("Dedicated weapon mounts missing.");
            foreach (var r in rack.displays.GetComponentsInChildren<Renderer>())
                if (r.bounds.Contains(HomeLayout.Mirror + Vector3.up * 1.3f))
                    throw new InvalidOperationException("Weapon/display overlaps mirror: " + r.name);
            foreach (var filter in renovation.GetComponentsInChildren<MeshFilter>())
            {
                if (!filter.sharedMesh)
                    throw new InvalidOperationException("Detail mesh missing: " + filter.name);
                MeshSafety.Validate(filter.name, filter.sharedMesh.vertices, filter.sharedMesh.triangles);
                if (filter.sharedMesh.normals.Length != filter.sharedMesh.vertexCount || filter.sharedMesh.normals.Any(n => !MeshSafety.Finite(n) || n.sqrMagnitude < .01f))
                    throw new InvalidOperationException("Invalid new detail normals: " + filter.name);
            }

            var clips = game.Player.animationView.animator.runtimeAnimatorController.animationClips.Distinct();
            foreach (string name in new[]
            {
                "Sleep_Down",
                "Sleep_Loop",
                "Sleep_Up"
            }

            )
            {
                var clip = clips.Single(c => c.name == name);
                var scales = AnimationUtility.GetCurveBindings(clip).Where(b => b.type == typeof(Transform) && b.path.Contains("DEF_") && b.propertyName.StartsWith("m_LocalScale."));
                if (!scales.Any())
                    throw new InvalidOperationException("Sleep FK bake missing: " + name);
                foreach (var binding in scales)
                {
                    var values = AnimationUtility.GetEditorCurve(clip, binding).keys.Select(k => k.value).ToArray();
                    if (values.Any(v => !float.IsFinite(v) || Mathf.Abs(v - values[0]) > .00001f))
                        throw new InvalidOperationException("Changing sleep bone scale: " + name + " / " + binding.path);
                }
            }

            Debug.Log("Village overhaul references/geometry passed: " + skins + " NPC skin meshes, mill gearing, original music/Foley, dedicated mounts, generated geometry and fixed-scale sleep channels. This is not a visual or gameplay approval; test full Play Mode checklist.");
        }
    }
}
