#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using Sunward.Remaster;
namespace Sunward.Editor.Automation
{
    // Real Windflower Play Mode, original rigs, gameplay actions and audio.
    // A recording candidate still requires watching and ffprobe validation.
    public sealed class TrailerPlayback : MonoBehaviour
    {
        public static bool Active {get;private set;}
        public const int Width=3840,Height=2160,Fps=60,Frames=1800;
        GameFlow game;OrbitCamera orbit;Gamepad pad,previousPad;NativeAmaterasu body;
        string profile;Vector3 originalPoint;Quaternion originalRotation;float hp,stamina,ink;
        int oldCapture,oldRate,oldVsync,frame,shot=-1;bool restored,record,oldForm;
        FarmCrop[] crops;bool[] harvest;float[] regrow;
        UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset pipeline;float oldScale,oldShadowDistance,oldAudioVolume;int oldMsaa,oldCascades;
        RenderTexture target,oldTarget;Camera camera;RecorderVideoBridge recorder;
        string output,digOverride;float t;EnemyBrain boss;
        public static void Begin(GameFlow flow,bool capture)
        {
            if(Active || !flow || flow.CinematicActive || flow.Services.Resting || flow.GetComponent<FestivalChallenges>().Active || flow.InTrial || flow.Health<=0 || VillageInteriors.AnyRoom(flow.Player.transform.position) || flow.GetComponent<VillageLife>().Carrying)return;
            var go=new GameObject("Sunward thirty-second original-asset trailer");var film=go.AddComponent<TrailerPlayback>();film.StartFilm(flow,capture);
        }
        void StartFilm(GameFlow flow,bool capture)
        {
            var music=gameObject.AddComponent<AudioSource>();music.clip=Resources.Load<AudioClip>("Okami/NativeAudio/house-melody-67");music.loop=true;music.volume=.10f;if(music.clip)music.Play();
            game=flow;record=capture;Active=true;profile=JsonUtility.ToJson(game.Profile);originalPoint=game.Player.transform.position;originalRotation=game.Player.transform.rotation;
            hp=game.Health;stamina=game.Stamina;ink=game.Energy;oldAudioVolume=AudioListener.volume;AudioListener.volume=1;game.Save.PreviewOnly=true;
            crops=FindObjectsByType<FarmCrop>(FindObjectsSortMode.None);harvest=new bool[crops.Length];regrow=new float[crops.Length];for(int i=0;i<crops.Length;i++){harvest[i]=crops[i].Harvested;regrow[i]=crops[i].PreviewRegrowRemaining;}
            digOverride=game.Player.input.Dig.bindings[0].overridePath;
            game.Close();body=game.Player.GetComponent<NativeAmaterasu>();oldForm=body && body.Shiranui;if(oldForm)body.ApplyShiranuiForm();
            orbit=FindFirstObjectByType<OrbitCamera>();if(orbit)orbit.BeginCinematic();previousPad=Gamepad.current;pad=InputSystem.AddDevice<Gamepad>();pad.MakeCurrent();
            oldCapture=Time.captureFramerate;oldRate=Application.targetFrameRate;oldVsync=QualitySettings.vSyncCount;Time.captureFramerate=60;Application.targetFrameRate=60;QualitySettings.vSyncCount=0;
            game.Profile.coins=Mathf.Max(game.Profile.coins,10000);game.Energy=game.MaxEnergy;
            if(record)
            {
                pipeline=UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline as UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset;
                if(pipeline){oldScale=pipeline.renderScale;oldMsaa=pipeline.msaaSampleCount;oldShadowDistance=pipeline.shadowDistance;oldCascades=pipeline.shadowCascadeCount;pipeline.renderScale=1;pipeline.msaaSampleCount=4;pipeline.shadowDistance=100;pipeline.shadowCascadeCount=4;}
                camera=Camera.main;if(!camera){Debug.LogError("No gameplay camera available for trailer export.");Restore();Destroy(gameObject);return;}oldTarget=camera.targetTexture;target=new RenderTexture(Width,Height,24);target.Create();camera.targetTexture=target;
                output=Path.Combine(Application.persistentDataPath,"Trailers","Sunward-"+DateTime.Now.ToString("yyyyMMdd-HHmmss"));
                recorder=new RecorderVideoBridge();recorder.Start(target,Fps,output,true,true);
                if(recorder.status!="recording_candidate_unverified")
                {Debug.LogError("4K trailer export could not start: "+recorder.status+" "+recorder.detail+". Install Unity Recorder before recording. No video was produced.");Restore();Destroy(gameObject);return;}
            }
            digOverride=game.Player.input.Dig.bindings[0].overridePath;game.Player.input.Dig.ApplyBindingOverride(0,"<Gamepad>/dpad/up");
            StartCoroutine(CompleteAtFrameEnd());
        }
        void Place(Vector3 p,float yaw=0){p.y=game.valley.Height(p)+.04f;game.Player.Teleport(p);game.Player.transform.rotation=Quaternion.Euler(0,yaw,0);}
        void EnterShot(int next)
        {
            if(game.Transformation && game.Transformation.Playing)game.Transformation.Skip();
            if(game.BossTransformation && game.BossTransformation.Playing)game.BossTransformation.Skip();
            if(game.Presentation && game.Presentation.Playing)game.Presentation.Cancel();
            game.Combat.Cancel();game.Player.Locked=false;game.Player.StopMotion();
            if(orbit)orbit.BeginCinematic();
            switch(next)
            {
                case 0:game.Profile.night=false;Place(new Vector3(0,0,-21));break;
                case 1:Place(new Vector3(42,0,21),0);break;
                case 2:
                    game.GetComponent<VillageLife>().CancelDig();game.GetComponent<VillageLife>().ClearPreviewCarry();game.Profile.night=true;Place(new Vector3(0,0,-10));game.GetComponent<FestivalChallenges>().Begin(1);if(game.Presentation)game.Presentation.Cancel();if(orbit)orbit.BeginCinematic();break;
                case 3:
                    game.GetComponent<FestivalChallenges>().Cancel();Place(new Vector3(35,0,-7));game.StartTrial();break;
                case 4:
                    if(game.InTrial)game.Finish(false);game.Close();game.Profile.night=true;Place(new Vector3(-6,0,-27));game.Buy("weapon:wp29");game.Buy("strength");game.Combat.Equip();CelestialBrush.Burst("SpiritGlow",game.Player.transform.position+Vector3.up,18,.4f);game.Close();break;
                case 5:
                    Place(new Vector3(8,0,0));game.Player.Recover(game.Player.transform.position);game.Transformation.Begin(body);break;
                case 6:
                    LowerArena.RevealShaft();game.Player.Teleport(LowerArena.Centre+new Vector3(0,1,-8));game.StartBossTrial();game.Health=game.MaxHealth;foreach(var e in game.Enemies)if(e && e.definition.id=="boss")boss=e;
                    if(boss){boss.Damage(100000,Vector3.back,0);boss.GetComponent<CrimsonHelmAscension>().Skip();boss.Damage(100000,Vector3.back,0);boss.GetComponent<CrimsonHelmAscension>().Skip();}
                    if(orbit)orbit.BeginCinematic();break;
                case 7:
                    if(game.InTrial)game.Finish(true);game.Close();if(body && body.Shiranui)body.ApplyShiranuiForm();game.Profile.night=true;Place(new Vector3(-17,0,-23),0);
                    game.Player.Locked=true;game.Player.animationView.Play("Bark",.12f,1.933f,true);game.Audio.VictoryHowl();
                    var moon=VillageFestival.Place(transform,"Okami/trailer-moon",game.Player.transform.position+new Vector3(-3,11,22),new Vector3(8,8,.1f),new Vector3(0,0,0));if(moon)foreach(var r in moon.GetComponentsInChildren<Renderer>())r.sharedMaterial.shader=Resources.Load<Material>("Okami/Effects/Surface").shader;break;
            }
        }
        void Update()
        {
            if(restored || !game)return;
            if(Keyboard.current!=null && Keyboard.current.escapeKey.wasPressedThisFrame()){Restore();Destroy(gameObject);return;}
            t=frame/(float)Fps;int next=t<4?0:t<7?1:t<11?2:t<14?3:t<17?4:t<21?5:t<27?6:7;
            if(next!=shot){shot=next;EnterShot(shot);}
            Vector3 destination=game.Player.transform.position;bool move=false,attack=false,dig=false;
            if(shot==0){destination=new Vector3(0,0,-2);move=true;}
            if(shot==1)dig=frame==4*Fps+12;
            if(shot==2){float v=t-7;destination=v<1.3f?new Vector3(2,0,-2):v<2.6f?new Vector3(0,0,10):new Vector3(11,0,20);move=true;}
            if(shot==3 || shot==6)
            {
                EnemyBrain nearest=null;float distance=float.PositiveInfinity;
                foreach(var e in game.Enemies)if(e && !e.Dead){float d=Vector3.Distance(e.transform.position,game.Player.transform.position);if(d<distance){distance=d;nearest=e;}}
                if(nearest){destination=nearest.transform.position;move=distance>2.3f;attack=frame%28==2;}
                game.Health=game.MaxHealth;
                if(shot==6 && t>25.5f && boss && !boss.Dead)boss.Damage(100000,Vector3.back,0);
            }
            var forward=game.Player.view.forward;forward.y=0;forward.Normalize();var right=game.Player.view.right;right.y=0;right.Normalize();var direction=(destination-game.Player.transform.position);direction.y=0;direction=move?direction.normalized:Vector3.zero;
            var state=new GamepadState{leftStick=new Vector2(Vector3.Dot(direction,right),Vector3.Dot(direction,forward))};state=state.WithButton(GamepadButton.RightShoulder,attack).WithButton(GamepadButton.DpadUp,dig).WithButton(GamepadButton.LeftStick,shot==2 || (shot==0 && t>1.2f));
            // Dig has its own existing keyboard binding: use its existing action's
            // temporary gamepad binding, never call a fabricated animation pose.
            if(pad!=null)InputSystem.QueueStateEvent(pad,state);
            if(!game.CinematicActive && orbit)
            {
                float phase=shot==0?t/4:shot==6?(t-21)/6:shot==7?(t-27)/3:(t%3)/3;
                orbit.BeginCinematic();orbit.CinematicFrame(game.Player.transform.position+Vector3.up*(shot==7?3.8f:1),shot==7?0:Mathf.Lerp(32,65,phase),shot==7?-8:shot==1?38:23,shot==7?12:shot==6?18:shot==1?12:14,shot==7?50:48);
            }
            frame++;
        }
        IEnumerator CompleteAtFrameEnd()
        {
            while(frame<Frames && !restored)yield return new WaitForEndOfFrame();
            yield return new WaitForEndOfFrame();if(restored)yield break;
            string candidate=recorder!=null?recorder.candidate:"";Restore();
            if(record)Debug.Log("Trailer candidate: "+candidate+". Requested 3840x2160, 60 fps, 30 seconds; not yet visually or technically verified.");
            Destroy(gameObject);
        }
        void OnGUI(){if(record && target && Active)GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height),target,ScaleMode.ScaleToFit);}
        void Restore()
        {
            if(restored)return;restored=true;
            if(recorder!=null)recorder.Dispose();if(camera)camera.targetTexture=oldTarget;if(target){target.Release();Destroy(target);}
            if(game)
            {
                if(game.Transformation)game.Transformation.Cancel();if(game.BossTransformation)game.BossTransformation.Cancel();if(game.Presentation)game.Presentation.Cancel();
                game.GetComponent<VillageLife>().CancelDig();game.GetComponent<VillageLife>().ClearPreviewCarry();game.GetComponent<FestivalChallenges>().Cancel();if(game.InTrial)game.Finish(false);game.Close();game.ReturnHome();
                JsonUtility.FromJsonOverwrite(profile,game.Profile);game.Save.PreviewOnly=false;game.Health=hp;game.Stamina=stamina;game.Energy=ink;game.Combat.Equip();
                for(int i=0;i<crops.Length;i++)if(crops[i])crops[i].RestorePreview(harvest[i],regrow[i]);
                if(body && body.Shiranui!=oldForm)body.ApplyShiranuiForm();game.Player.Teleport(originalPoint);game.Player.transform.rotation=originalRotation;game.Player.Locked=false;
                if(digOverride==null)game.Player.input.Dig.RemoveBindingOverride(0);else game.Player.input.Dig.ApplyBindingOverride(0,digOverride);
            }
            AudioListener.volume=oldAudioVolume;
            if(pipeline){pipeline.renderScale=oldScale;pipeline.msaaSampleCount=oldMsaa;pipeline.shadowDistance=oldShadowDistance;pipeline.shadowCascadeCount=oldCascades;}
            if(pad!=null){InputSystem.RemoveDevice(pad);pad=null;}if(previousPad!=null)previousPad.MakeCurrent();
            if(orbit)orbit.EndCinematic();Time.captureFramerate=oldCapture;Application.targetFrameRate=oldRate;QualitySettings.vSyncCount=oldVsync;Time.timeScale=1;Active=false;
        }
        void OnDisable(){Restore();}
    }
}
#endif
