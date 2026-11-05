using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class ThunderWeaponAura:MonoBehaviour
    {
        public bool unscaled;float clock;
        void Update(){clock+=unscaled?Time.unscaledDeltaTime:Time.deltaTime;if(clock>=.8f){clock=0;var p=ThunderPainting.Bolt(transform,new Vector3(0,.05f,-.7f),.65f,.22f,.16f);if(p){var m=p.main;m.simulationSpace=ParticleSystemSimulationSpace.Local;}}}
    }
}
