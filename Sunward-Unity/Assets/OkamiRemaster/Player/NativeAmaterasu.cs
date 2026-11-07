using System;
using System.Collections.Generic;
using UnityEngine;

namespace Sunward.Remaster
{
    [DefaultExecutionOrder(-100)]
    public sealed class NativeAmaterasu : MonoBehaviour
    {
        [Serializable] public sealed class Binding
        {
            public string state, clip, intro;
            public bool loop, mirror;
            public float referenceSpeed;
        }
        [Serializable] sealed class Bindings { public Binding[] bindings; }
        public bool Ready { get; private set; }
        public bool Visible { get; private set; }
        public bool Shiranui { get; private set; }
        public int FormLevel {get;private set;}
        public bool FullPower=>FormLevel==2;
        NativePaintedRig surfaceRig;
        SkinnedMeshRenderer surfaceRenderer;
        public SkinnedMeshRenderer BodySurface
        {
            get
            {
                if(!Ready || rig==null)return null;
                if(surfaceRig==rig)return surfaceRenderer;
                SkinnedMeshRenderer largest=null;
                foreach(var r in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>())
                    if(r.sharedMesh && (!largest || r.sharedMesh.vertexCount>largest.sharedMesh.vertexCount))largest=r;
                surfaceRig=rig;surfaceRenderer=largest;return largest;
            }
        }
        public Transform Torso => Ready ? rig.Bones[1] : null; // Original native torso, not the raised weapon socket.
        public Transform Head => Ready ? rig.Bones[8] : null;  // Original MD bone 7, skull/ear parent.
        public Transform Back => Ready ? rig.Bones[31] : null; // Original MD bone 30, dorsal attachment.
        public Transform[] PowerBones => Ready ? new[] { rig.Bones[9], rig.Bones[14], rig.Bones[13], rig.Bones[18], rig.Bones[21], rig.Bones[25] } : null;
        public Transform[] Feet => Ready ? new[] { rig.Bones[18], rig.Bones[13], rig.Bones[26], rig.Bones[22] } : null;
        public float PlaybackRate => rate;
        public float Phase => tundraClock?tundraPhase:clip == null ? 0 : time / Mathf.Max(.001f, clip.Duration + (intro != null ? intro.Duration : 0));
        public float BlendPhase => blendDuration > 0 ? Mathf.Clamp01(blendTime / blendDuration) : 1;
        NativePaintedRig rig;
        NativePaintedRig amaterasuRig, shiranuiRig,fullPowerRig;
        NativePoseBank bank;
        Binding[] bindings;
        Renderer[] legacy;
        bool[] legacyEnabled;
        Vector3[] fromPosition, fromScale;
        Quaternion[] fromRotation;
        Binding binding;
        NativePoseBank.Clip clip, intro;
        float time, rate = 1, blendTime, blendDuration;
        string jumpState;
        bool tundraClock,tundraRecovering;
        float tundraPhase,tundraDuration;
        public void SetTundraPhase(float phase,float sourceDuration)
        {if(binding==null || !TundraAttackRules.Owns(binding.state))return;tundraClock=true;tundraPhase=Mathf.Clamp01(phase);tundraDuration=sourceDuration;}
        public void EndTundraAction()
        {
            if(binding==null || !TundraAttackRules.Owns(binding.state))return;
            tundraClock=false;Play("Idle_Natural",TundraAttackRules.ReturnBlend,0,true,false);
        }
        WolfMotor motor;
        sealed class Socket { public Transform bone, socket; public Vector3 offset; public Quaternion rotation; }
        readonly List<Socket> sockets = new List<Socket>();
        Vector3 dorsalBindOffset;Quaternion dorsalBindRotation=Quaternion.identity;
        public Transform AttachSocket(Transform original, Transform bone, string label)
        {
            var socket = new GameObject(label).transform;
            socket.SetParent(transform, false);
            socket.SetPositionAndRotation(original.position, original.rotation);
            sockets.Add(new Socket { bone = bone, socket = socket, offset = bone.InverseTransformPoint(original.position), rotation = Quaternion.Inverse(bone.rotation) * original.rotation });
            return socket;
        }
        public Transform CreateBackSocket()
        {
            // Original MD bone 30 is the dorsal weapon attachment. Import no
            // offsets/rotation from the unrelated FBX or its paw sockets.
            var socket = new GameObject("Original dorsal weapon attachment").transform;
            socket.SetParent(transform, false);
            sockets.Add(new Socket { bone = Back, socket = socket, offset = Vector3.zero, rotation = Quaternion.identity });
            socket.SetPositionAndRotation(Back.position, Back.rotation);
            return socket;
        }

