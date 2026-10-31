using System;
using UnityEngine;

namespace Sunward.Remaster
{
    [DefaultExecutionOrder(50)]
    public sealed class OriginalWeaponView : MonoBehaviour
    {
        NativePaintedRig rig;
        NativePoseBank bank;
        NativePoseBank.Clip idle, action;
        string package, family;
        float idleTime;
        Vector3[] position,scale;
        Quaternion[] rotation;
        public void Load(string source,string kind="reflector")
        {
            if(rig!=null)rig.Dispose();
            package=source;family=kind;rig=new NativePaintedRig("Okami/"+source,transform);
            bank=new NativePoseBank("Okami/"+source+"/Poses");
            if(bank.BoneCount!=rig.Bones.Length)throw new InvalidOperationException("Original weapon skeleton mismatch: "+source);
            position=new Vector3[bank.BoneCount];scale=new Vector3[bank.BoneCount];rotation=new Quaternion[bank.BoneCount];
            for(int i=0;i<position.Length;i++){position[i]=rig.Bones[i].localPosition;scale[i]=Vector3.one;rotation[i]=Quaternion.identity;}
            idle=bank.Find(package+(family=="glaive"?"_001":"_000"));
            if(idle==null)throw new InvalidOperationException("Original weapon idle is missing: "+source);
            // Rosary bones can extend beyond the shared actor's 8 m bounds.
            // Keep the original whip visible throughout its authored reach.
            foreach(var renderer in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>())
            {renderer.localBounds=new Bounds(Vector3.zero,new Vector3(64,32,64));renderer.updateWhenOffscreen=true;}
            rig.Root.SetActive(true);Sample(idle,0,true);
        }
        string Action(string state)
        {
            // Reflector/glaive placement is driven by their original PL dorsal
            // bone. Their 002..00f WP clips are static placeholders, not attacks.
            if(family!="rosary")return null;
            string suffix=state.Substring(state.LastIndexOf('_')+1);
            int index=suffix=="540"?1:suffix=="542"?2:suffix=="544"?3:suffix=="546"?4:suffix=="548"?5:suffix=="54a"?6:suffix=="54b"?8:suffix=="54f"?15:12;
            return package+"_"+index.ToString("x3");
        }
        public float AttackLength(string state)
        {var name=Action(state);var clip=name==null?null:bank.Find(name);return clip==null?0:clip.Duration;}
        public void BeginAttack(string state)
        {var name=Action(state);action=name==null?null:bank.Find(name);}
        public void AttackPhase(float phase)
        {if(action!=null)Sample(action,Mathf.Clamp01(phase)*action.Duration,false);}
        public void EndAttack(){action=null;}
        void LateUpdate()
        {
            if(rig==null || idle==null || action!=null)return;
            idleTime+=Time.deltaTime;Sample(idle,idleTime,true);
        }
        void Sample(NativePoseBank.Clip clip,float time,bool loop)=>bank.Sample(clip,time,rig.Bones,position,rotation,scale,1,loop);
        void OnDestroy(){if(rig!=null)rig.Dispose();}
    }
}
