using System;
using UnityEngine;

namespace Sunward.Remaster
{
    // Rigid original MD appearance for transient gameplay objects. Lifetime and
    // projectile movement remain Sunward mechanics, not fabricated native events.
    public sealed class OriginalVisual : MonoBehaviour
    {
        public Transform PaintRoot=>rig!=null?rig.Root.transform:transform;
        NativePaintedRig rig;bool motionBoundsExpanded;NativePoseBank motionBank;Vector3[] motionPositions,motionScales;Quaternion[] motionRotations;
        void PrepareMotion(string resource)
        {
            if(motionBank!=null)return;motionBank=new NativePoseBank(resource+"/Poses");if(motionBank.BoneCount!=rig.Bones.Length)throw new InvalidOperationException("Native prop motion skeleton mismatch");motionPositions=new Vector3[rig.Bones.Length];motionScales=new Vector3[rig.Bones.Length];motionRotations=new Quaternion[rig.Bones.Length];
        }
        public void SampleMotion(string resource,string clip,float time)
        {
            if(rig==null)return;PrepareMotion(resource);
            var selected=motionBank.Find(clip);if(selected!=null)motionBank.Sample(selected,time,rig.Bones,motionPositions,motionRotations,motionScales,1,false);
        }
        public void SampleBoneMotion(string resource,string clip,float time,int bone)
        {
            if(rig==null || bone<0 || bone>=rig.Bones.Length)return;PrepareMotion(resource);
            if(!motionBoundsExpanded){foreach(var renderer in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true)){var b=renderer.sharedMesh.bounds;renderer.localBounds=new Bounds(b.center,b.size+Vector3.one*1.5f);renderer.updateWhenOffscreen=true;}motionBoundsExpanded=true;}
            motionBank.SampleBone(motionBank.Find(clip),time,rig.Bones[bone],bone);
        }
        public bool Load(string resource, Vector3 offset, Vector3 scale)
        {
            try
            {
                rig = new NativePaintedRig(resource, transform);
                rig.Root.transform.localPosition = offset;
                rig.Root.transform.localScale = scale;
                foreach(var renderer in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>())
                    renderer.localBounds=renderer.sharedMesh.bounds;
                rig.Root.SetActive(true);
                return true;
            }
            catch (Exception error)
            {
                if (rig != null) rig.Dispose();
                Debug.LogError("Original effect appearance could not load: " + error.Message, this);
                return false;
            }
        }
        void OnDestroy() { if (rig != null) rig.Dispose(); }
    }
}
