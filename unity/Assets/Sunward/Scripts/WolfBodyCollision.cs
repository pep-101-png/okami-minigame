using UnityEngine;

namespace Sunward
{
    // A horizontal body sweep complements CharacterController's upright capsule.
    // World layer only: excludes the wolf, triggers, VFX and other probe volumes.
    public sealed class WolfBodyCollision : MonoBehaviour
    {
        const int Solid = 1 << 6;
        const float Radius = .34f, Front = 1.18f, Rear = -.60f;
        void Ends(Quaternion rotation, out Vector3 a, out Vector3 b)
        {
            var center = transform.position + Vector3.up * .83f;
            a = center + rotation * Vector3.forward * Rear;
            b = center + rotation * Vector3.forward * Front;
        }

        public Vector3 Sweep(Vector3 delta)
        {
            Vector3 horizontal = new Vector3(delta.x, 0, delta.z);
            float distance = horizontal.magnitude;
            if (distance < .00001f)
                return delta;
            Ends(transform.rotation, out var a, out var b);
            if (Physics.CapsuleCast(a, b, Radius, horizontal / distance, out var hit, distance + .025f, Solid, QueryTriggerInteraction.Ignore))
            {
                float travel = Mathf.Max(0, hit.distance - .025f);
                var allowed = horizontal.normalized * Mathf.Min(distance, travel);
                var slide = Vector3.ProjectOnPlane(horizontal - allowed, hit.normal);
                slide.y = 0;
                if (slide.sqrMagnitude > .000001f && !Physics.CapsuleCast(a + allowed, b + allowed, Radius, slide.normalized, slide.magnitude + .02f, Solid, QueryTriggerInteraction.Ignore))
                    allowed += slide;
                return new Vector3(allowed.x, delta.y, allowed.z);
            }

            return delta;
        }

        public bool CanTurn(Quaternion rotation)
        {
            Ends(rotation, out var a, out var b);
            return !Physics.CheckCapsule(a, b, Radius, Solid, QueryTriggerInteraction.Ignore);
        }
    }
}
