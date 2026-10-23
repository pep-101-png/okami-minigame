using UnityEngine;

namespace Sunward
{
    // Named, articulated meshes use their authored joint pivots. No Animator or
    // mesh replacement of the player's wolf is involved.
    public sealed class EnemyPresentation : MonoBehaviour
    {
        EnemyBrain brain;
        Transform torso, mask, leftArm, rightArm, leftLeg, rightLeg;
        Vector3 rest;
        Quaternion torsoRest, maskRest;
        float stride;
        public void Initialize(EnemyBrain owner)
        {
            brain = owner;
            torso = transform.Find("Spirit torso");
            mask = transform.Find("Spirit mask");
            leftArm = transform.Find("Spirit left arm");
            rightArm = transform.Find("Spirit right arm");
            leftLeg = transform.Find("Spirit left leg");
            rightLeg = transform.Find("Spirit right leg");
            rest = transform.localPosition;
            torsoRest = torso ? torso.localRotation : Quaternion.identity;
            maskRest = mask ? mask.localRotation : Quaternion.identity;
        }

        void LateUpdate()
        {
            if (!brain || !torso || !mask || !brain.game || brain.game.Blocked)
                return;
            float t = brain.PresentationClock;
            bool airborne = brain.definition.id == "wisp" || brain.definition.id == "ranged";
            float gait = brain.MovingSpeed;
            stride += gait * Time.deltaTime * 5.6f;
            float step = Mathf.Sin(stride) * Mathf.Clamp01(gait);
            float windup = brain.State == "windup" ? Mathf.SmoothStep(0, 1, brain.StateProgress) : 0;
            float strike = brain.State == "strike" ? Mathf.Sin(brain.StateProgress * Mathf.PI) : 0;
            float recover = brain.State == "recover" ? 1 - brain.StateProgress : 0;
            float stagger = brain.Stunned ? Mathf.Sin(t * 36) * 5 : 0;
            float crouch = windup * .10f + recover * .035f;
            transform.localPosition = rest + Vector3.up * (airborne ? .17f + Mathf.Sin(t * 2.3f) * .07f : .025f * step * step - crouch);
            float smooth = 1 - Mathf.Exp(-Time.deltaTime * 14);
            torso.localRotation = Quaternion.Slerp(torso.localRotation, torsoRest * Quaternion.Euler(-windup * 12 + strike * 15 + stagger, brain.MoveName == "sweep" ? -windup * 30 + strike * 65 : step * 3, Mathf.Sin(t * 1.5f) * 1.5f), smooth);
            mask.localRotation = Quaternion.Slerp(mask.localRotation, maskRest * Quaternion.Euler(windup * 8 - strike * 12, -step * 3, stagger * .4f), smooth);
            float raise = brain.MoveName == "slam" ? windup * 125 - strike * 65 : windup * 65;
            if (leftArm) leftArm.localRotation = Quaternion.Slerp(leftArm.localRotation, Quaternion.Euler(-step * 18 - raise, 0, 9 + windup * 12), smooth);
            if (rightArm) rightArm.localRotation = Quaternion.Slerp(rightArm.localRotation, Quaternion.Euler(step * 18 - raise - strike * 55, brain.MoveName == "sweep" ? strike * 70 : 0, -9 - windup * 12), smooth);
            if (leftLeg) leftLeg.localRotation = Quaternion.Slerp(leftLeg.localRotation, Quaternion.Euler(airborne ? 15 + Mathf.Sin(t * 2) * 7 : step * 16, 0, 0), smooth);
            if (rightLeg) rightLeg.localRotation = Quaternion.Slerp(rightLeg.localRotation, Quaternion.Euler(airborne ? 23 - Mathf.Sin(t * 2) * 7 : -step * 16, 0, 0), smooth);
        }
    }
}
