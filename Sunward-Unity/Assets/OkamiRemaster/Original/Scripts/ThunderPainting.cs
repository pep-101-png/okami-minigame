using UnityEngine;
namespace Sunward.Remaster
{
    // Recovered lightning/electricity paint on Sunward carriers with pinned contacts.
    public static class ThunderPainting
    {
        public static ParticleSystem Bolt(Transform parent,Vector3 point,float height,float width,float life)
        {
            var p=OriginalAtmosphere.Create("OriginalThunderSheet",parent,point,0,1,life,0);if(!p)return null;
            var main=p.main;main.useUnscaledTime=true;main.startRotation=0;main.startSize3D=true;main.startSizeX=width;main.startSizeY=height;main.startSizeZ=1;main.startColor=new Color(1,.95f,.68f,1);
            var velocity=p.velocityOverLifetime;velocity.enabled=false;var sheet=p.textureSheetAnimation;sheet.enabled=true;sheet.numTilesX=4;sheet.numTilesY=1;sheet.startFrame=new ParticleSystem.MinMaxCurve(0,1);sheet.frameOverTime=0;
            p.GetComponent<ParticleSystemRenderer>().renderMode=ParticleSystemRenderMode.VerticalBillboard;p.Emit(1);Object.Destroy(p.gameObject,life+.1f);return p;
        }
        public static void Arc(Transform parent,Vector3 start,Vector3 end,float width,float life,int seed=0)
        {
            var root=new GameObject("Original lightning paint · connected bolt");root.transform.SetParent(parent,false);
            var axis=end-start;var across=Vector3.Cross(axis.normalized,Vector3.up);if(across.sqrMagnitude<.01f)across=Vector3.right;across=across.normalized;var other=Vector3.Cross(axis.normalized,across);
            for(int layer=0;layer<2;layer++)
            {
                var obj=new GameObject(layer==0?"Soft electric corona":"Lightning core");obj.transform.SetParent(root.transform,false);var line=obj.AddComponent<LineRenderer>();line.useWorldSpace=false;line.positionCount=17;line.startWidth=width*(layer==0?3.8f:1);line.endWidth=line.startWidth*.45f;
                var mat=new Material(Resources.Load<Material>("Okami/Effects/SpiritRadiance")){mainTexture=Resources.Load<Texture2D>(layer==0?"Okami/Effects/SpiritGlow":"Okami/es4a/Texture-0")};line.sharedMaterial=mat;obj.AddComponent<OriginalParticleMaterial>();line.startColor=line.endColor=layer==0?new Color(1,.68f,.08f,.25f):new Color(1,.96f,.65f,.95f);
                for(int i=0;i<17;i++){float t=i/16f,fade=Mathf.Sin(t*Mathf.PI),sway=Mathf.Min(.75f,axis.magnitude*.09f);var offset=(across*Mathf.Sin(i*2.37f+seed*3.1f)+other*Mathf.Sin(i*4.13f+seed))*sway*fade;line.SetPosition(i,Vector3.Lerp(start,end,t)+offset);}
            }
            Object.Destroy(root,life);
        }
        public static void Burst(Transform parent,Vector3 point,bool charged)
        {
            float height=charged?12:4.5f;Arc(parent,point+Vector3.up*height,point,charged?.32f:.12f,charged?.32f:.2f,1);
            if(charged)for(int i=0;i<6;i++){float a=i*Mathf.PI/3;var foot=point+new Vector3(Mathf.Sin(a)*5,.08f,Mathf.Cos(a)*5);Arc(parent,point+Vector3.up*8,foot,.18f,.3f,i+3);}
            var flash=OriginalAtmosphere.Create("SpiritGlow",parent,point+Vector3.up*.08f,0,charged?13:2.6f,charged?.6f:.4f,0);
            if(charged){var sparks=OriginalAtmosphere.Create("Spark",parent,point+Vector3.up*.15f,0,.55f,.5f,6,.4f);if(sparks){var main=sparks.main;main.useUnscaledTime=true;main.startColor=new Color(1,.86f,.28f,1);sparks.Emit(28);Object.Destroy(sparks.gameObject,.8f);}}
            if(flash){var m=flash.main;m.useUnscaledTime=true;m.startRotation=0;m.startColor=new Color(1,.85f,.25f,.65f);var v=flash.velocityOverLifetime;v.enabled=false;flash.GetComponent<ParticleSystemRenderer>().renderMode=ParticleSystemRenderMode.HorizontalBillboard;flash.Emit(1);Object.Destroy(flash.gameObject,.75f);}
        }
    }
}
