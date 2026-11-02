using UnityEngine;
namespace Sunward.Remaster
{
    // Original DR06 bamboo-painted shoji, tiled at normal proportions.
    [DefaultExecutionOrder(10000)]
    public sealed class NativeInteriorDressing : MonoBehaviour
    {
        public GameFlow game;
        GameObject home,food;
        Mesh ceilingMesh;Material ceilingMaterial;
        Camera view;CameraClearFlags outdoorClear;Color outdoorBackground;
        Renderer[] roomRenderers;bool wasInside;
        sealed class HomeEnclosure{public NativeHomeRoom house;public GameObject root;}
        readonly System.Collections.Generic.List<HomeEnclosure> homes=new System.Collections.Generic.List<HomeEnclosure>();
        float scan;
        readonly System.Collections.Generic.Dictionary<Renderer,bool> priorVisibility=new System.Collections.Generic.Dictionary<Renderer,bool>();
        sealed class Cutaway{public GameObject panel,room;public Vector3 outward;}
        readonly System.Collections.Generic.List<Cutaway> cutaways=new System.Collections.Generic.List<Cutaway>();
        void Start()
        {
            ceilingMesh=Resources.Load<Mesh>("Okami/Interior/TimberCeiling");
            foreach(var floor in Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None))
                if(floor.name.Contains("central timber floor")){ceilingMaterial=floor.sharedMaterial;break;}
            home=Room("Amaterasu's original shoji interior",VillageInteriors.HomeCentre,13.12f,9.28f);
            food=Room("Original music-house shoji interior",VillageInteriors.FoodCentre,14.08f,11.52f,true);
            var backdrop=new GameObject("Bamboo-painted original shoji behind flute musician");backdrop.transform.SetParent(food.transform,false);backdrop.transform.position=new Vector3(10,-249.6f,-9.6f);Panel(backdrop.transform,3.6f);
            OriginalAtmosphere.Create("Flame",home.transform,new Vector3(2,.4f,0),3,.24f,.8f,.05f,.15f);
            foreach(var house in NativeHomeRoom.All)
            {
                var enclosure=Room("Original furnished village home enclosure",house.transform.position,8,6);
                homes.Add(new HomeEnclosure{house=house,root=enclosure});
            }
            AddEntrance("Amaterasu's front sliding door",VillageInteriors.HomeDoor,2.3f,180);
            AddEntrance("Music-house sliding entrance",new Vector3(4,.05f,-15),2.3f,90);
            AddEntrance("Dojo sliding entrance",new Vector3(0,.44f,15.45f),3.2f,180);
            foreach(var house in NativeHomeRoom.All)
            {
                AddEntrance("Village home "+house.number+" front door",house.door,1.9f,180);
                AddEntrance("Village home "+house.number+" interior sliding door",house.transform.position+Vector3.back*3,2.4f,180);
            }
            AddEntrance("Amaterasu's interior sliding exit",new Vector3(-34,-249.895f,-20.64f),2.4f,180);
            AddEntrance("Music-house interior sliding exit",new Vector3(2.96f,-249.6f,-15),2.4f,90);
            AddEntrance("Dojo interior sliding exit",new Vector3(0,-249.5f,12.9f),3.2f,180);
        }
        sealed class Entrance{public GameObject panel;public Vector3 door;}
        readonly System.Collections.Generic.List<Entrance> entrances=new System.Collections.Generic.List<Entrance>();
        void AddEntrance(string name,Vector3 at,float width,float yaw)
        {
            var obj=new GameObject(name);obj.transform.SetParent(transform,false);obj.transform.position=at;obj.transform.rotation=Quaternion.Euler(0,yaw,0);Panel(obj.transform,width);
            entrances.Add(new Entrance{panel=obj,door=at});
        }
        GameObject Room(string name,Vector3 centre,float width,float depth,bool sideDoor=false)
        {
            var root=new GameObject(name);root.transform.SetParent(transform,false);root.transform.position=centre;
            var lamp=new GameObject("Warm interior light");lamp.transform.SetParent(root.transform,false);lamp.transform.localPosition=new Vector3(0,2.5f,0);
            var light=lamp.AddComponent<Light>();light.type=LightType.Point;light.color=new Color(1,.8f,.6f);light.range=Mathf.Max(width,depth);light.intensity=1.3f;
            Wall(root.transform,new Vector3(0,0,depth/2),width,0,false);
            Wall(root.transform,new Vector3(-width/2,0,0),depth,90,sideDoor);
            Wall(root.transform,new Vector3(width/2,0,0),depth,-90,false);
            Wall(root.transform,new Vector3(0,0,-depth/2),width,180,!sideDoor);
            if(ceilingMesh && ceilingMaterial)
            {
                var ceiling=new GameObject("Original timber ceiling");ceiling.transform.SetParent(root.transform,false);ceiling.transform.localPosition=Vector3.up*3.02f;ceiling.transform.localRotation=Quaternion.Euler(180,0,0);
                var surface=new GameObject("Original wood surface");surface.transform.SetParent(ceiling.transform,false);
                var size=ceilingMesh.bounds.size;var scale=new Vector3(width/Mathf.Max(size.x,.001f),1,depth/Mathf.Max(size.z,.001f));
                surface.transform.localScale=scale;surface.transform.localPosition=-Vector3.Scale(ceilingMesh.bounds.center,scale);
                surface.AddComponent<MeshFilter>().sharedMesh=ceilingMesh;surface.AddComponent<MeshRenderer>().sharedMaterial=ceilingMaterial;
            }
            return root;
        }
        void Wall(Transform root,Vector3 position,float width,float yaw,bool door)
        {
            if(door){float part=(width-2.4f)*.5f,shift=(width+2.4f)*.25f;var axis=Quaternion.Euler(0,yaw,0)*Vector3.right;Wall(root,position-axis*shift,part,yaw,false);Wall(root,position+axis*shift,part,yaw,false);return;}
            int n=Mathf.CeilToInt(width/2.6f);float span=width/n;
            for(int i=0;i<n;i++)
            {
                float x=-width*.5f+span*(i+.5f);if(door && Mathf.Abs(x)<1.5f)continue;
                var panel=new GameObject("Original painted shoji panel");panel.transform.SetParent(root,false);panel.transform.localPosition=position+Quaternion.Euler(0,yaw,0)*new Vector3(x,0,0);panel.transform.localRotation=Quaternion.Euler(0,yaw,0);Panel(panel.transform,span);
                Vector3 outward=Mathf.Abs(position.x)>Mathf.Abs(position.z)?new Vector3(Mathf.Sign(position.x),0,0):new Vector3(0,0,Mathf.Sign(position.z));
                cutaways.Add(new Cutaway{panel=panel,room=root.gameObject,outward=outward});
            }
        }
        void Panel(Transform root,float width)
        {
            var asset=Resources.Load<TextAsset>("Okami/dr06/Model");if(!asset)return;
            var m=JsonUtility.FromJson<Model>(asset.text);Vector3 lo=Vector3.one*float.PositiveInfinity,hi=Vector3.one*float.NegativeInfinity;
            foreach(var p in m.parts)for(int i=0;i<p.positions.Length;i+=3){var v=new Vector3(p.positions[i],p.positions[i+1],p.positions[i+2]);lo=Vector3.Min(lo,v);hi=Vector3.Max(hi,v);}
            var d=hi-lo;var scale=new Vector3(width/Mathf.Max(d.x,.001f),3/Mathf.Max(d.y,.001f),1);
            root.gameObject.AddComponent<OriginalVisual>().Load("Okami/dr06",-Vector3.Scale(new Vector3((lo.x+hi.x)*.5f,lo.y,(lo.z+hi.z)*.5f),scale),scale);
        }
        [System.Serializable]sealed class Model{public Part[] parts;}
        [System.Serializable]sealed class Part{public float[] positions;}
        void LateUpdate()
        {
            if(!game || !game.Player)return;
            var player=game.Player.transform.position;bool inside=VillageInteriors.AnyRoom(player);
            foreach(var enclosure in homes)if(enclosure.root)enclosure.root.SetActive(enclosure.house.Contains(player));
            if(home)home.SetActive(VillageInteriors.Home(player));if(food)food.SetActive(VillageInteriors.Food(player));
            // Camera stays inside the room; do not remove walls and expose a
            // floating floor against the outdoor skybox.
            foreach(var wall in cutaways)if(wall.panel)wall.panel.SetActive(true);
            foreach(var entrance in entrances)if(entrance.panel)entrance.panel.SetActive(Vector3.Distance(player,entrance.door)>(entrance.door.y<-40?2.3f:3.5f));
            if(!view && Camera.main){view=Camera.main;outdoorClear=view.clearFlags;outdoorBackground=view.backgroundColor;}
            // forceRenderingOff is independent of native form masks and leaves
            // GameObject physics layers and floor raycasts unchanged.
            // Include newly instantiated native skins/particles. Classification
            // uses the renderer's transform, never its deliberately huge bounds.
            scan-=Time.unscaledDeltaTime;
            if(roomRenderers==null || scan<=0 || inside!=wasInside){roomRenderers=Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include,FindObjectsSortMode.None);scan=.2f;}
            foreach(var renderer in roomRenderers)if(renderer)
            {
                float y=renderer.transform.position.y;bool interior=y<-235 || (y>-65 && y<-45);
                if(!priorVisibility.ContainsKey(renderer))priorVisibility.Add(renderer,renderer.forceRenderingOff);
                renderer.forceRenderingOff=priorVisibility[renderer] || (inside?!interior:interior);
            }
            if(!view)return;
            wasInside=inside;
            view.clearFlags=inside?CameraClearFlags.SolidColor:outdoorClear;
            view.backgroundColor=inside?new Color(.12f,.075f,.04f):outdoorBackground;
        }
        void OnDisable()
        {
            if(view){view.clearFlags=outdoorClear;view.backgroundColor=outdoorBackground;}
            foreach(var pair in priorVisibility)if(pair.Key)pair.Key.forceRenderingOff=pair.Value;
        }
    }
}
