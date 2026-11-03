using UnityEngine;
namespace Sunward.Remaster
{
    // Original native roof, timber, rails, bowls and buckets; gameplay colliders
    // have no synthetic visible geometry. Farm lives beyond the north street.
    [DefaultExecutionOrder(-80)]
    public sealed class VillageFarm : MonoBehaviour
    {
        public GameFlow game;
        GameObject root;OriginalActor spaGuest;bool spaAnimated;
        void Start()
        {
            if(!game)game=GetComponent<GameFlow>();if(!game || !game.valley)return;
            NativeDailyRoutine.InvalidateNavigation();
            root=new GameObject("Northeast farm · clear central lane and animal yards");root.transform.SetParent(transform,false);
            Pen("Cattle paddock",24,35,27.8f,40,2.4f);Pen("Pig yard",37,43,28,40,1.5f);
            Pen("Chicken yard",45,50,29,40,1.5f);Pen("Rabbit garden",51,57,28.5f,34,1.2f);
            Shelter("Open cattle stable",new Vector3(29.5f,0,36),7.4f,7.3f,3.15f);
            Shelter("Chicken coop",new Vector3(47.5f,0,37.3f),2.8f,2.76f,.57f);
            Shelter("Rabbit hutch",new Vector3(54,0,32.4f),2.4f,2.36f,.35f);
            foreach(var p in new[]{new Vector3(25.4f,0,29),new Vector3(38.3f,0,30),new Vector3(46,0,30.8f),new Vector3(52,0,30)})
            {
                Place("Okami/vt49",p,new Vector3(.8f,.4f,.8f));
                Place("Okami/et2b",p+new Vector3(0,0,1.1f),new Vector3(.65f,.58f,.65f));
                Place("Okami/vt5e",p+new Vector3(1.1f,0,0),new Vector3(.8f,.32f,.65f));
            }
            Place("Okami/vt05",new Vector3(22,0,24),new Vector3(1.5f,2.5f,1.5f));
            Shelter("Farmer’s open rest hut",new Vector3(54,0,38.5f),4.8f,4.74f,1.7f);
            Place("Okami/vt64",new Vector3(54.2f,0,38.2f),new Vector3(1.2f,.16f,1.8f));
            Place("Okami/vt0b",new Vector3(52.8f,0,38.7f),new Vector3(.8f,.35f,.8f));
            OriginalAtmosphere.Create("Flame",root.transform,new Vector3(52.8f,Floor(new Vector3(52.8f,0,38.7f))+.2f,38.7f),5,.3f,.8f,.15f,.16f);
            var campLight=new GameObject("Farmer hut firelight");campLight.transform.SetParent(root.transform,false);campLight.transform.position=new Vector3(52.8f,Floor(new Vector3(52.8f,0,38.7f))+.8f,38.7f);var glow=campLight.AddComponent<Light>();glow.type=LightType.Point;glow.range=4;glow.intensity=3;glow.color=new Color(1,.55f,.2f);glow.shadows=LightShadows.None;
            Place("Okami/vt91",new Vector3(55.5f,0,38.8f),new Vector3(.65f,.35f,.65f));
            Place("Okami/vt65",new Vector3(55.5f,0,38.8f),new Vector3(.35f,.3f,.35f),.35f);
            // One continuous original low-poly bed; world-space paint feathers its edge into grass.
            Earth(new Vector3(46,0,23.5f),new Vector3(12.8f,.10f,6.8f),0);
            SpaResident();
        }
        float Floor(Vector3 p)=>game.valley.Height(p)+.025f;
        void Place(string asset,Vector3 p,Vector3 size,float lift=0)
        {p.y=Floor(p)+lift;VillageFestival.Place(root.transform,asset,p,size,Vector3.zero);}
        void Earth(Vector3 p,Vector3 size,float yaw)
        {
            p.y=Floor(p);var visual=VillageFestival.Place(root.transform,"Okami/farm-earth",p,size,new Vector3(0,yaw,0));
            if(visual)foreach(var renderer in visual.GetComponentsInChildren<Renderer>()){
                var material=new Material(Resources.Load<Material>("Okami/Effects/FarmEarthBlend"));material.SetTexture("_EarthTex",Resources.Load<Texture2D>("Okami/farm-earth/Earth"));material.SetTexture("_GrassTex",Resources.Load<Texture2D>("Okami/farm-earth/Grass"));renderer.sharedMaterial=material;
            }
        }
        void Shelter(string label,Vector3 p,float width,float depth,float headroom)
        {
            var shelter=new GameObject(label);shelter.transform.SetParent(root.transform,false);p.y=Floor(p);shelter.transform.position=p;
            // Actual tiled, hipped roof; the former 'canopy' was a washing platform.
            VillageFestival.Place(shelter.transform,"Okami/farm-pitched-roof",Vector3.up*headroom,new Vector3(width,width*.315f,depth),Vector3.zero);
            for(int x=-1;x<=1;x+=2)for(int z=-1;z<=1;z+=2)
                VillageFestival.Place(shelter.transform,"Okami/farm-post",new Vector3(x*width*.35f,0,z*depth*.35f),new Vector3(headroom<1?.12f:.22f,headroom,headroom<1?.12f:.22f),Vector3.zero);
            if(headroom<1)
            {
                Rail(p+new Vector3(0,0,depth*.5f),width,0,.55f);
                Rail(p+new Vector3(-width*.5f,0,0),depth,90,.55f);Rail(p+new Vector3(width*.5f,0,0),depth,90,.55f);
                Place("Okami/vt5e",p+new Vector3(0,0,-depth*.2f),new Vector3(width*.55f,.16f,depth*.4f));
            }
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
            int count=Mathf.Max(1,Mathf.CeilToInt(width/2.2f));float span=width/count;
            for(int i=0;i<count;i++)
            {
                var at=new Vector3(-width*.5f+span*(i+.5f),0,0);var world=go.transform.TransformPoint(at);at.y=game.valley.Height(world)+.025f-go.transform.position.y;
                VillageFestival.Place(go.transform,"Okami/farm-rail",at,new Vector3(span,height,.18f),Vector3.zero);
            }
            var collider=go.AddComponent<BoxCollider>();collider.size=new Vector3(width,height,.18f);collider.center=Vector3.up*height*.5f;
            // Share the real pen footprint with the farmer's existing path grid.
            var boxes=game.valley.Data.boxes;System.Array.Resize(ref boxes,boxes.Length+1);
            boxes[boxes.Length-1]=new BoxData{x=p.x,z=-p.z,halfX=yaw==90?.09f:width*.5f,halfZ=yaw==90?width*.5f:.09f};game.valley.Data.boxes=boxes;
        }
        void Update()
        {
            if(!spaAnimated && spaGuest && spaGuest.Ready){spaGuest.PlayActivity("hm05_003",true);spaAnimated=true;}
        }
        void SpaResident()
        {
            var woman=new GameObject("Original adult spa guest · seated native HM16");woman.SetActive(false);woman.transform.SetParent(root.transform,false);
            // Native seated pelvis is held below the source feet, not a standing
            // dance mistaken for bathing. Head and shoulders remain above water.
            woman.transform.position=new Vector3(GardenPond.X-1.05f,GardenPond.Water-.48f,GardenPond.Z+.65f);woman.transform.rotation=Quaternion.Euler(0,135,0);
            var actor=woman.AddComponent<OriginalActor>();spaGuest=actor;actor.game=game;actor.resource="Okami/spa-hm16";actor.idle="hm05_003";actor.walk=actor.run=actor.windup=actor.strike=actor.recover=actor.death=actor.idle;actor.modelScale=.83f;actor.seatedHeadMotion="hm05_001";actor.seatedHeadWeight=.65f;actor.seatedArmMotion="hm05_027";actor.seatedArmWeight=.7f;actor.seatedArmRate=.65f;actor.seatedArmPause=.8f;woman.SetActive(true);
        }
    }
}
