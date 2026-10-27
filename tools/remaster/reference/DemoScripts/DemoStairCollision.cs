using System;
using System.Collections.Generic;
using UnityEngine;

namespace SunwardVillageDemo
{
    public sealed class DemoStairCollision : MonoBehaviour
    {
        [Serializable] sealed class Data { public Ramp[] ramps; }
        [Serializable] sealed class Ramp { public string name; public Vector3[] vertices; public float rise, run, baseY; }
        readonly List<Mesh> meshes=new List<Mesh>();
        public void Initialize()
        {
            TextAsset text=Resources.Load<TextAsset>("DemoGeometry/StairRamps");
            if(text==null)throw new InvalidOperationException("The connected stair collision data is missing.");
            Data data=JsonUtility.FromJson<Data>(text.text);if(data==null||data.ramps==null)throw new InvalidOperationException("Invalid stair data.");
            foreach(Ramp ramp in data.ramps)
            {
                if(ramp.vertices==null||ramp.vertices.Length!=4||ramp.run<=0||ramp.rise/ramp.run>1)throw new InvalidOperationException("Invalid stair walking surface: "+ramp.name);
                GameObject item=new GameObject(ramp.name+" continuous walking surface");item.transform.SetParent(transform,false);
                Mesh mesh=new Mesh();mesh.name=ramp.name+" solid stair ramp";Vector3[] v=new Vector3[8];
                for(int i=0;i<4;++i){v[i]=ramp.vertices[i];v[i+4]=new Vector3(v[i].x,ramp.baseY,v[i].z);}
                int[] indices={0,1,2,0,2,3,4,6,5,4,7,6,0,4,5,0,5,1,1,5,6,1,6,2,2,6,7,2,7,3,3,7,4,3,4,0};
                Vector3 center=Vector3.zero;foreach(Vector3 p in v)center+=p/8;
                for(int i=0;i<indices.Length;i+=3){Vector3 a=v[indices[i]],b=v[indices[i+1]],c=v[indices[i+2]];if(Vector3.Dot(Vector3.Cross(b-a,c-a),(a+b+c)/3-center)<0){int swap=indices[i+1];indices[i+1]=indices[i+2];indices[i+2]=swap;}}
                mesh.vertices=v;mesh.triangles=indices;mesh.RecalculateBounds();item.AddComponent<MeshCollider>().sharedMesh=mesh;meshes.Add(mesh);
            }
            Debug.Log("Connected stair walking surfaces loaded: "+meshes.Count);
        }
        void OnDestroy(){foreach(Mesh m in meshes)if(m!=null){if(Application.isPlaying)Destroy(m);else DestroyImmediate(m);}meshes.Clear();}
    }
}
