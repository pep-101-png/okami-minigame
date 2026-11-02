using UnityEngine;
namespace Sunward.Remaster
{
    // Contact follows the original moving sword bone, not a guessed timer pose.
    [DefaultExecutionOrder(100)]
    public sealed class NativeSwordPractice : MonoBehaviour
    {
        public NativeVenueActor practice;
        Vector3 previous;
        bool sampled;
        float cooldown;
        void LateUpdate()
        {
            if(!practice || !practice.Performing || !practice.actor || !practice.actor.Ready || !practice.dummy){sampled=false;return;}
            var sword=practice.actor.NativeBone(20);if(!sword)return;
            Vector3 tip=sword.TransformPoint(new Vector3(0,0,2.03f));
            cooldown=Mathf.Max(0,cooldown-Time.deltaTime);
            if(sampled && Time.deltaTime>0)
            {
                var segment=tip-previous;var centre=practice.dummy.transform.position+Vector3.up;
                float u=segment.sqrMagnitude>.0001f?Mathf.Clamp01(Vector3.Dot(centre-previous,segment)/segment.sqrMagnitude):0;
                if(cooldown<=0 && segment.magnitude/Time.deltaTime>1.5f && Vector3.Distance(previous+segment*u,centre)<1)
                {
                    cooldown=.3f;practice.dummy.PracticeContact();
                    BrushStrokeFlash.Slash(previous,tip);CelestialBrush.Burst("Spark",centre,5,.2f);
                }
            }
            previous=tip;sampled=true;
        }
    }
}
