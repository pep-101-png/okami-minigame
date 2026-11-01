using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(90)]
    public sealed class NativeHeldInstrument : MonoBehaviour
    {
        public OriginalActor actor;
        GameObject flute;
        void LateUpdate()
        {
            if(flute || !actor || !actor.Ready)return;
            var wrist=actor.NativeBone(7);if(!wrist)return;
            flute=new GameObject("Original shakuhachi held in the musician's hands");flute.transform.SetParent(wrist,false);
            flute.AddComponent<OriginalVisual>().Load("Okami/native-flute",Vector3.zero,Vector3.one*.72f);
        }
    }
}
