using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class SpaRest : MonoBehaviour
    {
        public GameFlow game;
        public float Remaining {get;private set;}
        public int Bonus=>Remaining>0?25:0;
        bool bathing;ParticleSystem sparkle;
        public static bool Near(Vector3 p)=>Mathf.Abs(p.y-GardenPond.Water)<2 && ((p.x-GardenPond.X)*(p.x-GardenPond.X)/(GardenPond.RadiusX*GardenPond.RadiusX)+(p.z-GardenPond.Z)*(p.z-GardenPond.Z)/(GardenPond.RadiusZ*GardenPond.RadiusZ)<1.8f);
        public void Bathe()
        {
            if(!game || game.InTrial || game.Blocked || game.Health<=0 || !Near(game.Player.transform.position))return;
            Remaining=300;bathing=true;
            game.Services.RestAt(new Vector3(GardenPond.X+.9f,GardenPond.Water-.34f,GardenPond.Z-.5f),320);
            if(!sparkle){sparkle=OriginalAtmosphere.Create("SpiritGlow",game.Player.transform,Vector3.up*.45f,9,.16f,1.6f,.18f,.8f);if(sparkle){var main=sparkle.main;main.startColor=new Color(.35f,1,.52f,.8f);}}
            game.Notify("Spring blessing · vitality grows as you rest · +25 maximum health for five minutes");
        }
        void Update()
        {
            if(!game || !game.Player)return;
            if(game.Health<=0){Remaining=0;bathing=false;game.Services.CancelRest();}
            if(bathing && !game.Services.Resting){bathing=false;if(sparkle)Destroy(sparkle.gameObject);sparkle=null;}
            if(!bathing && sparkle){Destroy(sparkle.gameObject);sparkle=null;}
            if(bathing)Remaining=300;
            else if(Remaining>0 && !game.Blocked){Remaining=Mathf.Max(0,Remaining-Time.deltaTime);if(Remaining==0)game.Health=Mathf.Min(game.Health,game.MaxHealth);}
        }
        void OnDestroy(){if(sparkle)Destroy(sparkle.gameObject);}
    }
}
