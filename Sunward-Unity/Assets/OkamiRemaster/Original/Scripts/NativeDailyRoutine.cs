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
        bool indoors, resting,teaVisit;
        public void InviteForTea(NativeHomeRoom room){home=room;teaVisit=true;destination=-1;wait=0;resting=false;if(actor)actor.EndActivity();}
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
            if(!home && !farmer)home=NativeHomeRoom.For(seed);
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
            int phase=farmer && game.Profile.night?4:teaVisit?1:farmer?(int)((Time.time+seed*7)/16)%4:(int)((Time.time+seed*13)/40)%4;
            if(wait>0){wait-=Time.deltaTime;return;}
            if(farmer && Vector3.Distance(transform.position,game.Player.transform.position)<3.2f){actor.EndActivity();return;}
            if(phase!=destination)
            {
                destination=phase;resting=false;actor.EndActivity();
                if(indoors && home){SetPosition(home.exitPoint);indoors=false;}
                var target=farmer && game.Profile.night?new Vector3(37.2f,0,18.2f):farmer?workplace+(phase==0?Vector3.zero:phase==1?new Vector3(7,0,0):phase==2?new Vector3(10,0,1.5f):new Vector3(2,0,2.8f)):phase==1 && home?home.Approach:phase==2?new Vector3(GardenPond.X+Mathf.Cos((seed*47+20)*Mathf.Deg2Rad)*4.25f,0,GardenPond.Z+Mathf.Sin((seed*47+20)*Mathf.Deg2Rad)*2.9f):workplace;
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
                if(!farmer && phase==1 && home){SetPosition(teaVisit?home.transform.position+new Vector3(.7f,.02f,-.7f):home.bed+new Vector3(.8f,0,0));indoors=true;}
                if(!farmer && phase==2){var d=new Vector3(GardenPond.X,transform.position.y,GardenPond.Z)-transform.position;if(d.sqrMagnitude>.01f)transform.rotation=Quaternion.LookRotation(d);}
                // Own original seated action, only where present. No cross-rig pose copy.
                string seat=(actor.resource.EndsWith("hm09") || actor.resource.EndsWith("hm05"))?"hm05_003":actor.resource.EndsWith("hm00")?"hm00_003":null;
                if(!farmer && !string.IsNullOrEmpty(seat) && actor.ActivityLength(seat)>0)actor.PlayActivity(seat,true,.8f);
                else if(farmer && actor.ActivityLength("hm00_003")>0)actor.PlayActivity("hm00_003",true,.7f);
            }
            var playerRoom=NativeHomeRoom.At(game.Player.transform.position);
            bool visible=indoors?playerRoom==home:!playerRoom && !VillageInteriors.Inside(game.Player.transform.position);
            actor.SetVenueVisible(visible);
        }
        void SetPosition(Vector3 p){transform.position=p;if(body)body.position=p;}
        void OnDisable(){if(actor)actor.EndActivity();if(resident)resident.enabled=true;}
    }
}
