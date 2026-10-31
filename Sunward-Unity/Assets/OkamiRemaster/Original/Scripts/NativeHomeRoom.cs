using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class NativeHomeRoom : MonoBehaviour
    {
        static readonly List<NativeHomeRoom> rooms=new List<NativeHomeRoom>();
        public int number;
        public Vector3 door,entrance,exitPoint,bed,hearth;
        public GameObject[] contents;
        public GameFlow game;
        public bool Contains(Vector3 p)=>Mathf.Abs(p.x-transform.position.x)<4.1f && Mathf.Abs(p.z-transform.position.z)<3.1f && Mathf.Abs(p.y-transform.position.y)<5;
        void OnEnable(){rooms.Add(this);}
        void OnDisable(){rooms.Remove(this);}
        public static NativeHomeRoom At(Vector3 p)=>rooms.Find(r=>r && r.Contains(p));
        public static Vector3 Guard(Vector3 previous,Vector3 next)
        {
            var room=At(previous);if(!room)return next;
            next.x=Mathf.Clamp(next.x,room.transform.position.x-3.65f,room.transform.position.x+3.65f);
            next.z=Mathf.Clamp(next.z,room.transform.position.z-2.65f,room.transform.position.z+2.65f);
            return next;
        }
        public static NativeHomeRoom For(int index)=>rooms.Count==0?null:rooms[Mathf.Abs(index)%rooms.Count];
        public static bool Height(Vector3 p,out float y){var room=At(p);y=room?room.transform.position.y:0;return room;}
        public static bool NearestAction(Vector3 p,out string action)
        {
            var current=At(p);if(current){action="home:"+current.number+":exit";return true;}
            foreach(var room in rooms)if(Vector3.Distance(p,room.door)<2){action="home:"+room.number+":enter";return true;}
            action="";return false;
        }
        public static void Interact(GameFlow game,string action)
        {
            string[] parts=action.Split(':');if(parts.Length!=3 || !int.TryParse(parts[1],out int number))return;
            var room=rooms.Find(r=>r.number==number);if(!room)return;
            game.Combat.Cancel();game.Player.Teleport(parts[2]=="exit"?room.exitPoint:room.entrance);
            var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();
            game.Notify(parts[2]=="exit"?"Back in the village":"Village home · bed, hearth and a place for tea · E to leave");
        }
        ParticleSystem fire;
        Light glow;
        void LateUpdate()
        {
            if(!game || !game.Player)return;
            bool visible=Contains(game.Player.transform.position);
            foreach(var obj in contents)if(obj && obj.activeSelf!=visible)obj.SetActive(visible);
            if(visible && !fire)
            {
                fire=OriginalAtmosphere.Create("Flame",transform,hearth-transform.position,4,.45f,1.1f,.12f,.2f);
                if(fire){var obj=new GameObject("Hearth light");obj.transform.SetParent(fire.transform,false);glow=obj.AddComponent<Light>();glow.type=LightType.Point;glow.color=new Color(1,.55f,.2f);glow.range=6;glow.intensity=2;}
            }
            if(fire)fire.gameObject.SetActive(visible);
            if(visible && Vector3.Distance(game.Player.transform.position,bed)<1.4f && game.Player.input.Dig.WasPressedThisFrame())game.Services.RestAt(bed,90);
        }
    }
}
