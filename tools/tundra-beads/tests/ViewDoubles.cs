using System;
using System.Linq;
using UnityEngine;
namespace UnityEngine
{
    [AttributeUsage(AttributeTargets.Class)]public sealed class DefaultExecutionOrder:Attribute{public DefaultExecutionOrder(int n){}}
    public class MonoBehaviour:Object
    {
        public Transform transform=new Transform();
        public static Sunward.WolfCombat Combat;
        public T GetComponentInParent<T>()where T:class=>Combat as T;
    }
    public struct Bounds{public Bounds(Vector3 p,Vector3 size){}}
    public sealed class Mesh{public string name;}
    public sealed class SkinnedMeshRenderer:Object
    {public bool enabled=true,updateWhenOffscreen;public Bounds localBounds;public Mesh sharedMesh;}
    public static class Time{public static float deltaTime=1f/60;}
}
namespace Sunward
{
    public sealed class GameFlow:UnityEngine.Object {public bool Blocked;}
    public sealed class WolfCombat:UnityEngine.Object
    {
        public GameFlow game=new GameFlow();public int callbacks,lastCount;
        public void TundraBeadContacts(Vector3[] points,int count){callbacks++;lastCount=count;}
    }
}
namespace Sunward.Remaster
{
    public sealed class NativePaintedRig:IDisposable
    {
        public static NativePaintedRig Last;
        public readonly GameObject Root=new GameObject();public readonly Transform[] Bones;
        public NativePaintedRig(string resource,Transform parent)
        {
            int count=new NativePoseBank(resource+"/Poses").BoneCount;
            Bones=Enumerable.Range(0,count).Select(_=>new Transform{localScale=Vector3.one,localRotation=new Quaternion(0,0,0,1)}).ToArray();
            Root.renderers=Enumerable.Range(1,4).Select(i=>new SkinnedMeshRenderer{sharedMesh=new Mesh{name="Native-"+i+"-0"}}).ToArray();Last=this;
        }
        public void Dispose(){}
    }
}
