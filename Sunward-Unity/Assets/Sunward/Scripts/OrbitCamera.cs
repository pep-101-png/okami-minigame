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
        bool cinematic;
        CinemachineBrain brain;
        bool savedIgnoreTimeScale;
        float savedFov,cinematicYaw,cinematicPitch,cinematicDistance;
        Vector3 cinematicFocus;
        bool cinematicCollisions=true;
        public void BeginCinematic(bool avoidObstacles=true)
        {
            if(cinematic || !virtualCamera)return;
            cinematicCollisions=avoidObstacles;cinematic=true;savedFov=virtualCamera.Lens.FieldOfView;
            brain=Camera.main?Camera.main.GetComponent<CinemachineBrain>():null;
            if(brain){savedIgnoreTimeScale=brain.IgnoreTimeScale;brain.IgnoreTimeScale=true;}
        }
        public void CinematicFrame(Vector3 point,float angle,float elevation,float range,float fov)
        {
            cinematicFocus=point;cinematicYaw=angle;cinematicPitch=elevation;cinematicDistance=range;
            if(virtualCamera){var lens=virtualCamera.Lens;lens.FieldOfView=fov;virtualCamera.Lens=lens;}
        }
        public void EndCinematic()
        {
            if(!cinematic)return;
            cinematic=false;if(virtualCamera){var lens=virtualCamera.Lens;lens.FieldOfView=savedFov;virtualCamera.Lens=lens;}
            if(brain)brain.IgnoreTimeScale=savedIgnoreTimeScale;
            SnapFocus();
        }
        public void ReturnCinematic(float blend)
        {
            cinematicFocus=Vector3.Lerp(cinematicFocus,target.transform.position+Vector3.up*.9f,blend);
            cinematicYaw=Mathf.LerpAngle(cinematicYaw,yaw,blend);cinematicPitch=Mathf.Lerp(cinematicPitch,pitch,blend);
            cinematicDistance=Mathf.Lerp(cinematicDistance,distance,blend);
            if(virtualCamera){var lens=virtualCamera.Lens;lens.FieldOfView=Mathf.Lerp(lens.FieldOfView,savedFov,blend);virtualCamera.Lens=lens;}
        }
        public void RotateHeading(float degrees){yaw+=degrees;SnapFocus();}
        public void SnapFocus(){initialized=false;}
        void LateUpdate()
        {
            if (!target)
                return;
            if(cinematic)
            {
                Vector3 cinematicOffset=Quaternion.Euler(cinematicPitch,cinematicYaw,0)*Vector3.back*cinematicDistance;
                if(cinematicCollisions && Physics.SphereCast(cinematicFocus,.18f,cinematicOffset.normalized,out var obstruction,cinematicDistance,1<<6,QueryTriggerInteraction.Ignore))
                    cinematicOffset=cinematicOffset.normalized*Mathf.Max(.4f,obstruction.distance-.2f);
                virtualCamera.transform.SetPositionAndRotation(cinematicFocus+cinematicOffset,Quaternion.LookRotation(-cinematicOffset));
                return;
            }
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
            bool indoors=Sunward.Remaster.VillageInteriors.AnyRoom(target.transform.position);
            float viewDistance=indoors?Mathf.Clamp(distance,6,9):distance;
            Vector3 offset = Quaternion.Euler(indoors?Mathf.Max(28,pitch):pitch, yaw, 0) * Vector3.back * viewDistance, position = focus + offset;
            if (Physics.SphereCast(focus, .25f, offset.normalized, out var hit, viewDistance, 1 << 6, QueryTriggerInteraction.Ignore))
                position = focus + offset.normalized * Mathf.Max(.35f, hit.distance - .28f);
            if(indoors)position=Sunward.Remaster.VillageInteriors.CameraPosition(target.transform.position,position);
            virtualCamera.transform.SetPositionAndRotation(position, Quaternion.LookRotation(focus - position));
        }
    }
}
