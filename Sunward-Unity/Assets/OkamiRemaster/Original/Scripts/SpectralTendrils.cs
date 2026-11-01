using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class SpectralTendrils : MonoBehaviour
    {
        NativeAmaterasu native;
        TrailRenderer[] ribbons,halos;
        Material paint,glowPaint;
        Light aura;
        void Start(){native=GetComponent<NativeAmaterasu>();}
        TrailRenderer Ribbon(int index,bool halo)
        {
            var obj=new GameObject("Original spirit tendril "+index+(halo?" · soft radiance":" · painted core"));obj.transform.SetParent(transform,false);
            var trail=obj.AddComponent<TrailRenderer>();trail.sharedMaterial=halo?glowPaint:paint;
            trail.time=1.6f;trail.minVertexDistance=.055f;trail.widthMultiplier=halo?1.05f:.42f;
            trail.widthCurve=AnimationCurve.Linear(0,1,1,0);
            trail.startColor=halo?new Color(1.1f,1.5f,2.2f,.24f):new Color(2.4f,2.15f,1.4f,.9f);
            trail.endColor=new Color(.6f,.9f,1.5f,0);trail.emitting=false;return trail;
        }
        void LateUpdate()
        {
            if(!native || !native.Ready)return;
            if(ribbons==null)
            {
                var source=Resources.Load<Material>("Okami/Effects/SpiritRadiance");var texture=Resources.Load<Texture2D>("Okami/Effects/Spirit");var halo=Resources.Load<Texture2D>("Okami/Effects/SpiritGlow");if(!source || !texture || !halo)return;
                paint=new Material(source){mainTexture=texture};glowPaint=new Material(source){mainTexture=halo};ribbons=new TrailRenderer[18];halos=new TrailRenderer[18];
                for(int i=0;i<ribbons.Length;i++){ribbons[i]=Ribbon(i,false);halos[i]=Ribbon(i,true);}
                var lamp=new GameObject("Shiranui spirit radiance light");lamp.transform.SetParent(transform,false);lamp.transform.localPosition=Vector3.up*1.5f;
                aura=lamp.AddComponent<Light>();aura.type=LightType.Point;aura.color=new Color(.6f,.85f,1);aura.range=5;aura.intensity=7;
            }
            bool active=native.Shiranui && !GetComponent<WolfMotor>().game.Blocked;if(aura)aura.enabled=active;
            for(int i=0;i<ribbons.Length;i++)
            {
                ribbons[i].emitting=halos[i].emitting=active;
                if(!active){ribbons[i].Clear();halos[i].Clear();continue;}
                float t=Time.time*1.25f+i*Mathf.PI*2/ribbons.Length;
                Vector3 p=transform.TransformPoint(new Vector3(Mathf.Cos(t)*(1.1f+.2f*Mathf.Sin(t*2)),1.25f+.75f*Mathf.Sin(t*1.4f),Mathf.Sin(t)*2.1f));
                ribbons[i].transform.position=halos[i].transform.position=p;
            }
        }
        void OnDestroy(){if(paint)Destroy(paint);if(glowPaint)Destroy(glowPaint);}
    }
}
