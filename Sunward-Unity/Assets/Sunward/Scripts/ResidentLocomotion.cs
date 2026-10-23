using UnityEngine;

namespace Sunward
{
    // Distance-driven gait on the retained rig. Contact targets are bounded in
    // the character's frame and replanted on sharp turns, stops and teleports.
    [DefaultExecutionOrder(30)]
    public sealed class ResidentLocomotion : MonoBehaviour
    {
        public Transform hips, spine, head;
        public Transform[] thighs, shins, feet, arms, forearms;
        public GameFlow game;
        public bool stallkeeper;
        public bool Seated;
        float seatedBlend;
        public AudioSource stepSource;
        public AudioClip footstep;
        Vector3 previous, hipRest;
        Quaternion previousRotation;
        float phase, blend;
        readonly Vector3[] planted = new Vector3[2], swingFrom = new Vector3[2];
        readonly bool[] stance = new bool[2];
        readonly Quaternion[] plantedRotation = new Quaternion[2];
        bool initialized;
        readonly ResidentStepClock stepClock = new ResidentStepClock();
        static readonly ResidentSoundBudget soundBudget = new ResidentSoundBudget();
        readonly RaycastHit[] groundHits = new RaycastHit[12];

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetAudioClock() { soundBudget.Reset(); }

        void Start()
        {
            if (!hips || !spine || !head || thighs == null || shins == null || feet == null || arms == null || forearms == null ||
                thighs.Length < 2 || shins.Length < 2 || feet.Length < 2 || arms.Length < 2 || forearms.Length < 2)
            {
                Debug.LogError("Resident rig is incomplete: " + name, this);
                enabled = false;
                return;
            }
            hipRest = hips.localPosition;
            if (stepSource)
            {
                stepSource.Stop();
                stepSource.loop = false;
                stepSource.playOnAwake = false;
                stepSource.spatialBlend = 0; // Gate by player, not the elevated camera.
            }
            ResetFeet();
        }

        float Floor(Vector3 p)
        {
            // Raised interiors are supported by their colliders, rather than
            // pulling a food-hall resident's feet down through its floor.
            int count = Physics.RaycastNonAlloc(p + Vector3.up * .45f, Vector3.down, groundHits, 1.25f, 1 << 6, QueryTriggerInteraction.Ignore);
            float height = float.NegativeInfinity;
            for (int i = 0; i < count; i++)
            {
                var hit = groundHits[i];
                if (!hit.collider || hit.collider.transform.IsChildOf(transform) || hit.collider.GetComponentInParent<ResidentLocomotion>()) continue;
                if (hit.normal.y > .5f) height = Mathf.Max(height, hit.point.y);
            }
            if (!float.IsNegativeInfinity(height)) return height;
            return game && game.valley ? game.valley.Height(p) : transform.position.y;
        }

        Vector3 Neutral(int i)
        {
            Vector3 p = transform.TransformPoint(new Vector3(i == 0 ? -.14f : .14f, .065f, .015f));
            p.y = Floor(p) + .065f;
            return p;
        }

        void ResetFeet()
        {
            previous = transform.position;
            previousRotation = transform.rotation;
            phase = 0;
            for (int i = 0; i < 2; i++)
            {
                planted[i] = swingFrom[i] = Neutral(i);
                stance[i] = false;
                plantedRotation[i] = transform.rotation;
            }
            initialized = true;
        }

