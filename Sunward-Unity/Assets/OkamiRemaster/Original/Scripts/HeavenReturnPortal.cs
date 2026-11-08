using UnityEngine;
namespace Sunward.Remaster
{
    // The visible gate owns its passage. Physics and a swept local-space probe
    // share this component; no realm, interaction or ground-ray gate can trap it.
    [DefaultExecutionOrder(50)]
    public sealed class HeavenReturnPortal:MonoBehaviour
    {
        public GameFlow game;
        bool returning,havePrevious;Vector3 previous;int teleportRevision;
        public static bool Contains(Vector3 p)=>Mathf.Abs(p.x)<=2.3f && p.y>=-1.25f && p.y<=7.5f && Mathf.Abs(p.z)<=1.4f;
        static bool Clip(float p,float d,float lo,float hi,ref float enter,ref float leave)
        {
            if(Mathf.Abs(d)<.00001f)return p>=lo && p<=hi;
            float a=(lo-p)/d,b=(hi-p)/d;if(a>b){float t=a;a=b;b=t;}enter=Mathf.Max(enter,a);leave=Mathf.Min(leave,b);return enter<=leave;
        }
        public static bool Crosses(Vector3 from,Vector3 to)
        {
            if(Contains(to))return true;
            var d=to-from;float enter=0,leave=1;
            return Clip(from.x,d.x,-2.3f,2.3f,ref enter,ref leave) && Clip(from.y,d.y,-1.25f,7.5f,ref enter,ref leave) && Clip(from.z,d.z,-1.4f,1.4f,ref enter,ref leave);
        }
        void OnEnable(){returning=havePrevious=false;}
        void Update()
        {
            if(!game || !game.Player)return;
            var local=transform.InverseTransformPoint(game.Player.transform.position);
            if(returning){returning=Contains(local);previous=local;teleportRevision=game.Player.TeleportRevision;havePrevious=true;return;}
            bool continuous=havePrevious && teleportRevision==game.Player.TeleportRevision;
            bool entered=continuous?Crosses(previous,local):Contains(local);previous=local;teleportRevision=game.Player.TeleportRevision;havePrevious=true;
            if(entered)Enter();
        }
        void OnTriggerEnter(Collider other){Touch(other);}
        void OnTriggerStay(Collider other){Touch(other);}
        void Touch(Collider other)
        {if(game && game.Player && other && other.GetComponentInParent<WolfMotor>()==game.Player)Enter();}
        void Enter()
        {
            if(returning || !game || !game.Player || game.Health<=0 || game.CinematicActive)return;
            returning=true;game.ReturnHome();
        }
    }
}
