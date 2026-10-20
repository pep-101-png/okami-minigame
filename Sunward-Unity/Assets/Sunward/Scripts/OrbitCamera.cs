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
            if (Physics.SphereCast(focus, .25f, offset.normalized, out var hit, distance, 1 << 6, QueryTriggerInteraction.Ignore))
                position = focus + offset.normalized * Mathf.Max(.35f, hit.distance - .28f);
            virtualCamera.transform.SetPositionAndRotation(position, Quaternion.LookRotation(focus - position));
        }
    }
}
