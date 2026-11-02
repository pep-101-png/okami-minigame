using UnityEngine;
namespace Sunward.Remaster
{
    // Original child and dog models with their own recovered locomotion banks.
    // Ball movement and routes are Sunward gameplay, not invented skeletal clips.
    public sealed class VillageStreetPlay : MonoBehaviour
    {
        public GameFlow game;
        public bool Ready {get;private set;}
        readonly OriginalActor[] children=new OriginalActor[2],puppies=new OriginalActor[3];
        GameObject ball;
        Vector3 from,to;
        float phase;
        bool outbound=true;
        static readonly Vector3 A=new Vector3(-1.8f,0,-5.2f),B=new Vector3(1.8f,0,-1.3f);
        public static Vector3 BallPosition(float t,bool forward)
        {
            Vector3 p=Vector3.Lerp(forward?A:B,forward?B:A,Mathf.Clamp01(t));
            p.y=.18f+Mathf.Sin(Mathf.Clamp01(t)*Mathf.PI)*.065f;return p;
        }
        void Start()
        {
            if(!game)game=GetComponent<GameFlow>();if(!game)return;
            children[0]=Actor("Original red-clothed village child","hm1c","hm1c_000","hm1c_011",.9618765f,-.010982f,A-Vector3.right*.8f);
            children[1]=Actor("Original yellow-clothed village child","hm1d","hm1c_000","hm1c_011",.9143342f,.0086383f,B+Vector3.right*.8f);
            for(int i=0;i<puppies.Length;i++)puppies[i]=Actor("Original village puppy "+(i+1),"an05","an18_000","an18_011",.48152315f*(.9f+i*.06f),.006065f,A+new Vector3(i*.65f-1,0,-1.1f));
            ball=new GameObject("Original ET50 patterned play ball");ball.transform.SetParent(transform,false);
            // Original model, centred so rolling does not orbit its old origin.
            ball.AddComponent<OriginalVisual>().Load("Okami/et50",new Vector3(.00165f,-.02013f,-.00174f),Vector3.one*.13658f);
            from=A;to=B;ball.transform.position=Floor(BallPosition(0,true));Ready=true;
        }
        OriginalActor Actor(string label,string model,string idle,string gait,float scale,float offset,Vector3 position)
        {
            // Unity invokes OriginalActor.Awake on activation. Configure its source
            // while inactive so Awake never tries to load an empty resource path.
            var obj=new GameObject(label);obj.SetActive(false);obj.transform.SetParent(transform,false);position.y=game.valley.Height(position)+.025f;obj.transform.position=position;
            var actor=obj.AddComponent<OriginalActor>();actor.game=game;actor.resource="Okami/"+model;actor.idle=idle;actor.walk=actor.run=gait;actor.windup=actor.strike=actor.recover=actor.death=idle;actor.modelScale=scale;actor.modelOffset=Vector3.up*offset;actor.walkMetresPerSecond=model=="an05"?1.05f:1.25f;obj.SetActive(true);return actor;
        }
        Vector3 Floor(Vector3 p){float height=p.y;p.y=game.valley.Height(p)+height;return p;}
        void Move(OriginalActor actor,Vector3 target,float speed)
        {
            if(!actor)return;
            var p=actor.transform.position;target.y=p.y;
            if(game.Player)
            {
                var away=p-game.Player.transform.position;away.y=0;
                if(away.sqrMagnitude<1.25f*1.25f && away.sqrMagnitude>.01f)target+=away.normalized*.75f;
            }
            target.x=Mathf.Clamp(target.x,-2.7f,2.7f);target.z=Mathf.Clamp(target.z,-6.9f,.1f);
            var next=Vector3.MoveTowards(p,target,speed*Time.deltaTime);next.y=game.valley.Height(next)+.025f;
            var d=next-p;d.y=0;if(d.sqrMagnitude>.00001f)actor.transform.rotation=Quaternion.Slerp(actor.transform.rotation,Quaternion.LookRotation(d),Time.deltaTime*8);
            actor.transform.position=next;
        }
        void Update()
        {
            if(!Ready || !game || game.Blocked)return;
            phase+=Time.deltaTime/3.6f;
            if(phase>=1){phase-=1;outbound=!outbound;from=outbound?A:B;to=outbound?B:A;}
            var p=BallPosition(phase,outbound);ball.transform.position=Floor(p);ball.transform.Rotate(180*Time.deltaTime,0,65*Time.deltaTime);
            var direction=(to-from).normalized;var active=outbound?0:1;
            Move(children[active],ball.transform.position-direction*.75f,1.3f);
            Move(children[1-active],to+new Vector3(outbound?.5f:-.5f,0,.5f),.9f);
            for(int i=0;i<puppies.Length;i++)
            {
                float angle=Time.time*(.7f+i*.13f)+i*2.1f;
                var around=new Vector3(Mathf.Cos(angle)*.8f,0,Mathf.Sin(angle)*.65f);
                Move(puppies[i],ball.transform.position+around,1.1f+i*.08f);
            }
        }
    }
}
