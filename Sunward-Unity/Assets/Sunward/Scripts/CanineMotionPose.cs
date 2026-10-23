using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    // FK/IK animation on the existing DEF skeleton. No replacement mesh, container
    // scale writes or root translation: WolfMotor alone owns physical movement.
    // Rest-relative poses keep the authored limb lengths through each paddle.
    internal sealed class CanineMotionPose
    {
        readonly Transform frame;
        readonly bool ready;
        readonly Transform[] bones;
        readonly Vector3[] restPosition, animatedPosition;
        readonly Quaternion[] restRotation, animatedRotation;
        readonly Transform hips, neck, head, chest;
        bool modified;
        readonly Transform[] upper = new Transform[4], lower = new Transform[4], end = new Transform[4];
        readonly Vector3[] footRest = new Vector3[4];
        readonly Quaternion[] footRotation = new Quaternion[4];

        public CanineMotionPose(Transform model, Transform movementFrame)
        {
            frame = movementFrame;
            var found = new List<Transform>();
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true))
                if (t.name.StartsWith("DEF_")) found.Add(t);
            bones = found.ToArray();
            restPosition = new Vector3[bones.Length];
            restRotation = new Quaternion[bones.Length];
            animatedPosition = new Vector3[bones.Length];
            animatedRotation = new Quaternion[bones.Length];
            for (int i = 0; i < bones.Length; i++)
            {
                restPosition[i] = bones[i].localPosition;
                restRotation[i] = bones[i].localRotation;
            }
            hips = Find("DEF_hips"); chest = Find("DEF_chest"); neck = Find("DEF_neck_base"); head = Find("DEF_head");
            for (int i = 0; i < 4; i++)
            {
                string kind = i < 2 ? "front" : "rear", side = i % 2 == 0 ? "L" : "R";
                upper[i] = Find("DEF_" + kind + "_upper." + side);
                lower[i] = Find("DEF_" + kind + "_lower." + side);
                // Hind legs retain their hock and paw chain rather than stretching
                // a third segment into a two-bone solver.
                end[i] = Find("DEF_" + kind + (i < 2 ? "_paw." : "_hock.") + side);
            }
            var missing = new List<string>();
            if (!hips) missing.Add("DEF_hips");
            for (int i = 0; i < 4; i++)
                if (!upper[i] || !lower[i] || !end[i]) missing.Add("limb " + i);
            ready = missing.Count == 0;
            if (!ready)
                Debug.LogWarning("Canine swim/jump pose is missing skeleton bindings: " + string.Join(", ", missing.ToArray()) + ". Source animations remain active; inspect the rig import.", model);
        }

        Transform Find(string name)
        {
            string normalized = name.Replace(".", "");
            foreach (Transform t in bones)
                if (t.name.Replace(".", "") == normalized) return t;
            return null;
        }

        public void Apply(bool swimming, float phase, float vertical, float age, float weight, bool sitting = false)
        {
            if (!ready || !hips || !frame || weight <= 0) return;
            // Save the evaluated Animator pose, then blend back to it at water/land
            // transitions. Capturing/restoring only DEF bones leaves controls alone.
            modified = true;
            for (int i = 0; i < bones.Length; i++)
            {
                animatedPosition[i] = bones[i].localPosition;
                animatedRotation[i] = bones[i].localRotation;
                bones[i].localPosition = restPosition[i];
                bones[i].localRotation = restRotation[i];
            }
            for (int i = 0; i < 4; i++)
                if (end[i]) { footRest[i] = end[i].position; footRotation[i] = end[i].rotation; }

            float pitch = sitting ? -22 : swimming ? -5 + Mathf.Sin(phase * 2) * 1.2f : Mathf.Clamp(-vertical * 1.7f, -11, 12);
            hips.rotation = Quaternion.AngleAxis(pitch, frame.right) * hips.rotation;
            if (sitting) hips.position += -Vector3.up * .43f - frame.forward * .12f;
            if (swimming) hips.position += Vector3.up * (Mathf.Sin(phase * 2) * .018f);
            // Keep the muzzle above water and eyes toward the bank.
            if (neck) neck.rotation = Quaternion.AngleAxis(swimming ? -9 : -pitch * .35f, frame.right) * neck.rotation;
            if (head) head.rotation = Quaternion.AngleAxis(swimming ? -5 : -pitch * .25f, frame.right) * head.rotation;
            for (int i = 0; i < 4; i++)
            {
                if (!upper[i] || !lower[i] || !end[i]) continue;
                Vector3 target;
                if (sitting)
                {
                    // Front paws remain on the mat; folded hocks support the
                    // lowered haunches. Spine incline lifts the chest naturally.
                    target = footRest[i] + (i < 2 ? Vector3.zero : -Vector3.up * .35f + frame.forward * .30f);
                }
                else if (swimming)
                {
                    // Alternating diagonal pairs: broad submerged power stroke,
                    // folded recovery. Hind paddles are smaller than front ones.
                    float p = phase + ((i == 0 || i == 3) ? 0 : Mathf.PI);
                    float reach = i < 2 ? .30f : .19f;
                    float lift = i < 2 ? .22f : .16f;
                    target = footRest[i] + frame.forward * (Mathf.Cos(p) * reach)
                        + Vector3.up * (.12f - Mathf.Sin(p) * lift);
                }
                else
                {
                    // Hindquarters push off, all four paws gather beneath the body
                    // near the apex, then forepaws reach for the landing.
                    float tuck = Mathf.SmoothStep(0, 1, Mathf.Clamp01((vertical + 5) / 10)) * Mathf.SmoothStep(0, 1, age / .13f);
                    float reach = vertical < -1 ? Mathf.SmoothStep(0, 1, Mathf.Clamp01((-vertical - 1) / 6)) : 0;
                    target = footRest[i] + Vector3.up * (tuck * (i < 2 ? .31f : .39f))
                        + frame.forward * (i < 2 ? -.16f * tuck + .16f * reach : .23f * tuck);
                }
                Solve(upper[i], lower[i], end[i], target, frame.forward * (i < 2 ? -1 : 1));
                if (sitting) end[i].rotation = footRotation[i];
            }
            for (int i = 0; i < bones.Length; i++)
            {
                bones[i].localPosition = Vector3.Lerp(animatedPosition[i], bones[i].localPosition, weight);
                bones[i].localRotation = Quaternion.Slerp(animatedRotation[i], bones[i].localRotation, weight);
            }
        }

        // Restore before the next Animator evaluation. Otherwise an unkeyed
        // bone can accumulate a procedural offset across successive frames.
        public void Restore()
        {
            if (!modified) return;
            for (int i = 0; i < bones.Length; i++)
            {
                bones[i].localPosition = animatedPosition[i];
                bones[i].localRotation = animatedRotation[i];
            }
            modified = false;
        }

        void Capture(bool reset)
        {
            modified = true;
            for (int i = 0; i < bones.Length; i++)
            {
                animatedPosition[i] = bones[i].localPosition;
                animatedRotation[i] = bones[i].localRotation;
                if (reset) { bones[i].localPosition = restPosition[i]; bones[i].localRotation = restRotation[i]; }
            }
            for (int i = 0; i < 4; i++)
                if (end[i]) { footRest[i] = end[i].position; footRotation[i] = end[i].rotation; }
        }

        public void Gait(float phase, float speed, float weight)
        {
            if (!ready || speed < .1f || weight <= 0) return;
            Capture(true);
            float gallop = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(4.3f, 6.5f, speed));
            float walk = 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.9f, 2.5f, speed));
            float stride = Mathf.Lerp(.68f, 1.60f, Mathf.InverseLerp(.8f, 7.2f, speed));
            hips.position += Vector3.up * (Mathf.Sin(phase * Mathf.PI * 4) * Mathf.Lerp(.010f, .023f, gallop));
            hips.rotation = Quaternion.AngleAxis(Mathf.Sin(phase * Mathf.PI * 2) * 2.2f * gallop, frame.right) * hips.rotation;
            if (neck) neck.rotation = Quaternion.AngleAxis(-Mathf.Sin(phase * Mathf.PI * 2) * 1.4f * gallop, frame.right) * neck.rotation;
            for (int i = 0; i < 4; i++)
            {
                float trot = i == 0 || i == 3 ? 0 : .5f;
                float walking = i == 0 ? 0 : i == 1 ? .5f : i == 2 ? .75f : .25f;
                float running = i < 2 ? i * .14f : .53f + (i - 2) * .14f;
                float offset = Mathf.Lerp(Mathf.Lerp(trot, walking, walk), running, gallop);
                float p = Mathf.Repeat(phase + offset, 1);
                const float contact = .60f;
                float z, lift = 0;
                if (p < contact) z = stride * (.30f - p);
                else
                {
                    float u = (p - contact) / (1 - contact);
                    z = Mathf.Lerp(-stride * .30f, stride * .30f, Mathf.SmoothStep(0, 1, u));
                    lift = Mathf.Sin(u * Mathf.PI) * Mathf.Lerp(.065f, .15f, gallop);
                }
                Vector3 target = footRest[i] + frame.forward * z + Vector3.up * lift;
                Solve(upper[i], lower[i], end[i], target, frame.forward * (i < 2 ? -1 : 1));
                end[i].rotation = footRotation[i];
            }
            for (int i = 0; i < bones.Length; i++)
            {
                bones[i].localPosition = Vector3.Lerp(animatedPosition[i], bones[i].localPosition, weight);
                bones[i].localRotation = Quaternion.Slerp(animatedRotation[i], bones[i].localRotation, weight);
            }
        }

        public void Combat(float progress, bool heavy, int side)
        {
            if (!ready) return;
            Capture(false);
            float anticipation = Mathf.Sin(Mathf.Clamp01(progress / .32f) * Mathf.PI);
            float sweep = Mathf.Sin(Mathf.Clamp01((progress - .20f) / .80f) * Mathf.PI);
            float weight = Mathf.Sin(progress * Mathf.PI);
            float yaw = side * (-anticipation * 9 + sweep * (heavy ? 16 : 12));
            hips.position += -frame.up * (anticipation * .045f + weight * .025f);
            hips.rotation = Quaternion.AngleAxis(yaw, frame.up) * Quaternion.AngleAxis(sweep * (heavy ? 5 : 3), frame.right) * hips.rotation;
            if (chest) chest.rotation = Quaternion.AngleAxis(-yaw * .28f, frame.up) * chest.rotation;
            if (neck) neck.rotation = Quaternion.AngleAxis(-yaw * .45f, frame.up) * neck.rotation;
            for (int i = 0; i < 4; i++)
            {
                Vector3 target = footRest[i];
                if (i == (side > 0 ? 0 : 1)) target += frame.forward * sweep * .12f + Vector3.up * sweep * .055f;
                Solve(upper[i], lower[i], end[i], target, frame.forward * (i < 2 ? -1 : 1));
                end[i].rotation = footRotation[i];
            }
        }

        static void Solve(Transform a, Transform b, Transform c, Vector3 target, Vector3 pole)
        {
            Vector3 origin = a.position;
            float l1 = Vector3.Distance(origin, b.position), l2 = Vector3.Distance(b.position, c.position);
            Vector3 offset = target - origin;
            if (offset.sqrMagnitude < .000001f || l1 < .0001f || l2 < .0001f) return;
            Vector3 axis = offset.normalized;
            LimbArc.Solve(l1, l2, offset.magnitude, out float along, out float bend, out float distance);
            Vector3 side = Vector3.ProjectOnPlane(pole, axis);
            if (side.sqrMagnitude < .0001f) side = Vector3.ProjectOnPlane(Vector3.up, axis);
            Vector3 knee = origin + axis * along + side.normalized * bend;
            a.rotation = Quaternion.FromToRotation(b.position - origin, knee - origin) * a.rotation;
            b.rotation = Quaternion.FromToRotation(c.position - b.position, origin + axis * distance - b.position) * b.rotation;
        }
    }
}
