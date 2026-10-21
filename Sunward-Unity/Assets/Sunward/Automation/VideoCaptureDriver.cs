#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
namespace Sunward.Editor.Automation
{
    [DefaultExecutionOrder(-10000)]
    public sealed class VideoCaptureDriver : MonoBehaviour
    {
        [Serializable] public class Options
        {
            public int Fps=30, Width=960, Height=540, TimeoutSeconds=900, MaxFrames=2400, MaxFrameMegabytes=2048;
            public bool PreferRecorder=true;
        }
        [Serializable] public class Clip
        {
            public string name, category, angle, status="preparing", error="", framesDirectory, telemetryFile, recorderStatus, recorderDetail, recorderCandidate;
            public int expectedFrames, frames, airborneFrames, landingTransitions, dodgeFrames, outOfViewFrames;
            public float fps, durationSeconds, distance;
            public int width, height;
            public long bytes;
            public Vector3 startPosition, cameraOffset;
            public string[] observedStates, missingStates;
        }
        [Serializable] public class Campaign
        {
            public int schemaVersion=1, protocol=VideoCapturePlan.Version, seed=1337;
            public string status="preparing", error="", graphics, unityVersion;
            public string scope="Actual Windflower Play Mode. Input-driven motor/combat; fixed-step diagnostic footage, no animation/artistic approval. Camera render excludes screen-space UI and audio.";
            public string determinism="Fixed inputs, clip resets, seed, capture timestep and camera offsets. Physics, wall-clock hit-stop, procedural effects and GPUs can still differ between builds.";
            public List<Clip> clips=new List<Clip>();
        }
        Options options;
        Campaign report;
        List<VideoClipSpec> plan;
        int index=-1, warmup, preparedFrame=-1, writtenFrame=-1;
        bool active, completing, finishing, resetPending;
        Gamepad pad;
        InputSettings.UpdateMode previousInputMode;
        Sunward.GameFlow game;
        Camera captureCamera;
        RenderTexture target;
        Texture2D image;
        StreamWriter telemetry;
        RecorderVideoBridge recorder;
        string output, stage;
        Clip clip;
        HashSet<string> observed=new HashSet<string>();
        Transform[] paws;
        Vector3 previousPosition;
        bool previousGrounded;
        long totalBytes;
        int totalFrames;
        readonly System.Diagnostics.Stopwatch timer=new System.Diagnostics.Stopwatch();
        public void Initialize()
        {
            try {
                output=VideoCaptureRuntime.Output;
                options=JsonUtility.FromJson<Options>(File.ReadAllText(Path.Combine(output,"video-options.json")));
                if (options.Fps<12 || options.Fps>60 || options.Width<320 || options.Width>1920 || options.Height<180 || options.Height>1080 || options.Width%2!=0 || options.Height%2!=0 || options.TimeoutSeconds<30 || options.MaxFrames<1 || options.MaxFrameMegabytes<1) throw new Exception("Invalid video capture options.");
                stage=Environment.GetEnvironmentVariable("SUNWARD_AUTOMATION_STAGE") ?? "gameplay-video";
                if (!System.Text.RegularExpressions.Regex.IsMatch(stage,"^[a-z0-9-]+$")) throw new Exception("Invalid stage name.");
                report=new Campaign { graphics=SystemInfo.graphicsDeviceType.ToString(),unityVersion=Application.unityVersion };
                plan=VideoCapturePlan.Build();
                if (plan.Sum(p=>p.seconds*options.Fps)>options.MaxFrames) throw new Exception("Plan exceeds configured frame budget.");
                previousInputMode=InputSystem.settings.updateMode;
                foreach (var device in InputSystem.devices) InputSystem.DisableDevice(device);
                pad=InputSystem.AddDevice<Gamepad>("SunwardCaptureGamepad");
                InputSystem.settings.updateMode=InputSettings.UpdateMode.ProcessEventsManually;
                Time.captureDeltaTime=1f/options.Fps; Time.fixedDeltaTime=1f/options.Fps;
                QualitySettings.vSyncCount=0; Application.targetFrameRate=options.Fps;
                timer.Start(); active=true; resetPending=true;
                SaveReport();
            } catch (Exception e) { Fail(e); }
        }
        void BeginClip()
        {
            index++;
            if (index>=plan.Count) { Finish(); return; }
            var spec=plan[index];
            // Fresh save and real scene lifecycle for EACH clip. Never alter the user's save.
            Environment.SetEnvironmentVariable("SUNWARD_AUTOMATION_DATA",Path.Combine(output,"save-data","video-"+spec.name));
            UnityEngine.Random.InitState(1337);
            InputSystem.QueueStateEvent(pad,new GamepadState()); InputSystem.Update();
            EditorSceneManager.LoadSceneInPlayMode(VideoCaptureRuntime.ScenePath,new LoadSceneParameters(LoadSceneMode.Single));
            game=UnityEngine.Object.FindFirstObjectByType<Sunward.GameFlow>();
            if (!game || !game.Player || !game.Combat) throw new Exception("Actual Windflower player/combat unavailable.");
            game.Close();
            Time.captureDeltaTime=1f/options.Fps; Time.fixedDeltaTime=1f/options.Fps;
            QualitySettings.vSyncCount=0; Application.targetFrameRate=options.Fps;
            Vector3 start=spec.category=="gameplay" ? new Vector3(0,0,-18) : new Vector3(35,0,-8);
            start.y=game.valley.Height(start); game.Player.Teleport(start); game.Player.transform.rotation=Quaternion.identity;
            clip=new Clip { name=spec.name,category=spec.category,angle=spec.angle,expectedFrames=spec.seconds*options.Fps,fps=options.Fps,width=options.Width,height=options.Height };
            clip.framesDirectory="video-frames/"+stage+"/"+spec.name;
            clip.telemetryFile=clip.framesDirectory+"/telemetry.csv";
            Directory.CreateDirectory(Path.Combine(output,clip.framesDirectory));
            File.WriteAllText(Path.Combine(output,clip.framesDirectory,".sunward-owned-frames"),clip.name);
            report.clips.Add(clip); observed.Clear(); warmup=30; completing=false;
            preparedFrame=writtenFrame=-1;
            report.status="recording";
            SaveReport();
            Debug.Log("SUNWARD VIDEO WARMUP: "+spec.name);
        }
        void PrepareRecording()
        {
            var spec=plan[index];
            if (spec.category=="combat") {
                game.StartTrial();
                var start=new Vector3(35,0,-8); start.y=game.valley.Height(start);
                game.Player.Teleport(start); game.Player.transform.rotation=Quaternion.identity;
            }
            if (game.Blocked || game.Player.Locked) throw new Exception("Actual gameplay remains blocked/locked.");
            var original=Camera.main;
            if (!original) throw new Exception("Gameplay camera missing.");
            if (!captureCamera) {
                var obj=new GameObject("Automation video diagnostic camera"); obj.transform.SetParent(transform);
                captureCamera=obj.AddComponent<Camera>();
            }
            captureCamera.CopyFrom(original); captureCamera.enabled=false;
            captureCamera.fieldOfView=42; captureCamera.aspect=options.Width/(float)options.Height;
            var originalData=original.GetComponent<UniversalAdditionalCameraData>();
            if (originalData) EditorUtility.CopySerialized(originalData,captureCamera.GetUniversalAdditionalCameraData());
            target=new RenderTexture(options.Width,options.Height,24,RenderTextureFormat.ARGB32); target.Create();
            image=new Texture2D(options.Width,options.Height,TextureFormat.RGB24,false);
            clip.cameraOffset=spec.angle=="side"?new Vector3(4.2f,1,0):spec.angle=="front"?new Vector3(0,1,4.2f):new Vector3(-3.4f,1.1f,-3.4f);
            clip.startPosition=game.Player.transform.position; previousPosition=clip.startPosition; previousGrounded=game.Player.Grounded;
            string[] names={"DEF_front_paw.L","DEF_front_paw.R","DEF_rear_paw.L","DEF_rear_paw.R"};
            var bones=game.Player.animationView.animator.GetComponentsInChildren<Transform>(true);
            paws=names.Select(n=>bones.FirstOrDefault(t=>t.name==n)).ToArray();
            if (paws.Any(p=>!p)) throw new Exception("Existing paw bones missing; no replacement rig is created.");
            telemetry=new StreamWriter(Path.Combine(output,clip.telemetryFile),false,new System.Text.UTF8Encoding(false));
            telemetry.WriteLine("frame,nominal_seconds,game_seconds,delta_time,time_scale,x,y,z,yaw,speed,grounded,animation,animator_speed,in_transition,state_normalized_time,transition_normalized_time,paw_fl_x,paw_fl_y,paw_fl_z,paw_fl_terrain_y,paw_fr_x,paw_fr_y,paw_fr_z,paw_fr_terrain_y,paw_rl_x,paw_rl_y,paw_rl_z,paw_rl_terrain_y,paw_rr_x,paw_rr_y,paw_rr_z,paw_rr_terrain_y,camera_x,camera_y,camera_z");
            recorder=new RecorderVideoBridge();
            recorder.Start(target,options.Fps,Path.Combine(output,"recorder",stage,clip.name),options.PreferRecorder);
            clip.recorderStatus=recorder.status; clip.recorderDetail=recorder.detail;
            clip.recorderCandidate=string.IsNullOrEmpty(recorder.candidate)?"":"recorder/"+stage+"/"+clip.name+".mp4";
            clip.status="recording"; SaveReport();
        }
        void Update()
        {
            if (!active || finishing) return;
            try {
                if (timer.Elapsed.TotalSeconds>options.TimeoutSeconds) throw new TimeoutException("Gameplay video campaign timed out.");
                if (resetPending) { resetPending=false; BeginClip(); return; }
                if (completing) { CompleteClip(); resetPending=true; return; }
                if (!game) throw new Exception("Gameplay scene/player disappeared.");
                if (warmup>0) {
                    game.Close(); // close only the startup welcome panel during warmup.
                    InputSystem.QueueStateEvent(pad,new GamepadState()); InputSystem.Update(); warmup--;
                    if (warmup==0) PrepareRecording();
                    return;
                }
                if (game.Blocked || game.Player.Locked) throw new Exception("Player died/entered a blocking state; footage incomplete.");
                var command=VideoCapturePlan.Command(plan[index],clip.frames,options.Fps);
                Vector3 world=new Vector3(command.worldX,0,command.worldZ);
                Vector3 forward=game.Player.view.forward; forward.y=0; forward.Normalize();
                Vector3 right=game.Player.view.right; right.y=0; right.Normalize();
                var state=new GamepadState { leftStick=new Vector2(Vector3.Dot(world,right),Vector3.Dot(world,forward)), leftTrigger=command.walk?1:0,rightTrigger=command.heavy?1:0 };
                state=state.WithButton(GamepadButton.South,command.jump).WithButton(GamepadButton.East,command.dodge).WithButton(GamepadButton.RightShoulder,command.light).WithButton(GamepadButton.LeftStick,command.sprint);
                InputSystem.QueueStateEvent(pad,state); InputSystem.Update();
                preparedFrame=Time.frameCount;
            } catch (Exception e) { Fail(e); }
        }
        public void CaptureFrame()
        {
            if (!active || finishing || warmup>0 || completing || resetPending || preparedFrame!=Time.frameCount || writtenFrame==Time.frameCount) return;
            try {
                var camera=clip.angle=="gameplay"?Camera.main:captureCamera;
                if (!camera) throw new Exception("Capture camera disappeared.");
                if (clip.angle!="gameplay") {
                    Vector3 focus=game.Player.transform.position+Vector3.up*.65f;
                    camera.transform.SetPositionAndRotation(focus+clip.cameraOffset,Quaternion.LookRotation(-clip.cameraOffset));
                }
                var request=new UniversalRenderPipeline.SingleCameraRequest { destination=target };
                if (!RenderPipeline.SupportsRenderRequest(camera,request)) throw new NotSupportedException("Graphics/SRP offscreen video rendering unavailable.");
                RenderPipeline.SubmitRenderRequest(camera,request);
                var previous=RenderTexture.active;
                try { RenderTexture.active=target; image.ReadPixels(new Rect(0,0,options.Width,options.Height),0,0); image.Apply(); }
                finally { RenderTexture.active=previous; }
                var bytes=image.GetRawTextureData<byte>(); int variation=0,step=Math.Max(3,(bytes.Length/256/3)*3);
                for (int n=0;n+2<bytes.Length;n+=step) for (int c=0;c<3;c++) variation=Math.Max(variation,Math.Abs(bytes[n+c]-bytes[c]));
                if (variation<3) throw new Exception("Almost-uniform rendered frame; usable footage not established.");
                byte[] png=image.EncodeToPNG();
                if (totalFrames>=options.MaxFrames || totalBytes+png.Length>options.MaxFrameMegabytes*1024L*1024L) throw new Exception("Video frame storage/count budget exceeded; partial frames preserved.");
                string file=Path.Combine(output,clip.framesDirectory,"frame_"+clip.frames.ToString("D6")+".png");
                if (File.Exists(file)) throw new IOException("Refusing to overwrite captured frame.");
                File.WriteAllBytes(file,png); totalBytes+=png.Length; totalFrames++; clip.bytes+=png.Length;
                var p=game.Player.transform.position; clip.distance+=Vector3.ProjectOnPlane(p-previousPosition,Vector3.up).magnitude; previousPosition=p;
                if (!game.Player.Grounded) clip.airborneFrames++;
                if (!previousGrounded && game.Player.Grounded) clip.landingTransitions++;
                previousGrounded=game.Player.Grounded;
                if (game.Player.Dodging) clip.dodgeFrames++;
                string animation=game.Player.animationView.Current; observed.Add(animation);
                var frustum=GeometryUtility.CalculateFrustumPlanes(camera);
                if (!game.Player.GetComponentsInChildren<Renderer>().Any(r=>r.enabled&&GeometryUtility.TestPlanesAABB(frustum,r.bounds))) clip.outOfViewFrames++;
                var row=new List<string> { clip.frames.ToString(),F(clip.frames/(float)options.Fps),F(Time.timeSinceLevelLoad),F(Time.deltaTime),F(Time.timeScale),F(p.x),F(p.y),F(p.z),F(game.Player.transform.eulerAngles.y),F(game.Player.Speed),game.Player.Grounded?"1":"0",animation.Replace(","," ") };
                var animator=game.Player.animationView.animator;
                row.AddRange(new[] { F(animator.speed),animator.IsInTransition(0)?"1":"0",F(animator.GetCurrentAnimatorStateInfo(0).normalizedTime),F(animator.GetAnimatorTransitionInfo(0).normalizedTime) });
                foreach (var paw in paws) { var point=paw.position; row.AddRange(new[] {F(point.x),F(point.y),F(point.z),F(game.valley.Height(point))}); }
                var cp=camera.transform.position; row.AddRange(new[] {F(cp.x),F(cp.y),F(cp.z)}); telemetry.WriteLine(string.Join(",",row));
                clip.frames++; clip.durationSeconds=clip.frames/(float)options.Fps; writtenFrame=Time.frameCount;
                if (clip.frames%options.Fps==0) { telemetry.Flush(); Debug.Log("SUNWARD VIDEO FRAME: "+clip.name+" "+clip.frames+"/"+clip.expectedFrames); SaveReport(); }
                if (clip.frames>=clip.expectedFrames) completing=true;
            } catch (Exception e) { Fail(e); }
        }
        static string F(float value)=>value.ToString("R",CultureInfo.InvariantCulture);
        void CompleteClip()
        {
            ReleaseClip();
            clip.observedStates=observed.OrderBy(s=>s,StringComparer.Ordinal).ToArray();
            clip.missingStates=plan[index].expectedStates.Where(s=>!observed.Any(state=>state.Contains(s))).ToArray();
            bool coverage=clip.missingStates.Length==0 && clip.outOfViewFrames==0;
            if (clip.category=="jump") coverage&=clip.airborneFrames>0&&clip.landingTransitions>0;
            if (clip.category=="dodge") coverage&=clip.dodgeFrames>0;
            if (clip.category!="combat") coverage&=clip.distance>.25f;
            clip.status=coverage?"frames_captured_unreviewed":"frames_captured_coverage_incomplete";
            SaveReport(); Debug.Log("SUNWARD VIDEO CLIP END: "+clip.name+" "+clip.status);
        }
        void ReleaseClip()
        {
            telemetry?.Dispose(); telemetry=null;
            if (recorder!=null) { recorder.Dispose(); if (clip!=null) { clip.recorderStatus=recorder.status; clip.recorderDetail=recorder.detail; } recorder=null; }
            if (target) { target.Release(); Destroy(target); target=null; }
            if (image) { Destroy(image); image=null; }
        }
        void SaveReport()=>File.WriteAllText(Path.Combine(output,"video-capture.json"),JsonUtility.ToJson(report,true));
        void Fail(Exception error)
        {
            if (finishing) return;
            report=report??new Campaign(); report.status="failed"; report.error=error.ToString();
            if (clip!=null) { clip.status="failed"; clip.error=error.ToString(); }
            Finish();
        }
        void Finish()
        {
            if (finishing) return; finishing=true; active=false;
            try {
                ReleaseClip();
                if (report.status!="failed") report.status=report.clips.Count==plan.Count&&report.clips.All(c=>c.status=="frames_captured_unreviewed")?"frames_captured_unreviewed":"frames_captured_coverage_incomplete";
                SaveReport();
            } finally {
                InputSystem.settings.updateMode=previousInputMode;
                if (pad!=null) InputSystem.RemoveDevice(pad);
                EditorApplication.Exit(report.status=="failed"?2:0);
            }
        }
    }
}

#endif
