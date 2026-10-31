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
        public Vector2[] shaftRim;
        static LowerArena instance;
        public const float FloorY=-110, Radius=31;
        public static readonly Vector3 Centre=new Vector3(35,FloorY,0);
        public bool Unlocked { get; private set; }
        bool open, encounterStarted;
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
                for(int i=0;i<6;i++)
                {
                    float a=i*Mathf.PI/3;var anchor=new GameObject("Boss cavern ember light "+i);anchor.transform.SetParent(chamber.transform,false);
                    anchor.transform.position=Centre+new Vector3(Mathf.Cos(a)*27,4,Mathf.Sin(a)*27);
                    var light=anchor.AddComponent<Light>();light.type=LightType.Point;light.range=38;light.intensity=45;light.shadows=LightShadows.None;
                    light.color=i%2==0?new Color(1,.33f,.12f):new Color(.70f,.12f,.08f);
                    OriginalAtmosphere.Create("Flame",chamber.transform,anchor.transform.position+Vector3.down*3,5,1.4f,2.8f,.35f,.6f);
                }
                var mist=OriginalAtmosphere.Create("Steam",chamber.transform,Centre+Vector3.up*.8f,9,4,9,.06f,26);
                if(mist){var main=mist.main;main.startColor=new Color(.34f,.19f,.22f,.32f);}

            }
            Unlocked=game && game.Profile.wins>0;
            ApplyOpen(false,false);
        }
        public static bool Inside(Vector3 p)=>instance && instance.open && !NativeHomeRoom.At(p) && p.y<-3 && new Vector2(p.x-35,p.z).magnitude<Radius+2;
        public static bool Shaft(Vector3 p)
        {
            if(!instance || !instance.open)return false;
            var rim=instance.shaftRim;
            if(rim==null || rim.Length<3)return new Vector2(p.x-35,p.z).magnitude<3.8f;
            bool inside=false;
            for(int i=0,j=rim.Length-1;i<rim.Length;j=i++)
            {
                var a=rim[i];var b=rim[j];
                if((a.y>p.z)!=(b.y>p.z) && p.x<(b.x-a.x)*(p.z-a.y)/(b.y-a.y)+a.x)inside=!inside;
            }
            return inside;
        }
        public static bool Height(Vector3 p,out float y)
        {
            y=FloorY;
            if(!Inside(p)&&!Shaft(p))return false;
            // Ray only the native dais: ceiling, shaft and altar cannot become floor.
            int n=Physics.RaycastNonAlloc(new Vector3(p.x,Mathf.Max(p.y+.5f,FloorY+3),p.z),Vector3.down,floorHits,220,1<<6,QueryTriggerInteraction.Ignore);
            float top=float.NegativeInfinity;
            for(int i=0;i<n;i++)if(floorHits[i].collider.name.StartsWith("Original boss floor"))top=Mathf.Max(top,floorHits[i].point.y);
            if(!float.IsNegativeInfinity(top))y=top;
            return true;
        }
        static readonly RaycastHit[] floorHits=new RaycastHit[48];
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
            if(savedUnlock!=Unlocked && !game.InTrial)Unlocked=savedUnlock;
            // A previous save unlocks access, but only entering/completing the upper arena reveals the shaft.
            bool inUpper=new Vector2(game.Player.transform.position.x-35,game.Player.transform.position.z).magnitude<18;
            if(!game.InTrial && !Inside(game.Player.transform.position) && !Shaft(game.Player.transform.position))
            {if(!inUpper && open)ApplyOpen(false,false);else if(inUpper && Unlocked && !open)ApplyOpen(true,false);}
            if(game.Player.transform.position.y>-3)encounterStarted=false;
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
            if(p.y<FloorY-12){game.Player.Recover(Centre+Vector3.up*1.2f);return;}
            if(!encounterStarted && p.y<FloorY+2 && !game.InTrial){encounterStarted=true;game.StartBossTrial();}
            bool near=mirror && Vector3.Distance(p,mirror.position)<3.2f;
            game.WorldPrompt(near?"E · Return home through the memory mirror":"Crimson Helm’s chamber · E at the mirror returns home");
            if(near && game.Player.input.Interact.WasPressedThisFrame())game.ReturnHome();
        }
        void OnDestroy(){if(instance==this)instance=null;if(upperGround)upperGround.enabled=true;}
    }
}
