// Opt-in lifecycle stand-in: exercises Unity's immediate Awake-on-active-add
// ordering. It is not a Unity Editor or Play Mode test.
using System.Collections.Generic;
using System.Reflection;
using Sunward.Remaster;
using UnityEngine;
static class StreetActorLifecycle
{
 public static bool Enabled;
 static readonly HashSet<OriginalActor> awakened=new HashSet<OriginalActor>();
 static void Awake(OriginalActor actor)
 {if(Enabled && actor!=null && awakened.Add(actor))typeof(OriginalActor).GetMethod("Awake",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(actor,null);}
 public static void Added(object component,bool active){if(active && component is OriginalActor actor)Awake(actor);}
 public static void Activated(GameObject go){if(Enabled)Awake(go.GetComponent<OriginalActor>());}
}
