using UnityEngine;
namespace Sunward.Remaster
{
    // Actual core kaninari4p_2 and biri_00 paintings. This is Sunward timing,
    // not the native game's unrecovered effect event dispatcher.
    public static class ThunderPainting
    {
        public static ParticleSystem Bolt(Transform parent,Vector3 point,float height,float width,float life)
        {
            var p=OriginalAtmosphere.Create("OriginalThunderSheet",parent,point,0,1,life,0);if(!p)return null;
            var main=p.main;main.useUnscaledTime=true;main.startRotation=0;main.startSize3D=true;main.startSizeX=width;main.startSizeY=height;main.startSizeZ=1;main.startColor=new Color(1,.95f,.68f,1);
            var velocity=p.velocityOverLifetime;velocity.enabled=false;var sheet=p.textureSheetAnimation;sheet.enabled=true;sheet.numTilesX=4;sheet.numTilesY=1;sheet.startFrame=new ParticleSystem.MinMaxCurve(0,1);sheet.frameOverTime=0;
            p.GetComponent<ParticleSystemRenderer>().renderMode=ParticleSystemRenderMode.VerticalBillboard;p.Emit(1);Object.Destroy(p.gameObject,life+.1f);return p;
        }
        public static void Burst(Transform parent,Vector3 point,bool charged)
        {
            Bolt(parent,point+Vector3.up*(charged?4:1),charged?8:2,charged?1.8f:.65f,.18f);
            if(charged)foreach(float a in new[]{35f,150f,260f})
            {float r=a*Mathf.Deg2Rad;Bolt(parent,point+new Vector3(Mathf.Sin(r)*1.2f,1.8f,Mathf.Cos(r)*1.2f),3.6f,.9f,.15f);}
            var flash=OriginalAtmosphere.Create("OriginalElectricity",parent,point+Vector3.up*.12f,0,charged?5.3f:1.2f,.35f,0);
            if(flash){var m=flash.main;m.useUnscaledTime=true;m.startRotation=0;m.startColor=new Color(1,.85f,.25f,1);var v=flash.velocityOverLifetime;v.enabled=false;flash.GetComponent<ParticleSystemRenderer>().renderMode=ParticleSystemRenderMode.HorizontalBillboard;flash.Emit(1);Object.Destroy(flash.gameObject,.5f);}
        }
    }
}
