using UnityEngine;
namespace Sunward.Remaster
{
    // An original diner walks a clear aisle, then returns to his own seated clip.
    public sealed class NativeIndoorRoutine : MonoBehaviour
    {
        public OriginalActor actor;
        public Vector3[] route;
        Vector3 seat;
        Quaternion seatRotation;
        string seated,hands;
        int index=-1;
        float wait=10;
        GameFlow game;
        void Start()
        {
            game=Object.FindFirstObjectByType<GameFlow>();seat=transform.position;seatRotation=transform.rotation;
            var old=GetComponent<NativeVenueActor>();if(old){seated=old.seatedMotion;hands=old.handMotion;old.enabled=false;}
        }
        void Update()
        {
            if(!game || game.Blocked || !actor || !actor.Ready || !VillageInteriors.Food(game.Player.transform.position))return;
            if(wait>0){wait-=Time.deltaTime;if(index<0 && actor.CurrentSourceMotion!=seated)actor.PlayActivity(seated,true,.65f);return;}
            if(route==null || route.Length==0 || actor.ActivityLength("hm00_010")<=0)return;
            Vector3 target=index<0?route[0]:index<route.Length?route[index]:seat;
            if(Vector3.Distance(transform.position,game.Player.transform.position)<1.4f)return;
            Vector3 direction=target-transform.position;direction.y=0;
            if(direction.magnitude>.08f)
            {
                actor.seatedArmMotion=null;
                if(actor.CurrentSourceMotion!="hm00_010")actor.PlayActivity("hm00_010",true,.85f);
                transform.position=Vector3.MoveTowards(transform.position,target,Time.deltaTime*.65f);
                transform.rotation=Quaternion.RotateTowards(transform.rotation,Quaternion.LookRotation(direction),Time.deltaTime*110);
            }
            else
            {
                index++;if(index>route.Length){index=-1;wait=16;transform.rotation=seatRotation;actor.seatedArmMotion=hands;actor.PlayActivity(seated,true,.65f);}
            }
        }
    }
}