        void LateUpdate()
        {
            if (!initialized || !game) return;
            Vector3 delta = transform.position - previous;
            delta.y = 0;
            float moved = delta.magnitude;
            float turn = Quaternion.Angle(previousRotation, transform.rotation);
            previous = transform.position;
            previousRotation = transform.rotation;
            if (moved > .75f || turn > 35)
            {
                blend = 0;
                ResetFeet();
                return;
            }
            if (game.Blocked || game.Home.Active) return;
            float dt = Mathf.Max(Time.deltaTime, .0001f);
            float speed = moved / dt;
            blend = Mathf.MoveTowards(blend, speed > .035f ? 1 : 0, dt * 6);
            bool realStep = stepClock.Advance(moved, dt, !Seated && speed > .12f);
            if (realStep && stepSource && footstep && game.Player && !game.InTrial)
            {
                float distance = Vector3.Distance(transform.position, game.Player.transform.position);
                if (distance < 5.5f && soundBudget.Allow(Time.time))
                {
                    // One quiet local step at a time, maximum five per second village-wide.
                    stepSource.Stop();
                    stepSource.pitch = .96f + (GetInstanceID() & 7) * .012f;
                    stepSource.PlayOneShot(footstep, .045f * (1 - distance / 5.5f));
                }
            }
            phase = Mathf.Repeat(phase + moved / .64f, 1);
            float cycle = phase * Mathf.PI * 2;
            hips.localPosition = hipRest + new Vector3(0, -.018f * blend + Mathf.Cos(cycle * 2) * .006f * blend, 0);
            hips.localRotation = Quaternion.Euler(0, Mathf.Sin(cycle) * 2.2f * blend, 0);
            spine.localRotation = Quaternion.Euler(0, -Mathf.Sin(cycle) * 2.4f * blend, Mathf.Sin(Time.time * .8f) * .35f);
            head.localRotation = Quaternion.Euler(0, Mathf.Sin(Time.time * .47f) * 3 * (1 - blend), 0);
            for (int i = 0; i < 2; i++)
            {
                float p = Mathf.Repeat(phase + i * .5f, 1);
                bool contact = p < .60f;
                Vector3 neutral = Neutral(i);
                // A fixed world foot must never remain behind after a turn or
                // obstacle changes the walk direction. Replant within reach.
                Vector3 local = transform.InverseTransformPoint(planted[i]);
                if (Mathf.Abs(local.z) > .29f || Mathf.Abs(local.x - (i == 0 ? -.14f : .14f)) > .16f || blend < .03f)
                {
                    planted[i] = swingFrom[i] = neutral;
                    plantedRotation[i] = transform.rotation;
                    stance[i] = false;
                }
                if (contact && !stance[i] && blend > .1f)
                {
                    planted[i] = feet[i].position;
                    planted[i].y = Floor(planted[i]) + .065f;
                    plantedRotation[i] = transform.rotation;
                    // Replanting is a pose correction, never an audio event.
                }
                if (!contact && stance[i]) swingFrom[i] = feet[i].position;
                stance[i] = contact;
                Vector3 goal = planted[i];
                if (!contact)
                {
                    float u = Mathf.Clamp01((p - .60f) / .40f);
                    Vector3 ahead = neutral + transform.forward * .16f;
                    ahead.y = Floor(ahead) + .065f;
                    goal = Vector3.Lerp(swingFrom[i], ahead, Mathf.SmoothStep(0, 1, u)) + Vector3.up * (Mathf.Sin(u * Mathf.PI) * .055f);
                }
                goal = Vector3.Lerp(neutral, goal, blend);
                Transform up = thighs[i], lo = shins[i], foot = feet[i];
                up.localRotation = lo.localRotation = Quaternion.identity;
                Vector3 a = up.position;
                float upper = Vector3.Distance(a, lo.position), lower = Vector3.Distance(lo.position, foot.position);
                Vector3 difference = goal - a;
                Vector3 axis = difference.sqrMagnitude > .00001f ? difference.normalized : Vector3.down;
                float along, lift, reach;
                LimbArc.Solve(upper, lower, difference.magnitude, out along, out lift, out reach);
                Vector3 bend = Vector3.ProjectOnPlane(transform.forward, axis);
                if (bend.sqrMagnitude < .001f) bend = Vector3.ProjectOnPlane(transform.up, axis);
                Vector3 knee = a + axis * along + bend.normalized * lift;
                up.rotation = Quaternion.FromToRotation(lo.position - a, knee - a) * up.rotation;
                lo.rotation = Quaternion.FromToRotation(foot.position - lo.position, a + axis * reach - lo.position) * lo.rotation;
                foot.rotation = contact && blend > .5f ? plantedRotation[i] : transform.rotation;
                float swing = Mathf.Sin((phase + i * .5f) * Mathf.PI * 2) * 12 * blend;
                float trade = stallkeeper ? Mathf.Sin(Time.time * 1.1f + i) * 3 * (1 - blend) : 0;
                arms[i].localRotation = Quaternion.Euler(-swing + trade, 0, i == 0 ? 4 : -4);
                forearms[i].localRotation = Quaternion.Euler(-5 - Mathf.Abs(trade), 0, 0);
            }
            seatedBlend = Mathf.MoveTowards(seatedBlend, Seated ? 1 : 0, dt * 2.6f);
            if (seatedBlend > 0)
            {
                hips.localPosition = Vector3.Lerp(hips.localPosition, hipRest + Vector3.down * .50f, seatedBlend);
                for (int i = 0; i < 2; i++)
                {
                    thighs[i].localRotation = Quaternion.Slerp(thighs[i].localRotation, Quaternion.Euler(-80, 0, 0), seatedBlend);
                    shins[i].localRotation = Quaternion.Slerp(shins[i].localRotation, Quaternion.Euler(138, 0, 0), seatedBlend);
                    feet[i].rotation = Quaternion.Slerp(feet[i].rotation, transform.rotation, seatedBlend);
                }
            }
        }
    }
}