        void Awake()
        {
            try
            {
                motor = GetComponent<WolfMotor>();
                legacy = GetComponentsInChildren<SkinnedMeshRenderer>(true);
                legacyEnabled = new bool[legacy.Length];
                for (int i = 0; i < legacy.Length; i++) legacyEnabled[i] = legacy[i].enabled;
                bank = new NativePoseBank("NativePlayer/pl00/Poses");
                var asset = Resources.Load<TextAsset>("NativePlayer/Bindings");
                if (!asset) throw new InvalidOperationException("Native action bindings are missing");
                bindings = JsonUtility.FromJson<Bindings>(asset.text).bindings;
                foreach (var b in bindings)
                    if (bank.Find(b.clip) == null || (!string.IsNullOrEmpty(b.intro) && bank.Find(b.intro) == null))
                        throw new InvalidOperationException("Missing original action for " + b.state);
                rig = new NativePaintedRig("NativePlayer/pl00", transform);
                amaterasuRig = rig;
                if (bank.BoneCount != rig.Bones.Length) throw new InvalidOperationException("Original model and motion skeletons disagree");
                fromPosition = new Vector3[bank.BoneCount]; fromRotation = new Quaternion[bank.BoneCount]; fromScale = new Vector3[bank.BoneCount];
                Ready = true;
                Play("Idle_Natural", 0, 0, false, false);
                var torso=rig.Bones[1];dorsalBindOffset=torso.InverseTransformPoint(Back.position);
                dorsalBindRotation=Quaternion.Inverse(torso.rotation)*Back.rotation;
            }
            catch (Exception e)
            {
                Ready = false; Show(false);
                if (rig != null) rig.Dispose();
                Debug.LogError("Original Amaterasu could not load; retained the working player visual. " + e.Message, this);
            }
        }
        Binding Find(string state)
        {
            if (bindings != null) foreach (var b in bindings) if (b.state == state) return b;
            return null;
        }
        public bool Play(string state, float blend, float duration, bool restart, bool phaseMatch)
        {
            if (!Ready || !isActiveAndEnabled) return false;
            var next = Find(state);
            if (state == "Air_Fall")
            {
                string fall = jumpState == "Jump_Sprint" ? "Fall_Sprint" : jumpState == "Jump_Jog" || jumpState == "Jump_Walk" ? "Fall_Jog" : jumpState == "Jump_Double" ? "Fall_Double" : state;
                next = Find(fall) ?? next;
            }
            if (state == "AirStrike" && motor && motor.game && motor.game.Profile.equipped != "sundial") next = Find("AirStrike_Glaive");
            if (next == null) { Show(false); return false; }
            if (state.StartsWith("Land_") || state.StartsWith("Walk_") || state.StartsWith("Jog_") || state.StartsWith("Sprint_") || state == "Idle_Natural") jumpState = null;
            if (binding == next && !restart && Visible) return true;
            if (!restart && Visible && binding != null && next.clip == binding.clip && next.intro == binding.intro && next.mirror == binding.mirror)
            {
                binding = next; return true; // Turn aliases keep the same native gait clock.
            }
            float phase = phaseMatch && clip != null ? Mathf.Repeat(time, clip.Duration) / clip.Duration : 0;
            // Capture the displayed pose, so crossfades remain continuous even
            // if another action interrupts an existing transition.
            for (int i = 0; i < bank.BoneCount; i++)
            {
                fromPosition[i] = rig.Bones[i].localPosition;
                fromRotation[i] = rig.Bones[i].localRotation;
                fromScale[i] = rig.Bones[i].localScale;
            }
            tundraClock=false;tundraRecovering=false;
            binding = next; clip = bank.Find(next.clip); intro = string.IsNullOrEmpty(next.intro) ? null : bank.Find(next.intro);
            time = phase * clip.Duration; blendTime = 0; blendDuration = Mathf.Max(0, blend);
            float length = clip.Duration + (intro != null ? intro.Duration : 0);
            if (state.StartsWith("Jump") && motor && motor.Vertical > 0)
            {
                jumpState = state;
                duration = motor.Vertical / WolfMotor.Gravity;
            }
            else if (state == "Air_Fall" && motor && motor.valley)
            {
                float height = Mathf.Max(0, transform.position.y - motor.valley.Height(transform.position));
                float v = motor.Vertical;
                duration = Mathf.Max(.08f, (v + Mathf.Sqrt(v * v + 2 * WolfMotor.Gravity * height)) / WolfMotor.Gravity);
            }
            rate = duration > 0 ? length / duration : 1;
            Show(true); Apply(); return true;
        }
        public void HoldChargePose()
        {
            if(!Ready || binding==null)return;
            // Every family keeps the inspected native preparation motion moving;
            // holding an attack must never stop its skeletal playback clock.
            if(binding.state.StartsWith("NativeCharge_")){tundraClock=false;rate=1;}
        }

