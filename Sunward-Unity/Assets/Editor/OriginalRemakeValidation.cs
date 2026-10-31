using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using Sunward.Remaster;

namespace Sunward.Editor
{
    public static class OriginalRemakeValidation
    {
        [Serializable] sealed class Model { public Bone[] bones; }
        [Serializable] sealed class Bone { public int parent; public float[] position; }
        static void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        static void Actor(OriginalActor actor)
        {
            Need(actor && actor.enabled, "Original actor binding missing.");
            var data = Resources.Load<TextAsset>(actor.resource + "/Model");
            Need(data, "Original model resource missing: " + actor.resource);
            var model = JsonUtility.FromJson<Model>(data.text);
            var bank = new NativePoseBank(actor.resource + "/Poses");
            Need(model != null && model.bones != null && bank.BoneCount == model.bones.Length + 1, "Original skeleton/bank mismatch: " + actor.resource);
            foreach (string name in new[] { actor.idle, actor.walk, actor.run, actor.windup, actor.strike, actor.recover, actor.death })
                Need(!string.IsNullOrEmpty(name) && bank.Find(name) != null, "Original motion binding missing: " + actor.resource + "/" + name);
            Need(float.IsFinite(actor.modelScale) && actor.modelScale > 0, "Invalid original actor scale.");
        }
        [MenuItem("Sunward/Validate Original Okami Remake")]
        public static void Validate()
        {
            Need(!EditorApplication.isPlaying, "Run static source validation outside Play Mode.");
            var game = UnityEngine.Object.FindFirstObjectByType<GameFlow>();
            Need(game && game.Player && game.Combat && game.valley && game.Home && game.Shelf, "Existing Windflower gameplay references missing.");
            Need(game.Player.GetComponent<NativeAmaterasu>(), "Existing player is not bound to native Amaterasu.");
            var body = new NativePoseBank("NativePlayer/pl00/Poses");
            foreach (string name in new[] { "pl00_000", "pl00_010", "pl00_011", "pl00_012", "pl00_021", "pl00_02d", "pl00_500", "pl00_501" })
                Need(body.Find(name) != null, "Original Amaterasu motion missing: " + name);
            Need(game.npcObjects.Length == 7, "Existing NPC identity count changed.");
            foreach (var npc in game.npcObjects)
            {
                Actor(npc.GetComponent<OriginalActor>());
                var improvised = npc.GetComponent<ResidentLocomotion>();
                Need(!improvised || !improvised.enabled, "Improvised NPC animation remains active: " + npc.name);
            }
            Need(game.spirits.Length == 6, "Existing enemy-role count changed.");
            foreach (var enemy in game.spirits)
            {
                Need(enemy && enemy.visual && enemy.hp > 0 && enemy.damage > 0, "Existing enemy mechanics missing.");
                Actor(enemy.visual.GetComponent<OriginalActor>());
            }
            Actor(game.Combat.spear.visual.GetComponent<OriginalActor>());
            Need(game.Combat.spear.visual.GetComponent<OriginalActor>().resource == "Okami/wp25", "Native glaive must use wp25, not a Solar Flare variant.");
            Need(game.Combat.sundial.visual.GetComponent<NativeSolarFlare>(), "Original Solar Flare adapter missing.");
            Need(new NativePoseBank("NativePlayer/wp24/Poses").Find("wp24_000") != null, "Original Solar Flare motion missing.");
            Need(Resources.Load<TextAsset>("Okami/Feedback"), "Original feedback resources missing.");
            Need(Resources.Load<Texture2D>("Okami/UI/Paper") && Resources.Load<Texture2D>("Okami/UI/Ink"), "Original UI painting missing.");
            for (int i = 0; i < 3; i++) Need(Resources.Load<AudioClip>("Okami/Audio/Amaterasu-" + i), "Original Amaterasu voice missing.");
            int visible = 0;
            foreach (var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!renderer.enabled || !renderer.gameObject.activeInHierarchy) continue;
                foreach (var material in renderer.sharedMaterials)
                {
                    Need(material && material.shader && !ShaderUtil.ShaderHasError(material.shader), "Broken original material: " + renderer.name);
                    Need(AssetDatabase.GetAssetPath(material).StartsWith("Assets/OkamiRemaster/Original/", StringComparison.Ordinal), "Visible non-original artwork remains: " + renderer.name);
                }
                visible++;
            }
            foreach (var particle in UnityEngine.Object.FindObjectsByType<ParticleSystemRenderer>(FindObjectsSortMode.None))
                Need(!particle.enabled, "Unmapped legacy particle artwork is active: " + particle.name);
            Debug.Log("Original Okami source connections checked: " + visible + " saved scene renderers, seven NPCs, six enemy roles, original player/weapon resources and voices. Static validation only; Unity Play Mode and visual approval are still required. Full EST/SEQ effects and authentic music/ambient banks remain unfinished.");
        }
    }
}
