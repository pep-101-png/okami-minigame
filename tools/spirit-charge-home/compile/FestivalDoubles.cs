namespace UnityEngine
{
 public struct Vector4{public float x,y,z,w;public Vector4(float a,float b,float c,float d){x=a;y=b;z=c;w=d;}}
 public static class RenderSettings{public static Light sun;public static Color fogColor,ambientLight;}
 public static class Shader{public static void SetGlobalTexture(string name,Texture2D texture){}public static void SetGlobalFloat(string name,float value){}public static void SetGlobalVectorArray(string name,Vector4[] value){}}
}
namespace Sunward{public static class HomeLayout{public static UnityEngine.Vector3 Bed=>new UnityEngine.Vector3(-37.36f,-249.82f,-14.08f);public static UnityEngine.Vector3 Mirror=>new UnityEngine.Vector3(-28.4f,-249.88f,-13.12f);}}

namespace Sunward.Remaster
{public static class OriginalWeaponCatalog{public static object Find(string id)=>new object();public static bool Buy(Sunward.ProfileData p,string id)=>false;}}
namespace UnityEngine
{
 public sealed class Rigidbody:Object{public bool isKinematic;public Vector3 position;}
 public struct Vector2Int{public int x,y;public Vector2Int(int a,int b){x=a;y=b;}public static Vector2Int left=>new Vector2Int(-1,0);public static Vector2Int right=>new Vector2Int(1,0);public static Vector2Int up=>new Vector2Int(0,1);public static Vector2Int down=>new Vector2Int(0,-1);}
}
namespace Sunward
{
 public static class VillageNavigation
 {public static bool Clear(Valley.ValleyData data,UnityEngine.Vector3 p,float r)=>true;public static bool SegmentClear(Valley.ValleyData data,UnityEngine.Vector3 a,UnityEngine.Vector3 b,float r)=>true;public static bool FindSafe(Valley.ValleyData data,UnityEngine.Vector3 p,out UnityEngine.Vector3 goal,float radius,float distance){goal=p;return true;}}
}

namespace Sunward.Remaster{public sealed class OriginalBillboard:UnityEngine.Object{}}
