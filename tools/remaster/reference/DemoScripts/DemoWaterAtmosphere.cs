using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace SunwardVillageDemo
{
    // Bounded runtime-only pools; the water pause button controls every effect.
    public sealed class DemoWaterAtmosphere : MonoBehaviour
    {
        sealed class Puff { public Transform transform; public Renderer renderer; public Vector3 start; public float age, life, seed; public bool steam; }
        readonly List<Puff> pool = new List<Puff>();
        Mesh quad, steamQuad; Material foam, steam; MaterialPropertyBlock properties;
        Camera view; int splashCursor, steamCursor; float splashClock, steamClock;
        readonly Vector3[] splashes = { new Vector3(12.05f,-.025f,3.95f),new Vector3(14.43f,-.025f,6.98f),new Vector3(12.12f,-.025f,-2.8f),new Vector3(14.4f,-.025f,17.2f) };
        public void Initialize()
        {
            Material source=Resources.Load<Material>("DemoMaterials/Mat-1f4e5d5c67c45d");
            Material particle=Resources.Load<Material>("Farm/PetalPaint0");
            Texture mist=Resources.Load<Texture>("Farm/BreezeSteam");
            if(source==null||particle==null||mist==null){Debug.LogError("Village Breeze water artwork is missing.");enabled=false;return;}
            // Reuse the recovered wave texture, cropped to its painted brush band.
            foam=new Material(particle);foam.name="Recovered wave splash paint";foam.mainTexture=source.mainTexture;
            steam=new Material(particle);steam.name="Soft rock pool steam";steam.mainTexture=mist;
            properties=new MaterialPropertyBlock();view=Camera.main;
            quad=new Mesh();quad.name="Shared cropped water brush billboard";
            quad.vertices=new[]{new Vector3(-.5f,0,0),new Vector3(.5f,0,0),new Vector3(.5f,1,0),new Vector3(-.5f,1,0)};
            quad.uv=new[]{new Vector2(0,.22f),new Vector2(1,.22f),new Vector2(1,.68f),new Vector2(0,.68f)};
            quad.colors=new[]{Color.white,Color.white,Color.white,Color.white};quad.triangles=new[]{0,1,2,0,2,3};quad.RecalculateBounds();
            steamQuad=Instantiate(quad);steamQuad.name="Shared soft steam billboard";steamQuad.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};
            for(int i=0;i<32;++i)
            {
                GameObject item=new GameObject(i<20?"Pooled small river splash":"Pooled gentle rock pool steam");item.transform.SetParent(transform,false);
                item.AddComponent<MeshFilter>().sharedMesh=i<20?quad:steamQuad;MeshRenderer renderer=item.AddComponent<MeshRenderer>();renderer.sharedMaterial=i<20?foam:steam;
                renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;item.SetActive(false);
                pool.Add(new Puff{transform=item.transform,renderer=renderer,steam=i>=20});
            }
        }
        void Emit(bool mist)
        {
            int index=mist?20+steamCursor++%12:splashCursor++%20;Puff p=pool[index];p.age=0;p.seed=index*1.731f+(mist?steamCursor:splashCursor)*.37f;
            p.life=mist?4.8f:1.1f;p.start=mist?new Vector3(-12+Mathf.Sin(p.seed)*.6f,.26f,21.5f+Mathf.Cos(p.seed)*.6f):splashes[(splashCursor/2)%splashes.Length];
            p.transform.position=p.start;p.transform.gameObject.SetActive(true);
        }
        void Update()
        {
            if(pool.Count==0)return;if(DemoWaterMotion.Active!=null&&!DemoWaterMotion.Active.Animated)return;
            float dt=Mathf.Min(Time.deltaTime,.075f);splashClock+=dt;steamClock+=dt;
            if(splashClock>.34f){splashClock=0;Emit(false);}if(steamClock>.55f){steamClock=0;Emit(true);}
            if(view==null)view=Camera.main;
            foreach(Puff p in pool)
            {
                if(!p.transform.gameObject.activeSelf)continue;p.age+=dt;float t=p.age/p.life;
                if(t>=1){p.transform.gameObject.SetActive(false);continue;}
                if(p.steam)
                {
                    p.transform.position=p.start+new Vector3(Mathf.Sin(p.age*.8f+p.seed)*.11f,p.age*.17f,p.age*.035f);
                    p.transform.localScale=new Vector3(.45f+t*.6f,.65f+t*.65f,1);
                }
                else
                {
                    p.transform.position=p.start+new Vector3(Mathf.Sin(p.seed)*t*.10f,Mathf.Sin(t*Mathf.PI)*.12f,-t*.22f);
                    p.transform.localScale=new Vector3(.22f+t*.22f,.14f+Mathf.Sin(t*Mathf.PI)*.17f,1);
                }
                if(view!=null)p.transform.rotation=view.transform.rotation;
                properties.Clear();properties.SetFloat("_Opacity",Mathf.Sin(t*Mathf.PI)*(p.steam?.15f:.62f));p.renderer.SetPropertyBlock(properties);
            }
        }
        void OnDestroy(){if(quad!=null)Destroy(quad);if(steamQuad!=null)Destroy(steamQuad);if(foam!=null)Destroy(foam);if(steam!=null)Destroy(steam);}
    }
}
