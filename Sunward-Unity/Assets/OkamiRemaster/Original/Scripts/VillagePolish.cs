using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(11000)]
    public sealed class VillagePolish:MonoBehaviour
    {
        public GameFlow game;GameObject memory;GameObject[] retired;
        void Start()
        {
            var list=new System.Collections.Generic.List<GameObject>();
            foreach(var t in FindObjectsByType<Transform>(FindObjectsInactive.Include,FindObjectsSortMode.None))
                if(t.name.Contains("home Solar Flare display") || t.name.Contains("home native glaive display") || t.name.Contains("memory mirror appearance"))list.Add(t.gameObject);
            retired=list.ToArray();
            memory=VillageFestival.Place(transform,"Okami/et90",HomeLayout.Mirror,new Vector3(2.3f,2.15f,3),new Vector3(0,180,0));
            if(memory)
            {
                foreach(var renderer in memory.GetComponentsInChildren<SkinnedMeshRenderer>())if(renderer.sharedMesh.name.StartsWith("Native-0-"))renderer.enabled=false;
                memory.name="Original save mirror · ET90 native stone circle and mirror frame";
                var seal=new GameObject("Original orange celestial save seal");seal.transform.SetParent(memory.transform,false);seal.transform.localPosition=new Vector3(0,.33f,.37f);seal.transform.localRotation=Quaternion.Euler(90,0,0);
                var line=seal.AddComponent<LineRenderer>();line.useWorldSpace=false;line.alignment=LineAlignment.TransformZ;line.positionCount=2;line.SetPosition(0,new Vector3(-.8f,0,0));line.SetPosition(1,new Vector3(.8f,0,0));line.startWidth=line.endWidth=1.65f;line.sharedMaterial=new Material(Resources.Load<Material>("Okami/Effects/Surface"));line.sharedMaterial.mainTexture=Resources.Load<Texture2D>("Okami/Effects/OriginalSaveSeal");line.startColor=line.endColor=new Color(1,.32f,.035f,.85f);seal.AddComponent<OriginalParticleMaterial>();
            }
        }
        void LateUpdate()
        {
            if(retired!=null)foreach(var obj in retired)if(obj)obj.SetActive(false);
            if(memory)memory.SetActive(VillageInteriors.Home(game.Player.transform.position));
        }
    }
}
