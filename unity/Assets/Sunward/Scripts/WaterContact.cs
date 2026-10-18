using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class WaterContact : MonoBehaviour
    {
        public GameFlow game;
        float timer;
        void Update()
        {
            timer -= Time.deltaTime;
            if (!game || game.Player.Speed < .3f || timer > 0)
                return;
            var p = game.Player.transform.position;
            float d = Valley.Depth(p);
            if (d > .02f && d < .35f && game.Player.Grounded)
            {
                p.y = -.32f;
                game.Fx.Ring(p, new Color(.75f, .9f, .85f), .22f);
                timer = .22f;
            }
        }
    }
}
