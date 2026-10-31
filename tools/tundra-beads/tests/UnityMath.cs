// Test doubles for data loading and math only. This is NOT a Unity engine build.
using System;
using System.IO;
using N=System.Numerics;
namespace UnityEngine
{
    public class Object {public static implicit operator bool(Object o)=>o!=null;public static T Instantiate<T>(T o)where T:Object=>(T)o.MemberwiseClone();}
    public class ScriptableObject:Object{}
    public class GameObject:Object{public SkinnedMeshRenderer[] renderers;public void SetActive(bool b){}public T[] GetComponentsInChildren<T>(bool b)=>Array.ConvertAll(renderers,r=>(T)(object)r);}
    [AttributeUsage(AttributeTargets.Class)]public sealed class CreateAssetMenuAttribute:Attribute {public string menuName;}
    public sealed class TextAsset:Object {public byte[] bytes;}
    public static class Resources
    {
        public static string Root;
        public static T Load<T>(string path) where T:class
        {
            foreach(var dir in Directory.EnumerateDirectories(Root,"Resources",SearchOption.AllDirectories))
            {var p=Path.Combine(dir,path+".bytes");if(File.Exists(p))return new TextAsset{bytes=File.ReadAllBytes(p)} as T;}
            return null;
        }
    }
    public struct Vector3
    {
        public float x,y,z;public Vector3(float a,float b,float c){x=a;y=b;z=c;}
        public static Vector3 zero=>new Vector3(0,0,0);public static Vector3 one=>new Vector3(1,1,1);
        public static Vector3 Lerp(Vector3 a,Vector3 b,float t)=>new Vector3(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t,a.z+(b.z-a.z)*t);
    }
    public struct Quaternion
    {
        public static Quaternion identity=>new Quaternion(0,0,0,1);
        public float x,y,z,w;public Quaternion(float a,float b,float c,float d){x=a;y=b;z=c;w=d;}
        public static Quaternion Slerp(Quaternion a,Quaternion b,float t)
        {var q=N.Quaternion.Slerp(new N.Quaternion(a.x,a.y,a.z,a.w),new N.Quaternion(b.x,b.y,b.z,b.w),t);return new Quaternion(q.X,q.Y,q.Z,q.W);}
    }
    public sealed class Transform {public Vector3 localPosition,localScale;public Quaternion localRotation;public Vector3 TransformPoint(Vector3 p){var v=N.Vector3.Transform(new N.Vector3(p.x*localScale.x,p.y*localScale.y,p.z*localScale.z),new N.Quaternion(localRotation.x,localRotation.y,localRotation.z,localRotation.w));return new Vector3(localPosition.x+v.X,localPosition.y+v.Y,localPosition.z+v.Z);}}
    public static class Mathf
    {public static float SmoothStep(float a,float b,float t){t=Clamp01(t);return a+(b-a)*t*t*(3-2*t);}
    public static int Max(int a,int b)=>Math.Max(a,b);public static float Clamp01(float x)=>Math.Max(0,Math.Min(1,x));public static float Repeat(float t,float n)=>t-MathF.Floor(t/n)*n;public static int FloorToInt(float x)=>(int)MathF.Floor(x);public static int Min(int a,int b)=>Math.Min(a,b);}
}
namespace Sunward {public sealed class ProfileData {public string[] owned;public string equipped;public int coins;}}
