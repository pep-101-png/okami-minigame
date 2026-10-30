using UnityEngine;

namespace Sunward.Remaster
{
    [DefaultExecutionOrder(50)]
    public sealed class OriginalWeaponView : MonoBehaviour
    {
        NativePaintedRig rig;
        NativePoseBank bank;
        NativePoseBank.Clip clip;
        string package;
        float time;
        Vector3[] position,scale;
        Quaternion[] rotation;
        public void Load(string source)
        {
            package=source;rig=new NativePaintedRig("Okami/"+source,transform);
            bank=new NativePoseBank("Okami/"+source+"/Poses");
            if(bank.BoneCount!=rig.Bones.Length)throw new System.InvalidOperationException("Original weapon skeleton mismatch: "+source);
            position=new Vector3[bank.BoneCount];scale=new Vector3[bank.BoneCount];rotation=new Quaternion[bank.BoneCount];
            for(int i=0;i<position.Length;i++){position[i]=rig.Bones[i].localPosition;scale[i]=Vector3.one;rotation[i]=Quaternion.identity;}
            clip=bank.Find(package+"_000");rig.Root.SetActive(true);Sample();
        }
        public void Attack(int chain,bool heavy)
        {
            var next=bank.Find(package+"_"+(heavy?4:1+chain%3).ToString("x3"));
            clip=next??bank.Find(package+"_000");time=0;
        }
        void LateUpdate()
        {
            if(rig==null || clip==null)return;
            time+=Time.deltaTime;
            if(!clip.Loop && time>clip.Duration){clip=bank.Find(package+"_000");time=0;}
            Sample();
        }
        void Sample(){if(clip!=null)bank.Sample(clip,time,rig.Bones,position,rotation,scale,1,clip.Loop);}
        void OnDestroy(){if(rig!=null)rig.Dispose();}
    }
}
