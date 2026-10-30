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
        bool groundedGait;
        Sunward.Remaster.NativeAmaterasu native;
        readonly System.Collections.Generic.HashSet<string> missingStates = new System.Collections.Generic.HashSet<string>();
        void Awake()
        {
            native = GetComponent<Sunward.Remaster.NativeAmaterasu>();
            if (!animator) return;
            if (native && native.Ready) animator.enabled = false;
            foreach (var t in animator.GetComponentsInChildren<Transform>())
            {
                if (t.name == "CTRL_root") rootBone = t;
                if (t.name == "DEF_hips") hips = t;
            }
            if (hips) { hipsRest = hips.localPosition; hipsRestRotation = hips.localRotation; }
        }

        void LateUpdate()
        {
            if (native && native.Ready && native.Visible) return;
            if (rootBone)
                rootBone.localPosition = Vector3.zero;
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
            if (state == Current && !restart)
                return;
            groundedGait = state.StartsWith("Walk_") || state.StartsWith("Jog_") || state.StartsWith("Sprint_");
            bool nativePhase = groundedGait && (Current.StartsWith("Walk_") || Current.StartsWith("Jog_") || Current.StartsWith("Sprint_"));
            if (native && native.Ready && native.Play(state, blend, duration, restart, nativePhase))
            {
                Current = state;
                if (animator) animator.enabled = false;
                return;
            }
            if (!animator) return;
            animator.enabled = true;
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
            if (native && native.Ready)
            {
                float originalLength = native.ClipLength(state);
                if (originalLength > 0) return originalLength;
            }
            foreach (var c in animator.runtimeAnimatorController.animationClips)
                if (c.name == state)
                    return c.length;
            return 1;
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
            if (native && native.Ready && native.Visible) native.GaitSpeed(filteredSpeed);
            else if (animator) animator.speed = Mathf.Lerp(animator.speed, rate, 1 - Mathf.Exp(-Time.deltaTime * 12));
        }
    }
}
