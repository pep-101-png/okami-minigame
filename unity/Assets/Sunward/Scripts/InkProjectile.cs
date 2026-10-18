using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class InkProjectile : MonoBehaviour
    {
        public GameFlow game;
        public Vector3 direction;
        public float damage;
        float life = 3.6f;
        void Update()
        {
            if (game.Blocked)
                return;
            Vector3 delta = direction * 7.5f * Time.deltaTime, p = transform.position;
            if (Physics.SphereCast(p, .2f, direction, out var hit, delta.magnitude, (1 << 6) | (1 << 7), QueryTriggerInteraction.Ignore))
            {
                if (hit.collider.GetComponentInParent<WolfMotor>())
                    game.Hurt(damage, direction);
                game.Fx.Impact(transform.position, new Color(.3f, .2f, .4f));
                Destroy(gameObject);
                return;
            }

            transform.position += delta;
            life -= Time.deltaTime;
            if (life <= 0)
                Destroy(gameObject);
        }
    }
}
