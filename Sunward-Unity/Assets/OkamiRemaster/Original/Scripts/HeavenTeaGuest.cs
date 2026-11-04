using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class HeavenTeaGuest:MonoBehaviour
    {
        public OriginalActor actor;public float phase;bool ready;
        void Update()
        {
            if(ready || !actor || !actor.Ready)return;ready=true;actor.seatedArmMotion="hm09_005";actor.seatedArmRate=.55f;actor.seatedArmPause=3.5f;actor.seatedArmWeight=.85f;actor.PlayActivity("hm05_003",true,1,phase);
            var wrist=actor.NativeBone(10);if(!wrist)return;var cup=VillageFestival.Place(wrist,"Okami/heaven-tea-cup",new Vector3(.01f,.01f,.045f),new Vector3(.13f,.13f,.13f),Vector3.zero);if(cup){cup.transform.rotation=Quaternion.Euler(0,actor.transform.eulerAngles.y,0);cup.name="Original tea cup held in the recovered native hand";}
        }
    }
}
