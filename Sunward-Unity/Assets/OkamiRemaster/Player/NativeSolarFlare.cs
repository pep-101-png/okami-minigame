using System;
using UnityEngine;

namespace Sunward.Remaster
{
    // Original wp24 geometry, paint and skeletal flame deformation. The EST
    // particle dispatcher is a separate outstanding port; do not label this a
    // complete reproduction of the original attack/impact effects.
    [DefaultExecutionOrder(-90)]
    public sealed class NativeSolarFlare : MonoBehaviour
    {
        public float visualScale = 1;
        public Vector3 visualOffset;
        public Quaternion visualRotation = Quaternion.identity;
        public bool freezePose;
        public bool Ready { get; private set; }
        NativePaintedRig rig;
        NativePoseBank bank;
        NativePoseBank.Clip clip;
        Renderer[] legacy;
        bool[] legacyEnabled;
        Vector3[] position, scale;
        Quaternion[] rotation;
        float time;
        void Awake()
        {
            legacy = GetComponentsInChildren<Renderer>(true); legacyEnabled = new bool[legacy.Length];
            for (int i = 0; i < legacy.Length; i++) legacyEnabled[i] = legacy[i].enabled;
            try
            {
                bank = new NativePoseBank("NativePlayer/wp24/Poses");
                clip = bank.Find("wp24_000");
                if (clip == null) throw new InvalidOperationException("Original Solar Flare motion is missing");
                rig = new NativePaintedRig("NativePlayer/wp24", transform);
                rig.Root.transform.localPosition = visualOffset;
                rig.Root.transform.localRotation = visualRotation;
                rig.Root.transform.localScale = Vector3.one * visualScale;
                if (bank.BoneCount != rig.Bones.Length) throw new InvalidOperationException("Solar Flare rig/motion mismatch");
                position = new Vector3[bank.BoneCount]; rotation = new Quaternion[bank.BoneCount]; scale = new Vector3[bank.BoneCount];
                for (int i = 0; i < bank.BoneCount; i++) { position[i] = rig.Bones[i].localPosition; rotation[i] = Quaternion.identity; scale[i] = Vector3.one; }
                Apply(); Ready = true; Show(true);
            }
            catch (Exception e)
            {
                Ready = false; if (rig != null) rig.Dispose(); Show(false);
                Debug.LogError("Original Solar Flare could not load; retained the working Sundial visual. " + e.Message, this);
            }
        }
        void Apply() { bank.Sample(clip, time, rig.Bones, position, rotation, scale, 1, clip.Loop); }
        void LateUpdate() { if (Ready && !freezePose) { time += Time.deltaTime; Apply(); } }
        void Show(bool native)
        {
            if (rig != null && rig.Root) rig.Root.SetActive(native);
            if (legacy != null) for (int i = 0; i < legacy.Length; i++) if (legacy[i]) legacy[i].enabled = !native && legacyEnabled[i];
        }
        void OnDisable() { if (Ready) Show(false); }
        void OnEnable() { if (Ready) Show(true); }
        void OnDestroy() { if (rig != null) rig.Dispose(); }
    }
}
