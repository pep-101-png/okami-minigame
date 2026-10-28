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
        }
        [Serializable] sealed class Bindings { public Binding[] bindings; }
        public bool Ready { get; private set; }
        public bool Visible { get; private set; }
        public Transform Head => Ready ? rig.Bones[8] : null;  // Original MD bone 7, skull/ear parent.
        public Transform Back => Ready ? rig.Bones[31] : null; // Original MD bone 30, dorsal attachment.
        public Transform[] PowerBones => Ready ? new[] { rig.Bones[9], rig.Bones[14], rig.Bones[13], rig.Bones[18], rig.Bones[21], rig.Bones[25] } : null;
        NativePaintedRig rig;
        NativePoseBank bank;
        Binding[] bindings;
        Renderer[] legacy;
        bool[] legacyEnabled;
        Vector3[] fromPosition, fromScale;
        Quaternion[] fromRotation;
        Binding binding;
        NativePoseBank.Clip clip, intro;
        float time, rate = 1, blendTime, blendDuration;
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
            if (state == "AirStrike" && motor && motor.game && motor.game.Profile.equipped != "sundial") next = Find("AirStrike_Glaive");
            if (next == null) { Show(false); return false; }
            if (binding == next && !restart && Visible) return true;
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
            rate = duration > 0 ? length / duration : 1;
            Show(true); Apply(); return true;
        }
        public float ClipLength(string state)
        {
            var b = Find(state);
            if (!Ready || !isActiveAndEnabled || b == null) return 0;
            return bank.Find(b.clip).Duration + (string.IsNullOrEmpty(b.intro) ? 0 : bank.Find(b.intro).Duration);
        }
        public void GaitRate(float value) { rate = Mathf.Clamp(value, .1f, 3); }
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
            time += Time.deltaTime * rate; blendTime += Time.deltaTime;
            Apply();
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
        void OnDestroy() { if (rig != null) rig.Dispose(); }
    }
}
