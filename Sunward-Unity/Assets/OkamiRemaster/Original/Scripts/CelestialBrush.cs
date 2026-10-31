using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Sunward.Remaster
{
    public sealed class CelestialBrush : MonoBehaviour
    {
        public GameFlow game;
        public bool Drawing { get; private set; }
        readonly List<Vector2> stroke=new List<Vector2>();
        readonly List<Vector3> world=new List<Vector3>();
        Texture2D ink;
        Vector2 cursor;bool pad;
        void Start(){ink=Resources.Load<Texture2D>("Okami/UI/Ink");}
        void Update()
        {
            if(!game || !game.Player)return;
            var input=game.Player.input;
            bool held=input.Brush.IsPressed() && game.Panel=="" && game.Health>0 && !game.Player.Locked;
            if(held && !Drawing){Drawing=true;pad=Gamepad.current!=null && Gamepad.current.dpad.up.isPressed;cursor=new Vector2(Screen.width*.5f,Screen.height*.5f);game.Combat.Cancel();stroke.Clear();world.Clear();}
            if(!held && Drawing){Drawing=false;if(game.Panel=="" && game.Health>0)Resolve();stroke.Clear();world.Clear();}
            if(!Drawing)return;
            if(input.Pause.WasPressedThisFrame()){Drawing=false;stroke.Clear();world.Clear();return;}
            if(pad && Gamepad.current!=null){cursor+=Gamepad.current.rightStick.ReadValue()*450*Time.unscaledDeltaTime;cursor.x=Mathf.Clamp(cursor.x,0,Screen.width);cursor.y=Mathf.Clamp(cursor.y,0,Screen.height);}
            else if(Mouse.current!=null)cursor=Mouse.current.position.ReadValue();
            Vector2 point=cursor;bool painting=input.Light.IsPressed();
            if(!painting || (stroke.Count>0 && Vector2.Distance(stroke[stroke.Count-1],point)<5))return;
            if(stroke.Count>=256)return;
            var camera=Camera.main;if(!camera)return;
            var ray=camera.ScreenPointToRay(point);Vector3 target;
            if(Physics.Raycast(ray,out var hit,250,(1<<6)|(1<<8),QueryTriggerInteraction.Ignore))target=hit.point;
            else {var plane=new Plane(Vector3.up,game.Player.transform.position);if(!plane.Raycast(ray,out var d))return;target=ray.GetPoint(d);}
            stroke.Add(point);world.Add(target);
        }
        void Resolve()
        {
            if(stroke.Count<8)return;
            float length=0;Vector2 lo=stroke[0],hi=lo;
            for(int i=1;i<stroke.Count;i++){length+=Vector2.Distance(stroke[i-1],stroke[i]);lo=Vector2.Min(lo,stroke[i]);hi=Vector2.Max(hi,stroke[i]);}
            float span=(hi-lo).magnitude,end=Vector2.Distance(stroke[0],stroke[stroke.Count-1]);
            if(span<60)return;
            bool bloom=end<span*.3f && length>span*1.8f;
            bool slash=end>60 && length/end<1.3f;
            if(!bloom && !slash){game.Notify("Draw a straight slash or a closed Bloom circle");return;}
            float cost=bloom?15:20;
            if(game.Energy<cost){game.Notify("Not enough ink · let it replenish");return;}
            Vector3 centre=Vector3.zero;foreach(var p in world)centre+=p;centre/=world.Count;
            if(Vector3.Distance(centre,game.Player.transform.position)>24){game.Notify("Brush target is too far away");return;}
            game.Energy-=cost;
            if(bloom)
            {
                var life=game.GetComponent<VillageLife>();int restored=life?life.Bloom(centre):0;
                Burst("Blossom",centre,35,1);game.Audio.Cue("collect");game.Notify(restored>0?"Bloom · the land answers your brush":"Bloom · a shower of petals");
            }
            else
            {
                int hits=0;var a=stroke[0];var b=stroke[stroke.Count-1];var camera=Camera.main;
                foreach(var enemy in game.Enemies)
                {
                    if(!enemy || enemy.Dead || Vector3.Distance(enemy.transform.position,game.Player.transform.position)>24)continue;
                    var q=camera.WorldToScreenPoint(enemy.transform.position+Vector3.up);if(q.z<=0)continue;
                    Vector2 delta=b-a;float t=Mathf.Clamp01(Vector2.Dot((Vector2)q-a,delta)/delta.sqrMagnitude);
                    if(Vector2.Distance(q,a+delta*t)>75)continue;
                    enemy.Damage(28*game.Combat.FormMultiplier,(enemy.transform.position-game.Player.transform.position).normalized,.6f);Burst("Spark",enemy.transform.position+Vector3.up,12,.5f);hits++;
                }
                foreach(var bolt in FindObjectsByType<InkProjectile>(FindObjectsSortMode.None))
                {
                    var q=camera.WorldToScreenPoint(bolt.transform.position);Vector2 delta=b-a;float t=Mathf.Clamp01(Vector2.Dot((Vector2)q-a,delta)/delta.sqrMagnitude);
                    if(q.z>0 && Vector2.Distance(q,a+delta*t)<65)Destroy(bolt.gameObject);
                }
                game.Audio.Cue("attack");game.Notify("Power Slash · "+hits+" enemies struck");
            }
        }
        public static void Burst(string sprite,Vector3 point,int count,float size)
        {var p=OriginalAtmosphere.Create(sprite,null,point,0,size,1.2f,.5f,.4f);if(p){p.Emit(count);Destroy(p.gameObject,2);}}
        void OnGUI()
        {
            if(!Drawing)return;
            GUI.Label(new Rect(20,150,600,40),"CELESTIAL BRUSH · hold R, draw with LMB, release R to cast · slash / circle");
            if(!ink)return;
            GUI.DrawTexture(new Rect(cursor.x-5,Screen.height-cursor.y-5,10,10),ink);
            for(int i=1;i<stroke.Count;i++)
            {
                Vector2 a=new Vector2(stroke[i-1].x,Screen.height-stroke[i-1].y),b=new Vector2(stroke[i].x,Screen.height-stroke[i].y);var matrix=GUI.matrix;
                GUIUtility.RotateAroundPivot(Mathf.Atan2(b.y-a.y,b.x-a.x)*Mathf.Rad2Deg,a);GUI.DrawTexture(new Rect(a.x,a.y-3,Vector2.Distance(a,b),6),ink);GUI.matrix=matrix;
            }
        }
        void OnDisable(){Drawing=false;}
    }
}
