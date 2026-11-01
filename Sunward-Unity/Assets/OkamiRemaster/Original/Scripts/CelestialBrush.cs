using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Sunward.Remaster
{
    [DefaultExecutionOrder(-300)]
    public sealed class CelestialBrush : MonoBehaviour
    {
        public GameFlow game;
        public bool Drawing { get; private set; }
        readonly List<Vector2> stroke=new List<Vector2>();
        readonly List<Vector3> world=new List<Vector3>();
        Texture2D ink,paper;
        bool savedCursor;
        Volume paperWorld;
        VolumeProfile paperProfile;
        UniversalAdditionalCameraData brushCamera;
        bool previousPost;
        Vector2 cursor;bool pad;
        void Start()
        {
            ink=Resources.Load<Texture2D>("Okami/UI/BrushTip");paper=Resources.Load<Texture2D>("Okami/UI/Paper");
            var root=new GameObject("Celestial Brush · paused sumi-e grade");root.transform.SetParent(transform,false);
            paperWorld=root.AddComponent<Volume>();paperWorld.isGlobal=true;paperWorld.priority=1000;paperWorld.weight=0;
            paperProfile=ScriptableObject.CreateInstance<VolumeProfile>();paperWorld.sharedProfile=paperProfile;
            var grade=paperProfile.Add<ColorAdjustments>();grade.saturation.Override(-90);grade.contrast.Override(8);grade.colorFilter.Override(new Color(1,.96f,.86f));
        }
        void PaperMode(bool active)
        {
            if(paperWorld)paperWorld.weight=active?1:0;
            if(active){brushCamera=Camera.main?Camera.main.GetComponent<UniversalAdditionalCameraData>():null;if(brushCamera){previousPost=brushCamera.renderPostProcessing;brushCamera.renderPostProcessing=true;}}
            else if(brushCamera){brushCamera.renderPostProcessing=previousPost;brushCamera=null;}
        }
        void Update()
        {
            if(!game || !game.Player)return;
            var input=game.Player.input;
            bool held=input.Brush.IsPressed() && game.Panel=="" && game.Health>0 && !game.Player.Locked;
            if(held && !Drawing){Drawing=true;PaperMode(true);savedCursor=Cursor.visible;Cursor.visible=false;pad=Gamepad.current!=null && Gamepad.current.dpad.up.isPressed;cursor=new Vector2(Screen.width*.5f,Screen.height*.5f);game.Combat.Cancel();stroke.Clear();world.Clear();}
            if(!held && Drawing){Drawing=false;PaperMode(false);Cursor.visible=savedCursor;if(game.Panel=="" && game.Health>0)Resolve();stroke.Clear();world.Clear();}
            if(!Drawing)return;
            if(input.Pause.WasPressedThisFrame()){Drawing=false;PaperMode(false);Cursor.visible=savedCursor;stroke.Clear();world.Clear();return;}
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
                Burst("Blossom",centre,45,.65f);Burst("Leaf",centre,14,.35f);var breath=OriginalAtmosphere.Create("Wind",null,centre+Vector3.up*.3f,0,2.4f,.8f,.15f,2);if(breath){breath.Emit(3);Destroy(breath.gameObject,1.5f);}game.Audio.Cue("collect");game.Notify(restored>0?"Bloom · the land answers your brush":"Bloom · a shower of petals");
            }
            else
            {
                BrushStrokeFlash.Slash(world[0]+Vector3.up*.6f,world[world.Count-1]+Vector3.up*.6f);
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
            if(!Drawing || !ink)return;
            var previous=GUI.matrix;var old=GUI.color;GUI.matrix=Matrix4x4.identity;
            if(paper){GUI.color=new Color(1,.96f,.88f,.13f);GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height),paper);}
            float scale=Mathf.Clamp(Screen.height/900f,.7f,1.6f);
            GUI.color=new Color(.035f,.025f,.02f,.88f);
            int stamps=0;
            for(int i=1;i<stroke.Count && stamps<700;i++)
            {
                Vector2 a=stroke[i-1],b=stroke[i];float distance=Vector2.Distance(a,b);int count=Mathf.Max(1,Mathf.CeilToInt(distance/(4*scale)));
                for(int k=0;k<count && stamps<700;k++,stamps++)
                {
                    Vector2 p=Vector2.Lerp(a,b,k/(float)count);float end=Mathf.Min((i+k/(float)count)/3f,(stroke.Count-i)/3f);
                    float width=(8+5*Mathf.Clamp01(end))*scale;
                    GUI.DrawTexture(new Rect(p.x-width*.5f,Screen.height-p.y-width*.5f,width,width),ink);
                }
            }
            GUI.color=new Color(.05f,.025f,.015f,.95f);float tip=42*scale;
            GUI.DrawTexture(new Rect(cursor.x-tip*.26f,Screen.height-cursor.y-tip*.76f,tip,tip),ink);
            GUI.color=Color.white;
            GUI.Label(new Rect(22,18,Screen.width-44,32),"CELESTIAL BRUSH · Ink "+Mathf.CeilToInt(game.Energy)+" · Slash / Bloom");
            GUI.color=old;GUI.matrix=previous;
        }
        void OnDestroy(){if(paperProfile)Destroy(paperProfile);}
        void OnDisable(){PaperMode(false);if(Drawing)Cursor.visible=savedCursor;Drawing=false;stroke.Clear();world.Clear();}
    }
}
