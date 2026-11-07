using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class ThunderWeaponAura:MonoBehaviour
    {
        public bool unscaled;float clock;int seed;OriginalWeaponView view;float rumble;
        void Update()
        {
            float dt=unscaled?Time.unscaledDeltaTime:Time.deltaTime;clock+=dt;rumble+=dt;
            if(!view)view=GetComponent<OriginalWeaponView>();
            if(clock>=.16f)
            {
                clock=0;Vector3 a,b;
                if(view && view.LightningEndpoints(out a,out b)){a=transform.InverseTransformPoint(a);b=transform.InverseTransformPoint(b);}
                else {a=new Vector3(0,0,.45f);b=new Vector3(0,0,-1.55f);}
                var side=new Vector3(Mathf.Sin(seed*2.1f),Mathf.Cos(seed*1.7f),0)*.35f;ThunderPainting.Arc(transform,a+side,b-side,.055f,.2f,seed++);ThunderPainting.Arc(transform,Vector3.Lerp(a,b,.5f),Vector3.Lerp(a,b,.5f)+side*2,.045f,.18f,seed++);
            }
            if(rumble>3.6f && view){rumble=0;var g=FindFirstObjectByType<GameFlow>();if(g && !g.Blocked)g.Audio.WeaponRumble();}
        }
    }
}
