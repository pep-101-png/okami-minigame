using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class NativeDailyRoutine : MonoBehaviour
    {
        public GameFlow game;
        public NativeHomeRoom home;
        public bool farmer;
        public int seed;
        public Vector3 workplace;
        OriginalActor actor;
        VillageResident resident;
        Rigidbody body;
        int destination=-1;
        float wait;
        bool indoors, resting;
        readonly List<Vector3> path=new List<Vector3>();
        int pathIndex;
        static bool[,] clear;
        const int W=121,H=89;
        static Vector3 Point(int x,int z)=>new Vector3(x-57,0,z-44);
        void Start()
        {
            actor=GetComponent<OriginalActor>();resident=GetComponent<VillageResident>();body=GetComponent<Rigidbody>();
            if(resident)resident.enabled=false;
            if(body)body.isKinematic=true;
            if(!home)home=NativeHomeRoom.For(seed);
            if(clear==null)
            {
                clear=new bool[W,H];for(int x=0;x<W;x++)for(int z=0;z<H;z++)clear[x,z]=VillageNavigation.Clear(game.valley.Data,Point(x,z),.38f);
            }
        }
        bool Route(Vector3 target)
        {
            path.Clear();pathIndex=0;
            if(!VillageNavigation.FindSafe(game.valley.Data,target,out var goal,.4f,5))return false;
            Vector3 start=transform.position;
            if(VillageNavigation.SegmentClear(game.valley.Data,start,goal,.4f)){path.Add(goal);return true;}
            int sx=Mathf.Clamp(Mathf.RoundToInt(start.x)+57,0,W-1),sz=Mathf.Clamp(Mathf.RoundToInt(start.z)+44,0,H-1),gx=Mathf.Clamp(Mathf.RoundToInt(goal.x)+57,0,W-1),gz=Mathf.Clamp(Mathf.RoundToInt(goal.z)+44,0,H-1);
            int first=sx*H+sz,last=gx*H+gz;var parents=new int[W*H];System.Array.Fill(parents,-2);var queue=new Queue<int>();queue.Enqueue(first);parents[first]=-1;
            while(queue.Count>0 && parents[last]==-2)
            {
                int c=queue.Dequeue(),x=c/H,z=c%H;
                foreach(var d in new[]{Vector2Int.left,Vector2Int.right,Vector2Int.up,Vector2Int.down})
                {int nx=x+d.x,nz=z+d.y;if(nx<0||nz<0||nx>=W||nz>=H||!clear[nx,nz])continue;int n=nx*H+nz;if(parents[n]!=-2)continue;parents[n]=c;queue.Enqueue(n);}
            }
            if(parents[last]==-2)return false;
            var reverse=new List<Vector3>();for(int n=last;n!=first && n>=0;n=parents[n])reverse.Add(Point(n/H,n%H));reverse.Reverse();path.AddRange(reverse);path.Add(goal);return true;
        }
        void Update()
        {
            if(!game || game.Blocked || !actor || !actor.Ready)return;
            int phase=farmer?(int)((Time.time+seed*7)/16)%4:(int)((Time.time+seed*13)/40)%4;
            if(wait>0){wait-=Time.deltaTime;return;}
            if(phase!=destination)
            {
                destination=phase;resting=false;actor.EndActivity();
                if(indoors && home){SetPosition(home.exitPoint);indoors=false;}
                var target=farmer?workplace+new Vector3(phase%2==0?-2:2,0,phase<2?4:8):phase==1 && home?home.door:phase==2?new Vector3(GardenPond.X+Mathf.Cos((seed*47+20)*Mathf.Deg2Rad)*4.25f,0,GardenPond.Z+Mathf.Sin((seed*47+20)*Mathf.Deg2Rad)*2.9f):workplace;
                if(!Route(target)){wait=5;destination=-1;return;}
            }
            if(indoors)
            {
                if(!resting){actor.PlayActivity(actor.idle,true);resting=true;}
            }
            else if(pathIndex<path.Count)
            {
                var target=path[pathIndex];target.y=game.valley.Height(target);Vector3 d=target-transform.position;d.y=0;
                if(d.magnitude<.12f)pathIndex++;
                else if(Vector3.Distance(transform.position,game.Player.transform.position)>1.3f)
                {var p=Vector3.MoveTowards(transform.position,target,Time.deltaTime*.65f);p.y=game.valley.Height(p);SetPosition(p);transform.rotation=Quaternion.Slerp(transform.rotation,Quaternion.LookRotation(d),Time.deltaTime*5);}
            }
            else if(!resting)
            {
                resting=true;
                if(!farmer && phase==1 && home){SetPosition(home.bed+new Vector3(.8f,0,0));indoors=true;}
                if(!farmer && phase==2){var d=new Vector3(GardenPond.X,transform.position.y,GardenPond.Z)-transform.position;if(d.sqrMagnitude>.01f)transform.rotation=Quaternion.LookRotation(d);}
                // Own original seated action, only where present. No cross-rig pose copy.
                string seat=(actor.resource.EndsWith("hm09") || actor.resource.EndsWith("hm05"))?"hm05_003":actor.resource.EndsWith("hm00")?"hm00_003":null;
                if(!farmer && !string.IsNullOrEmpty(seat) && actor.ActivityLength(seat)>0)actor.PlayActivity(seat,true,.8f);
                else if(farmer && actor.ActivityLength("hm00_003")>0)actor.PlayActivity("hm00_003",true,.7f);
            }
            var playerRoom=NativeHomeRoom.At(game.Player.transform.position);
            bool visible=indoors?playerRoom==home:!playerRoom;
            actor.SetVenueVisible(visible);
        }
        void SetPosition(Vector3 p){transform.position=p;if(body)body.position=p;}
        void OnDisable(){if(actor)actor.EndActivity();if(resident)resident.enabled=true;}
    }
}
