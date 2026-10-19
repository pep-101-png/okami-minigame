using UnityEngine;

namespace Sunward
{
    // The source residents had no skeleton. These are actual skinned limb bones,
    // animated with world-anchored stance paws, not whole-object bobbing.
    public sealed class ResidentLocomotion : MonoBehaviour
    {
        public Transform hips, spine, head;
        public Transform[] thighs, shins, feet, arms, forearms;
        public GameFlow game;
        public bool stallkeeper;
        public AudioSource stepSource;
        public AudioClip footstep;
        Vector3 previous;
        float phase, blend;
        Vector3[] planted = new Vector3[2], swingFrom = new Vector3[2];
        bool[] stance = new bool[2];
        Quaternion[] plantedRotation = new Quaternion[2];
        bool initialized;
        void Start()
        {
            ResetFeet();
        }

        void ResetFeet()
        {
            previous = transform.position;
            for (int i = 0; i < 2; i++)
            {
                planted[i] = swingFrom[i] = feet[i].position;
                stance[i] = false;
                plantedRotation[i] = transform.rotation;
            }

            initialized = true;
        }

        void LateUpdate()
        {
            if (!initialized || !game)
                return;
            Vector3 delta = transform.position - previous;
            delta.y = 0;
            previous = transform.position;
            if (delta.magnitude > 1)
            {
                ResetFeet();
                return;
            }

            if (game.Blocked || game.Home.Active)
                return;
            float speed = delta.magnitude / Mathf.Max(Time.deltaTime, .0001f);
            blend = Mathf.MoveTowards(blend, speed > .025f ? 1 : 0, Time.deltaTime * 5);
            phase += delta.magnitude / .44f;
            float t = Time.time;
            hips.localPosition = new Vector3(0, .74f - .055f * blend + Mathf.Sin(phase * Mathf.PI * 4) * .012f * blend, 0);
            hips.localRotation = Quaternion.Euler(0, Mathf.Sin(phase * Mathf.PI * 2) * 4 * blend, 0);
            spine.localRotation = Quaternion.Euler(0, -Mathf.Sin(phase * Mathf.PI * 2) * 5 * blend, Mathf.Sin(t * .8f) * .6f);
            head.localRotation = Quaternion.Euler(0, Mathf.Sin(t * .47f) * 5 * (1 - blend), 0);
            for (int i = 0; i < 2; i++)
            {
                float p = Mathf.Repeat(phase + i * .5f, 1);
                bool contact = p < .62f;
                Vector3 neutral = transform.TransformPoint(new Vector3(i == 0 ? -.14f : .14f, .065f, 0));
                if (blend > .02f)
                {
                    if (contact && !stance[i])
                    {
                        if (stepSource && footstep)
                            stepSource.PlayOneShot(footstep, .10f);
                        planted[i] = feet[i].position;
                        plantedRotation[i] = feet[i].rotation;
                        planted[i].y = game.valley.Height(planted[i]) + .065f;
                    }

                    if (!contact && stance[i])
                        swingFrom[i] = feet[i].position;
                    stance[i] = contact;
                }

                Vector3 goal;
                if (contact)
                    goal = planted[i];
                else
                {
                    float u = Mathf.SmoothStep(0, 1, (p - .62f) / .38f);
                    var ahead = neutral + transform.forward * .20f;
                    ahead.y = game.valley.Height(ahead) + .065f;
                    goal = Vector3.Lerp(swingFrom[i], ahead, u) + Vector3.up * (Mathf.Sin(u * Mathf.PI) * .085f);
                }

                neutral.y = game.valley.Height(neutral) + .065f;
                goal = Vector3.Lerp(neutral, goal, blend);
                var up = thighs[i];
                var lo = shins[i];
                var foot = feet[i];
                up.localRotation = lo.localRotation = Quaternion.identity;
                Vector3 a = up.position;
                float l1 = Vector3.Distance(a, lo.position), l2 = Vector3.Distance(lo.position, foot.position);
                Vector3 axis = (goal - a).normalized;
                LimbArc.Solve(l1, l2, (goal - a).magnitude, out float x, out float h, out float d);
                Vector3 knee = a + axis * x + Vector3.ProjectOnPlane(transform.forward, axis).normalized * h;
                up.rotation = Quaternion.FromToRotation(lo.position - a, knee - a) * up.rotation;
                lo.rotation = Quaternion.FromToRotation(foot.position - lo.position, a + axis * d - lo.position) * lo.rotation;
                foot.rotation = contact && blend > .5f ? plantedRotation[i] : transform.rotation;
                float swing = Mathf.Sin((phase + i * .5f) * Mathf.PI * 2) * 18 * blend;
                float trade = stallkeeper ? Mathf.Sin(t * 1.1f + i) * 7 * (1 - blend) : 0;
                arms[i].localRotation = Quaternion.Euler(-swing + trade, 0, i == 0 ? 8 : -8);
                forearms[i].localRotation = Quaternion.Euler(-8 - Mathf.Abs(trade) * 2, 0, 0);
            }
        }
    }
}
