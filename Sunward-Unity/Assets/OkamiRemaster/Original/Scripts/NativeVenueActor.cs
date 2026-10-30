using UnityEngine;

namespace Sunward.Remaster
{
    // The native bank owns every skeletal pose. This controller schedules those
    // curves, faces trainees toward their dummy and gives quiet contact feedback.
    public sealed class NativeVenueActor : MonoBehaviour
    {
        public OriginalActor actor;
        public TrainingDummy dummy;
        public string role, motion;
        public float seed;
        GameFlow game;
        bool ready, performing, contacted;
        float timer, elapsed, length;
        void OnEnable(){ready=false;}
        void Update()
        {
            if(!actor)actor=GetComponent<OriginalActor>();
            if(!actor || !actor.Ready)return;
            if(!game)game=FindFirstObjectByType<GameFlow>();
            if(!game)return;
            actor.game=game;
            if(game.Blocked)return;
            if(!ready)
            {
                ready=true;timer=.5f+Mathf.Repeat(seed,2.5f);performing=false;
                if(role!="training")actor.PlayActivity("venue_seated",true,.75f,Mathf.Repeat(seed,.9f));
            }
            timer-=Time.deltaTime;
            if(role=="training")
            {
                if(!dummy)return;
                Vector3 direction=dummy.transform.position-transform.position;direction.y=0;
                if(direction.sqrMagnitude>.001f)transform.rotation=Quaternion.LookRotation(direction);
                if(performing)
                {
                    elapsed+=Time.deltaTime;
                    if(!contacted && elapsed>=length*.58f && direction.magnitude<3.2f)
                    {contacted=true;dummy.PracticeContact();}
                }
                if(timer>0)return;
                performing=!performing;
                if(performing)
                {
                    length=Mathf.Max(.6f,actor.ActivityLength(motion));elapsed=0;contacted=false;
                    actor.PlayActivity(motion,false);timer=length;
                }
                else{actor.EndActivity();timer=1.3f+Mathf.Repeat(seed,1.7f);}
            }
            else if(timer<=0)
            {
                performing=!performing;
                actor.PlayActivity(performing?"venue_hands":"venue_seated",true,role=="musician"?.8f:.65f,Mathf.Repeat(seed,.7f));
                timer=role=="musician"?3.5f:4.5f+Mathf.Repeat(seed,3);
            }
        }
    }
}