        public float ClipLength(string state)
        {
            var b = Find(state);
            if (!Ready || !isActiveAndEnabled || b == null) return 0;
            return bank.Find(b.clip).Duration + (string.IsNullOrEmpty(b.intro) ? 0 : bank.Find(b.intro).Duration);
        }
        public void GaitSpeed(float metresPerSecond)
        {
            // Calibrated from original mtb3 travel at the same 0.075 m/unit as
            // the model, rather than the old FBX's unrelated stride speeds.
            float target = binding != null && binding.referenceSpeed > 0 ? metresPerSecond / binding.referenceSpeed : 1;
            rate = Mathf.Lerp(rate, Mathf.Clamp(target, 0, 3), 1 - Mathf.Exp(-Time.deltaTime * 12));
        }
        public void SwimSpeed(float speed)
        {
            if(binding==null || !binding.state.StartsWith("Swim_"))return;
            // Native water-family treading and forward loops retain their source
            // poses; forward cadence follows swimming speed.
            rate=Mathf.Lerp(rate,binding.state=="Swim_Idle"?1f:Mathf.Lerp(.8f,1.15f,Mathf.Clamp01(speed/2)),1-Mathf.Exp(-Time.deltaTime*8));
        }
        void Show(bool show)
        {
            Visible = show;
            if (rig != null && rig.Root) rig.Root.SetActive(show);
            if (legacy != null) for (int i = 0; i < legacy.Length; i++) if (legacy[i]) legacy[i].enabled = !show && legacyEnabled[i];
        }
        void LateUpdate()
        {
            if (!Ready || !Visible || clip == null) return;
            bool cinematic=motor && motor.game && (motor.game.CinematicActive || motor.game.Panel=="bossVictory");
            if (motor && motor.game && motor.game.Blocked && !cinematic) return;
            if (UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.pKey.wasPressedThisFrame)
                if(motor && motor.game && motor.game.Transformation)motor.game.Transformation.Begin(this);
            float dt=cinematic?Time.unscaledDeltaTime:Time.deltaTime;
            if(!tundraClock)time += dt * rate;
            blendTime += dt;
            Apply();
        }
        public bool PrepareShiranui()
        {
            try
            {
                if(shiranuiRig==null)shiranuiRig=new NativePaintedRig("Okami/pl0d",transform);
                if(shiranuiRig.Bones.Length!=bank.BoneCount)throw new InvalidOperationException("Shiranui skeleton does not match the native player motion bank");
                return true;
            }
            catch(Exception error){Debug.LogError("Original Shiranui appearance could not load: "+error.Message,this);return false;}
        }
        public bool PreparePowerForm(int level)
        {
            if(level!=2)return level==0 || PrepareShiranui();
            try{if(fullPowerRig==null)fullPowerRig=new NativePaintedRig("Okami/es3a",transform);if(fullPowerRig.Bones.Length!=bank.BoneCount)throw new InvalidOperationException("Original ES3A skeleton does not match the native wolf motions");return true;}
            catch(Exception error){Debug.LogError("Original full-power Shiranui could not load: "+error.Message,this);return false;}
        }
        public bool ApplyShiranuiForm()=>ApplyPowerForm(Shiranui?0:1);
        public bool ApplyPowerForm(int level)
        {
            if(level<0 || level>2 || !PreparePowerForm(level))return false;
            try
            {
                var previous=rig;var target=level==2?fullPowerRig:level==1?shiranuiRig:amaterasuRig;
                for(int i=0;i<target.Bones.Length;i++){target.Bones[i].localPosition=previous.Bones[i].localPosition;target.Bones[i].localRotation=previous.Bones[i].localRotation;target.Bones[i].localScale=previous.Bones[i].localScale;}
                foreach(var socket in sockets){int index=Array.IndexOf(previous.Bones,socket.bone);if(index>=0)socket.bone=target.Bones[index];}
                previous.Root.SetActive(false);rig=target;FormLevel=level;Shiranui=level>0;rig.Root.transform.localScale=Vector3.one*(FullPower?1.2f:1);rig.Root.SetActive(true);return true;
            }
            catch(Exception error){Debug.LogError("Original wolf form could not load: "+error.Message,this);return false;}
        }
        bool solarPose;float solarTime,solarRelease,solarFloor;Vector3 solarCentre;Quaternion solarRotation;
        public bool BeginSolarPose()
        {
            if(!Ready || bank.Find("pl00_017")==null || bank.Find("pl00_018")==null || bank.Find("pl00_021")==null)return false;
            for(int i=0;i<bank.BoneCount;i++){fromPosition[i]=rig.Bones[i].localPosition;fromRotation[i]=rig.Bones[i].localRotation;fromScale[i]=rig.Bones[i].localScale;}
            solarFloor=transform.position.y;solarRotation=rig.Root.transform.localRotation;solarPose=true;solarTime=solarRelease=0;return true;
        }
        public void SolarPose(float elapsed,Vector3 centre,float release)
        {solarTime=elapsed;solarCentre=centre;solarRelease=Mathf.Clamp01(release);}
        public void EndSolarPose()
        {solarPose=false;if(rig!=null){rig.Root.transform.localPosition=Vector3.zero;rig.Root.transform.localRotation=solarRotation;}Play("Idle_Natural",.18f,0,true,false);}
        void CaptureSolarPose()
        {for(int i=0;i<bank.BoneCount;i++){fromPosition[i]=rig.Bones[i].localPosition;fromRotation[i]=rig.Bones[i].localRotation;fromScale[i]=rig.Bones[i].localScale;}}
        void ApplySolarPose()
        {
            var roll=bank.Find("pl00_017");float phase=solarTime<1.8f?Mathf.Lerp(0,.30f,Mathf.SmoothStep(0,1,solarTime/1.8f)):.30f+.018f*Mathf.Sin(solarTime*2.8f);
            bank.Sample(roll,phase*roll.Duration,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,solarTime/.35f),false);
            // Preserve the approved ascent through 2.1s. Then pose 3 (native
            // 018 at 25%) folds into pose 2 (native 021 at 65%). Direct both
            // postures forward around the sun, rather than playing the native
            // backward-dodge action and reversing the requested roll direction.
            if(solarTime>2.1f)
            {
                CaptureSolarPose();
                var folded=bank.Find("pl00_018");
                bank.Sample(folded,folded.Duration*.25f,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,(solarTime-2.1f)/.42f),false);
            }
            if(solarTime>3.05f)
            {
                CaptureSolarPose();
                var tuck=bank.Find("pl00_021");float breath=.65f+.008f*Mathf.Sin((solarTime-3.05f)*2.8f);
                bank.Sample(tuck,tuck.Duration*breath,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,(solarTime-3.05f)/.60f),false);
            }
            float forwardRoll=720*Mathf.SmoothStep(0,1,(solarTime-2.1f)/2.3f);
            rig.Root.transform.localRotation=solarRotation*Quaternion.Euler(forwardRoll,0,0);
            if(solarTime>=ShiranuiUltimate.BlastTime)
            {
                // Unfurl into a native extended leap at the flash, then reach
                // down with the inspected early fall pose. Avoid the later
                // 022 stretch, which points the forelegs straight overhead.
                CaptureSolarPose();var extension=bank.Find("pl00_025");
                bank.Sample(extension,extension.Duration*.30f,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,(solarTime-ShiranuiUltimate.BlastTime)/.24f),false);
                if(solarTime>4.95f)
                {
                    CaptureSolarPose();var air=bank.Find("pl00_022");
                    float airPhase=Mathf.Lerp(.24f,.34f,Mathf.SmoothStep(0,1,(solarTime-4.95f)/(ShiranuiUltimate.LandingTime-4.95f)));
                    bank.Sample(air,air.Duration*airPhase,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,(solarTime-4.95f)/.30f),false);
                }
                if(solarTime>=ShiranuiUltimate.LandingTime)
                {
                    CaptureSolarPose();var landing=bank.Find("pl00_02d");float contact=solarTime-ShiranuiUltimate.LandingTime;
                    bank.Sample(landing,Mathf.Clamp01(contact/.50f)*landing.Duration,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,contact/.12f),false);
                    if(contact>.50f)
                    {
                        CaptureSolarPose();var rest=bank.Find("pl00_000");
                        bank.Sample(rest,0,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,(contact-.50f)/.20f),true);
                    }
                }
            }
            rig.Root.transform.localPosition=Vector3.zero;
            // Airborne poses stay centred in the sun. Hand ground contact back
            // to the native landing root before the paws touch down, so its
            // compression is not cancelled by a permanently pinned torso.
            float grounded=Mathf.SmoothStep(0,1,(solarTime-ShiranuiUltimate.LandingTime+.18f)/.18f);
            rig.Root.transform.position+=(solarCentre-rig.Bones[1].position)*(1-grounded);
            if(grounded>0)
            {
                float feet=Mathf.Min(Mathf.Min(rig.Bones[13].position.y,rig.Bones[18].position.y),Mathf.Min(rig.Bones[22].position.y,rig.Bones[26].position.y));
                float settle=Mathf.SmoothStep(0,1,(solarTime-ShiranuiUltimate.LandingTime-.50f)/.20f);
                rig.Root.transform.position+=Vector3.up*Mathf.Max(0,solarFloor+.06f-feet)*(1-settle);
            }
        }
        void Apply()
        {
            float t = time; var selected = clip;
            bool loop = binding.loop;
            if (intro != null)
            {
                if (t < intro.Duration) { selected = intro; loop = false; }
                else t -= intro.Duration;
            }
            if(binding.state.StartsWith("NativeCharge_"))
            {
                // Ease back and forth inside the original moving preparation
                // segment. No held frame and no hard wrap to its recovery pose.
                float pulse=(1-Mathf.Cos(time*Mathf.PI/Mathf.Max(.1f,clip.Duration)))*.5f;
                t=clip.Duration*Mathf.Lerp(binding.state=="NativeCharge_glaive"?.05f:.18f,binding.state=="NativeCharge_glaive"?.26f:.72f,pulse);loop=false;
            }
            if(tundraClock)
            {
                if(binding.state==TundraAttackRules.Cast)
                {
                    var recovery=bank.Find("pl00_543");
                    if(recovery==null)throw new InvalidOperationException("Original Tundra cast recovery pl00_543 is missing");
                    float finish=Mathf.Min(recovery.Duration,tundraDuration*.2f),release=Mathf.Max(.01f,tundraDuration-finish);
                    bool ending=tundraPhase*tundraDuration>=release;
                    t=ending?(tundraPhase*tundraDuration-release)/finish*recovery.Duration:Mathf.Clamp01(tundraPhase*tundraDuration/release)*clip.Duration;
                    if(ending && !tundraRecovering)
                    {
                        for(int i=0;i<bank.BoneCount;i++)
                        {fromPosition[i]=rig.Bones[i].localPosition;fromRotation[i]=rig.Bones[i].localRotation;fromScale[i]=rig.Bones[i].localScale;}
                        tundraRecovering=true;blendTime=0;blendDuration=.04f;
                    }
                    selected=ending?recovery:clip;loop=false;
                }
                else {t=tundraPhase*clip.Duration;loop=false;}
            }
            if(solarPose)ApplySolarPose();
            else bank.Sample(selected, t, rig.Bones, fromPosition, fromRotation, fromScale, blendDuration > 0 ? Mathf.SmoothStep(0, 1, blendTime / blendDuration) : 1, loop, binding.mirror);
            if(!solarPose && binding.state=="NativeAttack_524" && time>clip.Duration*.78f)
            {
                var rest=bank.Find("pl00_000");
                for(int i=0;i<bank.BoneCount;i++){fromPosition[i]=rig.Bones[i].localPosition;fromRotation[i]=rig.Bones[i].localRotation;fromScale[i]=rig.Bones[i].localScale;}
                bank.Sample(rest,0,rig.Bones,fromPosition,fromRotation,fromScale,Mathf.SmoothStep(0,1,(time/clip.Duration-.78f)/.22f),true);
            }
            // Follow the bone pose without inheriting its squash/stretch scale
            // into a separately skinned weapon. Skin scales remain untouched.
            foreach (var socket in sockets)
                if (socket.socket && socket.bone)
                {
                    // Charged MOTs intentionally place the dorsal control at the
                    // action origin. The held idle rosary instead belongs at the
                    // anatomical dorsal bind on the moving torso. Cast/strike
                    // curves still use their authored action-origin attachment.
                    bool held=socket.bone==Back && binding.state.StartsWith("NativeCharge_") && motor && motor.game && motor.game.Combat && motor.game.Combat.HoldingCharge;
                    Vector3 point=held?rig.Bones[1].TransformPoint(dorsalBindOffset):socket.bone.TransformPoint(socket.offset);
                    socket.socket.SetPositionAndRotation(point,(held?rig.Bones[1].rotation*dorsalBindRotation:socket.bone.rotation)*socket.rotation);
                }
        }
        void OnDisable() { Show(false); }
        void OnEnable() { if (Ready) Show(true); }
        void OnDestroy() { if (amaterasuRig != null) amaterasuRig.Dispose(); if (shiranuiRig != null) shiranuiRig.Dispose();if(fullPowerRig!=null)fullPowerRig.Dispose(); }
    }
}
