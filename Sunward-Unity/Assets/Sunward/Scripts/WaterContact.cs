using UnityEngine;

namespace Sunward
{
    public sealed class WaterContact : MonoBehaviour
    {
        public GameFlow game;
        float timer;
        Vector3 lastSafe;
        bool hasSafe;
        void Update()
        {
            if (!game || game.Blocked || game.Home.Active)
                return;
            var player = game.Player;
            var p = player.transform.position;
            timer -= Time.deltaTime;
            float depth = Valley.Depth(p);
            if (!game.InTrial && player.Grounded && VillageNavigation.Clear(game.valley.Data, p, .5f))
            {
                lastSafe = p;
                hasSafe = true;
            }

            // Swimming is intentional. Recovery is reserved for invalid/fallen
            // world positions, never elapsed time spent in the river.
            if (!MeshSafety.Finite(p) || p.y < -6)
            {
                Vector3 safe;
                var desired = MeshSafety.Finite(p) ? p : hasSafe ? lastSafe : new Vector3(-34, 0, -22);
                if (!VillageNavigation.FindSafe(game.valley.Data, desired, out safe, .55f, 16))
                {
                    if (!hasSafe && !VillageNavigation.FindSafe(game.valley.Data, new Vector3(-34, 0, -22), out lastSafe))
                    {
                        Debug.LogError("No safe river recovery point available.");
                        return;
                    }

                    safe = lastSafe;
                }

                game.Combat.Cancel();
                player.Recover(safe + Vector3.up * .04f);
                game.Fx.Ring(safe, new Color(.75f, .9f, .85f), 1.3f);
                game.Audio.Cue("land");
                game.Notify("Recovered from outside the playable world.");
                return;
            }

            if (player.Speed > .3f && timer <= 0 && ((player.Swimming && Valley.WaterDepth(p) > .28f) || (depth > .02f && depth < .35f && player.Grounded)))
            {
                p.y = -.32f;
                game.Fx.Ring(p, new Color(.75f, .9f, .85f), .22f);
                timer = player.Swimming ? .42f : .22f;
            }
        }
    }
}
