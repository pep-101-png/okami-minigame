using UnityEngine;
namespace Sunward.Remaster
{
    // Original DR06 bamboo-painted shoji, tiled at normal proportions.
    public sealed class NativeInteriorDressing : MonoBehaviour
    {
        public GameFlow game;
        GameObject home,food;
        sealed class Cutaway{public GameObject panel,room;public Vector3 outward;}
        readonly System.Collections.Generic.List<Cutaway> cutaways=new System.Collections.Generic.List<Cutaway>();
        void Start()
        {
            home=Room("Amaterasu's original shoji interior",VillageInteriors.HomeCentre,13.12f,9.28f);
            food=Room("Original music-house shoji interior",VillageInteriors.FoodCentre,14.08f,11.52f,true);
            var backdrop=new GameObject("Bamboo-painted original shoji behind flute musician");backdrop.transform.SetParent(food.transform,false);backdrop.transform.position=new Vector3(10,-249.6f,-9.6f);Panel(backdrop.transform,3.6f);
            OriginalAtmosphere.Create("Flame",home.transform,new Vector3(2,.4f,0),3,.24f,.8f,.05f,.15f);
        }
        GameObject Room(string name,Vector3 centre,float width,float depth,bool sideDoor=false)
        {
            var root=new GameObject(name);root.transform.SetParent(transform,false);root.transform.position=centre;
            Wall(root.transform,new Vector3(0,0,depth/2),width,0,false);
            Wall(root.transform,new Vector3(-width/2,0,0),depth,90,sideDoor);
            Wall(root.transform,new Vector3(width/2,0,0),depth,-90,false);
            Wall(root.transform,new Vector3(0,0,-depth/2),width,180,!sideDoor);return root;
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
        void LateUpdate(){if(!game || !game.Player)return;if(home)home.SetActive(VillageInteriors.Home(game.Player.transform.position));if(food)food.SetActive(VillageInteriors.Food(game.Player.transform.position));
            if(Camera.main)foreach(var wall in cutaways)if(wall.panel && wall.room.activeSelf){var view=Camera.main.transform.position-wall.room.transform.position;view.y=0;wall.panel.SetActive(Vector3.Dot(view,wall.outward)<=0);}}
    }
}
