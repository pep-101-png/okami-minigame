namespace UnityEngine
{
 public struct Vector4{public float x,y,z,w;public Vector4(float a,float b,float c,float d){x=a;y=b;z=c;w=d;}}
 public static class RenderSettings{public static Light sun;public static Color fogColor,ambientLight;}
 public static class Shader{public static void SetGlobalFloat(string name,float value){}public static void SetGlobalVectorArray(string name,Vector4[] value){}}
}
namespace Sunward{public static class HomeLayout{public static UnityEngine.Vector3 Bed=>UnityEngine.Vector3.zero;}}

namespace Sunward.Remaster
{public static class OriginalWeaponCatalog{public static object Find(string id)=>new object();public static bool Buy(Sunward.ProfileData p,string id)=>false;}}
