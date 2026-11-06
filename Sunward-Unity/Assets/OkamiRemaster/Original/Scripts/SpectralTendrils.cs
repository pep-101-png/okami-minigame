using UnityEngine;
namespace Sunward.Remaster
{
    // Original ES4A/ES4B mesh pair and their matching recovered et03 motion.
    public sealed class SpectralTendrils:MonoBehaviour
    {
        NativeAmaterasu native;NativePaintedRig[] rigs;NativePoseBank bank;
        Vector3[][] positions,scales;Quaternion[][] rotations;Transform[] anchors;
        Material[][] materials;Light aura;float clock;int form=-1;
        void Start(){native=GetComponent<NativeAmaterasu>();}
        void Build()
        {
            bank=new NativePoseBank("Okami/es4a/Poses");rigs=new NativePaintedRig[12];positions=new Vector3[12][];scales=new Vector3[12][];rotations=new Quaternion[12][];materials=new Material[12][];
            var shader=Resources.Load<Material>("Okami/Effects/SpiritRadiance").shader;
            for(int i=0;i<12;i++)
            {
                rigs[i]=new NativePaintedRig(i%2==0?"Okami/es4a":"Okami/es4b",transform);int n=rigs[i].Bones.Length;
                if(n!=bank.BoneCount)throw new System.InvalidOperationException("Original ES tendril skeleton mismatch");positions[i]=new Vector3[n];scales[i]=new Vector3[n];rotations[i]=new Quaternion[n];
                for(int b=0;b<n;b++){positions[i][b]=rigs[i].Bones[b].localPosition;scales[i][b]=Vector3.one;rotations[i][b]=Quaternion.identity;}
                var renderers=rigs[i].Root.GetComponentsInChildren<SkinnedMeshRenderer>();materials[i]=new Material[renderers.Length];
                for(int k=0;k<renderers.Length;k++){var renderer=renderers[k];renderer.sharedMaterial.shader=shader;renderer.sharedMaterial.SetFloat("_NativeRibbons",1);renderer.updateWhenOffscreen=true;renderer.localBounds=new Bounds(Vector3.zero,new Vector3(14,10,14));materials[i][k]=renderer.sharedMaterial;}
            }
            var lamp=new GameObject("Original Shiranui tendril radiance");lamp.transform.SetParent(transform,false);lamp.transform.localPosition=Vector3.up*1.2f;aura=lamp.AddComponent<Light>();aura.type=LightType.Point;aura.range=5;aura.shadows=LightShadows.None;
        }
        void LateUpdate()
        {
            if(!native || !native.Ready)return;if(rigs==null)Build();clock+=Time.unscaledDeltaTime;bool active=native.Shiranui;
            if(form!=native.FormLevel){form=native.FormLevel;var power=native.PowerBones;anchors=new[]{native.Back,native.Head,power[0],power[1],power[2],power[3]};}
            aura.enabled=active;aura.color=native.FullPower?new Color(1,.85f,.5f):new Color(.65f,.85f,1);aura.intensity=native.FullPower?4:2;
            for(int i=0;i<rigs.Length;i++)
            {
                var root=rigs[i].Root;root.SetActive(active);if(!active)continue;
                var anchor=anchors[i/2];float side=i%2==0?-1:1;root.transform.position=anchor.position+transform.right*(side*.13f)+Vector3.up*.08f;
                root.transform.rotation=transform.rotation*Quaternion.Euler(8*Mathf.Sin(clock*.65f+i),180+side*12,side*10);
                root.transform.localScale=Vector3.one*(native.FullPower?1.2f:1);
                var clip=bank.Find(i%3==0?"et03_000":"et03_006");float phase=(1-Mathf.Cos((clock+i*.37f)*Mathf.PI/clip.Duration))*.5f;
                bank.Sample(clip,phase*clip.Duration,rigs[i].Bones,positions[i],rotations[i],scales[i],1,false);
                foreach(var material in materials[i])material.SetColor("_Tint",native.FullPower?new Color(2.2f,1.9f,1.25f,.78f):new Color(1.35f,1.65f,2,.7f));
            }
        }
        void OnDestroy(){if(rigs!=null)foreach(var rig in rigs)if(rig!=null)rig.Dispose();}
    }
}
