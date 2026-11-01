using UnityEngine;
namespace Sunward.Remaster
{
    // Retargeting/hand alignment for the original guard rig and bow. The source
    // files lack a complete matching native draw/release clip; do not label this
    // adapter as a recovered Okami shooting animation.
    [DefaultExecutionOrder(80)]
    public sealed class NativeArcheryPose : MonoBehaviour
    {
        public NativeVenueActor practice;
        Quaternion gripRotation;
        bool ready;
        GameObject arrow;
        static void Solve(Transform upper,Transform elbow,Transform wrist,Vector3 target,Vector3 pole)
        {
            float a=Vector3.Distance(upper.position,elbow.position),b=Vector3.Distance(elbow.position,wrist.position);
            Vector3 delta=target-upper.position;float d=Mathf.Clamp(delta.magnitude,.02f,Mathf.Max(.02f,a+b-.005f));Vector3 forward=delta.normalized;
            Vector3 outward=Vector3.ProjectOnPlane(pole-upper.position,forward).normalized;if(outward.sqrMagnitude<.01f)outward=Vector3.up;
            float along=(a*a+d*d-b*b)/(2*d),height=Mathf.Sqrt(Mathf.Max(0,a*a-along*along));Vector3 bend=upper.position+forward*along+outward*height;
            upper.rotation=Quaternion.FromToRotation(elbow.position-upper.position,bend-upper.position)*upper.rotation;
            elbow.rotation=Quaternion.FromToRotation(wrist.position-elbow.position,upper.position+forward*d-elbow.position)*elbow.rotation;
        }
        void LateUpdate()
        {
            if(!practice || !practice.actor || !practice.actor.Ready || !practice.dummy)return;
            var actor=practice.actor;var left=actor.NativeBone(7);var right=actor.NativeBone(10);if(!left || !right)return;
            if(!ready){gripRotation=Quaternion.Inverse(transform.rotation)*left.rotation;ready=true;}
            float p=practice.ActivityPhase,release=practice.releasePhase;
            float draw=practice.Performing?(p<release?Mathf.SmoothStep(0,1,p/release):1-Mathf.SmoothStep(0,1,(p-release)/.18f)):0;
            Vector3 front=transform.forward,side=transform.right,basePoint=transform.position;
            Vector3 grip=basePoint+Vector3.up*1.30f+front*.42f+side*.25f;
            Vector3 pull=basePoint+Vector3.up*1.32f-side*.18f+front*Mathf.Lerp(.30f,-.12f,draw);
            Solve(actor.NativeBone(5),actor.NativeBone(6),left,grip,basePoint+side+Vector3.up*.8f);
            Solve(actor.NativeBone(8),actor.NativeBone(9),right,pull,basePoint-side+Vector3.up*.8f);
            left.rotation=transform.rotation*gripRotation;
            if(!arrow){arrow=new GameObject("Original arrow nocked in the bow");arrow.transform.SetParent(transform,false);arrow.AddComponent<OriginalVisual>().Load("Okami/dojo-arrow",Vector3.zero,Vector3.one*.7f);}
            arrow.SetActive(practice.Performing && p<release);arrow.transform.position=grip-front*(.08f+.20f*draw);arrow.transform.rotation=Quaternion.LookRotation(front);
        }
    }
}
