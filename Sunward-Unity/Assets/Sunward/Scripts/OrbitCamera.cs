using UnityEngine;
using Unity.Cinemachine;
using UnityEngine.InputSystem;

namespace Sunward
{
    [DefaultExecutionOrder(-200)]
    public sealed class OrbitCamera : MonoBehaviour
    {
        public WolfMotor target;
        public CinemachineCamera virtualCamera;
        float yaw = 37, pitch = 25, distance = 15;
        Vector3 focus;
        bool initialized;
        readonly RaycastHit[] obstructions = new RaycastHit[32];
        void LateUpdate()
        {
            if (!target)
                return;
            var input = target.input;
            if (!target.game.Blocked)
            {
                Vector2 look = Vector2.zero;
                if (Gamepad.current != null)
                    look = Gamepad.current.rightStick.ReadValue() * 120 * Time.unscaledDeltaTime;
                if (Mouse.current != null && input.Orbit.IsPressed())
                    look += Mouse.current.delta.ReadValue() * .16f;
                yaw += look.x;
                pitch = Mathf.Clamp(pitch - look.y, 12, 65);
                distance = Mathf.Clamp(distance - input.Zoom.ReadValue<float>() * .005f, 6, 22);
            }

            Vector3 desiredFocus = target.transform.position + Vector3.up * .9f + Vector3.ClampMagnitude(target.Velocity * .16f, 1);
            if (!initialized || (focus - desiredFocus).sqrMagnitude > 36)
            {
                focus = desiredFocus;
                initialized = true;
            }

            focus = Vector3.Lerp(focus, desiredFocus, 1 - Mathf.Exp(-Time.deltaTime * 8));
            Vector3 offset = Quaternion.Euler(pitch, yaw, 0) * Vector3.back * distance, position = focus + offset;
            // Cutaway rooms keep their walls solid for Ammy, while the camera
            // can look through the hidden panels instead of zooming into her.
            int hits = Physics.SphereCastNonAlloc(focus, .25f, offset.normalized,
                obstructions, distance, 1 << 6, QueryTriggerInteraction.Ignore);
            float nearest = distance;
            for (int i = 0; i < hits; i++)
            {
                var hit = obstructions[i];
                if (!hit.collider) continue;
                var interior = hit.collider.GetComponentInParent<VillageInterior>();
                if (interior && interior.Contains(target.transform.position)) continue;
                nearest = Mathf.Min(nearest, Mathf.Max(.35f, hit.distance - .28f));
            }
            position = focus + offset.normalized * nearest;
            virtualCamera.transform.SetPositionAndRotation(position, Quaternion.LookRotation(focus - position));
        }
    }
}
