using UnityEngine;
namespace Sunward.Remaster
{
    // Original core fire/smoke paintings on bounded billboard carriers.
    // This is a Sunward emitter, not a recovered EST interpreter.
    [DefaultExecutionOrder(70)]
    public sealed class ImpCannonPaint : MonoBehaviour
    {
        sealed class Layer
        {
            public string sprite; public int count;public Mesh mesh;public Material material;
            public Vector3[] vertices;public Color[] colors;public Vector2[] uv;
        }
        Layer[] layers;GameFlow game;float elapsed,life;int kind;Vector3 trail=Vector3.back;
        public static ImpCannonPaint Spawn(GameFlow game,Transform parent,Vector3 point,int kind)
        {
            var go=new GameObject(kind==0?"Original cannon fire in flight":kind==1?"Original cannon muzzle flash":"Original cannon explosion");
            if(parent)go.transform.SetParent(parent,false);go.transform.position=point;
            var paint=go.AddComponent<ImpCannonPaint>();paint.game=game;paint.kind=kind;paint.life=kind==0?100:kind==1?.5f:.9f;
            paint.layers=new[]{paint.Make("CannonCore",1,false),paint.Make("CannonFire",kind==2?8:3,false),paint.Make("CannonSmoke",kind==0?0:kind==1?5:10,true)};
            paint.Draw();return paint;
        }
        public void Trail(Vector3 velocity){if(velocity.sqrMagnitude>.001f)trail=-velocity.normalized;}
        Layer Make(string sprite,int count,bool atlas)
        {
            var layer=new Layer{sprite=sprite,count=count,vertices=new Vector3[count*4],colors=new Color[count*4],uv=new Vector2[count*4]};
            if(count==0)return layer;
            var go=new GameObject("Original paint · "+sprite);go.transform.SetParent(transform,false);
            layer.mesh=new Mesh{name="Original cannon billboard paint"};var triangles=new int[count*6];
            for(int i=0;i<count;i++)
            {
                float x=atlas?(i%2)*.5f:0,y=atlas?((i/2)%2)*.5f:0,size=atlas?.5f:1;
                int k=i*4;layer.uv[k]=new Vector2(x,y);layer.uv[k+1]=new Vector2(x+size,y);layer.uv[k+2]=new Vector2(x+size,y+size);layer.uv[k+3]=new Vector2(x,y+size);
                int a=i*6;triangles[a]=k;triangles[a+1]=k+1;triangles[a+2]=k+2;triangles[a+3]=k;triangles[a+4]=k+2;triangles[a+5]=k+3;
            }
            layer.mesh.vertices=layer.vertices;layer.mesh.triangles=triangles;layer.mesh.uv=layer.uv;
            go.AddComponent<MeshFilter>().sharedMesh=layer.mesh;
            layer.material=new Material(Resources.Load<Material>("Okami/Effects/Surface")){mainTexture=Resources.Load<Texture2D>("Okami/Effects/"+sprite)};
            go.AddComponent<MeshRenderer>().sharedMaterial=layer.material;return layer;
        }
        void Update(){if(game && game.Blocked)return;elapsed+=Time.deltaTime;if(kind!=0 && elapsed>=life)Destroy(gameObject);}
        void LateUpdate(){Draw();}
        void Draw()
        {
            if(layers==null)return;
            Vector3 right=Camera.main?Camera.main.transform.rotation*Vector3.right:Vector3.right;
            Vector3 up=Camera.main?Camera.main.transform.rotation*Vector3.up:Vector3.up;
            for(int g=0;g<layers.Length;g++)
            {
                var l=layers[g];if(l.count==0)continue;
                for(int i=0;i<l.count;i++)
                {
                    float t=elapsed,a=i*2.399963f,phase=Mathf.Clamp01(t/life),size,alpha,rotation;
                    Vector3 offset;Color color;
                    if(kind==0)
                    {
                        offset=g==0?Vector3.zero:trail*(.12f+i*.20f);size=g==0?.62f:.67f-i*.13f;alpha=g==0?1:.9f-i*.16f;rotation=t*(g==0?7:3)+a;
                        color=g==0?new Color(1,.78f,.38f,alpha):new Color(1,1,1,alpha);
                    }
                    else if(g==0)
                    {
                        float p=Mathf.Clamp01(t/(kind==1?.16f:.25f));offset=Vector3.zero;size=(kind==1?.7f:1.7f)+p*(kind==1?.65f:1.4f);alpha=1-p;rotation=t*8;
                        color=new Color(1,.82f,.46f,alpha);
                    }
                    else if(g==1)
                    {
                        float p=Mathf.Clamp01(t/(kind==1?.28f:.5f));float radius=p*(kind==1?.35f:1.5f);
                        offset=new Vector3(Mathf.Cos(a)*radius,p*.35f,Mathf.Sin(a)*radius);size=(kind==1?.6f:1.1f)*(1-.5f*p);alpha=1-p;rotation=a+p*2;
                        color=new Color(1,1,1,alpha);
                    }
                    else
                    {
                        float delay=kind==1?.03f:.08f;float smoke=Mathf.Clamp01((t-delay)/(life-delay));float radius=(kind==1?.15f:.45f)+smoke*(kind==1?.6f:1.8f);offset=new Vector3(Mathf.Cos(a)*radius,phase*(.45f+(i%3)*.14f),Mathf.Sin(a)*radius);
                        size=(kind==1?.45f:.8f)+phase*(kind==1?.5f:1.0f);alpha=t<delay?0:(1-smoke)*.55f;rotation=a+phase*.5f;
                        color=new Color(.40f,.35f,.31f,alpha);
                    }
                    Vector3 x=(right*Mathf.Cos(rotation)+up*Mathf.Sin(rotation))*size*.5f;
                    Vector3 y=(-right*Mathf.Sin(rotation)+up*Mathf.Cos(rotation))*size*.5f;
                    int k=i*4;Vector3 center=transform.position+offset;
                    l.vertices[k]=transform.InverseTransformPoint(center-x-y);l.vertices[k+1]=transform.InverseTransformPoint(center+x-y);l.vertices[k+2]=transform.InverseTransformPoint(center+x+y);l.vertices[k+3]=transform.InverseTransformPoint(center-x+y);
                    for(int j=0;j<4;j++)l.colors[k+j]=color;
                }
                l.mesh.vertices=l.vertices;l.mesh.colors=l.colors;l.mesh.RecalculateBounds();
            }
        }
        void OnDestroy(){if(layers!=null)foreach(var l in layers){if(l.mesh)Destroy(l.mesh);if(l.material)Destroy(l.material);}}
    }
}
