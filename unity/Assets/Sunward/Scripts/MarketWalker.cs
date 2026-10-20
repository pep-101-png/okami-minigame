using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    // Ambient shoppers are separate from the seven named quest/dialogue residents.
    [RequireComponent(typeof(Rigidbody))]
    public sealed class MarketWalker : MonoBehaviour
    {
        public GameFlow game;
        public Vector3[] route;
        public float phase;
        static readonly List<MarketWalker> walkers = new List<MarketWalker>();
        Rigidbody body;
        int next;
        float pause;
        void OnEnable()
        {
            walkers.Add(this);
        }

        void OnDisable()
        {
            walkers.Remove(this);
        }

        void Start()
        {
            body = GetComponent<Rigidbody>();
            pause = phase;
        }

        void FixedUpdate()
        {
            if (!game || game.Blocked || game.Home.Active || route == null || route.Length == 0)
                return;
            pause -= Time.fixedDeltaTime;
            if (pause > 0 || Vector3.Distance(transform.position, game.Player.transform.position) < 1.65f)
                return;
            var target = route[next];
            var delta = target - transform.position;
            delta.y = 0;
            if (delta.magnitude < .1f)
            {
                next = (next + 1) % route.Length;
                pause = 2.5f + phase;
                return;
            }

            var p = Vector3.MoveTowards(transform.position, target, Time.fixedDeltaTime * .52f);
            if (!VillageNavigation.SegmentClear(game.valley.Data, transform.position, p))
            {
                next = (next + 1) % route.Length;
                pause = 1;
                return;
            }

            foreach (var other in walkers)
                if (other != this && Vector3.Distance(p, other.transform.position) < .85f)
                    return;
            foreach (var other in game.npcObjects)
                if (other && Vector3.Distance(p, other.transform.position) < .9f)
                    return;
            p.y = game.valley.Height(p);
            body.MovePosition(p);
            body.MoveRotation(Quaternion.RotateTowards(body.rotation, Quaternion.LookRotation(delta), Time.fixedDeltaTime * 100));
        }
    }
}
