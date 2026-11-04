using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class GardenVisitor : MonoBehaviour
    {
        public GameFlow game;public Vector3 anchor;public float phase;
        void Update()
        {
            if(!game || game.Blocked || !HeavenlyGarden.Inside(game.Player.transform.position))return;
            // Keep the real walk clip active: the former 16-second divisor
            // moved below OriginalActor's .15 m/s walk activation threshold.
            float cycle=(Time.time+phase)/7;var goal=anchor+new Vector3(Mathf.Sin(cycle)*2.1f,0,Mathf.Cos(cycle)*1.4f);
            var p=Vector3.MoveTowards(transform.position,goal,Time.deltaTime*.65f);if(HeavenlyGarden.Height(p,out var h))p.y=h+.025f;
            var delta=p-transform.position;delta.y=0;if(delta.sqrMagnitude>.00001f)transform.rotation=Quaternion.RotateTowards(transform.rotation,Quaternion.LookRotation(delta),Time.deltaTime*70);transform.position=p;
        }
    }
}
