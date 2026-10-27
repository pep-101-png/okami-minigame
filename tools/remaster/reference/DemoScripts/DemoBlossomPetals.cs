using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace SunwardVillageDemo
{
    public sealed class DemoBlossomPetals : MonoBehaviour
    {
        [Serializable] sealed class Data { public Tree[] trees; public Room[] rooms; }
        [Serializable] sealed class Tree { public string name; public Vector3 center; public float radius, ground; }
        [Serializable] sealed class Room { public string name; public Vector3 center,size; public float yaw; }
        sealed class Falling { public Transform transform; public Renderer renderer; public Vector3 velocity; public float ground, age, life, seed; public int texture; public bool screen; }
        sealed class Settled { public Vector3 position; public float size, angle, born; public int texture; }
        readonly List<Falling> falling=new List<Falling>();
        readonly List<Settled> settled=new List<Settled>();
        readonly List<Mesh> groundMeshes=new List<Mesh>();
        readonly Material[] paints=new Material[3];
        Data data; DemoExplorer explorer; Camera view;
        Mesh quad;MaterialPropertyBlock properties;
        float treeClock,screenClock,groundClock,worldClock;int nextFalling,nextGround,nextTree;
        readonly System.Random random=new System.Random(261026);
        float Range(float a,float b){return a+(b-a)*(float)random.NextDouble();}
        public void Initialize()
        {
            TextAsset asset=Resources.Load<TextAsset>("DemoGeometry/BlossomTrees");if(asset==null){Debug.LogError("Blossom canopy data is missing.");enabled=false;return;}
            data=JsonUtility.FromJson<Data>(asset.text);if(data==null||data.trees==null||data.rooms==null){enabled=false;return;}
            for(int i=0;i<3;++i){paints[i]=Resources.Load<Material>("Farm/PetalPaint"+i);if(paints[i]==null){Debug.LogError("Original petal material missing.");enabled=false;return;}}
            properties=new MaterialPropertyBlock();view=Camera.main;explorer=FindFirstObjectByType<DemoExplorer>();
            quad=new Mesh();quad.name="Shared original petal billboard";quad.vertices=new[]{new Vector3(-.5f,-.5f,0),new Vector3(.5f,-.5f,0),new Vector3(.5f,.5f,0),new Vector3(-.5f,.5f,0)};quad.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};quad.colors=new[]{Color.white,Color.white,Color.white,Color.white};quad.triangles=new[]{0,1,2,0,2,3};quad.RecalculateBounds();
            for(int i=0;i<128;++i)
            {
                GameObject item=new GameObject("Pooled drifting original blossom petal");item.transform.SetParent(transform,false);item.AddComponent<MeshFilter>().sharedMesh=quad;MeshRenderer r=item.AddComponent<MeshRenderer>();r.shadowCastingMode=ShadowCastingMode.Off;r.receiveShadows=false;item.SetActive(false);falling.Add(new Falling{transform=item.transform,renderer=r});
            }
            for(int i=0;i<180;++i)settled.Add(new Settled{born=-1000});
            for(int i=0;i<3;++i)
            {
                GameObject item=new GameObject("Batched newly settled blossom petals "+i);item.transform.SetParent(transform,false);Mesh mesh=new Mesh();mesh.MarkDynamic();item.AddComponent<MeshFilter>().sharedMesh=mesh;MeshRenderer r=item.AddComponent<MeshRenderer>();r.sharedMaterial=paints[i];r.shadowCastingMode=ShadowCastingMode.Off;r.receiveShadows=false;groundMeshes.Add(mesh);
            }
            RebuildGround();
        }
        bool InsideRoom(Vector3 p)
        {
            foreach(Room room in data.rooms){Vector3 q=Quaternion.Inverse(Quaternion.Euler(0,room.yaw,0))*(p-room.center);if(Mathf.Abs(q.x)<room.size.x*.5f+.12f&&Mathf.Abs(q.z)<room.size.z*.5f+.12f)return true;}return false;
        }
        void Spawn(Vector3 p,float ground,bool screen)
        {
            if(InsideRoom(p))return;Falling f=falling[nextFalling++%falling.Count];f.texture=random.Next(3);f.renderer.sharedMaterial=paints[f.texture];f.age=0;f.life=screen?15:30;f.seed=Range(0,6.28f);f.screen=screen;f.ground=ground;f.velocity=new Vector3(Range(.22f,.42f),-Range(.28f,.43f),Range(.04f,.16f));f.transform.position=p;f.transform.localScale=Vector3.one*Range(.075f,.13f);f.transform.gameObject.SetActive(true);
        }
        void Update()
        {
            if(data==null||falling.Count==0)return;float dt=Mathf.Min(Time.deltaTime,.075f);treeClock+=dt;screenClock+=dt;groundClock+=dt;worldClock+=dt;
            if(data.trees.Length>0&&treeClock>1.3f/Mathf.Max(1,data.trees.Length))
            {
                treeClock=0;Tree tree=data.trees[nextTree++%data.trees.Length];float angle=Range(0,Mathf.PI*2),r=Mathf.Sqrt(Range(0,1))*tree.radius;
                Spawn(tree.center+new Vector3(Mathf.Cos(angle)*r,Range(-.35f,.25f),Mathf.Sin(angle)*r),tree.ground,false);
            }
            if(screenClock>.45f)
            {
                screenClock=0;if(explorer!=null&&explorer.IsWalking&&view!=null&&!InsideRoom(view.transform.position))
                {
                    Vector3 p=view.transform.position+view.transform.forward*Range(3.5f,6.5f)+view.transform.right*Range(-4.8f,4.8f)+Vector3.up*Range(.1f,1.5f);Spawn(p,explorer.VisitorPosition.y,true);
                }
            }
            if(worldClock>.25f)
            {
                worldClock=0;
                // Maintain a village/farm breeze in overview as well as on foot.
                Vector3 p=new Vector3(Range(-39,10),Range(2.8f,5.5f),Range(-11,23));
                if(!InsideRoom(p))Spawn(p,0,false);
            }
            foreach(Falling f in falling)
            {
                if(!f.transform.gameObject.activeSelf)continue;f.age+=dt;
                if(f.age>f.life){f.transform.gameObject.SetActive(false);continue;}
                Vector3 breeze=new Vector3(Mathf.Sin(f.age*.9f+f.seed)*.055f,0,Mathf.Cos(f.age*.7f+f.seed)*.035f);f.transform.position+=(f.velocity+breeze)*dt;
                if(InsideRoom(f.transform.position)){f.transform.gameObject.SetActive(false);continue;}
                if(view!=null)f.transform.rotation=view.transform.rotation*Quaternion.Euler(Mathf.Sin(f.age+f.seed)*25,Mathf.Cos(f.age*.8f+f.seed)*20,f.seed*57+f.age*15);
                properties.Clear();properties.SetFloat("_Opacity",Mathf.Min(1,f.age*2)*Mathf.Clamp01(f.life-f.age));f.renderer.SetPropertyBlock(properties);
                if(f.transform.position.y<f.ground+.06f)
                {
                    Vector3 p=f.transform.position;RaycastHit hit;
                    if(Physics.Raycast(p+Vector3.up*.6f,Vector3.down,out hit,1.4f,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))p.y=hit.point.y+.014f;else p.y=f.ground+.014f;
                    if(!f.screen&&!InsideRoom(p))
                    {
                        Settled s=settled[nextGround++%settled.Count];s.position=transform.InverseTransformPoint(p);s.size=f.transform.localScale.x;s.angle=Range(0,Mathf.PI*2);s.born=Time.time;s.texture=f.texture;
                    }
                    f.transform.gameObject.SetActive(false);
                }
            }
            if(groundClock>.8f){groundClock=0;RebuildGround();}
        }
        void RebuildGround()
        {
            for(int texture=0;texture<3;++texture)
            {
                List<Vector3> vertices=new List<Vector3>();List<Vector2> uv=new List<Vector2>();List<Color> colors=new List<Color>();List<int> triangles=new List<int>();
                foreach(Settled s in settled)
                {
                    float age=Time.time-s.born;if(age<0||age>240||s.texture!=texture)continue;float alpha=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(180,240,age));
                    Vector3 right=new Vector3(Mathf.Cos(s.angle),0,Mathf.Sin(s.angle))*s.size*.5f,up=new Vector3(-Mathf.Sin(s.angle),0,Mathf.Cos(s.angle))*s.size*.5f;int k=vertices.Count;
                    vertices.Add(s.position-right-up);vertices.Add(s.position+right-up);vertices.Add(s.position+right+up);vertices.Add(s.position-right+up);uv.AddRange(new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up});for(int i=0;i<4;++i)colors.Add(new Color(1,1,1,alpha));triangles.AddRange(new[]{k,k+2,k+1,k,k+3,k+2});
                }
                Mesh mesh=groundMeshes[texture];mesh.Clear();mesh.SetVertices(vertices);mesh.SetUVs(0,uv);mesh.SetColors(colors);mesh.SetTriangles(triangles,0);mesh.RecalculateBounds();
            }
        }
        void OnDestroy(){foreach(Mesh m in groundMeshes)if(m!=null){if(Application.isPlaying)Destroy(m);else DestroyImmediate(m);}if(quad!=null){if(Application.isPlaying)Destroy(quad);else DestroyImmediate(quad);}}
    }
}
