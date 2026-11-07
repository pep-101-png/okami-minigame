using UnityEngine;
namespace Sunward.Remaster
{
    // Original ES geometry/paint carried by continuous wind curves, full power only.
    public sealed class SpectralTendrils:MonoBehaviour
    {
        const int Segments=40;const float CurveLength=3.8271732f;
        NativeAmaterasu native;NativePaintedRig[] rigs;Material[][] materials;Vector4[][] curves;
        Light aura;float clock;
        readonly Vector3[] mounts={new Vector3(-.38f,-.02f,-.26f),new Vector3(.42f,.015f,-.34f),new Vector3(-.43f,0,-.48f),new Vector3(.35f,-.035f,-.54f),new Vector3(-.34f,.02f,-.68f),new Vector3(.40f,-.01f,-.75f),new Vector3(-.30f,.08f,-.38f),new Vector3(.29f,.06f,-.59f),new Vector3(-.41f,-.03f,-.79f),new Vector3(.37f,.09f,-.43f)};
        readonly float[] lengths={.76f,.94f,.82f,.88f,.71f,1.0f,.43f,.58f,1.14f,.65f};
        readonly float[] rates={.85f,1.08f,.94f,.77f,1.16f,.89f,1.03f,.81f,.96f,1.12f};
        readonly float[] phases={.43f,1.91f,3.72f,5.16f,7.88f,10.37f,12.19f,14.63f,17.31f,19.82f};
        readonly float[] headings={-3f,4.5f,1f,-5f,6f,-1.5f,2.7f,-4.2f,5.3f,-2.4f};
        readonly float[] breadth={.62f,.55f,.74f,.58f,.68f,.51f,.57f,.66f,.60f,.72f};
        readonly float[] widths={1f,1f,1f,1f,1f,1f,.65f,.80f,1.15f,.70f};
        void Start(){native=GetComponent<NativeAmaterasu>();}
        void Build()
        {
            rigs=new NativePaintedRig[lengths.Length];materials=new Material[lengths.Length][];curves=new Vector4[lengths.Length][];
            var shader=Resources.Load<Material>("Okami/Effects/SpiritRibbon").shader;
            for(int i=0;i<rigs.Length;i++)
            {
                rigs[i]=new NativePaintedRig(i%2==0?"Okami/es4a-flow":"Okami/es4b-flow",transform);curves[i]=new Vector4[Segments+1];
                var renderers=rigs[i].Root.GetComponentsInChildren<SkinnedMeshRenderer>();materials[i]=new Material[renderers.Length];
                for(int k=0;k<renderers.Length;k++)
                {
                    var renderer=renderers[k];var material=renderer.sharedMaterial;material.shader=shader;material.SetColor("_Tint",new Color(.92f,.95f,1,.38f));material.SetFloat("_CurveLength",CurveLength);material.SetFloat("_StrandWidth",widths[i]);renderer.updateWhenOffscreen=true;renderer.localBounds=new Bounds(Vector3.zero,new Vector3(14,10,14));materials[i][k]=material;
                }
            }
            var lamp=new GameObject("Original full-power wisp radiance");lamp.transform.SetParent(transform,false);lamp.transform.localPosition=Vector3.up*1.2f;aura=lamp.AddComponent<Light>();aura.type=LightType.Point;aura.range=5;aura.shadows=LightShadows.None;aura.color=new Color(.8f,.9f,1);aura.intensity=.4f;
        }
        void Flow(int i)
        {
            float step=CurveLength/Segments;var point=Vector3.zero;curves[i][0]=new Vector4(0,0,0,0);
            for(int j=0;j<Segments;j++)
            {
                float s=(j+.5f)*step,seed=phases[i],phase=s*1.85f-clock*rates[i]+seed;
                float cross=breadth[i]*(.78f*Mathf.Sin(phase)+.22f*Mathf.Sin(s*3.1f-clock*.68f+seed*1.37f));
                float rise=.10f+.25f*Mathf.Sin(s*1.35f-clock*.63f+seed*1.7f);
                // Integrate a unit tangent: the wave travels along a fixed arc
                // length. There is no spring, rest-pose bend or mirrored bone loop.
                point+=new Vector3(cross,rise,1).normalized*step;curves[i][j+1]=new Vector4(point.x,point.y,point.z,0);
            }
            foreach(var material in materials[i])material.SetVectorArray("_CurvePoints",curves[i]);
        }
        void LateUpdate()
        {
            if(!native || !native.Ready)return;bool active=native.FullPower;
            if(!active){if(aura)aura.enabled=false;if(rigs!=null)foreach(var rig in rigs)rig.Root.SetActive(false);return;}
            if(rigs==null)Build();clock+=Time.unscaledDeltaTime;aura.enabled=true;
            for(int i=0;i<rigs.Length;i++)
            {
                var root=rigs[i].Root;root.SetActive(true);root.transform.SetPositionAndRotation(native.Torso.position+transform.rotation*mounts[i],transform.rotation*Quaternion.Euler(0,180+headings[i],0));root.transform.localScale=Vector3.one*lengths[i];Flow(i);
            }
        }
        void OnDestroy(){if(rigs!=null)foreach(var rig in rigs)if(rig!=null)rig.Dispose();}
    }
}
