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
        public Transform Head => Ready ? rig.Bones[8] : null;  // Original MD bone 7, skull/ear parent.
        public Transform Back => Ready ? rig.Bones[31] : null; // Original MD bone 30, dorsal attachment.
        public Transform[] PowerBones => Ready ? new[] { rig.Bones[9], rig.Bones[14], rig.Bones[13], rig.Bones[18], rig.Bones[21], rig.Bones[25] } : null;
        public Transform[] Feet => Ready ? new[] { rig.Bones[18], rig.Bones[13], rig.Bones[26], rig.Bones[22] } : null;
        public float PlaybackRate => rate;
        public float Phase => clip == null ? 0 : time / Mathf.Max(.001f, clip.Duration + (intro != null ? intro.Duration : 0));
        public float BlendPhase => blendDuration > 0 ? Mathf.Clamp01(blendTime / blendDuration) : 1;
        NativePaintedRig rig;
        NativePaintedRig amaterasuRig, shiranuiRig;
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
        WolfMotor motor;
        sealed class Socket { public Transform bone, socket; public Vector3 offset; public Quaternion rotation; }
        readonly List<Socket> sockets = new List<Socket>();
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
            // Preserve original paddle curves while avoiding a rapid land-gait
            // cadence. This changes the motion clock, not the skeletal poses.
            rate=Mathf.Lerp(rate,binding.state=="Swim_Idle"?.55f:Mathf.Lerp(.55f,.85f,Mathf.Clamp01(speed/2)),1-Mathf.Exp(-Time.deltaTime*8));
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
            if (motor && motor.game && motor.game.Blocked) return;
            if (UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.pKey.wasPressedThisFrame)
                ToggleShiranui();
            time += Time.deltaTime * rate; blendTime += Time.deltaTime;
            Apply();
        }
        void ToggleShiranui()
        {
            try
            {
                if (shiranuiRig == null) shiranuiRig = new NativePaintedRig("Okami/pl0d", transform);
                if (shiranuiRig.Bones.Length != bank.BoneCount) throw new InvalidOperationException("Shiranui skeleton does not match the native player motion bank");
                var previous = rig; Shiranui = !Shiranui; rig = Shiranui ? shiranuiRig : amaterasuRig;
                for (int i = 0; i < rig.Bones.Length; i++)
                {
                    rig.Bones[i].localPosition = previous.Bones[i].localPosition;
                    rig.Bones[i].localRotation = previous.Bones[i].localRotation;
                    rig.Bones[i].localScale = previous.Bones[i].localScale;
                }
                foreach (var socket in sockets)
                {
                    int index = Array.IndexOf(previous.Bones, socket.bone);
                    if (index >= 0) socket.bone = rig.Bones[index];
                }
                previous.Root.SetActive(false); rig.Root.SetActive(true);
                if (motor && motor.game) motor.game.Notify(Shiranui ? "Shiranui · original karmic appearance · P to return" : "Amaterasu · P to test Shiranui");
            }
            catch (Exception error) { Debug.LogError("Original Shiranui appearance could not load: " + error.Message, this); }
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
            bank.Sample(selected, t, rig.Bones, fromPosition, fromRotation, fromScale, blendDuration > 0 ? Mathf.SmoothStep(0, 1, blendTime / blendDuration) : 1, loop, binding.mirror);
            // Follow the bone pose without inheriting its squash/stretch scale
            // into a separately skinned weapon. Skin scales remain untouched.
            foreach (var socket in sockets)
                if (socket.socket && socket.bone) socket.socket.SetPositionAndRotation(socket.bone.TransformPoint(socket.offset), socket.bone.rotation * socket.rotation);
        }
        void OnDisable() { Show(false); }
        void OnEnable() { if (Ready) Show(true); }
        void OnDestroy() { if (amaterasuRig != null) amaterasuRig.Dispose(); if (shiranuiRig != null) shiranuiRig.Dispose(); }
    }
}
