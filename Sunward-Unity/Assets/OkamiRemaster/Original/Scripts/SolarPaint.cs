using UnityEngine;
namespace Sunward.Remaster
{
    // Original DDS paintings on deterministic Sunward carriers. Not a recovered EST player.
    [DefaultExecutionOrder(80)]
    public sealed class SolarPaint:MonoBehaviour
    {
        sealed class Layer
        {
            public string sprite;public int count,tiles;public Mesh mesh;public Material material;
            public Vector3[] vertices;public Color[] colors;public Vector2[] uv;
        }
        Layer[] layers;GameFlow game;int mode;float elapsed,heat;Vector3 centre,ground;
        public static SolarPaint Create(GameFlow g,Vector3 point,int kind)
        {
            var root=new GameObject(kind==0?"Celestial sun · original paint":kind==1?"Celestial sunburst · original paint":"Divine sword · original dust and debris");
            root.transform.position=point;var p=root.AddComponent<SolarPaint>();p.game=g;p.mode=kind;p.ground=p.centre=point;
            p.layers=kind==0?new[]{p.Make("SolarGlow",1),p.Make("OriginalSun",1),p.Make("CannonFire",24),p.Make("SpiritGlow",48),p.Make("OriginalGodSeal",1)}:
                new[]{p.Make("SolarGlow",1),p.Make("CannonCore",1),p.Make("SolarBlast",kind==1?32:5),p.Make("CannonFire",kind==1?96:10),p.Make("SolarPuff",kind==1?72:12,4),p.Make("ImpactDust",kind==1?64:14),p.Make("OriginalWhiteRing",kind==1?6:1),p.Make("ImpactRocks",kind==1?96:20,4)};
            return p;
        }
        Layer Make(string sprite,int count,int tiles=1)
        {
            var l=new Layer{sprite=sprite,count=count,tiles=tiles,vertices=new Vector3[count*4],colors=new Color[count*4],uv=new Vector2[count*4]};
            var go=new GameObject("Original solar paint · "+sprite);go.transform.SetParent(transform,false);l.mesh=new Mesh{name=sprite+" bounded carrier"};var tri=new int[count*6];
            for(int i=0;i<count;i++){int j=i*6,k=i*4;tri[j]=k;tri[j+1]=k+1;tri[j+2]=k+2;tri[j+3]=k;tri[j+4]=k+2;tri[j+5]=k+3;}
            l.mesh.vertices=l.vertices;l.mesh.triangles=tri;l.mesh.uv=l.uv;go.AddComponent<MeshFilter>().sharedMesh=l.mesh;
            l.material=new Material(Resources.Load<Material>(sprite=="ImpactDust" || sprite=="SolarPuff" || sprite=="SolarBlast"?"Okami/Effects/DustSurface":sprite=="SolarGlow" || sprite=="SpiritGlow"?"Okami/Effects/SpiritRadiance":"Okami/Effects/Surface")){mainTexture=Resources.Load<Texture2D>("Okami/Effects/"+sprite)};l.material.SetFloat("_Tiles",tiles);go.AddComponent<MeshRenderer>().sharedMaterial=l.material;return l;
        }
        public void Gather(Vector3 at,float charge){centre=at;heat=Mathf.Clamp01(charge);}
        void Update()
        {
            if(mode==0)return;
            if(game && game.Blocked && !(game.Ultimate && game.Ultimate.Playing))return;
            elapsed+=Time.unscaledDeltaTime;if(elapsed>(mode==1?2.8f:1.5f))Destroy(gameObject);
        }
        void LateUpdate()
        {
            if(layers==null)return;
            Vector3 right=Camera.main?Camera.main.transform.rotation*Vector3.right:Vector3.right,up=Camera.main?Camera.main.transform.rotation*Vector3.up:Vector3.up;
            Vector3 back=Vector3.Cross(right,up);float clock=mode==0?Time.unscaledTime:elapsed;
            for(int g=0;g<layers.Length;g++)
            {
                var l=layers[g];
                for(int i=0;i<l.count;i++)
                {
                    float a=i*2.399963f,t=elapsed,u=Mathf.Clamp01(t/(mode==1?2.6f:1.35f)),size=1,alpha=0,rotation=a;Vector3 pos=ground;Color tint=Color.white;bool flat=false;int tile=i%(l.tiles*l.tiles);
                    if(mode==0)
                    {
                        float sun=Mathf.Lerp(2.4f,9.4f,heat);pos=centre;
                        if(g==0){size=sun*1.65f;alpha=Mathf.Lerp(.10f,.75f,heat*heat);pos+=back*.6f;tint=Color.Lerp(new Color(1,.36f,.04f),new Color(1,.92f,.58f),heat);}
                        else if(g==1){size=sun;alpha=.68f+heat*.2f;pos+=back;rotation=clock*.12f;tint=Color.Lerp(new Color(1,.50f,.08f),new Color(1,.96f,.65f),heat*heat);}
                        else if(g==2){float angle=a+clock*.55f;pos+=right*Mathf.Sin(angle)*sun*.44f+up*Mathf.Cos(angle)*sun*.44f+back*.65f;size=(.6f+heat)*(.8f+(i%3)*.13f);alpha=.32f+heat*.4f;rotation=-angle;}
                        else if(g==3){float v=Mathf.Repeat(i/48f+clock*.24f,1),angle=v*Mathf.PI*5+clock*.7f;pos=Vector3.Lerp(ground,centre,v)+new Vector3(Mathf.Cos(angle),0,Mathf.Sin(angle))*(1-v)*2.3f;size=.12f+heat*.18f;alpha=Mathf.Sin(v*Mathf.PI)*.7f;tint=new Color(1,.87f,.5f);}
                        else{pos=ground+Vector3.up*.055f;size=5+heat*6;alpha=.18f+heat*.1f;flat=true;rotation=-clock*.1f;tint=new Color(1,.78f,.3f);}
                    }
                    else
                    {
                        float power=mode==1?1:.3f;
                        if(g==0){float v=Mathf.Clamp01(t/.24f);pos=ground+Vector3.up*(mode==1?3.8f:.4f);size=(8+v*30)*power;alpha=(1-v)*.8f;tint=new Color(1,.95f,.72f);}
                        else if(g==1){float v=Mathf.Clamp01(t/.38f);pos=ground+Vector3.up*(mode==1?4:.5f);size=(5+v*13)*power;alpha=(1-v)*.9f;rotation=t*1.5f;tint=new Color(1,.83f,.42f);}
                        else if(g==2){float v=Mathf.Clamp01((t-(i%4)*.018f)/(mode==1?1.25f:.5f));pos+=new Vector3(Mathf.Sin(a),0,Mathf.Cos(a))*((i%4)*.6f+v*(12+(i%5)*2))*power+Vector3.up*(.5f+Mathf.Sin(v*Mathf.PI)*(2+i%5)*power);size=(7+v*7)*power;alpha=(1-v)*.8f;rotation=t*.3f+a;tint=new Color(1,.71f,.30f);}
                        else if(g==3){float v=Mathf.Clamp01(t/(mode==1?1.4f:.65f));float speed=12+(i%7)*2;pos+=new Vector3(Mathf.Sin(a),0,Mathf.Cos(a))*speed*t*power+Vector3.up*Mathf.Max(.08f,(3+i%5)*t-4*t*t);size=(3.6f-2.8f*v)*power;alpha=1-v;rotation=a+t*1.8f;}
                        else if(g==4){float delay=mode==1?.12f:.04f;float v=Mathf.Clamp01((t-delay)/(mode==1?2.4f:1.15f));pos+=new Vector3(Mathf.Sin(a),0,Mathf.Cos(a))*(2+v*(18+(i%6)*2))*power+Vector3.up*(.4f+v*(2+i%3)*power);size=(2+v*4)*power;alpha=t<delay?0:(1-v)*.64f;tile=(i+Mathf.Min(15,Mathf.FloorToInt(v*16)))%16;rotation=a*.08f;tint=new Color(.60f,.49f,.35f);}
                        else if(g==5){float v=Mathf.Clamp01(t/(mode==1?1.6f:1.1f));pos+=new Vector3(Mathf.Sin(a),0,Mathf.Cos(a))*(.2f+v*29)*power+Vector3.up*(.3f+v*1.6f*power);size=(2.5f+v*6)*power;alpha=Mathf.Sin(v*Mathf.PI)*.7f;rotation=-.2f*Mathf.Sin(a);tint=new Color(.84f,.72f,.50f);}
                        else if(g==6){float v=Mathf.Clamp01((t-i*(mode==1?.065f:.13f))/(mode==1?.95f:.45f));pos+=Vector3.up*(.09f+i*.025f);size=(1+v*88)*power;alpha=v<=0?0:(1-v)*.8f;flat=true;tint=new Color(1,.83f,.46f);rotation=0;}
                        else{float speed=(7+i%9)*power;pos+=new Vector3(Mathf.Sin(a),0,Mathf.Cos(a))*speed*t+Vector3.up*Mathf.Max(.03f,(5+(i%5))*t-7*t*t);size=(.22f+(i%4)*.1f)*(mode==1?1.3f:1);alpha=(1-u)*Mathf.Clamp01((pos.y-ground.y)*5);rotation=a+t*(2+i%4);tint=new Color(.9f,.83f,.7f);}
                    }
                    // Double the ultimate burst footprint and each painted layer.
                    // Keep charge, sword impacts and effect lifetimes unchanged.
                    if(mode==1){pos=ground+(pos-ground)*2;size*=2;}
                    Vector3 x=flat?Vector3.right:right,y=flat?Vector3.forward:up;var xx=(x*Mathf.Cos(rotation)+y*Mathf.Sin(rotation))*size*.5f;var yy=(-x*Mathf.Sin(rotation)+y*Mathf.Cos(rotation))*size*.5f;
                    int k=i*4;l.vertices[k]=pos-transform.position-xx-yy;l.vertices[k+1]=pos-transform.position+xx-yy;l.vertices[k+2]=pos-transform.position+xx+yy;l.vertices[k+3]=pos-transform.position-xx+yy;
                    for(int j=0;j<4;j++)l.colors[k+j]=new Color(tint.r,tint.g,tint.b,Mathf.Clamp01(alpha));
                    float s=1f/l.tiles,tx=(tile%l.tiles)*s,ty=(l.tiles-1-tile/l.tiles)*s;l.uv[k]=new Vector2(tx,ty);l.uv[k+1]=new Vector2(tx+s,ty);l.uv[k+2]=new Vector2(tx+s,ty+s);l.uv[k+3]=new Vector2(tx,ty+s);
                }
                l.mesh.vertices=l.vertices;l.mesh.colors=l.colors;l.mesh.uv=l.uv;l.mesh.RecalculateBounds();
            }
        }
        void OnDestroy(){if(layers!=null)foreach(var l in layers){if(l.mesh)Destroy(l.mesh);if(l.material)Destroy(l.material);}}
    }
}
