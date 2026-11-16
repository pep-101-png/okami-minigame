using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(90)]
    public sealed class VillageAdventures:MonoBehaviour
    {
        public GameFlow game;public WeaponMasteryTrials Mastery{get;private set;}public VillageFishing Fishing{get;private set;}public VillageProjects Projects{get;private set;}public MoonlitTrail Trail{get;private set;}
        public bool Playing=>Projects && Projects.Playing || Trail && Trail.Playing;
        public static readonly Vector3 PracticeCentre=new Vector3(500,60,0),TrailCentre=new Vector3(500,60,140);
        public static int Realm(Vector3 p)=>Mathf.Abs(p.x-500)<32 && Mathf.Abs(p.y-60)<14?(Mathf.Abs(p.z)<32?1:Mathf.Abs(p.z-140)<32?2:0):0;
        public static bool Inside(Vector3 p)=>Realm(p)!=0;
        public static bool Height(Vector3 p,out float y){y=60.025f;return Inside(p);}
        public static Vector3 Guard(Vector3 p)
        {var c=Realm(p)==1?PracticeCentre:TrailCentre;var d=p-c;d.y=0;if(d.magnitude>25){d=d.normalized*25;p.x=c.x+d.x;p.z=c.z+d.z;}return p;}
        void Start()
        {
            Mastery=gameObject.AddComponent<WeaponMasteryTrials>();Mastery.game=game;
            Fishing=gameObject.AddComponent<VillageFishing>();Fishing.game=game;
            Projects=gameObject.AddComponent<VillageProjects>();Projects.game=game;
            Trail=gameObject.AddComponent<MoonlitTrail>();Trail.game=game;
        }
        public static void Record(GameFlow g,string kind,int count=1)
        {if(g && g.Adventures && g.Adventures.Mastery)g.Adventures.Mastery.Record(kind,count);}
        public void Brush(string technique,Vector3 point)
        {if(Trail)Trail.Brush(technique,point);}
        public bool FishStroke(Vector3 start,Vector3 end)=>Fishing && Fishing.TryHook(start,end);
        public void Cancel(){if(Mastery)Mastery.Cancel();if(Fishing)Fishing.Cancel();if(Projects)Projects.Cancel();if(Trail)Trail.Cancel();}
        public void Skip(){if(Projects && Projects.Playing)Projects.Skip();else if(Trail && Trail.Playing)Trail.Skip();}
        public static GameObject Prop(Transform parent,string resource,Vector3 point,Vector3 size,float yaw=0)=>VillageFestival.Place(parent,"Okami/"+resource,point,size,new Vector3(0,yaw,0));
        public static GameObject Court(Transform parent,Vector3 centre,bool moon)
        {
            var root=new GameObject(moon?"Moonlit trail · original painted island":"Weapon mastery · separate practice courtyard");root.transform.SetParent(parent,false);root.transform.position=centre;
            var floor=Prop(root.transform,"celestial-grounded",Vector3.zero,new Vector3(64,.025f,64));
            foreach(var r in floor.GetComponentsInChildren<SkinnedMeshRenderer>()){var mat=new Material(Resources.Load<Material>("Okami/Effects/CelestialCourt"));mat.SetVector("_CourtCentre",centre);mat.SetFloat("_Eclipse",moon?1:0);mat.SetFloat("_Moonlit",moon?1:0);r.sharedMaterial=mat;r.gameObject.layer=6;r.gameObject.AddComponent<MeshCollider>().sharedMesh=r.sharedMesh;}
            for(int i=0;i<10;i++)
            {float a=i*Mathf.PI*.2f;var at=new Vector3(Mathf.Sin(a)*27,0,Mathf.Cos(a)*27);var cloud=Prop(root.transform,"heaven-cloud",at-Vector3.up*1.5f,new Vector3(16,4,12),i*36);foreach(var r in cloud.GetComponentsInChildren<SkinnedMeshRenderer>()){var mat=new Material(r.sharedMaterial);mat.shader=Resources.Load<Material>("Okami/Effects/HeavenCloud").shader;r.sharedMaterial=mat;}Prop(root.transform,"vt35",at*.83f,new Vector3(.9f,1.7f,.9f));if(i%2==0)Prop(root.transform,"heaven-gate",at*.94f,new Vector3(6,5,1.2f),i*36+180);}
            return root;
        }
    }
}
