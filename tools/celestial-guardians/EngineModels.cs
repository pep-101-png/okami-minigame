// Engine API doubles for original hierarchy sampling; not Unity physics/rendering.
namespace UnityEngine
{
 static class GuardianEngine
 {
  public static GameObject Clone(GameObject source,Transform parent)
  {
   var copy=new GameObject(source.name);copy.transform.SetParent(parent,false);
   var actor=source.GetComponent<Sunward.Remaster.OriginalActor>();
   if(actor!=null)
   {
    var next=copy.AddComponent<Sunward.Remaster.OriginalActor>();foreach(var f in typeof(Sunward.Remaster.OriginalActor).GetFields(System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.DeclaredOnly))f.SetValue(next,f.GetValue(actor));
    typeof(Sunward.Remaster.OriginalActor).GetMethod("Awake",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).Invoke(next,null);
   }
   foreach(var child in GameObject.created.ToArray())if(System.Object.ReferenceEquals(child.transform.parent,source.transform))Clone(child,copy.transform);
   return copy;
  }
 }
}
namespace Sunward.Remaster
{
 using UnityEngine;
 public sealed class NativePaintedRig:System.IDisposable
 {
  public string Resource;public GameObject Root=new GameObject();public Transform[] Bones;
  public NativePaintedRig(string resource,Transform parent)
  {
   Resource=resource;Root.transform.SetParent(parent,false);using var doc=System.Text.Json.JsonDocument.Parse(Resources.Load<TextAsset>(resource+"/Model").text);var j=doc.RootElement;var b=j.GetProperty("bones");Bones=new Transform[b.GetArrayLength()+1];Bones[0]=new GameObject().transform;Bones[0].SetParent(Root.transform,false);
   for(int i=0;i<b.GetArrayLength();i++){var t=new GameObject().transform;Bones[i+1]=t;t.SetParent(Bones[b[i].GetProperty("parent").GetInt32()+1],false);var p=b[i].GetProperty("position");t.localPosition=new Vector3(p[0].GetSingle(),p[1].GetSingle(),p[2].GetSingle());}
   var selected=j.TryGetProperty("visibleGroups",out var visible)?visible.EnumerateArray().Select(x=>x.GetInt32()).ToArray():j.GetProperty("parts").EnumerateArray().Select(x=>int.Parse(x.GetProperty("name").GetString().Split('-')[1])).Distinct().ToArray();
   Root.renderers=j.GetProperty("parts").EnumerateArray().Where(x=>selected.Contains(int.Parse(x.GetProperty("name").GetString().Split('-')[1]))).Select(x=>new SkinnedMeshRenderer{enabled=true,sharedMaterial=new Material((Material)null),sharedMesh=new Mesh{name=x.GetProperty("name").GetString(),vertexCount=x.GetProperty("positions").GetArrayLength()/3}}).ToArray();
  }
  public void Dispose(){}
 }
}
