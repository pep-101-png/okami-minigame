using UnityEngine;

namespace Sunward
{
    public sealed class WolfAnimation : MonoBehaviour
    {
        public Animator animator;
        Transform rootBone;
        readonly System.Collections.Generic.HashSet<string> missingStates = new System.Collections.Generic.HashSet<string>();
        void Start()
        {
            foreach (var t in animator.GetComponentsInChildren<Transform>())
                if (t.name == "CTRL_root")
                    rootBone = t;
        }

        void LateUpdate()
        {
            if (rootBone)
                rootBone.localPosition = Vector3.zero;
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

            Current = state;
            animator.speed = duration > 0 ? ClipLength(state) / duration : 1;
            animator.CrossFadeInFixedTime(state, blend, 0);
        }

        public float ClipLength(string state)
        {
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

            string gait = speed < .12f ? "Idle_Natural" : speed < 1 ? "Walk_Natural" : speed < 4 ? "Jog_Natural" : "Sprint_Fluid";
            if (speed > .2f && Mathf.Abs(turn) > .55f)
                gait = (speed < 1 ? "Walk" : speed < 4 ? "Jog" : "Sprint") + "_Turn_" + (turn < 0 ? "L" : "R");
            Play(gait);
            if (speed > .15f)
                animator.speed = Mathf.Clamp(speed / (speed < 1 ? .5667f : speed < 4 ? 2.448f : 4.9725f), .55f, 1.6f);
            else
                animator.speed = 1;
        }
    }
}
