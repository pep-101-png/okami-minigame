using UnityEngine;

namespace Sunward
{
    public sealed class MarketSoundscape : MonoBehaviour
    {
        public GameFlow game;
        public AudioSource music, market;
        float level;
        void Start()
        {
            // Retire the old continuous noise bed. Dialogue now comes from nearby
            // paired residents, with a shared cooldown rather than an overlapping loop.
            if (market) { market.Stop(); market.enabled = false; }
        }
        void Update()
        {
            if (!game || !game.Player)
                return;
            var p = game.Player.transform.position;
            float distance = new Vector2(p.x, p.z).magnitude;
            float target = game.InTrial || game.Blocked ? 0 : 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(8, 27, distance));
            level = Mathf.MoveTowards(level, target, Time.unscaledDeltaTime * .4f);
            bool foodHall = p.x > 4 && p.x < 17 && p.z > 4 && p.z < 16;
            if (music) music.volume = level * (foodHall ? 0 : .04f);
            if (market) market.volume = 0;
        }
    }
}
