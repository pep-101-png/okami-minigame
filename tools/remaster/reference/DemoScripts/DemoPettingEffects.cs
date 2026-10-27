using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace SunwardVillageDemo
{
    public sealed class DemoPettingEffects : MonoBehaviour
    {
        sealed class Heart { public Transform transform; public Renderer renderer; public Vector3 start, drift; public float age, life, size; }
        readonly List<Heart> pool = new List<Heart>();
        Mesh quad;
        AudioSource chimeSource; AudioClip chime;
        MaterialPropertyBlock properties;
        Camera cameraView;
        int cursor;
        static readonly int Opacity = Shader.PropertyToID("_Opacity");
        void Awake()
        {
            Material material = Resources.Load<Material>("Farm/HeartPaint");
            if (material == null) { Debug.LogError("Petting heart material is missing from the update."); enabled = false; return; }
            chime=Resources.Load<AudioClip>("Farm/PettingChime");
            GameObject audio=new GameObject("Quiet petting chime");audio.transform.SetParent(transform,false);chimeSource=audio.AddComponent<AudioSource>();chimeSource.playOnAwake=false;
            chimeSource.spatialBlend=1;chimeSource.minDistance=1;chimeSource.maxDistance=8;chimeSource.rolloffMode=AudioRolloffMode.Linear;
            chimeSource.volume=.16f;
            properties = new MaterialPropertyBlock(); cameraView = Camera.main;
            quad = new Mesh(); quad.name = "Shared petting heart billboard";
            quad.vertices = new[] { new Vector3(-.5f,-.5f,0), new Vector3(.5f,-.5f,0), new Vector3(.5f,.5f,0), new Vector3(-.5f,.5f,0) };
            quad.uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up }; quad.triangles = new[] {0,1,2,0,2,3}; quad.RecalculateBounds();
            for (int i=0;i<30;++i)
            {
                GameObject item=new GameObject("Pooled painted love heart");item.transform.SetParent(transform,false);item.AddComponent<MeshFilter>().sharedMesh=quad;
                MeshRenderer renderer=item.AddComponent<MeshRenderer>();renderer.sharedMaterial=material;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;item.SetActive(false);
                pool.Add(new Heart{transform=item.transform,renderer=renderer});
            }
        }
        public void Burst(Vector3 position,float animalHeight)
        {
            if(pool.Count==0)return;
            if(chime!=null){chimeSource.transform.position=position;chimeSource.PlayOneShot(chime);}
            for(int i=0;i<5;++i)
            {
                Heart h=pool[cursor++%pool.Count];float direction=(i-2)*.72f;h.age=0;h.life=1.6f+i*.08f;h.size=Mathf.Clamp(animalHeight*.19f,.15f,.28f);
                h.start=position+Vector3.up*(animalHeight+.12f)+new Vector3(Mathf.Sin(direction)*.10f,0,Mathf.Cos(direction)*.06f);
                h.drift=new Vector3(Mathf.Sin(direction)*.22f,.58f+i*.035f,Mathf.Cos(direction)*.12f);h.transform.position=h.start;h.transform.localScale=Vector3.zero;h.transform.gameObject.SetActive(true);
            }
        }
        void Update()
        {
            if(cameraView==null)cameraView=Camera.main;
            foreach(Heart h in pool)
            {
                if(!h.transform.gameObject.activeSelf)continue;h.age+=Time.deltaTime;
                if(h.age>=h.life){h.transform.gameObject.SetActive(false);continue;}
                float t=h.age/h.life;h.transform.position=h.start+h.drift*h.age+Vector3.right*(Mathf.Sin(h.age*4)*.025f);
                if(cameraView!=null)h.transform.rotation=cameraView.transform.rotation;
                float pop=Mathf.SmoothStep(0,1,Mathf.Clamp01(t/.15f));h.transform.localScale=Vector3.one*h.size*pop*(1+.06f*Mathf.Sin(h.age*7));
                properties.Clear();properties.SetFloat(Opacity,1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(.55f,1,t)));h.renderer.SetPropertyBlock(properties);
            }
        }
        void OnDestroy(){if(quad!=null){if(Application.isPlaying)Destroy(quad);else DestroyImmediate(quad);}}
    }
}
