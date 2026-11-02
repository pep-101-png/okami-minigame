using UnityEngine;
namespace Sunward.Remaster
{
    // The wolf's nose crosses the physical threshold before its long body capsule.
    // Segment tests prevent skipping a door while sprinting. Arrival points sit
    // clear of the receiving threshold, so exits need no input-blocking timer.
    [DefaultExecutionOrder(200)]
    public sealed class VillageDoorways : MonoBehaviour
    {
        public GameFlow game;
        Vector3 previous;
        bool sampled;
        public static bool Crossed(Vector3 from,Vector3 to,Vector3 door,Vector3 inward,float reach=1.65f,float halfWidth=.95f)
        {
            if(Mathf.Abs(to.y-door.y)>2.5f || (to-from).sqrMagnitude>25)return false;
            float a=Vector3.Dot(from-door,inward),b=Vector3.Dot(to-door,inward);
            if(b<=a+.00001f || b<-reach || a>1.0f)return false;
            // Also accept a player already in the approach zone. Requiring a
            // single plane crossing failed after bumps, pauses and low frames.
            float fraction=a<-reach?Mathf.Clamp01((-reach-a)/(b-a)):0;
            var at=Vector3.Lerp(from,to,fraction)-door;var side=at-inward*Vector3.Dot(at,inward);side.y=0;
            return side.sqrMagnitude<halfWidth*halfWidth;
        }
        void Update()
        {
            if(!game || !game.Player)return;
            var p=game.Player.transform.position;
            if(!sampled || game.Blocked || game.Player.Locked){previous=p;sampled=true;return;}
            {
                string room=null;
                if(VillageInteriors.Home(p))
                {if(Crossed(previous,p,new Vector3(-34,-249.895f,-20.64f),Vector3.back))room="home";}
                else if(VillageInteriors.Food(p))
                {if(Crossed(previous,p,new Vector3(2.96f,-249.6f,-15),Vector3.left))room="food";}
                else if(VillageInteriors.Dojo(p))
                {if(Crossed(previous,p,new Vector3(0,-249.5f,12.9f),Vector3.back))room="dojo";}
                else if(!NativeHomeRoom.At(p))
                {
                    if(Crossed(previous,p,VillageInteriors.HomeDoor,Vector3.forward))room="home";
                    else if(Crossed(previous,p,VillageInteriors.FoodDoor,Vector3.right))room="food";
                    else if(Crossed(previous,p,VillageInteriors.DojoDoor,Vector3.forward))room="dojo";
                }
                if(room!=null){VillageInteriors.Enter(game,room);}
                else foreach(var home in NativeHomeRoom.All)
                {
                    bool inside=home.Contains(p);
                    var door=inside?new Vector3(home.entrance.x,home.transform.position.y,home.transform.position.z-3):home.door;
                    if(Crossed(previous,p,door,inside?Vector3.back:home.doorInward,1.65f,inside?1.05f:home.doorHalfWidth))
                    {NativeHomeRoom.Interact(game,"home:"+home.number+(inside?":exit":":enter"));break;}
                }
            }
            previous=game.Player.transform.position;
        }
    }
}
