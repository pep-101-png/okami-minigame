using UnityEngine;

namespace Sunward
{
    public sealed class VillageResident : MonoBehaviour
    {
        public GameFlow game;
        public int index;
        public bool stallkeeper;
        public bool hasStation;
        public Vector3 station;
        public Vector3[] route = new Vector3[0];
        readonly Collider[] nearby = new Collider[12];
        Vector3 home, destination;
        float wait, stuck;
        int visit;
        Rigidbody body;
        void Start()
        {
            body = GetComponent<Rigidbody>();
            if(stallkeeper && hasStation)
            {
                home=destination=station;transform.position=station;
                if(body){body.isKinematic=true;body.position=station;}
                return;
            }
            if (!VillageNavigation.FindSafe(game.valley.Data, transform.position, out home))
                throw new System.InvalidOperationException("No safe village spawn for " + name);
            transform.position = destination = home;
            wait = 2 + index * .6f;
        }

        void FixedUpdate()
        {
            if (stallkeeper || game.Blocked || game.Home.Active)
                return;
            if (!VillageNavigation.Clear(game.valley.Data, transform.position))
            {
                if (VillageNavigation.FindSafe(game.valley.Data, home, out var safe))
                {
                    body.position = safe;
                    transform.position = safe;
                }

                destination = transform.position;
            }

            if (Vector3.Distance(transform.position, game.Player.transform.position) < 2.3f)
                return;
            wait -= Time.deltaTime;
            var delta = destination - transform.position;
            delta.y = 0;
            if (delta.magnitude < .07f)
            {
                if (wait > 0)
                    return;
                visit++;
                float angle = (visit * 2.39996f + index) * 1.0f;
                var candidate = route.Length > 0 ? route[(visit - 1) % route.Length] : home + new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * 1.3f;
                if (VillageNavigation.SegmentClear(game.valley.Data, transform.position, candidate))
                    destination = candidate;
                wait = 3 + (index + visit) % 5;
                return;
            }

            var next = Vector3.MoveTowards(transform.position, destination, Time.deltaTime * .38f);
            foreach (var other in game.npcObjects)
                if (other && other != gameObject && Vector3.Distance(next, other.transform.position) < .9f)
                {
                    stuck += Time.deltaTime;
                    if (stuck > 1)
                        destination = transform.position;
                    return;
                }

            if (!VillageNavigation.SegmentClear(game.valley.Data, transform.position, next))
            {
                destination = transform.position;
                return;
            }

            int count = Physics.OverlapCapsuleNonAlloc(next + Vector3.up * .45f, next + Vector3.up * 1.6f, .36f, nearby, 1 << 6, QueryTriggerInteraction.Ignore);
            for (int n = 0; n < count; n++)
                if (nearby[n].transform.root != transform.root)
                {
                    destination = transform.position;
                    return;
                }

            stuck = 0;
            next.y = game.valley.Height(next);
            body.MovePosition(next);
            body.MoveRotation(Quaternion.RotateTowards(body.rotation, Quaternion.LookRotation(delta), Time.deltaTime * 100));
        }
    }
}
