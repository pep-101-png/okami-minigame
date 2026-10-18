// Test-only numerical equivalents. Not a Unity engine or Unity API compile test.
using System;
namespace UnityEngine {
 public class MonoBehaviour {} public class TextAsset { public string text; }
 public static class JsonUtility { public static T FromJson<T>(string s)=>System.Text.Json.JsonSerializer.Deserialize<T>(s,new System.Text.Json.JsonSerializerOptions{IncludeFields=true}); }
 public struct Vector2 { public float x,y; public Vector2(float a,float b){x=a;y=b;} public float sqrMagnitude=>x*x+y*y; }
 public record struct Vector3Int(int x,int y,int z);
 public struct Vector3 {
 public float x,y,z;public Vector3(float a,float b,float c){x=a;y=b;z=c;}
 public static Vector3 zero=>new(0,0,0); public static Vector3 right=>new(1,0,0); public static Vector3 left=>new(-1,0,0);public static Vector3 forward=>new(0,0,1);public static Vector3 back=>new(0,0,-1);
 public float sqrMagnitude=>x*x+y*y+z*z; public float magnitude=>MathF.Sqrt(sqrMagnitude);
 public static Vector3 operator+(Vector3 a,Vector3 b)=>new(a.x+b.x,a.y+b.y,a.z+b.z);public static Vector3 operator-(Vector3 a,Vector3 b)=>new(a.x-b.x,a.y-b.y,a.z-b.z);
 public static Vector3 operator*(Vector3 a,float b)=>new(a.x*b,a.y*b,a.z*b);public static Vector3 Lerp(Vector3 a,Vector3 b,float t)=>a+(b-a)*Math.Clamp(t,0,1);public static float Distance(Vector3 a,Vector3 b)=>(a-b).magnitude;
 }
 public struct Bounds { public Vector3 min,max;public Bounds(Vector3 c,Vector3 size){min=c-size*.5f;max=c+size*.5f;}public Vector3 center=>(min+max)*.5f; public Vector3 size=>max-min;public void Encapsulate(Vector3 v){min=new(MathF.Min(min.x,v.x),MathF.Min(min.y,v.y),MathF.Min(min.z,v.z));max=new(MathF.Max(max.x,v.x),MathF.Max(max.y,v.y),MathF.Max(max.z,v.z));}}
 public static class Mathf {
 public const float PI=MathF.PI;public static float Sin(float x)=>MathF.Sin(x);public static float Cos(float x)=>MathF.Cos(x);public static float Pow(float x,float y)=>MathF.Pow(x,y);public static float Exp(float x)=>MathF.Exp(x);public static float Abs(float x)=>MathF.Abs(x);public static float Max(float x,float y)=>MathF.Max(x,y);public static int Max(int x,int y)=>Math.Max(x,y);public static float Min(float x,float y)=>MathF.Min(x,y);public static int CeilToInt(float x)=>(int)MathF.Ceiling(x);public static int RoundToInt(float x)=>(int)MathF.Round(x);public static float Clamp(float x,float lo,float hi)=>Math.Clamp(x,lo,hi);public static float Clamp01(float x)=>Math.Clamp(x,0,1);public static float Lerp(float a,float b,float t)=>a+(b-a)*Clamp01(t);
 }
}
