using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class SpectralTendrils : MonoBehaviour
    {
        NativeAmaterasu native;
        TrailRenderer[] ribbons;
        Material[] materials;
        void Start(){native=GetComponent<NativeAmaterasu>();}
        void LateUpdate()
        {
            if(!native || !native.Ready)return;
            if(ribbons==null)
            {
                var source=Resources.Load<Material>("Okami/Effects/Surface");var texture=Resources.Load<Texture2D>("Okami/Effects/Spirit");if(!source || !texture)return;
                ribbons=new TrailRenderer[6];materials=new Material[6];
                for(int i=0;i<6;i++)
                {
                    var obj=new GameObject("Original spirit artwork · spectral tendril "+i);obj.transform.SetParent(transform,false);
                    var trail=obj.AddComponent<TrailRenderer>();ribbons[i]=trail;materials[i]=new Material(source){mainTexture=texture};trail.sharedMaterial=materials[i];trail.time=.65f;trail.minVertexDistance=.035f;trail.widthMultiplier=.13f;
                    trail.widthCurve=AnimationCurve.Linear(0,1,1,0);trail.startColor=new Color(1,.94f,.75f,.65f);trail.endColor=new Color(.8f,.95f,1,0);trail.emitting=false;
                }
            }
            bool active=native.Shiranui && !GetComponent<WolfMotor>().game.Blocked;
            for(int i=0;i<ribbons.Length;i++)
            {
                var r=ribbons[i];r.emitting=active;if(!active){r.Clear();continue;}
                float t=Time.time*1.25f+i*Mathf.PI/3;
                r.transform.position=transform.TransformPoint(new Vector3(Mathf.Cos(t)*(.5f+.12f*Mathf.Sin(t*2)),.9f+.35f*Mathf.Sin(t*1.4f),Mathf.Sin(t)*1.05f));
            }
        }
        void OnDestroy(){if(materials!=null)foreach(var m in materials)if(m)Destroy(m);}
    }
}
