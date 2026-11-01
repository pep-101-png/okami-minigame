namespace UnityEngine
{
 public class Collider:Object{public string name;public bool enabled;}
 public struct Ray{public Vector3 GetPoint(float distance)=>Vector3.zero;}
 public struct Plane{public Plane(Vector3 n,Vector3 p){}public bool Raycast(Ray r,out float d){d=0;return true;}}
 public struct Matrix4x4{public static Matrix4x4 identity=>new Matrix4x4();}
 public class ScriptableObject:Object{public static T CreateInstance<T>()where T:new()=>new T();}
}
namespace UnityEngine.Rendering
{
 public class Volume:UnityEngine.MonoBehaviour{public bool isGlobal;public float priority,weight;public VolumeProfile sharedProfile;}
 public class VolumeProfile:UnityEngine.ScriptableObject{public T Add<T>()where T:new()=>new T();}
 public class Parameter<T>{public void Override(T value){}}
}
namespace UnityEngine.Rendering.Universal
{
 public class UniversalAdditionalCameraData:UnityEngine.Object{public bool renderPostProcessing;}
 public class ColorAdjustments{public UnityEngine.Rendering.Parameter<float> saturation=new UnityEngine.Rendering.Parameter<float>(),contrast=new UnityEngine.Rendering.Parameter<float>();public UnityEngine.Rendering.Parameter<UnityEngine.Color> colorFilter=new UnityEngine.Rendering.Parameter<UnityEngine.Color>();}
}
namespace Sunward
{
 public static class GardenPond{public const float X=-15,Z=-22;}
 public class InkProjectile:UnityEngine.MonoBehaviour{}
}
namespace Sunward.Remaster
{
 public class TrainingDummy:UnityEngine.MonoBehaviour{public Sunward.GameFlow game;public int contacts;public void PracticeContact(){contacts++;}}
 public class NativeDailyRoutine:UnityEngine.MonoBehaviour{public Sunward.GameFlow game;public int seed;public UnityEngine.Vector3 workplace;}
 public static class NativeHomeRoom{public static bool At(UnityEngine.Vector3 p)=>false;}
 public class OriginalVisual:UnityEngine.MonoBehaviour{public bool Load(string r,UnityEngine.Vector3 p,UnityEngine.Vector3 s)=>true;}
}
