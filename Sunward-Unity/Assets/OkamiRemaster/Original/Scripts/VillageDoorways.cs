using UnityEngine;
namespace Sunward.Remaster
{
    // The wolf's nose crosses the physical threshold before its long body capsule.
    // Segment tests prevent skipping a door while sprinting; a latch prevents an
    // arrival at the other threshold from immediately teleporting back.
    [DefaultExecutionOrder(200)]
    public sealed class VillageDoorways : MonoBehaviour
    {
        public GameFlow game;
        Vector3 previous;
        bool sampled;
        float cooldown;
        public static bool Crossed(Vector3 from,Vector3 to,Vector3 door,Vector3 inward,float reach=1.55f)
        {
            if(Mathf.Abs(to.y-door.y)>2.5f || (to-from).sqrMagnitude>25)return false;
            float a=Vector3.Dot(from-door,inward)+reach,b=Vector3.Dot(to-door,inward)+reach;
            if(b<=a+.00001f || a>0 || b<0)return false;
            var at=Vector3.Lerp(from,to,Mathf.Clamp01(-a/(b-a)))-door;
            var side=at-inward*Vector3.Dot(at,inward);side.y=0;
            return side.sqrMagnitude<.95f*.95f;
        }
        void Update()
        {
            if(!game || !game.Player)return;
            var p=game.Player.transform.position;
            if(!sampled || game.Blocked || game.Player.Locked){previous=p;sampled=true;return;}
            cooldown=Mathf.Max(0,cooldown-Time.deltaTime);
            if(cooldown==0)
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
                    else if(Crossed(previous,p,new Vector3(3.8f,.4f,-15),Vector3.right))room="food";
                    else if(Crossed(previous,p,new Vector3(0,.5f,15.4f),Vector3.forward))room="dojo";
                }
                if(room!=null){VillageInteriors.Enter(game,room);cooldown=.6f;}
                else foreach(var home in NativeHomeRoom.All)
                {
                    bool inside=home.Contains(p);
                    var door=inside?new Vector3(home.entrance.x,home.transform.position.y,home.transform.position.z-3):home.door;
                    if(Crossed(previous,p,door,inside?Vector3.back:Vector3.forward))
                    {NativeHomeRoom.Interact(game,"home:"+home.number+(inside?":exit":":enter"));cooldown=.6f;break;}
                }
            }
            previous=game.Player.transform.position;
        }
    }
}
