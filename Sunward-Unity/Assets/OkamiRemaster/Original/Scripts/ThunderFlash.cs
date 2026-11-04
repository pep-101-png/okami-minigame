using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class ThunderFlash:MonoBehaviour
    {
        public float life=.3f;float clock;Light glow;Renderer[] paint;
        void Update(){clock+=Time.unscaledDeltaTime;if(!glow)glow=GetComponent<Light>();if(glow)glow.intensity=Mathf.Max(0,1-clock/life)*8;if(paint==null)paint=GetComponentsInChildren<Renderer>();foreach(var r in paint)if(r && r.sharedMaterial)r.sharedMaterial.SetColor("_Color",new Color(1,1,1,Mathf.Clamp01(1-clock/life)));if(clock>=life)Destroy(gameObject);}
    }
}
