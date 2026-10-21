using UnityEngine;

namespace Sunward
{
    public sealed class MarketSoundscape : MonoBehaviour
    {
        public GameFlow game;
        public AudioSource music, market;
        float level;
        void Update()
        {
            if (!game || !game.Player)
                return;
            var p = game.Player.transform.position;
            float distance = new Vector2(p.x, p.z).magnitude;
            float target = game.InTrial || game.Blocked ? 0 : 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(8, 27, distance));
            level = Mathf.MoveTowards(level, target, Time.unscaledDeltaTime * .4f);
            if (music) music.volume = level * .055f;
            if (market) market.volume = level * .035f;
        }
    }
}
