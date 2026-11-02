using UnityEngine;
namespace Sunward.Remaster
{
    // Original native roof, timber, rails, bowls and buckets; gameplay colliders
    // have no synthetic visible geometry. Farm lives beyond the north street.
    [DefaultExecutionOrder(-80)]
    public sealed class VillageFarm : MonoBehaviour
    {
        public GameFlow game;
        GameObject root;
        void Start()
        {
            if(!game)game=GetComponent<GameFlow>();if(!game || !game.valley)return;
            root=new GameObject("Northeast farm · clear central lane and animal yards");root.transform.SetParent(transform,false);
            Pen("Cattle paddock",24,35,27.8f,35,2.4f);Pen("Pig yard",37,43,28,35,1.5f);
            Pen("Chicken yard",45,50,29,35,1.5f);Pen("Rabbit garden",51,55,28.5f,35,1.2f);
            Shelter("Open cattle stable",new Vector3(29.5f,0,33.2f),8,3.2f,2.2f);
            Shelter("Chicken coop",new Vector3(47.5f,0,33.8f),2.8f,1.9f,.85f);
            Shelter("Rabbit hutch",new Vector3(53,0,33.8f),2.4f,1.6f,.65f);
            foreach(var p in new[]{new Vector3(25.4f,0,29),new Vector3(38.3f,0,30),new Vector3(46,0,30.8f),new Vector3(52,0,30)})
            {
                Place("Okami/vt0d",p,new Vector3(1.1f,.23f,.6f));
                Place("Okami/et2b",p+new Vector3(0,0,1.1f),new Vector3(.65f,.58f,.65f));
                Place("Okami/vt18",p+new Vector3(1.1f,0,0),new Vector3(.8f,.32f,.65f));
            }
            Place("Okami/vt05",new Vector3(22,0,24),new Vector3(1.5f,2.5f,1.5f));
            SpaResident();
        }
        float Floor(Vector3 p)=>game.valley.Height(p)+.025f;
        void Place(string asset,Vector3 p,Vector3 size)
        {p.y=Floor(p);VillageFestival.Place(root.transform,asset,p,size,Vector3.zero);}
        void Shelter(string label,Vector3 p,float width,float depth,float headroom)
        {
            var shelter=new GameObject(label);shelter.transform.SetParent(root.transform,false);p.y=Floor(p);shelter.transform.position=p;
            VillageFestival.Place(shelter.transform,"Okami/farm-roof",Vector3.up*headroom,new Vector3(width,Mathf.Max(.65f,width*.18f),depth),Vector3.zero);
            for(int i=0;i<4;i++)
                VillageFestival.Place(shelter.transform,"Okami/vt08",new Vector3((i%2==0?-1:1)*(width*.5f-.35f),-.12f,(i<2?-1:1)*(depth*.5f-.25f)),new Vector3(.18f,headroom+.25f,.18f),Vector3.zero);
            if(headroom<1)
                VillageFestival.Place(shelter.transform,"Okami/farm-walls",Vector3.zero,new Vector3(width-.35f,headroom,depth-.2f),Vector3.zero);
            // Back and side native timber rails leave the entire front open.
            Rail(p+new Vector3(0,0,depth*.5f-.22f),width-.5f,0,Mathf.Min(headroom,.8f));
        }
        void Pen(string label,float x0,float x1,float z0,float z1,float opening)
        {
            float mid=(x0+x1)*.5f,w=x1-x0,d=z1-z0;
            Rail(new Vector3(mid,0,z1),w,0,.85f);Rail(new Vector3(x0,0,(z0+z1)*.5f),d,90,.85f);Rail(new Vector3(x1,0,(z0+z1)*.5f),d,90,.85f);
            float half=(w-opening)*.5f;
            Rail(new Vector3(x0+half*.5f,0,z0),half,0,.85f);Rail(new Vector3(x1-half*.5f,0,z0),half,0,.85f);
        }
        void Rail(Vector3 p,float width,float yaw,float height)
        {
            p.y=Floor(p);var go=new GameObject("Original timber farm railing");go.layer=6;go.transform.SetParent(root.transform,false);go.transform.position=p;go.transform.rotation=Quaternion.Euler(0,yaw,0);
            for(int i=0;i<2;i++)
            {
                var mesh=Resources.Load<Mesh>("Okami/Farm/Rail"+i);var paint=Resources.Load<Material>("Okami/Farm/Paint"+i);if(!mesh || !paint)continue;
                var source=Resources.Load<Mesh>("Okami/Farm/Rail0").bounds;Vector3 scale=new Vector3(width/source.size.x,height/source.size.y,1);
                var visual=new GameObject("Native fence division "+i);visual.transform.SetParent(go.transform,false);visual.transform.localScale=scale;
                visual.transform.localPosition=-Vector3.Scale(new Vector3(source.center.x,source.min.y,source.center.z),scale);
                visual.AddComponent<MeshFilter>().sharedMesh=mesh;visual.AddComponent<MeshRenderer>().sharedMaterial=paint;
            }
            var collider=go.AddComponent<BoxCollider>();collider.size=new Vector3(width,height,.18f);collider.center=Vector3.up*height*.5f;
        }
        void SpaResident()
        {
            var woman=new GameObject("Original adult spa guest · seated native HM16");woman.SetActive(false);woman.transform.SetParent(root.transform,false);
            // Native seated pelvis is held below the source feet, not a standing
            // dance mistaken for bathing. Head and shoulders remain above water.
            woman.transform.position=new Vector3(GardenPond.X-1.05f,GardenPond.Water-.48f,GardenPond.Z+.65f);woman.transform.rotation=Quaternion.Euler(0,135,0);
            var actor=woman.AddComponent<OriginalActor>();actor.game=game;actor.resource="Okami/spa-hm16";actor.idle="hm05_003";actor.walk=actor.run=actor.windup=actor.strike=actor.recover=actor.death=actor.idle;actor.modelScale=.83f;woman.SetActive(true);
        }
    }
}
