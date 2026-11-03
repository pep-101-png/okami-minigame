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
            home=Room("Amaterasu's timber and white-paper home",VillageInteriors.HomeCentre,13.12f,9.28f,false,"Okami/vt62");
            food=Room("Original painted music-house interior",VillageInteriors.FoodCentre,14.08f,11.52f,true,"Okami/dr0c");
            var backdrop=new GameObject("Bamboo-painted original shoji behind flute musician");backdrop.transform.SetParent(food.transform,false);backdrop.transform.position=new Vector3(10,-249.6f,-9.6f);Panel(backdrop.transform,3.6f,"Okami/dr06");
            foreach(float x in new[]{-3.4f,3.4f})foreach(float z in new[]{-2.2f,1.2f})
            {Prop(food.transform,"Okami/vt91",new Vector3(x,0,z),.42f,0);Prop(food.transform,"Okami/vt65",new Vector3(x,.42f,z),.22f,0);}
            OriginalAtmosphere.Create("Flame",home.transform,new Vector3(2,.4f,0),3,.24f,.8f,.05f,.15f);
            foreach(var house in NativeHomeRoom.All)
            {
                var enclosure=Room("Original furnished village home "+house.number,house.transform.position,8,6,false,house.wallResource);
                Decorate(house,enclosure.transform);
                homes.Add(new HomeEnclosure{house=house,root=enclosure});
            }
        }
        GameObject Room(string name,Vector3 centre,float width,float depth,bool sideDoor=false,string wallResource="Okami/vt62")
        {
            var root=new GameObject(name);root.transform.SetParent(transform,false);root.transform.position=centre;
            var lamp=new GameObject("Warm interior light");lamp.transform.SetParent(root.transform,false);lamp.transform.localPosition=new Vector3(0,2.5f,0);
            var light=lamp.AddComponent<Light>();light.type=LightType.Point;light.color=new Color(1,.8f,.6f);light.range=Mathf.Max(width,depth);light.intensity=1.3f;
            Wall(root.transform,new Vector3(0,0,depth/2),width,0,false,wallResource);
            Wall(root.transform,new Vector3(-width/2,0,0),depth,90,sideDoor,wallResource);
            Wall(root.transform,new Vector3(width/2,0,0),depth,-90,false,wallResource);
            Wall(root.transform,new Vector3(0,0,-depth/2),width,180,!sideDoor,wallResource);
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
        void Wall(Transform root,Vector3 position,float width,float yaw,bool door,string resource)
        {
            if(door){float part=(width-2.4f)*.5f,shift=(width+2.4f)*.25f;var axis=Quaternion.Euler(0,yaw,0)*Vector3.right;Wall(root,position-axis*shift,part,yaw,false,resource);Wall(root,position+axis*shift,part,yaw,false,resource);return;}
            int n=Mathf.CeilToInt(width/2.6f);float span=width/n;
            for(int i=0;i<n;i++)
            {
                float x=-width*.5f+span*(i+.5f);if(door && Mathf.Abs(x)<1.5f)continue;
                var panel=new GameObject("Original painted shoji panel");panel.transform.SetParent(root,false);panel.transform.localPosition=position+Quaternion.Euler(0,yaw,0)*new Vector3(x,0,0);panel.transform.localRotation=Quaternion.Euler(0,yaw,0);Panel(panel.transform,span,resource);
                Vector3 outward=Mathf.Abs(position.x)>Mathf.Abs(position.z)?new Vector3(Mathf.Sign(position.x),0,0):new Vector3(0,0,Mathf.Sign(position.z));
                cutaways.Add(new Cutaway{panel=panel,room=root.gameObject,outward=outward});
            }
        }
        void Panel(Transform root,float width,string resource)
        {
            var asset=Resources.Load<TextAsset>(resource+"/Model");if(!asset)return;
            var m=JsonUtility.FromJson<Model>(asset.text);Vector3 lo=Vector3.one*float.PositiveInfinity,hi=Vector3.one*float.NegativeInfinity;
            foreach(var p in m.parts)for(int i=0;i<p.positions.Length;i+=3){var v=new Vector3(p.positions[i],p.positions[i+1],p.positions[i+2]);lo=Vector3.Min(lo,v);hi=Vector3.Max(hi,v);}
            var d=hi-lo;var scale=new Vector3(width/Mathf.Max(d.x,.001f),3/Mathf.Max(d.y,.001f),1);
            root.gameObject.AddComponent<OriginalVisual>().Load(resource,-Vector3.Scale(new Vector3((lo.x+hi.x)*.5f,lo.y,(lo.z+hi.z)*.5f),scale),scale);
        }
        void Decorate(NativeHomeRoom house,Transform root)
        {
            // Distinct original belongings rather than the same furnished box.
            switch(house.roomStyle%6)
            {
                case 0:Prop(root,"Okami/vt7c",new Vector3(1.7f,0,2.1f),1.35f,180);Prop(root,"Okami/vt6b",new Vector3(-.8f,.8f,2.9f),1.2f,0);break;
                case 1:Prop(root,"Okami/vt9a",new Vector3(.2f,0,.1f),.42f,0);Prop(root,"Okami/vt8e",new Vector3(-1.8f,0,.6f),1.35f,90);break;
                case 2:Prop(root,"Okami/vt6b",new Vector3(.2f,.75f,2.88f),1.25f,0);Prop(root,"Okami/vt60",new Vector3(2.9f,0,-2.2f),.65f,0);break;
                case 3:Prop(root,"Okami/vt13",new Vector3(2.7f,0,2.45f),.65f,0);Prop(root,"Okami/vt12",new Vector3(2.7f,.55f,2.45f),.75f,0);break;
                case 4:Prop(root,"Okami/vt91",new Vector3(1.1f,0,-1.5f),.42f,0);Prop(root,"Okami/vt65",new Vector3(1.1f,.42f,-1.5f),.28f,0);break;
                case 5:Prop(root,"Okami/vt8e",new Vector3(-1.8f,0,.8f),1.2f,90);Prop(root,"Okami/vt13",new Vector3(2.75f,0,2.45f),.6f,0);break;
            }
        }
        void Prop(Transform parent,string resource,Vector3 at,float height,float yaw)
        {
            var asset=Resources.Load<TextAsset>(resource+"/Model");if(!asset)return;
            var model=JsonUtility.FromJson<Model>(asset.text);Vector3 lo=Vector3.one*float.PositiveInfinity,hi=Vector3.one*float.NegativeInfinity;
            foreach(var part in model.parts)for(int i=0;i<part.positions.Length;i+=3){var p=new Vector3(part.positions[i],part.positions[i+1],part.positions[i+2]);lo=Vector3.Min(lo,p);hi=Vector3.Max(hi,p);}
            float scale=height/Mathf.Max(.001f,hi.y-lo.y);var obj=new GameObject("Original home belonging "+resource);obj.transform.SetParent(parent,false);obj.transform.localPosition=at;obj.transform.localRotation=Quaternion.Euler(0,yaw,0);
            obj.AddComponent<OriginalVisual>().Load(resource,-new Vector3((lo.x+hi.x)*.5f,lo.y,(lo.z+hi.z)*.5f)*scale,Vector3.one*scale);
        }
        [System.Serializable]sealed class Model{public Part[] parts;}
        [System.Serializable]sealed class Part{public float[] positions;}
        void LateUpdate()
        {
            if(!game || !game.Player)return;
            var player=game.Player.transform.position;bool inside=VillageInteriors.AnyRoom(player);
            bool heaven=game.Heaven && game.Heaven.isActiveAndEnabled && HeavenlyGarden.Inside(player);
            foreach(var enclosure in homes)if(enclosure.root)enclosure.root.SetActive(enclosure.house.Contains(player));
            if(home)home.SetActive(VillageInteriors.Home(player));if(food)food.SetActive(VillageInteriors.Food(player));
            // Camera stays inside the room; do not remove walls and expose a
            // floating floor against the outdoor skybox.
            foreach(var wall in cutaways)if(wall.panel)wall.panel.SetActive(true);
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
                // One visibility owner handles both detached interiors and heaven.
                // Bounds also retain unparented, world-space player effects in the realm.
                bool hidden=heaven?!game.Heaven.OwnsRenderer(renderer):inside?!interior:interior;
                renderer.forceRenderingOff=priorVisibility[renderer] || hidden;
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
