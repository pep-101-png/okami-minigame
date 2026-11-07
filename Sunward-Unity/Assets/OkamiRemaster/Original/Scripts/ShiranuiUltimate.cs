using UnityEngine;
namespace Sunward.Remaster
{
    // Original source poses and paintings; the cinematic direction is Sunward's.
    [DefaultExecutionOrder(-200)]
    public sealed class ShiranuiUltimate:MonoBehaviour
    {
        public const float BlastTime=4.65f,Duration=6.8f;
        public GameFlow game;public bool Playing{get;private set;}public bool Used{get;private set;}
        public bool Detonated=>exploded;public Vector3 SunCentre{get;private set;}
        float time,facingYaw,cameraYaw;Vector3 origin;Quaternion facing;OrbitCamera orbit;NativeAmaterasu body;SolarPaint gather,blast;Light sunlight;GameObject lightRoot;bool exploded,bossApplied;
        public bool Ready=>game && game.InTrial && !Used && !Playing && !game.Blocked && game.Health>0 && !game.Player.Locked && game.Player.Grounded && game.Player.GetComponent<NativeAmaterasu>() && game.Player.GetComponent<NativeAmaterasu>().FullPower && game.Enemies.Exists(e=>e && !e.Dead);
        public void ResetFight(){Cancel();Used=false;}
        public bool Begin()
        {
            if(!Ready)return false;body=game.Player.GetComponent<NativeAmaterasu>();if(!body.BeginSolarPose())return false;
            Used=Playing=true;time=0;exploded=bossApplied=false;origin=game.Player.transform.position;facing=game.Player.transform.rotation;facingYaw=game.Player.transform.eulerAngles.y;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;
            Vector3 inward=new Vector3(35-origin.x,0,-origin.z);
            cameraYaw=inward.sqrMagnitude>36?Mathf.Atan2(-inward.x,-inward.z)*Mathf.Rad2Deg:facingYaw;
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();game.Audio.FullPowerVoice();
            gather=SolarPaint.Create(game,origin,0);lightRoot=new GameObject("Sunburst · charging light");sunlight=lightRoot.AddComponent<Light>();sunlight.color=new Color(1,.65f,.15f);sunlight.range=30;sunlight.intensity=0;
            Frame();return true;
        }
        void Update()
        {
            if(!game || !game.Player){Cancel();return;}
            if(!Playing){if(game.Player.input.Ultimate.WasPressedThisFrame())Begin();return;}
            if(game.Health<=0 || !game.InTrial){Cancel();return;}
            time+=Time.unscaledDeltaTime;if(!exploded && time>=BlastTime)Explode();Frame();if(time>=Duration)Resolve();
        }
        void Frame()
        {
            float rise=Mathf.SmoothStep(0,1,time/2.1f),fall=Mathf.SmoothStep(0,1,(time-BlastTime-.15f)/1.75f),heat=Mathf.SmoothStep(0,1,time/BlastTime);
            float angle=rise*Mathf.PI*2.2f,radius=Mathf.Sin(rise*Mathf.PI)*.85f;
            SunCentre=origin+new Vector3(Mathf.Sin(angle)*radius,1.1f+rise*4.9f*(1-fall),Mathf.Cos(angle)*radius);
            game.Player.Teleport(origin+Vector3.up*(rise*4.9f*(1-fall)));game.Player.transform.rotation=facing*Quaternion.Euler(0,rise*300*(1-fall),Mathf.Sin(rise*Mathf.PI)*-12);
            if(body)body.SolarPose(time,SunCentre,fall);
            if(gather)gather.Gather(SunCentre,heat);
            if(sunlight){sunlight.transform.position=SunCentre;sunlight.intensity=exploded?Mathf.Lerp(7,0,Mathf.Clamp01((time-BlastTime)/.65f)):Mathf.Lerp(.5f,5,heat*heat);sunlight.color=Color.Lerp(new Color(1,.45f,.06f),new Color(1,.96f,.72f),heat);}
            game.Audio.SolarCharge(exploded?0:heat);
            if(orbit)
            {
                float blastView=Mathf.SmoothStep(0,1,(time-BlastTime+.3f)/.65f);Vector3 focus=Vector3.Lerp(SunCentre,new Vector3(35,origin.y+1.3f,0),blastView);
                orbit.CinematicFrame(focus,cameraYaw+Mathf.Lerp(-28,28,rise),Mathf.Lerp(16,32,blastView),Mathf.Lerp(Mathf.Lerp(10,14,heat),37,blastView),Mathf.Lerp(44,60,blastView));
                if(time>Duration-.4f)orbit.ReturnCinematic(Mathf.SmoothStep(0,1,(time-Duration+.4f)/.4f));
            }
        }
        void Explode()
        {
            if(exploded)return;exploded=true;if(gather){Destroy(gather.gameObject);gather=null;}
            blast=SolarPaint.Create(game,origin,1);game.Audio.SolarExplosion();if(orbit)orbit.Shake(.42f,.75f);
            // Kill at the flash so the camera shows the result; boss rebirth owns
            // a separate camera and therefore waits until this camera is returned.
            foreach(var enemy in game.Enemies.ToArray())if(enemy && !enemy.Dead && enemy.definition.id!="boss")enemy.SunburstHit(origin);
        }
        public void Skip(){if(!Playing)return;Explode();Resolve();}
        void Resolve()
        {
            var targets=game.Enemies.ToArray();Finish(false);
            if(!bossApplied){bossApplied=true;foreach(var enemy in targets)if(enemy && !enemy.Dead && enemy.definition.id=="boss")enemy.Damage(enemy.MaxHp+1,(enemy.transform.position-origin).normalized,.7f);}
            game.Notify("Celestial Sunburst · ultimate spent for this fight");
        }
        void Finish(bool cancelled)
        {
            Playing=false;game?.Audio?.SolarCharge(0,true);if(body)body.EndSolarPose();
            if(game && game.Player){game.Player.Teleport(origin);game.Player.transform.rotation=facing;game.Player.Locked=game.Health<=0;game.Player.animationView.Play("Idle_Natural",.18f,0,true);}
            if(orbit)orbit.EndCinematic();if(gather)Destroy(gather.gameObject);if(lightRoot)Destroy(lightRoot);if(cancelled && blast)Destroy(blast.gameObject);gather=null;sunlight=null;lightRoot=null;
        }
        public void Cancel(){if(Playing)Finish(true);}
        void OnDisable(){Cancel();}
    }
}
