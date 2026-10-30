using System.Collections;
using UnityEngine;

namespace Sunward.Remaster
{
    public sealed class VillageServices : MonoBehaviour
    {
        public GameFlow game;
        public bool Resting { get; private set; }
        public static readonly Vector3 DojoDoor=new Vector3(0,.5f,15.1f), FoodDoor=new Vector3(15.5f,.65f,-15), Mat=new Vector3(8,.65f,-13.4f), Farmer=new Vector3(-48,0,22);
        public static bool InDojo(Vector3 p)=>Mathf.Abs(p.x)<6.5f && p.z>16.2f && p.z<33.6f && p.y<6;
        public static bool InFoodHouse(Vector3 p)=>Mathf.Abs(p.x-10)<4.4f && Mathf.Abs(p.z+15)<3.6f && p.y<6;
        public static bool Floor(Vector3 p,out float height)
        { height=InDojo(p)?Mathf.Abs(p.x)<2.72f && p.z>24.05f && p.z<29.43f?1.25f:.50f:.65f;return InDojo(p)||InFoodHouse(p); }
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
            if(action=="venue:dojo")game.Player.Teleport(InDojo(game.Player.transform.position)?new Vector3(0,.05f,13.8f):new Vector3(0,.52f,18.2f));
            else if(action=="venue:food")game.Player.Teleport(InFoodHouse(game.Player.transform.position)?new Vector3(16.8f,.05f,-15):new Vector3(13.2f,.67f,-15));
            else if(action=="venue:mat")StartCoroutine(Sit());
            else if(action=="venue:farmer") {game.Audio.Npc(3);game.Notify("The farmer tends the cattle, pigs and chickens. The pens have feed, water and shelter.");}
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
