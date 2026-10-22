using UnityEngine;

namespace Sunward
{
    public sealed class WolfAnimation : MonoBehaviour
    {
        public Animator animator;
        Transform rootBone, hips;
        Vector3 hipsRest;
        Quaternion hipsRestRotation;
        float filteredSpeed;
        bool groundedGait, swimming, jumpPose, seated, sitBlend;
        float waterSpeed, poseWeight, swimPhase, jumpAge, verticalSpeed;
        CanineMotionPose naturalPose;
        readonly System.Collections.Generic.HashSet<string> missingStates = new System.Collections.Generic.HashSet<string>();
        void Awake()
        {
            if (!animator) return;
            foreach (var t in animator.GetComponentsInChildren<Transform>())
            {
                if (t.name == "CTRL_root") rootBone = t;
                if (t.name == "DEF_hips") hips = t;
            }
            if (hips) { hipsRest = hips.localPosition; hipsRestRotation = hips.localRotation; }
            var motor = GetComponentInParent<WolfMotor>();
            naturalPose = new CanineMotionPose(animator.transform, motor ? motor.transform : transform);
        }

        void LateUpdate()
        {
            if (rootBone)
                rootBone.localPosition = Vector3.zero;
            bool activePose = swimming || jumpPose || seated;
            poseWeight = Mathf.MoveTowards(poseWeight, activePose ? 1 : 0, Time.deltaTime * 9);
            if (poseWeight <= 0 || (activePose && !seated)) sitBlend = false;
            swimPhase += Time.deltaTime * (waterSpeed > .2f ? 5.5f + Mathf.Min(waterSpeed, 4) * 1.1f : 3.2f);
            if (jumpPose) jumpAge += Time.deltaTime;
            if (naturalPose != null && poseWeight > 0)
            {
                naturalPose.Apply(swimming, swimPhase, verticalSpeed, jumpAge, poseWeight, sitBlend);
                return;
            }
            // Calm only the grounded gait's pelvis motion, not jumps/attacks or
            // bone scale. The source wolf mesh, markings and animation clips stay intact.
            if (hips && groundedGait && !animator.IsInTransition(0))
            {
                var p = hips.localPosition;
                p.y = Mathf.Lerp(hipsRest.y, p.y, .70f);
                hips.localPosition = p;
                hips.localRotation = Quaternion.Slerp(hipsRestRotation, hips.localRotation, .82f);
            }
        }

        public string Current { get; private set; } = "";

        public void Play(string state, float blend = .12f, float duration = 0, bool restart = false)
        {
            if (!animator || (state == Current && !restart))
                return;
            if (!animator.HasState(0, Animator.StringToHash(state)))
            {
                if (missingStates.Add(state))
                    Debug.LogError("Missing Amaterasu animation state: " + state + ". Rebuild the Windflower scene and validate imports.", this);
                return;
            }

            groundedGait = state.StartsWith("Walk_") || state.StartsWith("Jog_") || state.StartsWith("Sprint_");
            bool phaseMatch = groundedGait && (Current.StartsWith("Walk_") || Current.StartsWith("Jog_") || Current.StartsWith("Sprint_"));
            float phase = phaseMatch ? Mathf.Repeat((animator.IsInTransition(0) ? animator.GetNextAnimatorStateInfo(0) : animator.GetCurrentAnimatorStateInfo(0)).normalizedTime, 1) : 0;
            Current = state;
            animator.speed = duration > 0 ? ClipLength(state) / duration : 1;
            animator.CrossFadeInFixedTime(state, blend, 0, phase * ClipLength(state));
        }

        public float ClipLength(string state)
        {
            foreach (var c in animator.runtimeAnimatorController.animationClips)
                if (c.name == state)
                    return c.length;
            return 1;
        }

        public void NaturalJump(bool second, float speed)
        {
            jumpAge = 0;
            jumpPose = true;
            // Source jumps were ~1.8 s while the motor's ballistic arc is ~.7 s.
            // Retain the source actions but fit their timing to the actual jump.
            Play(second ? "Jump_Double" : speed > 4 ? "Jump_Sprint" : speed > 1 ? "Jump_Jog" : "Jump_Standing", .06f, .70f, true);
        }

        public void SetWaterMotion(bool inWater, float speed, bool grounded, float vertical)
        {
            swimming = inWater;
            waterSpeed = speed;
            verticalSpeed = vertical;
            if (grounded || inWater) jumpPose = false;
        }

        public void SitObserve(bool active)
        {
            seated = active;
            if (!active) return;
            sitBlend = true;
            swimming = jumpPose = groundedGait = false;
            Play("Idle_Natural", .18f);
            if (animator) animator.speed = .45f;
        }

        public void Swim(float speed)
        {
            // The native 47-state controller stays intact. A low-rate idle drives
            // secondary details while the same skeleton performs authored paddles.
            Play("Idle_Natural", .18f);
            groundedGait = false;
            if (animator) animator.speed = .45f;
        }

        public void Locomotion(float speed, float turn, bool air, float vy)
        {
            if (air)
            {
                Play(vy > 0 ? Current.StartsWith("Jump") ? Current : "Jump_Standing" : "Air_Fall");
                return;
            }

            filteredSpeed = Mathf.Lerp(filteredSpeed, speed, 1 - Mathf.Exp(-Time.deltaTime * 14));
            // Hysteresis prevents footstep/contact noise repeatedly restarting gaits.
            string gait = LocomotionTuning.Gait(filteredSpeed, turn, Current);
            Play(gait, .18f);
            float reference = LocomotionTuning.ReferenceSpeed(gait);
            float rate = filteredSpeed > .15f ? Mathf.Clamp(filteredSpeed / reference, .65f, 1.95f) : 1;
            animator.speed = Mathf.Lerp(animator.speed, rate, 1 - Mathf.Exp(-Time.deltaTime * 12));
        }
    }
}
