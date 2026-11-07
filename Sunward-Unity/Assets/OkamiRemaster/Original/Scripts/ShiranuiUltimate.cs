using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    // Sunward cinematic attack built from recovered PL poses and original sun/fire paintings.
    [DefaultExecutionOrder(-200)]
    public sealed class ShiranuiUltimate:MonoBehaviour
    {
        public GameFlow game;public bool Playing{get;private set;}public bool Used{get;private set;}
        float time;Vector3 origin;Quaternion facing;OrbitCamera orbit;GameObject sun;bool exploded;
        readonly List<GameObject> effects=new List<GameObject>();
        public bool Ready=>game && game.InTrial && !Used && !Playing && !game.Blocked && game.Health>0 && !game.Player.Locked && game.Player.Grounded && game.Player.GetComponent<NativeAmaterasu>() && game.Player.GetComponent<NativeAmaterasu>().FullPower && game.Enemies.Exists(e=>e && !e.Dead);
        public void ResetFight(){Cancel();Used=false;}
        public bool Begin()
        {
            if(!Ready)return false;Used=Playing=true;time=0;exploded=false;origin=game.Player.transform.position;facing=game.Player.transform.rotation;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;game.Player.animationView.Play("Sleep_Down",.12f,.8f,true);
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic(false);game.Audio.FullPowerVoice();
            sun=Paint("OriginalSun",origin+Vector3.up*4,1,1,12,0,0);Paint("SpiritGlow",origin+Vector3.up,24,.25f,3,-.35f,2).name="Sunlight gathering";return true;
        }
        GameObject Paint(string name,Vector3 at,int count,float size,float life,float speed,float radius)
        {
            var p=OriginalAtmosphere.Create(name,null,at,0,size,life,speed,radius);if(!p)return new GameObject("Unavailable original ultimate paint");
            var main=p.main;main.useUnscaledTime=true;main.startRotation=0;main.startColor=new Color(1,.79f,.34f,.9f);if(name=="OriginalSun")main.simulationSpace=ParticleSystemSimulationSpace.Local;
            p.Emit(count);effects.Add(p.gameObject);return p.gameObject;
        }
        void Update()
        {
            if(!game || !game.Player)return;
            if(!Playing){if(game.Player.input.Ultimate.WasPressedThisFrame())Begin();return;}
            if(game.Health<=0){Cancel();return;}time+=Time.unscaledDeltaTime;
            if(time>.8f && time-Time.unscaledDeltaTime<=.8f)game.Player.animationView.Play("Sleep_Loop",.14f,0,true);
            float rise=Mathf.SmoothStep(0,1,(time-.5f)/2),fall=Mathf.SmoothStep(0,1,(time-5.2f)/1.1f);game.Player.Teleport(origin+Vector3.up*(3.8f*rise*(1-fall)));game.Player.transform.rotation=facing;
            if(sun){float size=Mathf.Lerp(.25f,9,Mathf.SmoothStep(0,1,time/5));sun.transform.localScale=Vector3.one*size;}
            if(orbit)orbit.CinematicFrame(origin+Vector3.up*2,game.Player.transform.eulerAngles.y+Mathf.Lerp(-65,55,time/6.5f),Mathf.Lerp(12,36,time/6.5f),Mathf.Lerp(8,24,Mathf.SmoothStep(0,1,(time-3.5f)/2)),43);
            if(!exploded && time>=5.2f)Explode();
            if(time>=6.5f)Resolve();
        }
        void Explode()
        {
            if(exploded)return;exploded=true;if(sun)sun.SetActive(false);Paint("SpiritGlow",origin+Vector3.up*2,1,48,.45f,0,0);var ring=Paint("OriginalWhiteRing",origin+Vector3.up*.2f,1,70,1.3f,0,0);var r=ring.GetComponent<ParticleSystemRenderer>();if(r)r.renderMode=ParticleSystemRenderMode.HorizontalBillboard;
            Paint("Flame",origin+Vector3.up*.5f,120,2.8f,1.5f,14,9);Paint("Spark",origin+Vector3.up,100,.7f,1.6f,18,8);game.Audio.SolarExplosion();
        }
        public void Skip(){if(!Playing)return;Explode();Resolve();}
        void Resolve()
        {
            var targets=game.Enemies.ToArray();Finish();
            foreach(var enemy in targets)if(enemy && !enemy.Dead)enemy.Damage(enemy.MaxHp+1,(enemy.transform.position-origin).normalized,.7f);
            game.Notify("Celestial Sunburst · ultimate spent for this fight");
        }
        void Finish()
        {
            Playing=false;if(orbit)orbit.EndCinematic();if(game && game.Player){game.Player.Teleport(origin);game.Player.transform.rotation=facing;game.Player.Locked=game.Health<=0;game.Player.animationView.Play("Idle_Natural",.2f,0,true);}
            foreach(var effect in effects)if(effect)Destroy(effect,exploded?1.5f:0);effects.Clear();sun=null;
        }
        public void Cancel(){if(Playing)Finish();}
        void OnDisable(){Cancel();}
    }
}
