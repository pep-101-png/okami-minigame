using UnityEngine;

namespace Sunward.Remaster
{
    // Material instances are owned by each short-lived emitter.
    public sealed class OriginalParticleMaterial : MonoBehaviour
    {
        void OnDestroy() { var r=GetComponent<ParticleSystemRenderer>();if(r && r.sharedMaterial)Destroy(r.sharedMaterial); }
    }
}
