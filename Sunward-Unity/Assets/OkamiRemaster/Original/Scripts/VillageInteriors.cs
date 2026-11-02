using UnityEngine;
namespace Sunward.Remaster
{
    // Three expanded spaces in Windflower, isolated from the outdoor shells.
    // Geometry/furniture remain original assets; portals and bounds are Sunward.
    public static class VillageInteriors
    {
        public const float OffsetY=-250;
        public static readonly Vector3 HomeCentre=new Vector3(-34,-249.895f,-16),FoodCentre=new Vector3(10,-249.6f,-15),DojoCentre=new Vector3(0,-249.5f,25);
        public static bool Home(Vector3 p)=>Mathf.Abs(p.y-HomeCentre.y)<8 && Mathf.Abs(p.x+34)<6.7f && Mathf.Abs(p.z+16)<5;
        public static bool Food(Vector3 p)=>Mathf.Abs(p.y-FoodCentre.y)<8 && Mathf.Abs(p.x-10)<7.1f && Mathf.Abs(p.z+15)<5.8f;
        public static bool Dojo(Vector3 p)=>Mathf.Abs(p.y-DojoCentre.y)<10 && Mathf.Abs(p.x)<9.7f && Mathf.Abs(p.z-25)<13;
        public static bool Inside(Vector3 p)=>Home(p)||Food(p)||Dojo(p);
        public static bool Height(Vector3 p,out float y)
        {
            y=HomeCentre.y;if(Home(p))return true;
            y=FoodCentre.y;if(Food(p))return true;
            y=DojoCentre.y;if(!Dojo(p))return false;
            // Original raised dojo platform and steps keep their mesh collision.
            int n=Physics.RaycastNonAlloc(new Vector3(p.x,-240,p.z),Vector3.down,hits,16,1<<6,QueryTriggerInteraction.Ignore);
            for(int i=0;i<n;i++)if(hits[i].collider.name.Contains("dojo-floor") && hits[i].point.y>y && hits[i].point.y<-245)y=hits[i].point.y;
            return true;
        }
        static readonly RaycastHit[] hits=new RaycastHit[32];
        public static Vector3 Guard(Vector3 previous,Vector3 next)
        {
            Vector3 c;float x,z;
            if(Home(previous)){c=HomeCentre;x=6.15f;z=4.25f;}
            else if(Food(previous)){c=FoodCentre;x=6.55f;z=5.15f;}
            else if(Dojo(previous)){c=DojoCentre;x=9;z=12.1f;}
            else return next;
            next.x=Mathf.Clamp(next.x,c.x-x,c.x+x);next.z=Mathf.Clamp(next.z,c.z-z,c.z+z);return next;
        }
        public static Vector3 Mat=>new Vector3(6.8f,-249.54f,-12.44f);
        public static Vector3 HomeDoor=>new Vector3(-34,.1f,-20.2f);
        public static string Action(Vector3 p)
        {
            if(Home(p))return Vector3.Distance(p,HomeLayout.Bed)<1.9f?"bed":Vector3.Distance(p,HomeLayout.Mirror)<2?"mirror":"interior:home";
            if(Food(p))return Vector3.Distance(p,Mat)<1.35f?"venue:mat":"interior:food";
            if(Dojo(p))return "interior:dojo";
            if(Vector3.Distance(p,HomeDoor)<2.3f)return "interior:home";
            return null;
        }
        public static void Enter(GameFlow game,string room)
        {
            var p=game.Player.transform.position;Vector3 target;
            if(room=="home")target=Home(p)?new Vector3(-34,.12f,-21.4f):new Vector3(-34,-249.865f,-19.5f);
            else if(room=="food")target=Food(p)?new Vector3(2.8f,.05f,-15):new Vector3(4,-249.57f,-15);
            else target=Dojo(p)?new Vector3(0,.05f,13.3f):new Vector3(0,-249.47f,14);
            game.Combat.Cancel();game.Services.CancelRest();game.Player.Teleport(target);
            game.Player.transform.rotation=Quaternion.Euler(0,room=="food"?90:0,0);
            var camera=Object.FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();
            game.Notify(Inside(target)?"E · leave through the entrance · furnished village interior":"Back in the village");
        }
    }
}
