using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class PracticeArrow : MonoBehaviour
    {
        TrainingDummy target;Vector3 from,to;float t,duration;
        public static void Fire(Vector3 start,TrainingDummy dummy)
        {
            var root=new GameObject("Original archery practice arrow");var flight=root.AddComponent<PracticeArrow>();flight.target=dummy;flight.from=start;flight.to=dummy.transform.position+Vector3.up*1.1f;flight.duration=Vector3.Distance(start,flight.to)/13;
            root.transform.position=start;root.transform.rotation=Quaternion.LookRotation(flight.to-start);
            root.AddComponent<OriginalVisual>().Load("Okami/dojo-arrow",Vector3.zero,Vector3.one*.7f);
        }
        void Update()
        {
            var game=target?target.game:null;if(game && game.Blocked)return;
            if(!target){Destroy(gameObject);return;}
            t+=Time.deltaTime;transform.position=Vector3.Lerp(from,to,t/Mathf.Max(.05f,duration));
            if(t>=duration){target.PracticeContact();CelestialBrush.Burst("Spark",to,4,.18f);Destroy(gameObject);}
        }
    }
}
