using UnityEngine;
namespace Sunward.Remaster
{
    // Smooth cylindrical carrier for the original soft spirit paint; no billboard corners.
    public sealed class PalaceSeal:MonoBehaviour
    {
        Mesh mesh;Material material;
        void Start()
        {
            const int around=128,up=12;var vertices=new Vector3[(around+1)*(up+1)];var uv=new Vector2[vertices.Length];var triangles=new int[around*up*6];int k=0;
            for(int y=0;y<=up;y++)for(int i=0;i<=around;i++){float a=i*Mathf.PI*2/around;int at=y*(around+1)+i;vertices[at]=new Vector3(Mathf.Sin(a)*3.7f,y*6f/up,Mathf.Cos(a)*3.7f);uv[at]=new Vector2(i/(float)around,y/(float)up);if(y==up || i==around)continue;triangles[k++]=at;triangles[k++]=at+around+1;triangles[k++]=at+1;triangles[k++]=at+1;triangles[k++]=at+around+1;triangles[k++]=at+around+2;}
            mesh=new Mesh{name="Smooth continuous celestial seal"};mesh.vertices=vertices;mesh.uv=uv;mesh.triangles=triangles;mesh.RecalculateBounds();gameObject.AddComponent<MeshFilter>().sharedMesh=mesh;
            material=new Material(Resources.Load<Material>("Okami/Effects/PalaceVeil"));material.SetFloat("_SoftSeal",1);material.SetColor("_BarrierTint",new Color(.38f,.62f,.95f,.75f));gameObject.AddComponent<MeshRenderer>().sharedMaterial=material;
        }
        void OnDestroy(){if(mesh)Destroy(mesh);if(material)Destroy(material);}
    }
}
