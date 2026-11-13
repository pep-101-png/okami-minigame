using UnityEngine;
namespace Sunward.Remaster
{
    // Re-emit the original static sky/seal painting whenever its arena is enabled.
    public sealed class CelestialStillPaint:MonoBehaviour
    {
        void OnEnable()
        {
            var p=GetComponent<ParticleSystem>();if(!p)return;
            p.Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);
            var motion=p.velocityOverLifetime;motion.enabled=false;var fade=p.colorOverLifetime;fade.enabled=false;
            var main=p.main;main.startLifetime=9999;main.startRotation=0;main.simulationSpace=ParticleSystemSimulationSpace.Local;
            p.Play();p.Emit(1);
        }
    }
}
