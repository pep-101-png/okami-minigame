using System;
using UnityEngine;

namespace Sunward.Remaster
{
    // Rigid original MD appearance for transient gameplay objects. Lifetime and
    // projectile movement remain Sunward mechanics, not fabricated native events.
    public sealed class OriginalVisual : MonoBehaviour
    {
        NativePaintedRig rig;
        public bool Load(string resource, Vector3 offset, Vector3 scale)
        {
            try
            {
                rig = new NativePaintedRig(resource, transform);
                rig.Root.transform.localPosition = offset;
                rig.Root.transform.localScale = scale;
                rig.Root.SetActive(true);
                return true;
            }
            catch (Exception error)
            {
                if (rig != null) rig.Dispose();
                Debug.LogError("Original effect appearance could not load: " + error.Message, this);
                return false;
            }
        }
        void OnDestroy() { if (rig != null) rig.Dispose(); }
    }
}
