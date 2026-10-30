using UnityEngine;

namespace Sunward.Remaster
{
    public sealed class TrainingDummy : MonoBehaviour
    {
        public GameFlow game;
        int hits;
        void Awake()
        {
            gameObject.layer=8;
            if(!GetComponent<Collider>())
            {var box=gameObject.AddComponent<BoxCollider>();box.center=Vector3.up;box.size=new Vector3(.7f,2,.7f);}
        }
        public void Strike()
        {
            hits++;
            if(!game)game=FindFirstObjectByType<GameFlow>();
            if(game){game.Audio.Cue("impact");game.Notify("Training dummy · "+hits+" hits · no coins or progression consumed");}
            var p=OriginalAtmosphere.Create("Spark",null,transform.position+Vector3.up*.9f,0,.25f,.35f,.25f);
            if(p){p.Emit(5);Destroy(p.gameObject,1);}
        }
    }
}
