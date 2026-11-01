using UnityEngine;

namespace Sunward.Remaster
{
    // Material instances are owned by each short-lived emitter.
    public sealed class OriginalParticleMaterial : MonoBehaviour
    {
        void OnDestroy() { var r=GetComponent<Renderer>();if(r && r.sharedMaterial)Destroy(r.sharedMaterial); }
    }
}
