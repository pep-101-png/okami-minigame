using UnityEngine;
namespace Sunward.Remaster
{
    // Original Wind painting on a short-lived slash ribbon; native EST timing
    // is not claimed. The screen ink itself uses the original fudesumi2 tip.
    public sealed class BrushStrokeFlash : MonoBehaviour
    {
        LineRenderer line;float age;
        public static void Slash(Vector3 from,Vector3 to)
        {
            var source=Resources.Load<Material>("Okami/Effects/SpiritRadiance");var art=Resources.Load<Texture2D>("Okami/Effects/Wind");if(!source || !art)return;
            var root=new GameObject("Power Slash · original painted wind");var effect=root.AddComponent<BrushStrokeFlash>();effect.line=root.AddComponent<LineRenderer>();
            effect.line.sharedMaterial=new Material(source){mainTexture=art};effect.line.positionCount=2;effect.line.SetPosition(0,from);effect.line.SetPosition(1,to);effect.line.startWidth=effect.line.endWidth=.8f;
            root.AddComponent<OriginalParticleMaterial>();effect.Tint();
        }
        void Tint(){float a=Mathf.Clamp01(1-age/.4f);line.startColor=line.endColor=new Color(1.5f,1.7f,2,a*.85f);}
        void Update(){age+=Time.deltaTime;Tint();if(age>=.4f)Destroy(gameObject);}
    }
}
