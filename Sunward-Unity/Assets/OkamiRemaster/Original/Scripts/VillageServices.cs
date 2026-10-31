using System.Collections;
using UnityEngine;

namespace Sunward.Remaster
{
    public sealed class VillageServices : MonoBehaviour
    {
        public GameFlow game;
        public bool Resting { get; private set; }
        public static readonly Vector3 DojoDoor=new Vector3(0,.5f,15.1f), FoodDoor=new Vector3(4.8f,.4f,-15), Mat=new Vector3(8,.4f,-13.4f), Farmer=new Vector3(-48,0,22);
        public static bool InDojo(Vector3 p)=>Mathf.Abs(p.x)<6.5f && p.z>16.2f && p.z<33.6f && p.y<6;
        public static bool InFoodHouse(Vector3 p)=>Mathf.Abs(p.x-10)<4.4f && Mathf.Abs(p.z+15)<3.6f && p.y<6;
        static readonly RaycastHit[] floorHits=new RaycastHit[32];
        public static bool Floor(Vector3 p,out float height)
        {
            bool dojo=InDojo(p);height=dojo?.50f:.40f;
            if(!dojo && !InFoodHouse(p))return false;
            // The original dojo has bevels/slopes, not a flat two-level floor.
            // Use its real mesh collision for the existing player controller.
            int n=Physics.RaycastNonAlloc(new Ray(new Vector3(p.x,5.5f,p.z),Vector3.down),floorHits,9,1<<6,QueryTriggerInteraction.Ignore);
            bool found=false;
            for(int i=0;i<n;i++)
            {
                var hit=floorHits[i];string name=hit.collider.name;
                if(dojo?!name.Contains("dojo-floor"):!name.Contains("food house floor"))continue;
                if(!found || hit.point.y>height){height=hit.point.y;found=true;}
            }
            return true;
        }
        public static string Label(string action,Vector3 p)
        {
            if(action=="venue:dojo")return InDojo(p)?"E · Leave the training hall":"E · Enter the samurai training hall";
            if(action=="venue:food")return InFoodHouse(p)?"E · Leave the food house":"E · Enter the food & music house";
            if(action=="venue:mat")return "E · Sit on Amaterasu's mat";
            return "E · Speak with the farmer";
        }
        void Awake(){if(!game)game=GetComponent<GameFlow>();}
        public void Interact(string action)
        {
            if(Resting || !game)return;
            if(action=="venue:dojo")game.Player.Teleport(InDojo(game.Player.transform.position)?new Vector3(0,.05f,13.3f):new Vector3(0,.82f,18.3f));
            else if(action=="venue:food")game.Player.Teleport(InFoodHouse(game.Player.transform.position)?new Vector3(2.8f,.05f,-15):new Vector3(6.8f,.42f,-15));
            else if(action=="venue:mat")StartCoroutine(Sit());
            else if(action=="venue:farmer") {game.Audio.Npc(3,Farmer);game.Notify("The farmer tends the cattle, pigs and chickens. The pens have feed, water and shelter.");}
            if(action=="venue:dojo" || action=="venue:food")
            {
                var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();
            }
            game.Combat.Equip();
        }
        IEnumerator Sit()
        {
            Resting=true;game.Player.Locked=true;game.Combat.Cancel();game.Combat.Rest(true);
            game.Player.Teleport(Mat);game.Player.transform.rotation=Quaternion.Euler(0,180,0);
            game.Player.animationView.Play("Sit",.18f,0,true);game.Notify("Rest by the music · E or movement to stand");
            yield return null;
            while(!game.Player.input.Interact.WasPressedThisFrame() && !game.Player.input.Jump.WasPressedThisFrame() && !game.Player.input.Pause.WasPressedThisFrame() && game.Player.input.Move.ReadValue<Vector2>().sqrMagnitude<.1f)
            {game.Health=Mathf.Min(game.MaxHealth,game.Health+Time.deltaTime*3);yield return null;}
            game.Player.Locked=false;game.Player.animationView.Play("Idle_Natural",.15f,0,true);
            game.Combat.Rest(false);Resting=false;
        }
    }
}
