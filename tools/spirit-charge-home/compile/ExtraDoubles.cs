// Only stand-ins for semantic compilation, never a claim of Unity API/build verification.
namespace UnityEngine
{
 public enum FindObjectsSortMode{None}public enum QueryTriggerInteraction{Ignore}public enum AudioRolloffMode{Linear}public enum LightShadows{None}public enum LightType{Point,Spot}
 public struct RaycastHit{public float distance;}
 public struct Color{public float r,g,b,a;public Color(float x,float y,float z,float w=1){r=x;g=y;b=z;a=w;}public static Color white=>new Color(1,1,1);}
 public class Texture2D:Object{}
 public class AudioListener:Object{public bool enabled;public static float volume;}
 public class Light:Object{public bool enabled;public LightShadows shadows;public float spotAngle;public LightType type;public float range,intensity;public Color color;}
 public class ParticleSystem:Object
 {
  public GameObject gameObject=new GameObject();public Transform transform=>gameObject.transform;
  public struct MainModule{public bool useUnscaledTime;public Color startColor;public MinMaxCurve startSize;}public struct MinMaxCurve{public MinMaxCurve(float a,float b){}}public struct ShapeModule{public bool enabled;public ParticleSystemShapeType shapeType;public SkinnedMeshRenderer skinnedMeshRenderer;public ParticleSystemMeshShapeType meshShapeType;}public ShapeModule shape=>new ShapeModule();
  public struct EmissionModule{public float rateOverTime;}
  public MainModule main=>new MainModule();public EmissionModule emission=>new EmissionModule();public void Emit(int count){}
 }
 public struct Rect{public Rect(float x,float y,float w,float h){}}
 public static class GUI{public static Color color;public static void DrawTexture(Rect r,Texture2D t){}}
 public static class Screen{public static int width=1280,height=720;}
}
namespace UnityEngine.InputSystem
{
 public class VectorControl{public UnityEngine.Vector2 ReadValue()=>new UnityEngine.Vector2();}
 public class Gamepad{public static Gamepad current;public VectorControl rightStick=new VectorControl();}
 public class Mouse{public static Mouse current;public VectorControl delta=new VectorControl();}
 public class InputAction{public bool IsPressed()=>false;public T ReadValue<T>()=>default(T);}
}
namespace Sunward
{public class WolfInput{public UnityEngine.InputSystem.InputAction Orbit=new UnityEngine.InputSystem.InputAction(),Zoom=new UnityEngine.InputSystem.InputAction();}}
namespace Sunward.Remaster
{
 public static class OriginalAtmosphere
 {public static UnityEngine.ParticleSystem Create(string a,UnityEngine.Transform b,UnityEngine.Vector3 c,float d,float e,float f,float g,float h=0)=>new UnityEngine.ParticleSystem();}
}
