using System;
using System.Collections.Generic;
using UnityEngine;

namespace Sunward.Remaster
{
    // Venue-only support correction after native MOT skinning, including blends.
    // Foot vertex indices come from the original leg skin weights, not props.
    [DefaultExecutionOrder(60)]
    public sealed class NativePracticeAnchor : MonoBehaviour
    {
        [Serializable] public sealed class Foot { public string part; public int[] indices; }
        public OriginalActor actor;
        public Foot[] feet;
        readonly List<Vector3> vertices = new List<Vector3>();
        Mesh baked;
        SkinnedMeshRenderer[] renderers;
        Transform root;
        void LateUpdate()
        {
            if(!actor || !actor.Ready || feet==null)return;
            if(!root)
            {
                renderers=actor.GetComponentsInChildren<SkinnedMeshRenderer>();
                if(renderers.Length==0)return;
                root=renderers[0].transform.parent;
                baked=new Mesh { name="Native practice support sample" };
            }
            float low=float.PositiveInfinity;Vector3 centre=Vector3.zero;int count=0;
            foreach(var foot in feet)
            {
                var renderer=Array.Find(renderers,r=>r.name==foot.part);
                if(!renderer)continue;
                renderer.BakeMesh(baked);vertices.Clear();baked.GetVertices(vertices);
                Matrix4x4 matrix=root.worldToLocalMatrix*renderer.transform.localToWorldMatrix;
                foreach(int index in foot.indices)
                {
                    if(index<0 || index>=vertices.Count)continue;
                    var p=matrix.MultiplyPoint3x4(vertices[index]);
                    low=Mathf.Min(low,p.y);centre+=p;count++;
                }
            }
            if(count==0)return;
            centre/=count;
            root.localPosition=Vector3.Scale(new Vector3(-centre.x,-low,-centre.z),root.localScale);
        }
        void OnDestroy(){if(baked)Destroy(baked);}
    }
}
