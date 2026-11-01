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
        public string seatedMotion, handMotion;
        public float seed;
        public bool contactEnabled=true;
        public bool archer;
        public float releasePhase=.2f;
        GameFlow game;
        bool ready, performing, contacted;
        float timer, elapsed, length;
        public bool Performing=>performing;
        public float ActivityPhase=>performing?Mathf.Clamp01(elapsed/Mathf.Max(.01f,length)):0;
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
                if(role!="training")
                {
                    if(string.IsNullOrEmpty(seatedMotion))seatedMotion=actor.idle;
                    actor.seatedArmMotion=handMotion;
                    actor.PlayActivity(seatedMotion,true,.65f,Mathf.Repeat(seed,.9f));
                }
            }
            timer-=Time.deltaTime;
            if(role=="training")
            {
                if(!dummy)return;
                if(!dummy.game)dummy.game=game;
                Vector3 direction=dummy.transform.position-transform.position;direction.y=0;
                if(direction.sqrMagnitude>.001f)transform.rotation=Quaternion.LookRotation(direction);
                if(performing)
                {
                    elapsed+=Time.deltaTime;
                    if(contactEnabled && !contacted && elapsed>=length*(archer?releasePhase:.42f))
                    {
                        contacted=true;
                        if(archer){PracticeArrow.Fire(transform.position+Vector3.up*1.3f+direction.normalized*.65f,dummy);game.Audio.World("attack",transform.position,8,.12f);}
                        else if(direction.magnitude<3.2f){dummy.PracticeContact();BrushStrokeFlash.Slash(transform.position+Vector3.up*1.2f,dummy.transform.position+Vector3.up);CelestialBrush.Burst("Spark",dummy.transform.position+Vector3.up,5,.2f);}
                    }
                }
                if(timer>0)return;
                performing=!performing;
                if(performing)
                {
                    length=Mathf.Max(.6f,actor.ActivityLength(motion));elapsed=0;contacted=false;
                    actor.PlayActivity(archer?actor.idle:motion,archer);timer=length;
                }
                else{actor.EndActivity();timer=archer?1.4f+Mathf.Repeat(seed,1):.55f+Mathf.Repeat(seed,.65f);}
            }
            // Seated actors keep their own native seated clip. Their own arm
            // clip is layered without copying pelvis/leg translations from a
            // different rig or a standing gesture.
        }
    }
}
