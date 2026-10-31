using UnityEngine;

namespace Sunward.Remaster
{
    // Same Windflower scene. Existing wins unlock an empty chamber; it never
    // spawns enemies, changes the save schema or replaces the upper trial.
    [DefaultExecutionOrder(-60)]
    public sealed class LowerArena : MonoBehaviour
    {
        public GameFlow game;
        public GameObject cover, chamber;
        public Transform[] fragments;
        public Collider[] lidColliders;
        public Renderer upperGround;
        public Transform mirror;
        static LowerArena instance;
        public const float FloorY=-20, Radius=31;
        public static readonly Vector3 Centre=new Vector3(35,FloorY,0);
        public bool Unlocked { get; private set; }
        bool open;
        float collapse=-1;
        Vector3[] fragmentPositions;
        Quaternion[] fragmentRotations;
        bool groundVisible=true;
        void Awake(){instance=this;}
        void Start()
        {
            if(!game)game=FindFirstObjectByType<GameFlow>();
            fragmentPositions=new Vector3[fragments.Length];fragmentRotations=new Quaternion[fragments.Length];
            for(int i=0;i<fragments.Length;i++){fragmentPositions[i]=fragments[i].localPosition;fragmentRotations[i]=fragments[i].localRotation;}
            if(chamber)
            {
                chamber.SetActive(true);
                for(int i=0;i<8;i++)
                {
                    float a=i*Mathf.PI*.25f;var anchor=new GameObject("Original lantern light "+i);anchor.transform.SetParent(chamber.transform,false);
                    anchor.transform.position=Centre+new Vector3(Mathf.Cos(a)*26,5,Mathf.Sin(a)*26);
                    var light=anchor.AddComponent<Light>();light.type=LightType.Point;light.range=23;light.intensity=30f;light.shadows=LightShadows.None;
                    light.color=i%2==0?new Color(.34f,.65f,1):new Color(1,.64f,.30f);
                    OriginalAtmosphere.Create("SpiritGlow",chamber.transform,anchor.transform.position+Vector3.down*2,1,.35f,4,.08f,1.2f);
                }
                OriginalAtmosphere.Create("Spirit",chamber.transform,Centre+Vector3.up*3,3,.16f,8,.05f,23);
            }
            Unlocked=game && game.Profile.wins>0;
            ApplyOpen(Unlocked && !game.InTrial,false);
        }
        public static bool Inside(Vector3 p)=>instance && instance.open && p.y<-3 && new Vector2(p.x-35,p.z).magnitude<Radius+2;
        public static bool Shaft(Vector3 p)=>instance && instance.open && new Vector2(p.x-35,p.z).magnitude<3.8f;
        public static bool Height(Vector3 p,out float y)
        {y=FloorY;return Inside(p)||Shaft(p);}
        public static Vector3 Guard(Vector3 p)
        {
            if(!Inside(p))return p;
            Vector2 d=new Vector2(p.x-35,p.z);if(d.magnitude>Radius-.8f){d=d.normalized*(Radius-.8f);p.x=35+d.x;p.z=d.y;}
            return p;
        }
        public static void TrialStarted(){if(instance)instance.ApplyOpen(false,false);}
        public static void TrialFinished(bool won)
        {
            if(!instance)return;
            instance.Unlocked=instance.Unlocked||won;
            instance.ApplyOpen(instance.Unlocked,won);
        }
        void ApplyOpen(bool value,bool animate)
        {
            open=value;collapse=value && animate?0:-1;
            if(chamber)chamber.SetActive(value);
            if(cover)cover.SetActive(!value||animate);
            if(lidColliders!=null)foreach(var c in lidColliders)if(c)c.enabled=!value;
            if(!value && fragmentPositions!=null)
                for(int i=0;i<fragments.Length;i++){fragments[i].localPosition=fragmentPositions[i];fragments[i].localRotation=fragmentRotations[i];}
        }
        void Update()
        {
            if(!game || !game.Player)return;
            bool savedUnlock=game.Profile.wins>0;
            if(savedUnlock!=Unlocked && !game.InTrial){Unlocked=savedUnlock;ApplyOpen(Unlocked,false);}
            var p=game.Player.transform.position;
            bool visible=true;
            if(upperGround && groundVisible!=visible){upperGround.enabled=visible;groundVisible=visible;}
            if(collapse>=0 && !game.Blocked)
            {
                collapse+=Time.deltaTime;
                for(int i=0;i<fragments.Length;i++)
                {
                    fragments[i].localPosition=fragmentPositions[i]+Vector3.down*collapse*collapse*(4+i*.35f);
                    fragments[i].localRotation=fragmentRotations[i]*Quaternion.Euler(collapse*(18+i*7),collapse*(i%2==0?12:-12),collapse*(12-i*4));
                }
                if(collapse>1.6f){collapse=-1;cover.SetActive(false);}
            }
            if(!Inside(p)||game.Blocked)return;
            if(p.y<FloorY-3){game.Player.Recover(Centre+Vector3.up*.08f);return;}
            bool near=mirror && Vector3.Distance(p,mirror.position)<3.2f;
            game.WorldPrompt(near?"E · Return home through the memory mirror":"The chamber beneath the seal · no bosses yet");
            if(near && game.Player.input.Interact.WasPressedThisFrame())game.ReturnHome();
        }
        void OnDestroy(){if(instance==this)instance=null;if(upperGround)upperGround.enabled=true;}
    }
}
