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
        public bool foodHallRoute;
        public int mealWaypoint = 4;
        public int initialWaypoint;
        public bool Dining => foodHallRoute && pause > 0 && lastStop == mealWaypoint;
        int lastStop = -1;
        readonly RaycastHit[] pathHits = new RaycastHit[16];
        static MarketWalker foodHallInTransit;
        static readonly List<MarketWalker> walkers = new List<MarketWalker>();
        Rigidbody body;
        int next;
        float pause;
        public Transform conversationPartner;
        public bool Stationary => pause > 0;
        void OnEnable()
        {
            walkers.Add(this);
        }

        void OnDisable()
        {
            walkers.Remove(this);
            if (foodHallInTransit == this) foodHallInTransit = null;
        }

        void Start()
        {
            body = GetComponent<Rigidbody>();
            pause = foodHallRoute ? 27 + phase : phase;
            if (foodHallRoute) lastStop = mealWaypoint;
            next = route != null && route.Length > 0 ? Mathf.Clamp(initialWaypoint, 0, route.Length - 1) : 0;
        }

        void FixedUpdate()
        {
            if (!game || game.Blocked || game.Home.Active || route == null || route.Length == 0)
                return;
            pause -= Time.fixedDeltaTime;
            if (pause > 0 || Vector3.Distance(transform.position, game.Player.transform.position) < 1.65f)
            {
                if (pause > 0 && conversationPartner)
                {
                    var facing = conversationPartner.position - transform.position;
                    facing.y = 0;
                    if (facing.sqrMagnitude > .01f)
                        body.MoveRotation(Quaternion.RotateTowards(body.rotation, Quaternion.LookRotation(facing), Time.fixedDeltaTime * 80));
                }
                return;
            }
            if (foodHallRoute && lastStop == mealWaypoint)
            {
                // Only one diner traverses the doorway at a time. Others keep
                // eating rather than meeting head-on and blocking the entrance.
                if (foodHallInTransit && foodHallInTransit != this) return;
                foodHallInTransit = this;
            }
            var target = route[next];
            var delta = target - transform.position;
            delta.y = 0;
            if (delta.magnitude < .1f)
            {
                lastStop = next;
                if (foodHallRoute && lastStop == mealWaypoint && foodHallInTransit == this) foodHallInTransit = null;
                next = (next + 1) % route.Length;
                pause = foodHallRoute && lastStop == mealWaypoint ? 27 + phase : foodHallRoute ? .15f : 6.0f + phase;
                return;
            }

            var p = Vector3.MoveTowards(transform.position, target, Time.fixedDeltaTime * .52f);
            if (!PathClear(transform.position, p))
            {
                if (!foodHallRoute) next = (next + 1) % route.Length;
                pause = foodHallRoute ? .4f : 1;
                return;
            }

            foreach (var other in walkers)
                if (other != this && Vector3.Distance(p, other.transform.position) < .85f)
                    return;
            foreach (var other in game.npcObjects)
                if (other && Vector3.Distance(p, other.transform.position) < .9f)
                    return;
            p.y = game.valley.Height(p) + (foodHallRoute && p.x > 5.1f ? .07f : 0);
            body.MovePosition(p);
            body.MoveRotation(Quaternion.RotateTowards(body.rotation, Quaternion.LookRotation(delta), Time.fixedDeltaTime * 100));
        }
        bool PathClear(Vector3 from, Vector3 to)
        {
            if (!foodHallRoute) return VillageNavigation.SegmentClear(game.valley.Data, from, to);
            // This exception is restricted to the authored food-hall entrance
            // corridor. Actual walls/door jambs remain authoritative obstacles.
            if (to.x < 2.2f || to.x > 7.25f || to.z < 6.5f || to.z > 13.3f || Valley.Depth(to) > .1f) return false;
            Vector3 delta = to - from;
            delta.y = 0;
            if (delta.sqrMagnitude < .000001f) return true;
            int count = Physics.CapsuleCastNonAlloc(from + Vector3.up * .38f, from + Vector3.up * 1.55f,
                .25f, delta.normalized, pathHits, delta.magnitude + .015f, 1 << 6, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < count; i++)
                if (pathHits[i].collider && !pathHits[i].collider.transform.IsChildOf(transform)) return false;
            return true;
        }
    }
}
