using UnityEngine;
namespace Sunward.Remaster
{
    // Original ES ribbons and seamless authored wind loops; full-power ES3A only.
    public sealed class SpectralTendrils:MonoBehaviour
    {
        NativeAmaterasu native;NativePaintedRig[] rigs;NativePoseBank bank;
        Vector3[][] positions,scales;Quaternion[][] rotations;NativePoseBank.Clip[] clips;
        Material[][] materials;Light aura;float clock;bool attached;
        void Start(){native=GetComponent<NativeAmaterasu>();}
        void Build()
        {
            bank=new NativePoseBank("Okami/es4a/Poses");rigs=new NativePaintedRig[6];positions=new Vector3[6][];scales=new Vector3[6][];rotations=new Quaternion[6][];materials=new Material[6][];clips=new NativePoseBank.Clip[6];
            var shader=Resources.Load<Material>("Okami/Effects/SpiritRadiance").shader;
            for(int i=0;i<rigs.Length;i++)
            {
                rigs[i]=new NativePaintedRig(i%2==0?"Okami/es4a":"Okami/es4b",transform);int n=rigs[i].Bones.Length;
                if(n!=bank.BoneCount)throw new System.InvalidOperationException("Original ES tendril skeleton mismatch");positions[i]=new Vector3[n];scales[i]=new Vector3[n];rotations[i]=new Quaternion[n];
                for(int b=0;b<n;b++){positions[i][b]=rigs[i].Bones[b].localPosition;scales[i][b]=Vector3.one;rotations[i][b]=Quaternion.identity;}
                // These are native seamless, constant-length wind cycles, not the
                // large non-looping entrance/attack curves played back and forth.
                clips[i]=bank.Find(i%2==0?"et03_002":"et03_003");
                var renderers=rigs[i].Root.GetComponentsInChildren<SkinnedMeshRenderer>();materials[i]=new Material[renderers.Length];
                for(int k=0;k<renderers.Length;k++){var renderer=renderers[k];renderer.sharedMaterial.shader=shader;renderer.sharedMaterial.SetFloat("_NativeRibbons",1);renderer.sharedMaterial.SetColor("_Tint",new Color(1.7f,1.65f,1.3f,.58f));renderer.updateWhenOffscreen=true;renderer.localBounds=new Bounds(Vector3.zero,new Vector3(14,10,14));materials[i][k]=renderer.sharedMaterial;}
            }
            var lamp=new GameObject("Original full-power ribbon radiance");lamp.transform.SetParent(transform,false);lamp.transform.localPosition=Vector3.up*1.2f;aura=lamp.AddComponent<Light>();aura.type=LightType.Point;aura.range=5;aura.shadows=LightShadows.None;aura.color=new Color(1,.85f,.5f);aura.intensity=2;
        }
        void LateUpdate()
        {
            if(!native || !native.Ready)return;bool active=native.FullPower;
            if(!active){attached=false;if(aura)aura.enabled=false;if(rigs!=null)foreach(var rig in rigs)rig.Root.SetActive(false);return;}
            if(rigs==null)Build();clock+=Time.unscaledDeltaTime;aura.enabled=true;
            float smooth=1-Mathf.Exp(-10*Time.unscaledDeltaTime);
            for(int i=0;i<rigs.Length;i++)
            {
                var root=rigs[i].Root;root.SetActive(true);float side=i%2==0?-1:1;int row=i/2;
                // All six roots follow the dorsal torso, never the head or paws.
                var point=native.Back.position+transform.rotation*new Vector3(side*.27f,-.20f+row*.015f,(row-1)*.32f);
                var rotation=transform.rotation*Quaternion.Euler(-2,180+side*(10+row*4),side*7);
                bool snap=!attached || Vector3.Distance(root.transform.position,point)>5;
                root.transform.SetPositionAndRotation(snap?point:Vector3.Lerp(root.transform.position,point,smooth),snap?rotation:Quaternion.Slerp(root.transform.rotation,rotation,smooth));root.transform.localScale=Vector3.one*1.05f;
                var clip=clips[i];bank.Sample(clip,clock*.32f+i*.21f,rigs[i].Bones,positions[i],rotations[i],scales[i],1,true);
            }
            attached=true;
        }
        void OnDestroy(){if(rigs!=null)foreach(var rig in rigs)if(rig!=null)rig.Dispose();}
    }
}
