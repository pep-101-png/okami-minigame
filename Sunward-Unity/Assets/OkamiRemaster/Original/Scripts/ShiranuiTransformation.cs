using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    // Cinematic direction around original PL animation, PL0D/ES3A skins and original
    // core sprites/audio. This is not a recovered original game cutscene.
    [DefaultExecutionOrder(-250)]
    public sealed class ShiranuiTransformation : MonoBehaviour
    {
        public GameFlow game;
        readonly TransformationTimeline timeline=new TransformationTimeline();
        readonly List<GameObject> effects=new List<GameObject>();
        NativeAmaterasu body;
        OrbitCamera orbit;
        Light glow;
        ParticleSystem gathering;
        Texture2D ink;
        bool ownsControl,returning,fullPower;int targetForm;
        public bool Playing=>ownsControl;
        // P deliberately remains the unrestricted testing shortcut.
        public void Begin(NativeAmaterasu player)=>BeginAt(player,(player.FormLevel+1)%3);
        public void BeginEarned(NativeAmaterasu player)
        {
            int unlocked=game.Profile.shiranuiUnlock;
            if(unlocked<=0){game.Notify("The sleeping wolf's light has not yet answered.");return;}
            BeginAt(player,(player.FormLevel+1)%(unlocked+1));
        }
        public void Reveal(NativeAmaterasu player,int form)=>BeginAt(player,form,true);
        void BeginAt(NativeAmaterasu player,int form,bool reveal=false)
        {
            if(!game || !player || !player.Ready || Playing || game.Blocked || game.Health<=0 || (!reveal && !game.Player.Grounded) || game.Player.Locked || game.Player.Swimming)return;
            targetForm=form;fullPower=targetForm==2;if(!player.PreparePowerForm(targetForm))return;
            body=player;returning=targetForm==0;
            game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;ownsControl=true;timeline.Begin();Time.timeScale=0;if(fullPower)game.Audio.FullPowerVoice();
            game.Player.animationView.Play("Idle_Natural",.1f,0,true);
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();
            ink=Resources.Load<Texture2D>("Okami/UI/Ink");
            gathering=Particles("SpiritGlow",18,.22f,1.2f,-1.1f,2.2f,new Color(.7f,.87f,1,.65f));
            var lightObject=new GameObject("Shiranui reveal light");effects.Add(lightObject);
            lightObject.transform.position=game.Player.transform.position+Vector3.up*1.5f;
            glow=lightObject.AddComponent<Light>();glow.type=LightType.Point;glow.range=9;glow.color=new Color(.65f,.82f,1);glow.intensity=0;
            Frame();
        }
        ParticleSystem Particles(string sprite,float rate,float size,float life,float speed,float radius,Color color)
        {
            var p=OriginalAtmosphere.Create(sprite,null,game.Player.transform.position+Vector3.up*.9f,rate,size,life,speed,radius);
            if(p){var main=p.main;main.useUnscaledTime=true;main.startColor=color;effects.Add(p.gameObject);}
            return p;
        }
        void Update()
        {
            if(!Playing)return;
            if(!game || !game.Player || !body){Cancel();return;}
            Handle(timeline.Tick(Time.unscaledDeltaTime/(fullPower?2:1)));
            if(Playing)Frame();
        }
        void Handle(TransformationCue cue)
        {
            if((cue&TransformationCue.Voice)!=0)
            {
                game.Player.animationView.Play("Bark",.14f,1.9333333f,true);
                game.Audio.TransformationVoice();
            }
            if((cue&TransformationCue.Reveal)!=0)
            {
                if(gathering){var emission=gathering.emission;emission.rateOverTime=0;}
                if(!body.ApplyPowerForm(targetForm)){Cancel();return;}
                game.Audio.TransformationBurst();if(fullPower){game.Player.animationView.Play("Bark",.18f,1.9333333f,true);}
                if(fullPower){var ring=Particles("OriginalWhiteRing",0,7,.8f,0,0,new Color(1,.9f,.55f,.8f));if(ring)ring.Emit(1);var seal=Particles("OriginalElectricity",0,5,.7f,0,0,new Color(1,.9f,.4f,.75f));if(seal)seal.Emit(1);}
                var flare=Particles("Spirit",0,2.5f,.55f,0,0,new Color(.75f,.9f,1,.85f));if(flare)flare.Emit(1);
                var burst=Particles("SpiritGlow",0,.65f,.85f,3.8f,.45f,new Color(.72f,.88f,1,.8f));if(burst)burst.Emit(fullPower?135:45);
                var sparks=Particles("Spark",0,.22f,.7f,4.3f,.35f,Color.white);if(sparks)sparks.Emit(fullPower?96:32);
                var leaves=Particles("Leaf",0,.18f,1.3f,2.3f,.8f,new Color(.8f,.93f,1,.8f));if(leaves)leaves.Emit(fullPower?72:24);
            }
            if((cue&TransformationCue.Settle)!=0)game.Player.animationView.Play("Idle_Natural",.22f,0,true);
            if((cue&TransformationCue.Finish)!=0)Finish();
        }
        void Frame()
        {
            float p=Mathf.Clamp01(timeline.Elapsed/TransformationTimeline.Duration),s=Mathf.SmoothStep(0,1,p);
            if(glow)glow.intensity=(fullPower?24:12)*Mathf.Pow(Mathf.Sin(p*Mathf.PI),2)+(fullPower?65:30)*Mathf.Exp(-Mathf.Pow((timeline.Elapsed-TransformationTimeline.RevealTime)/.18f,2));
            if(orbit)
            {
                orbit.CinematicFrame(game.Player.transform.position+Vector3.up*.95f,game.Player.transform.eulerAngles.y+Mathf.Lerp(fullPower?-110:-65,fullPower?80:24,s),Mathf.Lerp(12,fullPower?26:19,s),Mathf.Lerp(fullPower?6.2f:5.4f,fullPower?9.5f:6.8f,s),Mathf.Lerp(37,43,s));
                orbit.ReturnCinematic(Mathf.SmoothStep(0,1,(timeline.Elapsed-(TransformationTimeline.Duration-.4f))/.4f));
            }
        }
        public void Skip(){if(Playing)Handle(timeline.Skip());}
        void Finish()
        {
            Cleanup();
            if(game)game.Notify(returning?"Amaterasu · spirit restored":fullPower?"Shiranui full power · 20% larger · 10% stronger than awakened form":"Shiranui awakened · double strength, speed and attack speed");
        }
        public void Cancel(){if(Playing)Cleanup();}
        void Cleanup()
        {
            timeline.Cancel();ownsControl=false;
            if(orbit)orbit.EndCinematic();
            if(game)
            {
                if(game.Audio)game.Audio.StopTransformation();
                if(game.Player){game.Player.Locked=false;game.Player.animationView.Play("Idle_Natural",.15f,0,true);}
                Time.timeScale=game.Panel=="pause"?0:1;
            }
            foreach(var effect in effects)if(effect)Destroy(effect);effects.Clear();glow=null;gathering=null;
        }
        void OnGUI()
        {
            if(!Playing || !ink)return;
            float t=timeline.Elapsed;
            float alpha=Mathf.Min(Mathf.Clamp01(t/.25f),Mathf.Clamp01((TransformationTimeline.Duration-t)/.3f));
            var previous=GUI.color;GUI.color=new Color(0,0,0,alpha);
            GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height*.065f),ink);
            GUI.DrawTexture(new Rect(0,Screen.height*.935f,Screen.width,Screen.height*.065f),ink);
            GUI.color=previous;
        }
        void OnDisable(){Cancel();}
        void OnDestroy(){Cancel();}
    }
}
