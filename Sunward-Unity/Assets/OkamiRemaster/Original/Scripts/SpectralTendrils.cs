using UnityEngine;
namespace Sunward.Remaster
{
    // Smoothed original ES ribbons and seamless authored wind loops; full-power ES3A only.
    public sealed class SpectralTendrils:MonoBehaviour
    {
        NativeAmaterasu native;NativePaintedRig[] rigs;NativePoseBank bank;
        Vector3[][] positions,scales;Quaternion[][] rotations,neutral,rest;NativePoseBank.Clip[] clips;
        Material[][] materials;Light aura;float clock;
        readonly Vector3[] mounts={new Vector3(-.38f,-.02f,-.26f),new Vector3(.42f,.015f,-.34f),new Vector3(-.43f,0,-.48f),new Vector3(.35f,-.035f,-.54f),new Vector3(-.34f,.02f,-.68f),new Vector3(.40f,-.01f,-.75f)};
        readonly float[] lengths={.76f,.94f,.82f,.88f,.71f,1.0f};
        readonly float[] rates={.19f,.27f,.23f,.16f,.29f,.21f};
        readonly float[] phases={.13f,.68f,1.07f,.31f,.87f,.49f};
        readonly float[] headings={-3f,4.5f,1f,-5f,6f,-1.5f};
        readonly float[] gains={.34f,.42f,.30f,.40f,.36f,.38f};
        readonly float[] rolls={-58f,37f,-24f,68f,-42f,16f};
        readonly float[] bows={.08f,.14f,.10f,.16f,.09f,.12f};
        readonly string[] motions={"et03_002","et03_003","et03_002","et03_001","et03_003","et03_002"};
        void Start(){native=GetComponent<NativeAmaterasu>();}
        void Build()
        {
            bank=new NativePoseBank("Okami/es4a/Poses");rigs=new NativePaintedRig[6];positions=new Vector3[6][];scales=new Vector3[6][];rotations=new Quaternion[6][];materials=new Material[6][];clips=new NativePoseBank.Clip[6];neutral=new Quaternion[6][];rest=new Quaternion[6][];
            var shader=Resources.Load<Material>("Okami/Effects/SpiritRibbon").shader;
            for(int i=0;i<rigs.Length;i++)
            {
                rigs[i]=new NativePaintedRig(i%2==0?"Okami/es4a-flow":"Okami/es4b-flow",transform);int n=rigs[i].Bones.Length;
                if(n!=bank.BoneCount)throw new System.InvalidOperationException("Original ES tendril skeleton mismatch");positions[i]=new Vector3[n];scales[i]=new Vector3[n];rotations[i]=new Quaternion[n];
                for(int b=0;b<n;b++){positions[i][b]=rigs[i].Bones[b].localPosition;scales[i][b]=Vector3.one;rotations[i][b]=Quaternion.identity;}
                // These are native seamless, constant-length wind cycles, not the
                // large non-looping entrance/attack curves played back and forth.
                clips[i]=bank.Find(motions[i]);neutral[i]=new Quaternion[n];rest[i]=new Quaternion[n];
                for(int b=0;b<n;b++){neutral[i][b]=Quaternion.Inverse(MeanRotation(clips[i],b));rest[i][b]=b<2?Quaternion.identity:Quaternion.Slerp(Quaternion.identity,neutral[i][b],bows[i]);}
                var renderers=rigs[i].Root.GetComponentsInChildren<SkinnedMeshRenderer>();materials[i]=new Material[renderers.Length];
                for(int k=0;k<renderers.Length;k++){var renderer=renderers[k];renderer.sharedMaterial.shader=shader;renderer.sharedMaterial.SetColor("_Tint",new Color(.94f,.96f,1,.72f));renderer.updateWhenOffscreen=true;renderer.localBounds=new Bounds(Vector3.zero,new Vector3(14,10,14));materials[i][k]=renderer.sharedMaterial;}
            }
            var lamp=new GameObject("Original full-power ribbon radiance");lamp.transform.SetParent(transform,false);lamp.transform.localPosition=Vector3.up*1.2f;aura=lamp.AddComponent<Light>();aura.type=LightType.Point;aura.range=5;aura.shadows=LightShadows.None;aura.color=new Color(1,.85f,.5f);aura.intensity=.65f;
        }
        Quaternion MeanRotation(NativePoseBank.Clip clip,int bone)
        {
            var reference=clip.Rotation[bone];float x=0,y=0,z=0,w=0;
            for(int f=0;f<clip.Samples;f++){var q=clip.Rotation[f*bank.BoneCount+bone];float sign=q.x*reference.x+q.y*reference.y+q.z*reference.z+q.w*reference.w<0?-1:1;x+=q.x*sign;y+=q.y*sign;z+=q.z*sign;w+=q.w*sign;}
            float length=Mathf.Sqrt(x*x+y*y+z*z+w*w);return new Quaternion(x/length,y/length,z/length,w/length);
        }
        Quaternion WindRotation(NativePoseBank.Clip clip,int bone,float time)
        {
            float frame=Mathf.Repeat(time,clip.Duration)/clip.Duration*(clip.Samples-1);int a=Mathf.FloorToInt(frame),b=Mathf.Min(a+1,clip.Samples-1);
            return Quaternion.Slerp(clip.Rotation[a*bank.BoneCount+bone],clip.Rotation[b*bank.BoneCount+bone],frame-a);
        }
        void LateUpdate()
        {
            if(!native || !native.Ready)return;bool active=native.FullPower;
            if(!active){if(aura)aura.enabled=false;if(rigs!=null)foreach(var rig in rigs)rig.Root.SetActive(false);return;}
            if(rigs==null)Build();clock+=Time.unscaledDeltaTime;aura.enabled=true;
            for(int i=0;i<rigs.Length;i++)
            {
                var root=rigs[i].Root;root.SetActive(true);
                // Pin each root to the torso. No elastic following, paired fan,
                // changing length, or mirrored left/right choreography.
                root.transform.SetPositionAndRotation(native.Torso.position+transform.rotation*mounts[i],transform.rotation*Quaternion.Euler(0,180+headings[i],rolls[i]));
                root.transform.localScale=Vector3.one*lengths[i];
                var clip=clips[i];
                for(int b=0;b<rigs[i].Bones.Length;b++)
                {
                    var bone=rigs[i].Bones[b];var variation=neutral[i][b]*WindRotation(clip,b,clock*rates[i]+phases[i]-b*.19f);
                    // The original clips include a strong fixed bend. Keep only
                    // their small wind variation around a shallow trailing bow.
                    // Delayed sampling carries the wave outward along the chain.
                    bone.localRotation=rest[i][b]*Quaternion.Slerp(Quaternion.identity,variation,gains[i]);
                    bone.localPosition=positions[i][b];bone.localScale=Vector3.one;
                }
            }
        }
        void OnDestroy(){if(rigs!=null)foreach(var rig in rigs)if(rig!=null)rig.Dispose();}
    }
}
