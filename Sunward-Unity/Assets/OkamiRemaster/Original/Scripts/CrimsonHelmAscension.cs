using UnityEngine;
namespace Sunward.Remaster
{
    // New Sunward phase direction using EM11's original skeletal group,
    // EM65_032 motion and core flame artwork. Not a recovered EST/SEQ cutscene.
    [DefaultExecutionOrder(-250)]
    public sealed class CrimsonHelmAscension : MonoBehaviour
    {
        const float Duration=3.4f,RevealTime=1.05f;
        EnemyBrain boss;
        OriginalActor actor;
        GameFlow game;
        OrbitCamera orbit;
        ParticleSystem flames;
        Light glow;
        GameObject lightRoot;
        Texture2D ink;
        bool pending,playing,revealed;
        float elapsed,fromScale=1,toScale=2;
        int targetPhase;
        public bool Playing=>pending || playing;
        public void Initialise(EnemyBrain owner,OriginalActor native)
        {boss=owner;actor=native;game=owner.game;ApplyForm(1,false);}
        public void Begin(EnemyBrain owner,OriginalActor native)
        {
            if(Playing)return;
            boss=owner;actor=native;game=owner.game;pending=true;revealed=false;targetPhase=boss.BossPhase+1;fromScale=boss.BossScale;toScale=fromScale*2;
            // Defer combat cancellation until Update: Begin can be called
            // from inside WolfCombat's damage/contact iteration.
            game.TrackBossTransformation(this);
        }
        void StartSequence()
        {
            pending=false;playing=true;elapsed=0;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;Time.timeScale=0;
            game.Player.animationView.Play("Idle_Natural",.12f,0,true);
            Vector3 away=game.Player.transform.position-boss.transform.position;away.y=0;
            float clearance=Mathf.Min(23,6*toScale);
            if(away.magnitude<clearance)
            {
                if(away.sqrMagnitude<.01f)away=LowerArena.Centre-boss.transform.position;
                if(away.sqrMagnitude<.01f)away=Vector3.back;
                Vector3 destination=boss.transform.position+away.normalized*clearance;
                if(new Vector2(destination.x-35,destination.z).magnitude>28)
                {away=LowerArena.Centre-boss.transform.position;away.y=0;destination=boss.transform.position+away.normalized*clearance;}
                destination=LowerArena.Guard(destination);
                if(LowerArena.Height(destination,out float floor))destination.y=floor+.1f;
                game.Player.Teleport(destination);
            }
            if(actor && actor.Ready)actor.BeginBossCinematic();
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();
            ink=Resources.Load<Texture2D>("Okami/UI/Ink");
            game.Audio.BossTransformationVoice();
            Frame();
        }
        void Update()
        {
            if(!Playing)return;
            if(!game || !boss || !game.InTrial || !game.BossTrial){Cancel();return;}
            if(pending)StartSequence();
            elapsed+=Time.unscaledDeltaTime;
            if(elapsed>=RevealTime)Reveal();
            float grow=Mathf.SmoothStep(0,1,(elapsed-.65f)/1.85f);
            boss.SetRebirthScale(Mathf.Lerp(fromScale,toScale,grow));
            Frame();
            if(elapsed>=Duration)Finish();
        }
        void Reveal()
        {
            if(revealed)return;revealed=true;
            ApplyForm(targetPhase,true);game.Audio.Cue("flame");
        }
        void ApplyForm(int phase,bool unscaled)
        {
            if(!actor || !actor.SetCrimsonPhase(phase))
                Debug.LogError("Crimson Helm's original phase body is unavailable. Reimport the EM11 body and original WP19 armour assets.",this);
            if(flames){Destroy(flames.gameObject);flames=null;}
            if(lightRoot){Destroy(lightRoot);lightRoot=null;glow=null;}
            if(phase==2)return;
            float size=phase==3?2:1;
            flames=OriginalAtmosphere.Create("Flame",transform,Vector3.zero,phase==3?145:95,1.1f*size,1.15f,.28f);
            if(flames)
            {
                var main=flames.main;main.useUnscaledTime=unscaled;main.startSize=new ParticleSystem.MinMaxCurve(.65f*size,1.3f*size);
                if(actor && actor.CrimsonSurface)
                {var shape=flames.shape;shape.enabled=true;shape.shapeType=ParticleSystemShapeType.SkinnedMeshRenderer;shape.skinnedMeshRenderer=actor.CrimsonSurface;shape.meshShapeType=ParticleSystemMeshShapeType.Triangle;}
                flames.Emit(35);
            }
            lightRoot=new GameObject("Crimson Helm native flame glow");lightRoot.transform.SetParent(transform,false);lightRoot.transform.localPosition=Vector3.up*(phase==3?5:2);
            glow=lightRoot.AddComponent<Light>();glow.type=LightType.Point;glow.range=phase==3?24:15;glow.intensity=phase==3?38:24;glow.color=new Color(1,.3f,.08f);
        }
        void Frame()
        {
            float p=Mathf.Clamp01(elapsed/Duration),s=Mathf.SmoothStep(0,1,p);
            if(orbit)
            {
                orbit.CinematicFrame(boss.transform.position+Vector3.up*(1.7f*Mathf.Lerp(fromScale,toScale,s)),boss.transform.eulerAngles.y+Mathf.Lerp(-52,28,s),17,Mathf.Lerp(13*Mathf.Sqrt(fromScale),19*Mathf.Sqrt(toScale),s),40);
                orbit.ReturnCinematic(Mathf.SmoothStep(0,1,(elapsed-(Duration-.45f))/.45f));
            }
        }
        void Finish()
        {Reveal();boss.CompleteRebirth();Cleanup(true);game.Notify(targetPhase==2?"CRIMSON HELM · ARMOUR SHATTERED":"CRIMSON HELM · SKELETAL INFERNO");}
        public void Skip()
        {
            if(!Playing)return;
            if(pending)StartSequence();
            Finish();
        }
        public void Cancel(){if(Playing)Cleanup(false);}
        void Cleanup(bool keepFlames)
        {
            pending=playing=false;
            if(actor)actor.EndBossCinematic();
            if(orbit)orbit.EndCinematic();
            if(keepFlames && flames){var main=flames.main;main.useUnscaledTime=false;}
            else if(flames){Destroy(flames.gameObject);flames=null;}
            if(!keepFlames && lightRoot){Destroy(lightRoot);lightRoot=null;glow=null;}
            if(game)
            {
                game.ReleaseBossTransformation(this);game.Audio.StopTransformation();
                if(game.Player){game.Player.Locked=game.Health<=0;game.Player.animationView.Play("Idle_Natural",.12f,0,true);}
                Time.timeScale=game.Panel=="pause"?0:1;
            }
        }
        void OnGUI()
        {
            if(!playing || !ink)return;
            float fade=Mathf.Min(Mathf.Clamp01(elapsed/.2f),Mathf.Clamp01((Duration-elapsed)/.35f));
            Color previous=GUI.color;GUI.color=new Color(0,0,0,fade);
            GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height*.065f),ink);
            GUI.DrawTexture(new Rect(0,Screen.height*.935f,Screen.width,Screen.height*.065f),ink);GUI.color=previous;
        }
        void OnDisable(){Cancel();}
        void OnDestroy(){Cancel();}
    }
}
